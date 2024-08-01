import melee
import Chains
import random
from melee.enums import Action, Button, Character
from Tactics.tactic import Tactic
from Tactics.punish import Punish
from Chains.shffl import SHFFL_DIRECTION

class Approach(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        self.random_approach = random.randint(0, 100)

    def shouldapproach(smashbro_state, opponent_state, gamestate, framedata, logger):
        if len(gamestate.projectiles) > 0:
            return False
        # Specify that this needs to be platform approach
        framesleft = Punish.framesleft(opponent_state, framedata, smashbro_state)
        if logger:
            logger.log("Notes", " framesleft: " + str(framesleft) + " ", concat=True)
        if framesleft >= 9:
            return True
        return False

    def approach_too_dangerous(smashbro_state, opponent_state, gamestate, framedata):
        # TODO Do we actually care about this projectile?
        if len(gamestate.projectiles) > 0:
            return True
        if framedata.is_attack(opponent_state.character, opponent_state.action):
            return True
        return False

    def step(self, gamestate, smashbro_state, opponent_state):
        self._propagate  = (gamestate, smashbro_state, opponent_state)
        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbro_state, opponent_state)
            return

        # They're fishing for grabs by the ledge, bait them away
        if gamestate.custom["grab_cheese_count"] > 2 and abs(
                melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(opponent_state.position.x)) < 15:
            # Get into position away from the edge.
            pivotpoint = 0

            if abs(smashbro_state.position.x - pivotpoint) > 5:
                self.chain = None
                self.pickchain(Chains.DashDance, [pivotpoint])
                return
            elif len(gamestate.projectiles) == 0:
                self.pickchain(Chains.Laser)
            return

        needswavedash = smashbro_state.action in [Action.DOWN_B_GROUND, Action.DOWN_B_STUN, \
            Action.DOWN_B_GROUND_START, Action.LANDING_SPECIAL, Action.SHIELD, Action.SHIELD_START, \
            Action.SHIELD_RELEASE, Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        if needswavedash:
            self.pickchain(Chains.Wavedash, [True])
            return

        # Are we behind in the game?
        losing = smashbro_state.stock < opponent_state.stock or (smashbro_state.stock == opponent_state.stock and smashbro_state.percent > opponent_state.percent)
        opp_top_platform = False
        top_platform_height, top_platform_left, top_platform_right = melee.top_platform_position(gamestate.stage)
        if top_platform_height is not None:
            opp_top_platform = (opponent_state.position.y+1 >= top_platform_height) and (top_platform_left-1 < opponent_state.position.x < top_platform_right+1)

        # If opponent is on a side platform and we're not
        on_main_platform = smashbro_state.position.y < 1 and smashbro_state.on_ground
        if not opp_top_platform:
            if opponent_state.position.y > 10 and opponent_state.on_ground and on_main_platform:
                self.pickchain(Chains.BoardSidePlatform, [opponent_state.position.x > 0])
                return

        # if opponent is lying or teching on top platform, board it
        if opp_top_platform and opponent_state.action in \
                [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN, Action.BACKWARD_TECH, Action.TECH_MISS_DOWN,
                 Action.TECH_MISS_UP, Action.NEUTRAL_TECH, Action.GROUND_ROLL_BACKWARD_UP, Action.GROUND_ROLL_BACKWARD_DOWN]:
            self.pickchain(Chains.BoardTopPlatform)
            return

        if top_platform_height is not None:
            if abs(opponent_state.position.x) < 20 and opponent_state.position.y >= top_platform_height + 15:
                self.pickchain(Chains.BoardTopPlatform)
                return

        # If opponent is on top platform. Unless we're ahead. Then let them camp
        if opp_top_platform and losing and random.randint(0, 20) == 0:
            self.pickchain(Chains.BoardTopPlatform)
            return

        # Jump over Samus Bomb
        # TODO Don't jump on top of an existing bomb
        samus_bomb = opponent_state.character == Character.SAMUS and opponent_state.action == Action.SWORD_DANCE_4_MID
        if samus_bomb and opponent_state.position.y < 5:
            landing_spot = opponent_state.position.x
            if opponent_state.position.x < smashbro_state.position.x:
                landing_spot -= 10
            else:
                landing_spot += 10

            # Don't jump off the stage
            if abs(landing_spot) < melee.stages.EDGE_GROUND_POSITION[gamestate.stage]:
                self.pickchain(Chains.JumpOver, [landing_spot])
                return

        # SHFFL at opponent sometimes (33% chance per approach)
        if self.random_approach < 33:
            if not self.framedata.is_attack(opponent_state.character, opponent_state.action):
                # We need to be dashing towards our opponent. Not too close to the ledge (35 > 50)
                vertical_distance = abs(smashbro_state.position.y - opponent_state.position.y)
                facing_opponent = smashbro_state.facing == (smashbro_state.position.x < opponent_state.position.x)
                if smashbro_state.action == Action.DASHING and facing_opponent:
                    if vertical_distance < 20 and gamestate.distance < 35 and \
                            abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbro_state.position.x)) \
                            > 50:
                        if opponent_state.action in [Action.CROUCHING, Action.CROUCH_START, Action.CROUCH_END]:
                            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.DOWN])
                            print('approaching dair')
                            return
                        else:
                            self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.NEUTRAL])
                            print("approaching nair")
                            return

        self.chain = None
        self.pickchain(Chains.DashDance, [opponent_state.position.x])
