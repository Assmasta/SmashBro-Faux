import melee
from melee.enums import Action, Button
from Chains.chain import Chain

from Chains.shffl import SHFFL_DIRECTION

# unfinished
# Shine, then bair
class RShineBair(Chain):
    # Distance argument is a multiplier to how high we'll jump
    # 0 is short hop
    # 1 is full jump
    def __init__(self, height=0):
        self.hasshined = False
        self.height = height

    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller

        shineablestates = [Action.TURNING, Action.STANDING, Action.WALK_SLOW, Action.WALK_MIDDLE, \
                           Action.WALK_FAST, Action.EDGE_TEETERING_START, Action.EDGE_TEETERING, Action.CROUCHING, \
                           Action.RUNNING, Action.RUN_BRAKE, Action.CROUCH_START, Action.CROUCH_END,
                           Action.SHIELD_RELEASE]
        jcshine = (smashbro_state.action == Action.KNEE_BEND) and (smashbro_state.action_frame == 3)
        lastdashframe = (smashbro_state.action == Action.DASHING) and (smashbro_state.action_frame == 12)
        landing_over = (smashbro_state.action == Action.LANDING) and (smashbro_state.action_frame >= 4)

        # Do the shine if we can
        if not self.hasshined and (
                (smashbro_state.action in shineablestates) or lastdashframe or jcshine or landing_over):
            self.interruptible = False
            controller.press_button(Button.BUTTON_B)
            controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            self.hasshined = True
            return

        # If we're in the early knee bend frames, just hang on and wait
        if (smashbro_state.action == Action.KNEE_BEND) and (smashbro_state.action_frame < 3):
            controller.empty_input()
            return

        # Pivot. You can't shine from a dash animation. So make it a pivot
        if smashbro_state.action == Action.DASHING:
            # Turn around
            self.interruptible = True
            controller.release_button(Button.BUTTON_B)
            controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbro_state.facing), .5)
            # controller.press_button(Button.BUTTON_Y) #attempt JC shine instead of pivot shine
            return

        # there is an off-chance that rshinebair.py gets called during GRAB_WAIT

        isInShineStart = smashbro_state.action in [Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND]
        needsJC = smashbro_state.action in [Action.SHIELD, Action.TURNING_RUN]

        # Jump out of shield, turning run, or tilt turn
        if needsJC or (smashbro_state.action == Action.TURNING and smashbro_state.action_frame in range(2,12)): #
            if controller.prev.button[Button.BUTTON_Y]:
                controller.empty_input()
                return
            self.interruptible = False
            controller.press_button(Button.BUTTON_Y)
            return

        if isInShineStart:
            self.interruptible = False
            if smashbro_state.action_frame >= 3:
                # grounded short hop bair
                if smashbro_state.on_ground and self.height == 0:
                    self.pickchain(Chains.Shffl, [SHFFL_DIRECTION.BACK])
                    return
                # airborne and grounded full hop bair
                else:
                    controller.press_button(Button.BUTTON_Y)
                return
            else:
                controller.empty_input()
                return

        # for grounded high full hop
        if self.height == 1:
            if controller.prev.button[Button.BUTTON_Y] and smashbro_state.action != Action.KNEE_BEND:
                controller.release_button(Button.BUTTON_Y)
                return
            else:
                controller.press_button(Button.BUTTON_Y)
                # Only jump to the side if we're far away horizontally. If they're right above, then just straight up and drift
                x = int(self.target_x > smashbro_state.position.x)
                if abs(self.target_x - smashbro_state.position.x) < 10:
                    x = 0.5
                controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
                return

            # Once we're airborne, do an attack
            if not self.framedata.is_attack(smashbro_state.character, smashbro_state.action):
                # If the C stick wasn't set to middle, then
                if controller.prev.c_stick != (.5, .5):
                    controller.tilt_analog(Button.BUTTON_C, .5, .5)
                    return
                controller.tilt_analog(Button.BUTTON_C, int(not smashbro_state.facing), .5)
                return

        jumping = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD]

        # high bair
        if controller.prev.button[Button.BUTTON_Y] and not self.framedata.is_attack(smashbro_state.character, smashbro_state.action):
            # If the C stick wasn't set to middle, then
            if controller.prev.c_stick != (.5, .5):
                controller.tilt_analog(Button.BUTTON_C, .5, .5)
                return

            controller.tilt_analog(Button.BUTTON_C, int(not smashbro_state.facing), .5)
            return

        # if smashbro_state.action == Action.BAIR:
        #     # needs replacement (does it cancel shhfl)?
        #     self.interruptible = False
        #     controller.empty_input()
        #     return

        else:
            self.interruptible = True

        controller.empty_input()