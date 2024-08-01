import melee
from melee.enums import Action, Button, Character
from Chains.chain import Chain

class Crouchcancel(Chain):
    def __init__(self, hold=False):
        self.hold = hold
        self.direction = None

    def step(self, gamestate, smashbro_state, opponent_state):
        controller = self.controller

        # Don't try to crouch in the air
        if not smashbro_state.on_ground:
            self.interruptible = True
            controller.empty_input()
            return

        actionable_landing = smashbro_state.action == Action.LANDING and smashbro_state.action_frame >= 4

        # If standing or turning, crouch
        if smashbro_state.action in [Action.STANDING] or actionable_landing:
            controller.tilt_analog(Button.BUTTON_MAIN, .5, 0)
            self.interruptible = True
            # print('crouch initiated', smashbro_state.action, opponent_state.action_frame)
            return

        # FireFox is different
        firefox = opponent_state.action in [Action.SWORD_DANCE_4_HIGH, Action.SWORD_DANCE_4_MID] and opponent_state.character in [Character.FOX, Character.FALCO]

        # If we get to cooldown, let go
        attackstate = self.framedata.attack_state(opponent_state.character, opponent_state.action, opponent_state.action_frame)
        if attackstate in [melee.enums.AttackState.COOLDOWN, melee.enums.AttackState.NOT_ATTACKING] \
                and len(gamestate.projectiles) == 0 and not firefox:
            self.interruptible = True
            controller.empty_input()
            # print('crouch cancel finish', smashbro_state.action)
            return

        # Hold onto the crouch until the attack is done
        if self.hold:
            self.interruptible = False
            controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
            # print('crouch cancel hold', smashbro_state.action)
            return

        # Also hold the shield in case we pressed too soon and opponent is still attacking
        if attackstate == melee.AttackState.ATTACKING and smashbro_state.action in [Action.CROUCHING, Action.CROUCH_START, Action.CROUCH_END]:
            self.interruptible = False
            controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0)
            # print('crouch cancel hold', smashbro_state.action)
            return

        # We're done if we are forced to release crouch
        if not smashbro_state.action in [Action.CROUCHING, Action.CROUCH_START, Action.CROUCH_END] and controller.tilt_analog(Button.BUTTON_MAIN, 0.5, 0):
            self.interruptible = True
            controller.empty_input()
            # print('crouch cancel finish', smashbro_state.action)
            return

        self.interruptible = True
        controller.empty_input()
