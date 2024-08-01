import melee
import Chains
import random
from melee.enums import Action, Button
from Tactics.tactic import Tactic
from Chains.grabandthrow import THROW_DIRECTION
from Chains.shffl import SHFFL_DIRECTION
from Chains.dshffl import DSHFFL_DIRECTION

# Shield pressure
class Pressure(Tactic):
    def __init__(self, logger, controller, framedata, difficulty):
        Tactic.__init__(self, logger, controller, framedata, difficulty)
        # Pick a random max number of shines
        self.shinemax = random.randint(0, 2)
        self.shinecount = 0

        self.waveshine = False
        self.shffl = False
        self.dashdance = False
        # to fix
        self.rshinebair = False
        self.dshffl = False

        dashchance = 2
        # TODO Remove the dash dance from the random pool if we're in a spot where it would be bad
        # if self.smashbro_state.action not in [Action.STANDING, Action.TURNING, Action.DASHING]:
        #     dashchance = 0

        # What sort of shield pressure should this be? Pick one at random
        rand = random.choice([1]*5 + [2]*3 + [3]*dashchance)

        # On difficulty 1 and 2, only do dash dance
        if self.difficulty <= 2:
            rand = 3

        # 50% chance of being SHFFL style pressure
        if rand == 1:
            self.shffl = True
        # 30% chance of being waveshine style pressure
        if rand == 2:
            self.waveshine = True
        # 20% chance of being dashdance style pressure
        if rand == 3:
            self.dashdance = True

    # We can shield pressuring if...
    def canpressure(opponent_state, gamestate):
        # Opponent must be shielding
        shieldactions = [Action.SHIELD_START, Action.SHIELD, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        shielding = opponent_state.action in shieldactions

        if opponent_state.invulnerability_left > 0:
            return False

        # We must be in close range
        inrange = gamestate.distance < 30

        return shielding and inrange

    def step(self, gamestate, smashbro_state, opponent_state):
        self._propagate  = (gamestate, smashbro_state, opponent_state)

        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step(gamestate, smashbro_state, opponent_state)
            return

        if self.dashdance:
            self.chain = None
            # Don't try to dashdance if we know we can't
            if smashbro_state.action in [Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND]:
                distance = max(gamestate.distance / 20, 1)
                self.pickchain(Chains.Wavedash, [distance])
                return
            self.pickchain(Chains.DashDance, [opponent_state.position.x])
            return

        # Keep a running count of how many shines we've done
        if smashbro_state.action == Action.DOWN_B_GROUND_START and \
            smashbro_state.action_frame == 2:
            self.shinecount += 1

        canshine = smashbro_state.action in [Action.TURNING, Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
            Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, Action.CROUCHING, \
            Action.RUNNING, Action.DOWN_B_STUN, Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND, Action.KNEE_BEND]

        candash = smashbro_state.action in [Action.DASHING, Action.TURNING, Action.RUNNING, \
            Action.EDGE_TEETERING_START, Action.EDGE_TEETERING]

        inshinerange = gamestate.distance < 11.80-3
        # Where will opponent end up, after sliding is accounted for? (at the end of our grab)
        endposition = opponent_state.position.x + self.framedata.slide_distance(opponent_state, opponent_state.speed_ground_x_self, 7)
        ourendposition = smashbro_state.position.x + self.framedata.slide_distance(smashbro_state, smashbro_state.speed_ground_x_self, 7)
        ingrabrange = abs(endposition - ourendposition) < 13.5

        # If we're out of range, and CAN dash, then let's just dash in no matter
        #   what other options are here.
        if not inshinerange and candash:
            # Dash dance at our opponent
            self.chain = None
            self.pickchain(Chains.DashDance, [opponent_state.position.x])
            return

        neutral = smashbro_state.action in [Action.STANDING, Action.DASHING, Action.TURNING, \
            Action.RUNNING, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING]

        facingopponent = smashbro_state.facing == (smashbro_state.position.x < opponent_state.position.x)
        # If we're turning, then any action will turn around, so take that into account
        if smashbro_state.action == Action.TURNING:
            facingopponent = not facingopponent

        # Multishine if we're in range, facing our opponent and haven't used up all our shines
        if inshinerange and facingopponent and (self.shinecount < self.shinemax) and gamestate.custom["shine_count"] < 3:
            self.pickchain(Chains.Multishine)
            shinecount = 0
            return

        # Here's where things get complicated...
        else:
            # If we're not in range, then we need to get back into range. But how?
            #   Wavedash or SHFFL?
            if not inshinerange:
                if self.waveshine:
                    x = 0.5
                    # If opponent is facing us, do the max distance wavedash to cross them up (avoid grab)
                    if (opponent_state.position.x < smashbro_state.position.x) == opponent_state.facing:
                        x = 1.0
                    self.chain = None
                    self.pickchain(Chains.Waveshine, [x])
                    if smashbro_state.action in [Action.DOWN_B_GROUND] and smashbro_state.action_frame == 1:
                        print('shield pressure waveshine')
                    return
                if self.shffl:
                    self.chain = None
                    shffl_rng = random.randint(0, 1)
                    if (opponent_state.position.x < smashbro_state.position.x) == opponent_state.facing and not facingopponent:
                        self.pickchain(Chains.Dshffl, [DSHFFL_DIRECTION.BACK])
                        if smashbro_state.action_frame == 1:
                            print("shield pressure late bair")
                        return
                    elif (opponent_state.position.x < smashbro_state.position.x) == opponent_state.facing and \
                            facingopponent and shffl_rng == 0:
                        self.pickchain(Chains.Dshffl, [DSHFFL_DIRECTION.NEUTRAL])
                        if smashbro_state.action_frame == 1:
                            print("shield pressure late nair")
                        return
                    elif shffl_rng == 1:
                        self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.NEUTRAL])
                        if smashbro_state.action_frame == 1:
                            print("shield pressure nair")
                        return
                    else:
                        self.pickchain(Chains.Shffl)
                        if smashbro_state.action_frame == 1:
                            print("shield pressure dair")
                        return

            # Recalculate facing for the slide end
            facingopponent = smashbro_state.facing == (ourendposition < endposition)
            if smashbro_state.action == Action.TURNING and smashbro_state.action_frame == 1:
                facingopponent = not facingopponent

            # Grab opponent
            if ingrabrange and facingopponent and (self.shinecount >= self.shinemax) and gamestate.custom["shield_frame"] >= 12:
                if opponent_state.percent < 89:
                    self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.UP])
                    # if smashbro_state.action_frame == 1:
                    print('pressure uthrow, shield frame:', gamestate.custom["shield_frame"])
                else:
                    self.pickchain(Chains.GrabAndThrow, [THROW_DIRECTION.DOWN])
                    # if smashbro_state.action_frame == 1:
                    print('pressure dthrow, shield frame:', gamestate.custom["shield_frame"])
                return

        # If we fall through, then just dashdance at our opponent
        self.chain = None
        self.pickchain(Chains.DashDance, [opponent_state.position.x])
