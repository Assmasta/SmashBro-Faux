import melee
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class SHINEUPSMASH_DIRECTION(Enum):
    FORWARD = 1
    BACK = 2

class Shineupsmash(Chain):
    def __init__(self, direction = SHINEUPSMASH_DIRECTION.FORWARD):
        self.direction = direction

    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller

        # Pivot if we're dashing. Or else we might dash right off stage, which is annoying
        if smashbro_state.action in [Action.DASHING]:
            self.interruptible = True
            controller.tilt_analog(Button.BUTTON_MAIN, int(not smashbro_state.facing), 0.5)
            return

        actionable_landing = smashbro_state.action == Action.LANDING and smashbro_state.action_frame >= 4

        # If standing or turning, shine
        if smashbro_state.action in [Action.STANDING, Action.TURNING] or actionable_landing:
            controller.press_button(Button.BUTTON_B)
            controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            self.interruptible = False
            return

        # jc upsmash
        if smashbro_state.action == Action.KNEE_BEND:
            if smashbro_state.action_frame == 2:
                controller.tilt_analog(Button.BUTTON_C, .5, 1)
                self.interruptible = False
                return
            if smashbro_state.action_frame == 1:
                self.interruptible = True
                controller.empty_input()
                return

        isInShineStart = (smashbro_state.action == Action.DOWN_B_STUN or \
                          smashbro_state.action == Action.DOWN_B_GROUND_START or \
                          smashbro_state.action == Action.DOWN_B_GROUND)

        # Jump out of shine
        if isInShineStart and smashbro_state.action_frame >= 3 and smashbro_state.on_ground:
            controller.press_button(Button.BUTTON_X)
            self.interruptible = False
            return

        # Catchall
        self.interruptible = True
        controller.empty_input()