import melee
import math
import random
from melee.enums import Action, Button
from Chains.chain import Chain
from enum import Enum

class FIREFOX(Enum):
    HIGH = 0
    EDGE = 1
    HORIZONTAL = 2
    RANDOM = 3
    # Added SAFERANDOM option so Smashbot wouldn't random a straight horizontal upB and SD below the stage
    SAFERANDOM = 4

class Firefox(Chain):
    def __init__(self, direction=FIREFOX.RANDOM):
        if direction == FIREFOX.RANDOM:
            self.direction = FIREFOX(random.randint(0, 2))
        elif direction == FIREFOX.SAFERANDOM:
            self.direction = FIREFOX(random.randint(0, 1))
        else:
            self.direction = direction

    def get_low_corner(self, stage):
        """Returns the (x, y) coords of the lowest point of the stage where we can ride up the wall

        Basically, we need to aim ABOVE this point, or we'll FF below the stage.
        """
        if stage == melee.Stage.YOSHIS_STORY:
            return (melee.EDGE_POSITION[stage], -1000)
        if stage == melee.Stage.BATTLEFIELD:
            return (melee.EDGE_POSITION[stage], -10)
        if stage == melee.Stage.FINAL_DESTINATION:
            return (45, -66.21936)
        if stage == melee.Stage.DREAMLAND:
            return (63, -47.480972)
        if stage == melee.Stage.POKEMON_STADIUM:
            return (70, -29.224771)
        if stage == melee.Stage.FOUNTAIN_OF_DREAMS:
            return (66, -50) # arbitrarily chosen

        return (0, 0)

    def getangle(self, gamestate, smashbro_state):
        # Make sure we don't angle below the stage's low corner.
        #   If we do, we'll SD
        corner_x, corner_y = self.get_low_corner(gamestate.stage)

        # The point we grab the edge at is a little below the stage
        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x))
        diff_y = abs(smashbro_state.position.y + 5)

        # adjustments for BF
        if corner_y == -10:
            # ceiling ride
            if abs(melee.stages.EDGE_POSITION[gamestate.stage]) > abs(smashbro_state.position.x):
                diff_x += 5
                diff_y = (max(0, 100**2 - diff_x**2))**0.5

            # adjusting for BF's jank ledge
            elif smashbro_state.position.y < 0 and 0.75*diff_x > diff_y:
                diff_x = diff_x - 2
                diff_y = diff_y + 3

        # adjustments for PS
        if corner_y == -29.224771 and smashbro_state.position.y < 0:
            diff_y = diff_y + 5

        # adjustments for wallriding: YS, FD, DL, PS
        if corner_y in [-1000, -66.21936, -47.480972, -29.224771]:
            diff_x = (max(0, 100**2 - diff_y**2))**0.5

        larger_magnitude = max(diff_x, diff_y)

        # Scale down values to between 0 and 1
        x = diff_x / larger_magnitude
        y = diff_y / larger_magnitude

        # Now scale down to be between .5 and 1
        # f that, scale down to between .25 and .5, we want all the inputs to fit on the control stick
        # scaled from .25 up to .35 to fit additional directions
        if smashbro_state.position.x < 0:
            x = 0.5 + (x/4)*(7/5)
            corner_x *= -1
        else:
            x = 0.5 - (x/4)*(7/5)

        if smashbro_state.position.y < 0:
            y = 0.5 + (y/4)*(7/5)
        else:
            y = 0.5 - (y/4)*(7/5)

        # Angle adjustments
        # turn around if under battlefield
        if abs(melee.stages.EDGE_POSITION[gamestate.stage]) > abs(smashbro_state.position.x) and corner_y == -10:
            x = -(x - 0.5) + 0.5

        # too low to wallride, just go straight up: FD, DL, PS
        if corner_y in [-66.21936, -47.480972, -29.224771]:
            if smashbro_state.position.y < corner_y and diff_x != 0:
                m = (y - 0.5)/(x - 0.5)
                xgap = corner_x - smashbro_state.position.x
                yint = m*xgap + smashbro_state.position.y
                # print("lower corner y: -47.48")
                # print("wallride check, slope:", round(m, 2), "projected y-int", round(yint, 2))
                if yint < corner_y and abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x)) < 20\
                    and not abs(corner_y) > abs(smashbro_state.position.x):
                    x, y = 0.5, 1

        # FD panic measure
        if corner_y == -66.21936 and smashbro_state.position.y < corner_y and \
                abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x)) < 25 and \
                abs(melee.stages.EDGE_POSITION[gamestate.stage]) > abs(smashbro_state.position.x):
            x, y = 0.5, 1

        # can't detect stick movements under 0.107, avoid unintended horizontal angles
        if 0.5 < y < 0.607:
            y = 0.61

        if smashbro_state.action_frame == 42:
            print("position x, y:", round(smashbro_state.position.x, 0), round(smashbro_state.position.y, 0))
            print("diff x:", round(diff_x, 0), "diff y:", round(diff_y, 0))
            print("potential target retrieved; x stick:", round(x, 2), "y stick:", round(y, 2))
        return x, y

    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller

        # We're done here if...
        if smashbro_state.on_ground or smashbro_state.action in [Action.EDGE_CATCHING, Action.EDGE_HANGING, Action.SWORD_DANCE_1_AIR]:
            self.interruptible = True
            controller.empty_input()
            return

        # If we're traveling in the air, let go of the stick
        if smashbro_state.action in [Action.FIREFOX_AIR, Action.DEAD_FALL]:
            self.interruptible = False
            controller.empty_input()
            return

        # We need to jump out of our shine
        if smashbro_state.action in [Action.DOWN_B_AIR, Action.DOWN_B_STUN]:
            controller.release_button(Button.BUTTON_B)
            controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0.5)
            if controller.prev.button[Button.BUTTON_Y]:
                controller.release_button(Button.BUTTON_Y)
            else:
                controller.press_button(Button.BUTTON_Y)
            return

        x = int(smashbro_state.position.x < 0)
        y = 1
        # random bad angle: high
        diff_x = abs(melee.stages.EDGE_POSITION[gamestate.stage] - abs(smashbro_state.position.x))
        # Which way should we point?
        if smashbro_state.action == Action.FIREFOX_WAIT_AIR:
            self.interruptible = False
            if self.direction == FIREFOX.HIGH:
                # print("firefox high") # is high supposed to be a mangle?
                if diff_x > 20:
                    # print("firefox high")
                    # generate random x value
                    if smashbro_state.position.x > 0:
                        x = -1
                    else:
                        x = 1
                    x = 0.5 + 0.5*(0.01*(abs(x)/x)*random.randint(22,70))
                    controller.tilt_analog(Button.BUTTON_MAIN, x, 0.85)
                    return
                else:
                    controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 1)
                    return
            if self.direction == FIREFOX.HORIZONTAL and smashbro_state.position.y > -8:
                controller.tilt_analog(Button.BUTTON_MAIN, x, .5)
                return
            if self.direction == FIREFOX.EDGE:
                # print("firefox edge")
                x, y = self.getangle(gamestate, smashbro_state)
                controller.tilt_analog(Button.BUTTON_MAIN, x, y)
                return
            controller.tilt_analog(Button.BUTTON_MAIN, x, 1)
            return

        # Is this a "forbidden" angle? Don't try it if it is.
        if self.direction == FIREFOX.EDGE:
            x, y = self.getangle(gamestate, smashbro_state)
            # Let's add a little extra room, so we don't miscalculate
            # if .3625 < y < .6375 or .3625 < x < .6375, converted for new transformation (*14/5)
            if (.3525 < y*14/5 < .6475) or (.3525 < x*14/5 < .6475) and (smashbro_state.position.y > -15):
                # Unless we're in range to just grab the edge. Then the angle doesn't matter
                if not ((-16.4 < smashbro_state.position.y < -5) and (diff_x < 10)):
                    controller.empty_input()
                    return

        # If we already pressed B last frame, let go
        if controller.prev.button[Button.BUTTON_B]:
            self.interruptible = True
            controller.empty_input()
            return

        controller.press_button(Button.BUTTON_B)
        controller.tilt_analog(Button.BUTTON_MAIN, .5, 1)
        self.interruptible = False
