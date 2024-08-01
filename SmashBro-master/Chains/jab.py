import melee
from melee.enums import Action, Button
from Chains.chain import Chain

class Jab(Chain):
    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller
        self.interruptible = True

        controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0.5)
        if controller.prev.button[Button.BUTTON_A]:
            controller.release_button(Button.BUTTON_A)
        else:
            controller.press_button(Button.BUTTON_A)