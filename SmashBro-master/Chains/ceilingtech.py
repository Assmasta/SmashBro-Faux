import melee
import random
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class CEILINGTECH_DIRECTION(Enum):
    CEILINGTECH_IN_PLACE = 0

class CeilingTech(Chain):
    def __init__(self, direction=CEILINGTECH_DIRECTION.CEILINGTECH_IN_PLACE):
        """probably boned if you have to call this"""
            self.direction = direction

    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller

        # If we're on the ground, we're done here
        if smashbro_state.on_ground:
            self.interruptible = False
            controller.empty_input()
            return

        if gamestate.custom["tech_lockout"] > 0:
            controller.empty_input()
            return

        if self.direction == CEILINGTECH_DIRECTION.CEILINGTECH_IN_PLACE:
            controller.press_button(Button.BUTTON_L)
            return

        self.interruptible = True
        controller.empty_input()
        return