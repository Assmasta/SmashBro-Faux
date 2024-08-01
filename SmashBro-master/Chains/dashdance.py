import melee
import random
from Chains.chain import Chain
from melee.enums import Action, Button

class DashDance(Chain):
    def __init__(self, pivot, radius=0, hold_a=True):
        self.pivotpoint = pivot
        self.radius = radius
        self.interruptible = True
        self.hold_a = hold_a

    def step(self, gamestate, smashbro_state, opponent_state):
        if smashbro_state.moonwalkwarning and self.hold_a:
            self.controller.press_button(Button.BUTTON_A)

        if not self.hold_a and self.controller.prev.button[Button.BUTTON_A]:
            self.controller.release_button(Button.BUTTON_A)

        if smashbro_state.moonwalkwarning and self.controller.prev.main_stick[0] != 0.5:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0.5)
            return

        # Causes an empty_input if hitting left did not cause Smashbro to be TURNING or DASHING left, i.e. if Smashbro attempts a dashback during frames 1-3 of initial dash forward.
        if (self.controller.prev.main_stick[0] == 1) and (smashbro_state.action == Action.DASHING and not smashbro_state.facing):
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0.5)
            return

        # Causes an empty_input if hitting left did not cause Smashbro to be TURNING or DASHING left, i.e. if Smashbro attempts a dashback during frames 1-3 of initial dash forward.
        if (self.controller.prev.main_stick[0] == 0) and (smashbro_state.action == Action.DASHING and smashbro_state.facing):
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0.5)
            return


        if smashbro_state.action == Action.ON_HALO_WAIT:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 0)
            return

        if smashbro_state.action in [Action.LYING_GROUND_UP, Action.LYING_GROUND_DOWN]:
            roll = random.randint(0, 3)
            if roll == 1:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0.5, 1)
                return
            elif roll == 2:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 1, 0.5)
                return
            elif roll == 3:
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, 0, 0.5)
                return
            else:
                self.controller.press_button(Button.BUTTON_A)
                return

        # If we're in spotdodge or shield, do nothing
        if smashbro_state.action in [Action.SPOTDODGE, Action.SHIELD_RELEASE]:
            self.controller.empty_input()
            return

        # If we're stuck wavedashing, just hang out and do nothing
        if smashbro_state.action == Action.LANDING_SPECIAL and smashbro_state.action_frame < 28:
            self.controller.empty_input()
            return

        # Smashbro normally acts on frame 10 (stored as frame 28) of LANDING_SPECIAL. However, this can prevent him from teetering the ledge when wavedashing forward towards it.
        edgedistance = abs(smashbro_state.position.x) - melee.stages.EDGE_GROUND_POSITION[gamestate.stage]
        if smashbro_state.action == Action.LANDING_SPECIAL and smashbro_state.action_frame == 28 and edgedistance < 2:
            self.controller.empty_input()
            return

        #If we're walking, stop for a frame
        #Also, if we're shielding, don't try to dash. We will accidentally roll
        if smashbro_state.action == Action.WALK_SLOW or \
            smashbro_state.action == Action.WALK_MIDDLE or \
            smashbro_state.action == Action.WALK_FAST or \
            smashbro_state.action == Action.SHIELD_START or \
            smashbro_state.action == Action.SHIELD_REFLECT or \
            smashbro_state.action == Action.SHIELD:
                self.controller.empty_input()
                return

        #If we're starting the turn around animation, keep pressing that way or
        #   else we'll get stuck in the slow turnaround
        if smashbro_state.action == Action.TURNING and smashbro_state.action_frame == 1:
            return

        #Dash back, since we're about to start running
        # #Action.FOX_DASH_FRAMES
        # action_frame changed from 11 to lengthen dash-dance
        dashdance_rng = random.randint(11, 12)
        if melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - abs(smashbro_state.position.x) < 3:
            dashdance_rng = 11
        if smashbro_state.action == Action.DASHING and smashbro_state.action_frame >= dashdance_rng:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(not smashbro_state.facing), .5)
            return

        # Continue holding down if you enter RUN_BRAKE or CROUCH_START. Removed Action.RUNNING from these action states because that was causing down inputs which disrupted waveshine combos.
        # #Action.FOX_DASH_FRAMES
        if smashbro_state.action in [Action.RUN_BRAKE, Action.CROUCH_START]:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, .5, 0)
            return

        #We can't dashback while in CROUCH_END. We can, however, dash forward.
        if smashbro_state.action == Action.CROUCH_END:
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbro_state.facing), 0)
            return

        # Do nothing during the first 2 frames of DOWN_B_GROUND_START
        if smashbro_state == Action.DOWN_B_GROUND_START and smashbro_state.action_frame < 3:
            self.controller.empty_input()
            return

        # We need to input a jump to wavedash out of these states if dash/run gets called while in one of these states, or else we get stuck
        jcstates = smashbro_state.action in [Action.TURNING_RUN] or smashbro_state.action == Action.DOWN_B_GROUND_START and smashbro_state.action_frame == 3
        if jcstates or (smashbro_state.action == Action.TURNING and smashbro_state.action_frame in range(2,12)): #Also detects accidental tilt turns & decides to wavedash
            self.controller.press_button(Button.BUTTON_Y)
            return

        # Sometimes, we find ourselves getting past frame 3 of DOWN_B_GROUND_START and/or entering DOWN_B_GROUND. The old inputs would cause Smashbro to keep inputting Y and get stuck in shine.
        stuckinshine = (smashbro_state.action == Action.DOWN_B_GROUND_START and smashbro_state.action_frame > 3) or smashbro_state.action == Action.DOWN_B_GROUND
        if stuckinshine:
            if bool(gamestate.frame % 2):
                self.controller.press_button(Button.BUTTON_Y)
            else:
                self.controller.release_button(Button.BUTTON_Y)
            return

        # Airdodge for the wavedash
        jumping = [Action.JUMPING_ARIAL_FORWARD, Action.JUMPING_ARIAL_BACKWARD, Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD]
        jumpcancel = (smashbro_state.action == Action.KNEE_BEND) and (smashbro_state.action_frame == 3)
        if jumpcancel or (smashbro_state.action in jumping and abs(smashbro_state.position.x) < melee.stages.EDGE_GROUND_POSITION[gamestate.stage] and -5 < smashbro_state.position.y < 5):
            self.controller.press_button(Button.BUTTON_L)
            onleft = smashbro_state.position.x < opponent_state.position.x
            # Normalize distance from (0->1) to (0.5 -> 1)
            x = 1
            if onleft != False:
                x = 0
            # Don't airdodge/WD offstage
            if abs(smashbro_state.position.x) > \
                melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - 25:
                    x = 0
                    if smashbro_state.position.x < 0:
                        x = 1
            self.controller.tilt_analog(Button.BUTTON_MAIN, x, 0.35)
            return

        # We can't dash IMMEDIATELY after landing. So just chill for a bit
        if (smashbro_state.action == Action.LANDING and smashbro_state.action_frame < 4):
            self.controller.empty_input()
            return

        if not smashbro_state.on_ground:
            # Do a fastfall if we're not already
            if smashbro_state.speed_y_self > -3:
                self.controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
            else:
                self.controller.tilt_analog(Button.BUTTON_MAIN, int(smashbro_state.position.x < opponent_state.position.x), 0.5)
            return

        # Don't run off the stage
        # safety buffer changed from 6.6
        if abs(smashbro_state.position.x) > \
            melee.stages.EDGE_GROUND_POSITION[gamestate.stage] - 6.6:#(3 * FOX_DASH_SPEED):
                x = 0
                if smashbro_state.position.x < 0:
                    x = 1
                self.controller.tilt_analog(melee.Button.BUTTON_MAIN, x, .5)
                return

        # Are we inside the given radius of dash dancing?
        if (smashbro_state.position.x > self.pivotpoint - self.radius) and (smashbro_state.position.x < self.pivotpoint + self.radius):
            # Dash the direction we're facing to keep going through to the end of the radius
            self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbro_state.facing), .5)
            return

        # Dash towards the pivot point
        self.controller.tilt_analog(melee.Button.BUTTON_MAIN, int(smashbro_state.position.x < self.pivotpoint), .5)
        return
