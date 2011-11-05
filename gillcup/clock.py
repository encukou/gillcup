class Clock(object):
    def __init__(self, time=0):
        self.time = time

    def advance(self, dt):
        self.time += dt
