import melee
from Chains.chain import Chain

class Nothing(Chain):
    def step(self, gamestate, smashbro_state, opponent_state):
        self.controller.empty_input()
        self.interruptible = True
