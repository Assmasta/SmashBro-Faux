from abc import ABCMeta

class Chain:
    __metaclass__ = ABCMeta
    interruptible = True
    logger = None
    controller = None
    framedata = None
    difficulty = None

    def step(self, gamestate, smashbro_state, opponent_state): ...
