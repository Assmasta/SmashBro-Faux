import melee
import Chains
import random
from melee.enums import Action, Button, Character
from Tactics.tactic import Tactic
from Chains.firefox import FIREFOX

class Mitigate(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        self.random_di = random.randint(0, 1)

    def needsmitigation(smashbro_state):
        # Always interrupt if we got hit. Whatever chain we were in will have been broken anyway
        if smashbro_state.action in [Action.GRABBED, Action.GRAB_PUMMELED, Action.GRAB_PULL, \
                Action.GRAB_PUMMELED, Action.GRAB_PULLING_HIGH, Action.GRABBED_WAIT_HIGH, Action.PUMMELED_HIGH]:
            return True

        # teching
        if smashbro_state.action == Action.NEUTRAL_TECH and smashbro_state.action_frame == 1:
            return True

        # Thrown action
        if smashbro_state.action in [Action.THROWN_FORWARD, Action.THROWN_BACK, \
                Action.THROWN_UP, Action.THROWN_DOWN, Action.THROWN_DOWN_2]:
            return True

        if smashbro_state.hitstun_frames_left == 0:
            return False

        if Action.DAMAGE_HIGH_1.value <= smashbro_state.action.value <= Action.DAMAGE_FLY_ROLL.value:
            return True
        if smashbro_state.action == Action.TUMBLING:
            return True


        return False

    # establish wall positions
    def get_wall(self, stage):
        """Returns the (x, y1, y2) coordinates of the tech-able wall immediately below edge
           treats them all like flat walls .-.
        """
        if stage == melee.Stage.YOSHIS_STORY:
            return melee.EDGE_POSITION[stage], -1000
        if stage == melee.Stage.BATTLEFIELD:
            return melee.EDGE_POSITION[stage], -10
        if stage == melee.Stage.FINAL_DESTINATION:
            return melee.EDGE_POSITION[stage], -30
        if stage == melee.Stage.DREAMLAND:
            return melee.EDGE_POSITION[stage], -47.480972
        if stage == melee.Stage.POKEMON_STADIUM:
            return melee.EDGE_POSITION[stage], -29.224771

        return 0, 0

    def step(self, gamestate, smashbro_state, opponent_state):
        self._propagate = (gamestate, smashbro_state, opponent_state)

        # consider platforms
        top_platform_height, top_platform_left, top_platform_right = (0, 0, 0)
        left_platform_height, left_platform_left, left_platform_right = (0, 0, 0)
        right_platform_height, right_platform_left, right_platform_right = (0, 0, 0)

        if gamestate.stage in [melee.Stage.BATTLEFIELD, melee.Stage.DREAMLAND, melee.Stage.YOSHIS_STORY]:
            top_platform_height, top_platform_left, top_platform_right = melee.top_platform_position(gamestate.stage)
            left_platform_height, left_platform_left, left_platform_right = melee.left_platform_position(gamestate.stage)
            right_platform_height, right_platform_left, right_platform_right = melee.right_platform_position(gamestate.stage)

        if gamestate.stage == melee.Stage.POKEMON_STADIUM:
            left_platform_height, left_platform_left, left_platform_right = melee.left_platform_position(
                gamestate.stage)
            right_platform_height, right_platform_left, right_platform_right = melee.right_platform_position(
                gamestate.stage)

        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbro_state, opponent_state)
            return

        # Did we get grabbed?
        if smashbro_state.action in [Action.GRABBED, Action.GRAB_PUMMELED, Action.GRAB_PULL, \
                Action.GRAB_PUMMELED, Action.GRAB_PULLING_HIGH, Action.GRABBED_WAIT_HIGH, Action.PUMMELED_HIGH]:
            self.pickchain(Chains.Struggle)
            return

        # For throws, randomize the TDI
        if smashbro_state.action in [Action.THROWN_FORWARD, Action.THROWN_BACK, Action.THROWN_DOWN, Action.THROWN_DOWN_2]:
            self.chain = None
            self.pickchain(Chains.DI, [random.choice([0, 0.5, 1]), random.choice([0, 0.5, 1])])
            return
        # Up throws are a little different. Don't DI up and down
        if smashbro_state.action == Action.THROWN_UP:
            self.chain = None
            self.pickchain(Chains.DI, [random.choice([0, 0.3, 0.5, 0.7, 1]), 0.5])
            return

        # Trajectory DI
        if smashbro_state.hitlag_left == 1:
            self.pickchain(Chains.TDI)
            return

        # Smash DI
        if smashbro_state.hitlag_left > 1:
            self.pickchain(Chains.SDI)
            return

        # Tech if we need to
        if smashbro_state.action == Action.NEUTRAL_TECH and smashbro_state.action_frame == 1:
            print('>>>tech roll hopefully')
            self.controller.tilt_analog(Button.BUTTON_MAIN, 1, .5)
            return

        #   Calculate when we will land
        if smashbro_state.position.y > -4 and not smashbro_state.on_ground and \
                Action.DAMAGE_HIGH_1.value <= smashbro_state.action.value <= Action.DAMAGE_FLY_ROLL.value:
            framesuntillanding = 0
            speed = smashbro_state.speed_y_attack + smashbro_state.speed_y_self
            height = smashbro_state.position.y
            gravity = self.framedata.characterdata[smashbro_state.character]["Gravity"]
            termvelocity = self.framedata.characterdata[smashbro_state.character]["TerminalVelocity"]

            while height > 0:
                height += speed
                speed -= gravity
                speed = max(speed, -termvelocity)
                framesuntillanding += 1
                # Shortcut if we get too far
                if framesuntillanding > 120:
                    break
                # platform scenario, only works if falling onto platform
                if speed < 0:
                    if top_platform_height < smashbro_state.position.y + smashbro_state.ecb.bottom.y < (2.5 + top_platform_height) \
                            and top_platform_left < smashbro_state.position.x < top_platform_right:
                        framesuntillanding = 0
                    if left_platform_height < smashbro_state.position.y + smashbro_state.ecb.bottom.y < (2.5 + left_platform_height) \
                            and left_platform_left < smashbro_state.position.x < left_platform_right:
                        framesuntillanding = 0
                    if right_platform_height < smashbro_state.position.y + smashbro_state.ecb.bottom.y < (2.5 + right_platform_height) \
                            and right_platform_left < smashbro_state.position.x < right_platform_right:
                        framesuntillanding = 0
            # Do the tech
            if framesuntillanding < 4:
                self.pickchain(Chains.Tech)
                return

        # WallTech if we need to
        # Calculate when we will hit the wall
        wall_x_coord, wall_bottom = self.get_wall(gamestate.stage)
        if wall_bottom < smashbro_state.position.y < 4\
                and abs(smashbro_state.position.x - wall_x_coord) < 4\
                and not smashbro_state.on_ground \
                and Action.DAMAGE_HIGH_1.value <= smashbro_state.action.value <= Action.DAMAGE_FLY_ROLL.value:
            framesuntilimpact = 0
            # x_speed = abs(smashbro_state.speed_x_attack + smashbro_state.speed_x_self)
            while abs(smashbro_state.position.x - wall_x_coord) > 0:
                # Cancel if too far
                framesuntilimpact += 1
                if framesuntilimpact > 120:
                    break
            # Do the walltech
            if framesuntilimpact < 4:
                self.pickchain(Chains.WallTech)
                return

        # underside tech
        if smashbro_state.position.y < 0\
                and abs(smashbro_state.position.x) < wall_x_coord + 1\
                and not smashbro_state.on_ground \
                and Action.DAMAGE_HIGH_1.value <= smashbro_state.action.value <= Action.DAMAGE_FLY_ROLL.value:
            self.pickchain(Chains.WallTech)
            return

        # Meteor cancel 8 frames after hitlag ended
        # TODO: Don't SDI an up input if we want to meteor cancel
        if smashbro_state.speed_y_attack < 0 and smashbro_state.action_frame == 8:
            if smashbro_state.jumps_left > 0:
                if gamestate.custom["meteor_jump_lockout"] == 0:
                    self.pickchain(Chains.Jump, [int(smashbro_state.position.x < 0)])
                    return
            elif gamestate.custom["meteor_ff_lockout"] == 0:
                self.pickchain(Chains.Firefox, [FIREFOX.SAFERANDOM])
                return

        if smashbro_state.action == Action.TUMBLING:
            x = gamestate.frame % 2
            self.chain = None
            self.pickchain(Chains.DI, [x, 0.5])
            return

        # DI randomly as a fallback
        self.pickchain(Chains.DI, [self.random_di, 0.5])
        return
