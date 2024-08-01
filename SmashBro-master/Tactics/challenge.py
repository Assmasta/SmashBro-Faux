import melee
import Chains
import random
from melee.enums import Action, Character, Stage
from Tactics.tactic import Tactic
from Tactics.punish import Punish
from Chains.smashattack import SMASH_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.tilt import TILT_DIRECTION
from Chains.airattack import AirAttack, AIR_ATTACK_DIRECTION

class Challenge(Tactic):
    """Challenge is for when we throw out a hitbox to beat out (challenge) an opponent's attack

    This comes with some risk of the hitboxes not lining up right. Since it's not purely timing based.

    But Punish won't work here, since opponent is not in a lag state
    """
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        self.keep_running = False

    def canchallenge(smashbro_state, opponent_state, gamestate, framedata, difficulty):
        if opponent_state.invulnerability_left > 0:
            return False

        # If we're ahead and opponent is on a platform, don't challenge.
        losing = smashbro_state.stock < opponent_state.stock or (smashbro_state.stock == opponent_state.stock and smashbro_state.percent > opponent_state.percent)
        if not losing and opponent_state.on_ground and opponent_state.position.y > 10:
            return False

        # Rapid jabs
        if opponent_state.action == Action.LOOPING_ATTACK_MIDDLE:
            return True
        if opponent_state.character == Character.PIKACHU and opponent_state.action == Action.NEUTRAL_ATTACK_1:
            return True
        if opponent_state.character == Character.MARTH and opponent_state.action in [Action.NEUTRAL_ATTACK_1, Action.NEUTRAL_ATTACK_2]:
            return True

        # Falling spacies
        if opponent_state.character in [Character.FOX, Character.FALCO]:
            if not opponent_state.on_ground and opponent_state.speed_y_self < 0:
                return True

        # laser taken
        if gamestate.custom["laser_taken"]:
            return True

        # if opponent is within sharking distance
        # if 27 < abs(smashbro_state.position.y - opponent_state.position.y) < 40 and smashbro_state.on_ground and\
        #         abs(smashbro_state.position.x - opponent_state.position.x) < 20 and opponent_state.speed_y_self < 0 and \
        #         not opponent_state.on_ground:
        #     print('sharking time')
        #     return True

        return False

    def step(self, gamestate, smashbro_state, opponent_state):
        self._propagate  = (gamestate, smashbro_state, opponent_state)

        # If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbro_state, opponent_state)
            return

        # If we chose to run, keep running
        if type(self.chain) == Chains.Run and self.keep_running:
            self.pickchain(Chains.Run, [opponent_state.position.x > smashbro_state.position.x])
            return

        edge = melee.stages.EDGE_GROUND_POSITION[gamestate.stage]

        # mark opponents as light/heavy and fast-faller/floaty
        if opponent_state.character in [Character.FOX, Character.FALCO, Character.PIKACHU, Character.JIGGLYPUFF]:
            light = True
            heavy = False
        else:
            light = False
            heavy = True

        if opponent_state.character in [Character.FOX, Character.FALCO, Character.CPTFALCON]:
            fastfaller = True
            floaty = False
        else:
            fastfaller = False
            floaty = True

        # Dash dance up to the correct spacing
        pivotpoint = opponent_state.position.x
        bufferzone = 30
        if opponent_state.character == Character.FALCO:
            bufferzone = 40
        if opponent_state.character == Character.CPTFALCON:
            bufferzone = 35
        if opponent_state.character == Character.MARTH:
            bufferzone = 40
        if opponent_state.character == Character.SHEIK:
            bufferzone = 38
        if opponent_state.position.x > smashbro_state.position.x:
            bufferzone *= -1

        side_plat_height, side_plat_left, side_plat_right = melee.side_platform_position(opponent_state.position.x > 0, gamestate.stage)
        on_side_plat = False
        if side_plat_height is not None:
            on_side_plat = opponent_state.on_ground and abs(opponent_state.position.y - side_plat_height) < 5

        if on_side_plat:
            bufferzone = 0

        # Falling spacies
        falling_spacie = False
        if opponent_state.character in [Character.FOX, Character.FALCO]:
            if not opponent_state.on_ground and opponent_state.speed_y_self < 0:
                bufferzone = 0
                falling_spacie = True

        pivotpoint += bufferzone

        # Don't run off the stage though, adjust this back inwards a little if it's off
        edgebuffer = 10
        pivotpoint = min(pivotpoint, edge - edgebuffer)
        pivotpoint = max(pivotpoint, (-edge) + edgebuffer)

        if self.logger:
            self.logger.log("Notes", "pivotpoint: " + str(pivotpoint) + " ", concat=True)

        if on_side_plat and abs(smashbro_state.position.x - pivotpoint) < 2 and smashbro_state.action == Action.TURNING:
            if opponent_state.action_frame < 6:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.UP])
                if smashbro_state.action_frame == 1:
                    print('challenge platform uair')
                return

        smash_now = opponent_state.action_frame < 6
        if opponent_state.character == Character.CPTFALCON:
            smash_now = opponent_state.action_frame in [4, 12, 20, 27]
        if opponent_state.character == Character.MARTH:
            smash_now = opponent_state.action_frame < 6

        spacing_grace_zone = 2
        if falling_spacie:
            spacing_grace_zone = 8

        laser_taken = gamestate.custom["laser_taken"]
        if laser_taken > 0:
            if gamestate.distance < 10:
                self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.UP])
                if smashbro_state.action_frame == 1:
                    print('laser taken, uair attempted')
                return
            # to add full hop intercept approaches
            elif abs(opponent_state.speed_air_x_self) > 1.2 and not opponent_state.on_ground:
                self.pickchain(Chains.AirAttack, [0, 0, 2, AIR_ATTACK_DIRECTION.NEUTRAL])
                if smashbro_state.action_frame == 1:
                    print('laser taken, full hop nair intercept attempted')
                return
            else:
                radius = 4
                self.pickchain(Chains.DashDance, [pivotpoint, radius])
                if smashbro_state.action_frame == 1:
                    print('laser taken, dashback attempted')
                return

        # If spacing and timing is right, do a smash attack
        if abs(smashbro_state.position.x - pivotpoint) < spacing_grace_zone:
            if smashbro_state.action == Action.TURNING:
                if smash_now and not on_side_plat and not falling_spacie:
                    # For marth, it's actually more reliable to run between slashes
                    if opponent_state.character == Character.MARTH:
                        self.keep_running = True
                        self.pickchain(Chains.Run, [opponent_state.position.x > smashbro_state.position.x])
                        return

                    self.chain = None
                    if opponent_state.position.x < smashbro_state.position.x:
                        self.pickchain(Chains.SmashAttack, [0, SMASH_DIRECTION.LEFT])
                        if smashbro_state.action_frame == 1:
                            print('challenge fsmash')
                    else:
                        self.pickchain(Chains.SmashAttack, [0, SMASH_DIRECTION.RIGHT])
                        if smashbro_state.action_frame == 1:
                            print('challenge fsmash')
                    return
                if falling_spacie and abs(opponent_state.position.y - smashbro_state.position.y) < 36:
                    self.chain = None
                    if opponent_state.percent > 89:
                        if smashbro_state.action_frame == 1:
                            print('challenge bair')
                        self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.BACK])
                        return
                    elif gamestate.distance > 30:
                        if smashbro_state.action_frame == 1:
                            print('wavedash back')
                        self.pickchain(Chains.Wavedash, [True])
                        return
                    else:
                        self.pickchain(Chains.SmashAttack, [0, SMASH_DIRECTION.UP])
                        if smashbro_state.action_frame == 1:
                            print('challenge usmash')
                        return
                elif falling_spacie and abs(opponent_state.position.y - smashbro_state.position.y) < 36:
                    self.chain = None
                    return
            elif smashbro_state.action == Action.DASHING:
                self.pickchain(Chains.Run, [not smashbro_state.facing])
                return
            elif smashbro_state.action == Action.STANDING and opponent_state.percent < 50 and falling_spacie:
                self.pickchain(Chains.Tilt, [TILT_DIRECTION.UP])
                print('juggle utilt')
                return

        # sharking
        # if 27 < abs(smashbro_state.position.y - opponent_state.position.y) < 40 and smashbro_state.on_ground and \
        #         abs(smashbro_state.position.x - opponent_state.position.x) < 20 and opponent_state.speed_y_self < 0 and \
        #         not opponent_state.on_ground:
        #     print('add shark routine')
        #     return

        # If we're stuck in shield, wavedash back
        if smashbro_state.action in [Action.SHIELD_RELEASE, Action.SHIELD]:
            self.pickchain(Chains.Wavedash, [1.0, False])
            return

        # Otherwise dash dance to the pivot point
        self.pickchain(Chains.DashDance, [pivotpoint, 0, False])
