import melee
from melee.enums import Action, Button
from Chains.chain import Chain

# Edgestall
class Edgestall(Chain):
    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller

        # If we just grabbed the edge, wait
        if smashbro_state.action == Action.EDGE_CATCHING:
            self.interruptible = True
            controller.empty_input()
            return

        # If we are able to let go of the edge, do it
        if smashbro_state.action == Action.EDGE_HANGING:
            # If we already pressed back last frame, let go
            if controller.prev.c_stick != (0.5, 0.5):
                controller.empty_input()
                return
            x = 1
            if smashbro_state.position.x < 0:
                x = 0
            self.interruptible = False
            controller.tilt_analog(Button.BUTTON_C, x, 0.5)
            return

        # Once we're falling, UP-B
        if smashbro_state.action == Action.FALLING:
            self.interruptible = False
            controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 1)
            controller.press_button(Button.BUTTON_B)
            print('edgestall')
            return

        self.interruptible = True
        controller.empty_input()
