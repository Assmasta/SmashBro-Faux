import melee
import math
import statistics
from statistics import mode
from Strategies.bait import Bait

from melee.enums import ProjectileType, Action, Button, Character

class ESAgent():
    """
    Expert system agent for SmashBro.
    This is the "manually programmed" TAS-looking agent.
    """
    def __init__(self, dolphin, smashbro_port, opponent_port, controller, difficulty=4):
        self.smashbro_port = smashbro_port
        self.opponent_port = opponent_port
        self.controller = controller
        self.framedata = melee.framedata.FrameData()
        self.logger = dolphin.logger
        self.difficulty = difficulty

        self.attack_list = []
        self.aerial_count = 0
        self.grab_count = 0
        self.grounded_attack_count = 0
        self.aerial_fraction = 0
        self.grab_fraction = 0
        self.Main_SDI_list = []
        self.C_SDI_list = []
        self.predominant_SDI = ''
        self.predominant_SDI_direction = ''
        self.tech_list = []
        self.predominant_tech = None
        self.predominant_hit_tech = None
        self.action_list = []
        self.op_action_list = []
        self.laser_taken = 0
        self.shield_frame = 0

        self.ledge_grab_count = 0
        self.shine_count = 0
        self.grab_cheese_count = 0
        self.tech_lockout = 0
        self.meteor_jump_lockout = 0
        self.meteor_ff_lockout = 0
        self.strategy = Bait(self.logger,
                            self.controller,
                            self.framedata,
                            self.difficulty)

    def remove_values_from_list(self, the_list, val):
        return [value for value in the_list if value != val]

    def act(self, gamestate):
        knownprojectiles = []
        for projectile in gamestate.projectiles:
            # Held turnips
            if projectile.type == ProjectileType.TURNIP and projectile.type == 0:
                continue
            if projectile.type not in [ProjectileType.UNKNOWN_PROJECTILE, ProjectileType.PEACH_PARASOL, \
                ProjectileType.FOX_LASER, ProjectileType.SHEIK_CHAIN, ProjectileType.SHEIK_SMOKE]:
                knownprojectiles.append(projectile)
        gamestate.projectiles = knownprojectiles

        # debugging
        # tracker_trigger = False
        # if gamestate.player[self.opponent_port].on_ground:
        #     tracker_trigger = True
        # if tracker_trigger:
        #     print('opponent action/frame:',
        #           gamestate.player[self.opponent_port].action, gamestate.player[self.opponent_port].action_frame,
        #           'smashbro action/frame:',
        #           gamestate.player[self.smashbro_port].action, gamestate.player[self.smashbro_port].action_frame)

        # tracker
        self.action_list.append(gamestate.player[self.smashbro_port].action)
        if len(self.action_list) > 60:
            self.action_list.pop(0)

        self.op_action_list.append(gamestate.player[self.opponent_port].action)
        if len(self.op_action_list) > 60:
            self.op_action_list.pop(0)

        # to prevent random early shinegrabs
        shield_actions = [Action.SHIELD_START, Action.SHIELD, Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        if gamestate.player[self.opponent_port].action in shield_actions:
            self.shield_frame += 1
        else:
            self.shield_frame = 0

        # take laser?
        if gamestate.player[self.smashbro_port].action_frame == 1 and self.action_list[len(self.action_list) - 2] == \
                Action.DAMAGE_HIGH_1 and gamestate.player[self.smashbro_port].action != Action.DAMAGE_HIGH_1 and \
                gamestate.player[self.opponent_port].character == Character.FALCO:
            self.laser_taken = 15
            # self.laser_taken = True
        elif self.laser_taken > 0:
            self.laser_taken -= 1
        else:
            self.laser_taken = 0

        # attack list for rps
        if gamestate.player[self.opponent_port].action_frame == 1 and gamestate.player[self.opponent_port].action in \
                [Action.NEUTRAL_ATTACK_1, Action.UPTILT, Action.DOWNTILT, Action.FTILT_LOW, Action.FTILT_MID,\
                 Action.FTILT_HIGH, Action.FTILT_LOW_MID, Action.FTILT_HIGH_MID, Action.DASH_ATTACK,\
                 Action.FSMASH_MID, Action.FSMASH_LOW, Action.FSMASH_HIGH, Action.FSMASH_MID_LOW, Action.FSMASH_MID_HIGH,\
                 Action.UAIR, Action.DAIR, Action.FAIR, Action.BAIR, Action.GRAB, Action.GRAB_RUNNING]:
            self.attack_list.append(gamestate.player[self.opponent_port].action)
            if len(self.attack_list) > 20:
                self.attack_list.pop(0)

        self.aerial_count = self.attack_list.count(Action.UAIR) + self.attack_list.count(Action.DAIR) + \
                            self.attack_list.count(Action.FAIR) + self.attack_list.count(Action.BAIR)
        self.grab_count = self.attack_list.count(Action.GRAB) + self.attack_list.count(Action.GRAB_RUNNING)
        self.grounded_attack_count = len(self.attack_list) - self.aerial_count - self.grab_count

        self.aerial_fraction = round(self.aerial_count/max(1, len(self.attack_list)), 2)*100
        self.grab_fraction = round(self.grab_count/max(1, len(self.attack_list)), 2)*100

        # DI tracker (note main and C stick positions when in hitstun)
        mainstick = gamestate.player[self.opponent_port].controller_state.main_stick
        cstick = gamestate.player[self.opponent_port].controller_state.c_stick
        opxatkspeed = gamestate.player[self.opponent_port].speed_x_attack
        if gamestate.player[self.opponent_port].hitstun_frames_left > 1 and opxatkspeed != 0:
            # check main stick for SDI
            main_direction = ''
            if (abs(opxatkspeed)/opxatkspeed == 1 and mainstick[0] < 0.5) or \
                    (abs(opxatkspeed)/opxatkspeed == -1 and mainstick[0] > 0.5):
                main_direction += 'in'
            if (abs(opxatkspeed)/opxatkspeed == 1 and mainstick[0] > 0.5) or \
                    (abs(opxatkspeed)/opxatkspeed == -1 and mainstick[0] < 0.5):
                main_direction += 'out'
            if mainstick[1] > 0.5:
                main_direction += 'up'
            if mainstick[1] < 0.5:
                main_direction += 'down'
            self.Main_SDI_list.append(main_direction)
            if len(self.Main_SDI_list) > 60:
                self.Main_SDI_list.pop(0)

            # check c stick for ASDI
            c_direction = ''
            if (abs(opxatkspeed) / opxatkspeed == 1 and cstick[0] < 0.5) or \
                    (abs(opxatkspeed) / opxatkspeed == -1 and cstick[0] > 0.5):
                c_direction += 'in'
            if (abs(opxatkspeed) / opxatkspeed == 1 and cstick[0] > 0.5) or \
                    (abs(opxatkspeed) / opxatkspeed == -1 and cstick[0] < 0.5):
                c_direction += 'out'
            if cstick[1] > 0.5:
                c_direction += 'up'
            if cstick[1] < 0.5:
                c_direction += 'down'
            self.C_SDI_list.append(c_direction)
            if len(self.C_SDI_list) > 60:
                self.C_SDI_list.pop(0)

            if self.Main_SDI_list != []:
                self.predominant_SDI = mode(self.Main_SDI_list)
            if self.remove_values_from_list(self.Main_SDI_list, '') != []:
                self.predominant_SDI_direction = mode(self.remove_values_from_list(self.Main_SDI_list, ''))

        # tech options
        if gamestate.player[self.opponent_port].action_frame == 1 and gamestate.player[self.opponent_port].action in \
                [Action.NEUTRAL_TECH, Action.FORWARD_TECH, Action.BACKWARD_TECH, Action.TECH_MISS_UP, Action.TECH_MISS_DOWN]:
            self.tech_list.append(gamestate.player[self.opponent_port].action)
            if len(self.tech_list) > 20:
                self.tech_list.pop(0)

        self.predominant_tech = max(self.tech_list.count(Action.NEUTRAL_TECH), \
                                    self.tech_list.count(Action.FORWARD_TECH), self.tech_list.count(Action.BACKWARD_TECH),\
                                    self.tech_list.count(Action.TECH_MISS_UP), self.tech_list.count(Action.TECH_MISS_DOWN))
        if self.predominant_tech == 0:
            main_tech = None
        elif self.predominant_tech in [self.tech_list.count(Action.TECH_MISS_UP), self.tech_list.count(Action.TECH_MISS_DOWN)]:
            main_tech = 'tech miss'
        elif self.predominant_tech == self.tech_list.count(Action.NEUTRAL_TECH):
            main_tech = 'tech in place'
        elif self.predominant_tech == self.tech_list.count(Action.FORWARD_TECH):
            main_tech = 'tech toward'
        elif self.predominant_tech == self.tech_list.count(Action.BACKWARD_TECH):
            main_tech = 'tech away'
        self.predominant_hit_tech = max(self.tech_list.count(Action.NEUTRAL_TECH), self.tech_list.count(Action.FORWARD_TECH), self.tech_list.count(Action.BACKWARD_TECH))
        if self.predominant_hit_tech == 0:
            most_hit_tech = None
        elif self.predominant_hit_tech == self.tech_list.count(Action.NEUTRAL_TECH):
            most_hit_tech = 'tech in place'
        elif self.predominant_hit_tech == self.tech_list.count(Action.FORWARD_TECH):
            most_hit_tech = 'tech toward'
        elif self.predominant_hit_tech == self.tech_list.count(Action.BACKWARD_TECH):
            most_hit_tech = 'tech away'

        # when player on halo, print lists
        if gamestate.player[self.opponent_port].action_frame == 1 and gamestate.player[self.opponent_port].action in \
                [Action.ON_HALO_DESCENT]:
            print()
            print('>>> Player Stats')
            print('>>> Standard attack breakdown:')
            print('>>> Aerials (%)', round(self.aerial_fraction, 2))
            print('>>> Grabs (%)', round(self.grab_fraction, 2))
            print('>>> Predominant SDI direction:', self.predominant_SDI_direction)
            print('>>> Main tech option:', main_tech)
            print('>>> Most hit:', most_hit_tech)
            print()

        # Tech lockout
        if gamestate.player[self.smashbro_port].controller_state.button[Button.BUTTON_L]:
            self.tech_lockout = 40
        else:
            self.tech_lockout -= 1
            self.tech_lockout = max(0, self.tech_lockout)

        # Jump meteor cancel lockout
        if gamestate.player[self.smashbro_port].controller_state.button[Button.BUTTON_Y] or \
            gamestate.player[self.smashbro_port].controller_state.main_stick[1] > 0.8:
            self.meteor_jump_lockout = 40
        else:
            self.meteor_jump_lockout -= 1
            self.meteor_jump_lockout = max(0, self.meteor_jump_lockout)

        # Firefox meteor cancel lockout
        if gamestate.player[self.smashbro_port].controller_state.button[Button.BUTTON_B] and \
            gamestate.player[self.smashbro_port].controller_state.main_stick[1] > 0.8:
            self.meteor_ff_lockout = 40
        else:
            self.meteor_ff_lockout -= 1
            self.meteor_ff_lockout = max(0, self.meteor_ff_lockout)

        # Keep a shine count
        if gamestate.player[self.smashbro_port].action in [Action.DOWN_B_GROUND_START, Action.DOWN_B_GROUND] \
                and gamestate.player[self.smashbro_port].action_frame == 2:
            self.shine_count += 1
        if not gamestate.player[self.smashbro_port].on_ground and self.shine_count != 0\
                and gamestate.player[self.smashbro_port].position.y > 2:
            self.shine_count = 0
        if gamestate.frame == -123:
            self.shine_count = 0

        # Keep a grab count
        if gamestate.player[self.opponent_port].action == Action.GRAB and gamestate.player[
            self.opponent_port].action_frame == 1:
            self.grab_cheese_count += 1
        if abs(gamestate.player[self.opponent_port].position.x) - melee.stages.EDGE_GROUND_POSITION[gamestate.stage] > 15:
            self.grab_cheese_count = 0
        if gamestate.frame == -123:
            self.grab_cheese_count = 0

        # Keep a ledge grab count
        if gamestate.player[self.opponent_port].action == Action.EDGE_CATCHING and gamestate.player[self.opponent_port].action_frame == 1:
            self.ledge_grab_count += 1
        if gamestate.player[self.opponent_port].on_ground:
            self.ledge_grab_count = 0
        if gamestate.frame == -123:
            self.ledge_grab_count = 0

        gamestate.custom["aerial_fraction"] = self.aerial_fraction
        gamestate.custom["grab_fraction"] = self.grab_fraction
        gamestate.custom["predominant_SDI_direction"] = self.predominant_SDI_direction
        gamestate.custom["shine_count"] = self.shine_count
        gamestate.custom["grab_cheese_count"] = self.grab_cheese_count
        gamestate.custom["ledge_grab_count"] = self.ledge_grab_count
        gamestate.custom["tech_lockout"] = self.tech_lockout
        gamestate.custom["meteor_jump_lockout"] = self.meteor_jump_lockout
        gamestate.custom["meteor_ff_lockout"] = self.meteor_ff_lockout
        gamestate.custom["laser_taken"] = self.laser_taken
        gamestate.custom["shield_frame"] = self.shield_frame

        # Let's treat Counter-Moves as invulnerable. So we'll know to not attack during that time
        countering = False
        if gamestate.player[self.opponent_port].character in [Character.ROY, Character.MARTH]:
            if gamestate.player[self.opponent_port].action in [Action.MARTH_COUNTER, Action.MARTH_COUNTER_FALLING]:
                # We consider Counter to start a frame early and a frame late
                if 4 <= gamestate.player[self.opponent_port].action_frame <= 30:
                    countering = True
        if gamestate.player[self.opponent_port].character == Character.PEACH:
            if gamestate.player[self.opponent_port].action in [Action.UP_B_GROUND, Action.DOWN_B_STUN]:
                if 4 <= gamestate.player[self.opponent_port].action_frame <= 30:
                    countering = True
        if countering:
            gamestate.player[self.opponent_port].invulnerable = True
            gamestate.player[self.opponent_port].invulnerability_left = max(29 - gamestate.player[self.opponent_port].action_frame, gamestate.player[self.opponent_port].invulnerability_left)

        self.strategy.step(gamestate,
                           gamestate.players[self.smashbro_port],
                           gamestate.players[self.opponent_port])
