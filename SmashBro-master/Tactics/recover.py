import melee
import Chains
import random
import math
from melee.enums import Action
from Tactics.punish import Punish
from Tactics.tactic import Tactic
from Chains.firefox import FIREFOX
from Chains.illusion import SHORTEN

class Recover(Tactic):
    # Do we need to recover?
    def needsrecovery(smashbro_state, opponent_state, gamestate):
        onedge = smashbro_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]
        opponentonedge = opponent_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING, Action.EDGE_GETUP_SLOW, \
        Action.EDGE_GETUP_QUICK, Action.EDGE_ATTACK_SLOW, Action.EDGE_ATTACK_QUICK, Action.EDGE_ROLL_SLOW, Action.EDGE_ROLL_QUICK]

        # If the opponent is on-stage, and Smashbro is on-edge, Smashbro needs to ledgedash
        if not opponent_state.off_stage and onedge:
            return True

        # If we're on stage, then we don't need to recover
        if not smashbro_state.off_stage:
            return False

        if smashbro_state.on_ground:
            return False

        # We can now assume that we're off the stage...

        # If opponent is dead
        if opponent_state.action in [Action.DEAD_DOWN, Action.DEAD_RIGHT, Action.DEAD_LEFT, \
                Action.DEAD_FLY, Action.DEAD_FLY_STAR, Action.DEAD_FLY_SPLATTER]:
            return True

        # If opponent is on stage
        if not opponent_state.off_stage:
            return True

        # If opponent is in hitstun, then recover, unless we're on the edge.
        if opponent_state.off_stage and opponent_state.hitstun_frames_left > 0 and not onedge:
            return True

        if opponent_state.action == Action.DEAD_FALL and opponent_state.position.y < -30:
            return True

        # If opponent is closer to the edge, recover
        diff_x_opponent = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(opponent_state.position.x))
        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x))

        # Using (opponent_state.position.y + 15)**2 was causing a keepdistance/dashdance bug.
        opponent_dist = math.sqrt( (opponent_state.position.y)**2 + (diff_x_opponent)**2 )
        smashbro_dist = math.sqrt( (smashbro_state.position.y)**2 + (diff_x)**2 )

        if opponent_dist < smashbro_dist and not onedge:
            return True

        if smashbro_dist >= 20:
            return True

        # If we're both fully off stage, recover
        if opponent_state.off_stage and smashbro_state.off_stage and not onedge and not opponentonedge:
            return True

        # If opponent is ON the edge, recover
        if opponentonedge and not onedge:
            return True

        if -100 < smashbro_state.position.y < -50:
            return True

        return False

    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        # We need to decide how we want to recover
        self.useillusion = bool(random.randint(0, 1))
        self.logger = logger

    def step(self, gamestate, smashbro_state, opponent_state):
        self._propagate  = (gamestate, smashbro_state, opponent_state)

        opponentonedge = opponent_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING, Action.EDGE_GETUP_SLOW, \
        Action.EDGE_GETUP_QUICK, Action.EDGE_ATTACK_SLOW, Action.EDGE_ATTACK_QUICK, Action.EDGE_ROLL_SLOW, Action.EDGE_ROLL_QUICK]

        # If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbro_state, opponent_state)
            return

        if smashbro_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]:
            # It takes 16 frames to go from frame 1 of hanging to standing.
            frames_left = Punish.framesleft(opponent_state, self.framedata, smashbro_state)
            refresh = frames_left < 16 and smashbro_state.invulnerability_left < 16
            self.pickchain(Chains.Edgedash, [refresh])
            # print("ledge caught, coordinates:", smashbro_state.position.x, smashbro_state.position.y)
            return

        # If we can't possibly illusion to recover, don't try
        if smashbro_state.position.y < -15 and smashbro_state.jumps_left == 0 and smashbro_state.speed_y_self < 0:
            self.useillusion = False

        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x))

        # If we can just grab the edge with a firefox, do that
        facinginwards = smashbro_state.facing == (smashbro_state.position.x < 0)
        if not facinginwards and smashbro_state.action == Action.TURNING and smashbro_state.action_frame == 1:
            facinginwards = True

        if smashbro_state.action == Action.DEAD_FALL:
            self.chain = None
            self.pickchain(Chains.DI, [int(smashbro_state.position.x < 0), 0.5])
            return

        # FireFox high
        if smashbro_state.action == Action.SWORD_DANCE_1_AIR and smashbro_state.position.y > 10:
            self.chain = None
            self.pickchain(Chains.DI, [int(smashbro_state.position.x < 0), 0.5])
            return

        # Are we facing the wrong way in shine? Turn around
        if smashbro_state.action == Action.DOWN_B_STUN and not facinginwards:
            x = 0
            if smashbro_state.position.x < 0:
                x = 1
            self.chain = None
            self.pickchain(Chains.DI, [x, 0.5])
            return

        # If we can just do nothing and grab the edge, do that
        # Action.SWORD_DANCE_1_AIR is Fox's initial freefall after his upB finishes launching.
        # Fox can ledgegrab from behind in this animation, but he oftentimes needs to fastfall to hit the window.
        if -12 < smashbro_state.position.y and (diff_x < 10) and (facinginwards or smashbro_state.action == Action.SWORD_DANCE_1_AIR) and smashbro_state.speed_y_self <= 0:
            # Do a Fastfall if we're not already
            if smashbro_state.action == Action.FALLING and smashbro_state.speed_y_self > -3.3:
                self.chain = None
                self.pickchain(Chains.DI, [0.5, 0])
                return

            # If we are currently moving away from the stage, DI in
            if (smashbro_state.speed_air_x_self > 0) == (smashbro_state.position.x > 0):
                x = 0
                if smashbro_state.position.x < 0:
                    x = 1
                self.chain = None
                self.pickchain(Chains.DI, [x, 0.5])
                return
            else:
                self.pickchain(Chains.Nothing)
                return

        # look out for edgehogs
        opponent_edgedistance = abs(opponent_state.position.x) - abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
        opponentfacinginwards = opponent_state.facing == (opponent_state.position.x < 0)
        if not opponentfacinginwards and opponent_state.action == Action.TURNING and opponent_state.action_frame == 1:
            opponentfacinginwards = True
        opponentpotentialedgehog = False
        if opponentfacinginwards and opponent_edgedistance < 45 and -30 < opponent_state.position.y < 30:
            opponentpotentialedgehog = True

        # If we're lined up, do the illusion
        # 88 is a little longer than the illusion max length
        # Also, we have to adjust the min illusion height upwards on BF
        min_height = -16.4
        if gamestate.stage == melee.enums.Stage.BATTLEFIELD:
            min_height = -10
        illusion_rng = random.randint(0, 3)
        if self.useillusion and (min_height < smashbro_state.position.y < -5) and (10 < diff_x < 88) \
                and not opponentonedge and (not opponentpotentialedgehog or illusion_rng == 0):
            length = SHORTEN.LONG
            if diff_x < 50:
                length = SHORTEN.MID
            if diff_x < 40:
                length = SHORTEN.MID_SHORT
            if diff_x < 31:
                length = SHORTEN.SHORT

            self.pickchain(Chains.Illusion, [length])
            return

        # If we illusion at this range when the opponent is holding ledge, Smashbro dies.
        # Firefox instead if the opponent is grabbing edge. Opponent has to get up or get burned.
        if (-16.4 < smashbro_state.position.y < -5) and (diff_x < 10) and facinginwards:
            if gamestate.stage == melee.enums.Stage.BATTLEFIELD:
                # If Smashbro does a random or horizontal sideB here, he pretty reliably SDs on Battlefield
                self.pickchain(Chains.Firefox, [FIREFOX.EDGE])
            else:
                self.pickchain(Chains.Firefox, [FIREFOX.RANDOM])
            return

        # Is the opponent going offstage to edgeguard us?
        opponent_edgedistance = abs(opponent_state.position.x) - abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
        opponentxvelocity = opponent_state.speed_air_x_self + opponent_state.speed_ground_x_self
        opponentmovingtoedge = not opponent_state.off_stage and (opponent_edgedistance < 20) and (opponentxvelocity > 0 == opponent_state.position.x > 0)
        opponentgoingoffstage = opponent_state.action in [Action.FALLING, Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD, Action.LANDING_SPECIAL,\
            Action.DASHING, Action.WALK_MIDDLE, Action.WALK_FAST, Action.NAIR, Action.FAIR, Action.UAIR, Action.BAIR, Action.DAIR]

        # Don't airdodge recovery if we still have attack velocity. It just causes an SD
        hit_movement = abs(smashbro_state.speed_x_attack) > 0.2

        # airdodge x-distance shortened from 18, y-distance shortened from 24 to be safer
        # airdodge length max 20.5x, 24y
        # 45 degree 16x, 16y
        x_canairdodge = abs(smashbro_state.position.x) - 16 <= abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage])
        y_canairdodge = smashbro_state.position.y >= -16
        if x_canairdodge and y_canairdodge and (opponentgoingoffstage or opponentmovingtoedge) and not hit_movement:
            corner_x, corner_y = melee.stages.EDGE_POSITION[gamestate.stage], 0
            diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x))
            diff_y = abs(smashbro_state.position.y + smashbro_state.ecb.bottom.y + 5)
            diff_x = (max(0, 100 ** 2 - diff_y ** 2)) ** 0.5
            larger_magnitude = max(diff_x, diff_y)
            x = diff_x / larger_magnitude
            y = diff_y / larger_magnitude
            if smashbro_state.position.x < 0:
                x = 0.5 + (x / 4) * (7 / 5)
                corner_x *= -1
            else:
                x = 0.5 - (x / 4) * (7 / 5)
            if smashbro_state.position.y < 0:
                y = 0.5 + (y / 4) * (7 / 5)
            else:
                y = 0.5 - (y / 4) * (7 / 5)
            self.pickchain(Chains.Airdodge, [x, y])
            #self.pickchain(Chains.Airdodge, [int(smashbro_state.position.x < 0), int(smashbro_state.position.y + smashbro_state.ecb.bottom.y < 5)])
            if smashbro_state.action_frame == 1:
                print('recovery airdodge:', round(x ,3), round(y, 3))
            return

        # Jump if we're falling, are below stage, and have a jump
        if smashbro_state.speed_y_self < 0 and smashbro_state.jumps_left > 0 and smashbro_state.position.y < 0:
            self.pickchain(Chains.Jump)
            return

        # First jump back to the stage if we're low
        # Fox can at least DJ from y = -55.43 and still sweetspot grab the ledge.
        # For reference, if Fox inputs a DJ at y = -58.83, he will NOT sweetspot grab the ledge.
        jump_randomizer = random.randint(0, 5) == 1

        if smashbro_state.jumps_left > 0 and (smashbro_state.position.y < -52 or opponentgoingoffstage or opponentmovingtoedge or jump_randomizer):
            self.pickchain(Chains.Jump)
            return

        elif smashbro_state.jumps_left > 0 and \
                abs(smashbro_state.position.x) - 100 <= abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage]):
            self.pickchain(Chains.Jump)
            return

        # Always just jump out of shine
        if smashbro_state.action == Action.DOWN_B_AIR:
            self.pickchain(Chains.Jump)
            return

        # If we're high and doing an Illusion, just let ourselves fall into place
        if self.useillusion and smashbro_state.position.y > -5:
            # DI into the stage
            x = 0
            if smashbro_state.position.x < 0:
                x = 1
            self.chain = None
            self.pickchain(Chains.DI, [x, 0.5])
            return

        # The height to start a firefox at
        firefox_height = -60 + random.randint(0, 30)

        # If opponent is in hitstun, just do it now
        if opponent_state.hitstun_frames_left > 0:
            firefox_height = 100

        # Don't firefox if we're super high up, wait a little to come down
        if smashbro_state.speed_y_self < 0 and smashbro_state.position.y < firefox_height:
            if gamestate.stage == melee.enums.Stage.BATTLEFIELD and diff_x < 30:
                # firefox toward edge if underneath battlefield
                self.pickchain(Chains.Firefox, [FIREFOX.EDGE])
            else:
                firefox_rng = random.randint(0, 4)

                if smashbro_state.position.y > 0:
                    if 0 < opponent_state.position.y < 15 \
                            and abs(abs(opponent_state.position.x) - melee.stages.EDGE_GROUND_POSITION[gamestate.stage]) < 15:
                        self.pickchain(Chains.Firefox, [FIREFOX.RANDOM])
                        return
                    else:
                        self.pickchain(Chains.Firefox, [FIREFOX.EDGE])
                        return
                else:
                    if smashbro_state.action_frame == 42:
                        print("opponent x distance:", round(abs(abs(opponent_state.position.x) - melee.stages.EDGE_GROUND_POSITION[gamestate.stage]), 2))
                    if opponentpotentialedgehog:  # and firefox_rng > 0:
                        self.pickchain(Chains.Firefox, [FIREFOX.HIGH])
                        if smashbro_state.action_frame == 42:
                            print("firefox high")
                        return
                    if not opponent_state.on_ground and smashbro_state.percent < 50:
                        self.pickchain(Chains.Firefox, [FIREFOX.HIGH])
                        if smashbro_state.action_frame == 42:
                            print("firefox high")
                        return
                    else:
                        self.pickchain(Chains.Firefox, [FIREFOX.EDGE])
                        if smashbro_state.action_frame == 42:
                            print("edge catch-all")
                        return
            return

        randomhighrecovery = smashbro_state.position.y > 0 and random.randint(0, 3) == 1
        if randomhighrecovery:
            print("random high recovery")
            if bool(random.randint(0, 1)) and abs(smashbro_state.position.x) - 70 <= abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage]):
                self.pickchain(Chains.Firefox, [FIREFOX.RANDOM])
            elif abs(smashbro_state.position.x) - 88 <= abs(melee.stages.EDGE_GROUND_POSITION[gamestate.stage]):
                self.pickchain(Chains.Illusion, [SHORTEN.LONG])
            else:
                self.pickchain(Chains.Firefox, [FIREFOX.SAFERANDOM])
            return

        # DI into the stage
        battlefielded = (smashbro_state.position.x < melee.stages.EDGE_POSITION[gamestate.stage] + 13) and gamestate.stage == melee.enums.Stage.BATTLEFIELD and smashbro_state.position.y < 0
        if not battlefielded:
            x = 0
            if smashbro_state.position.x < 0:
                x = 1
            self.chain = None
            self.pickchain(Chains.DI, [x, 0.5])
