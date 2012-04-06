import gillcup

from gillcup_graphics.mainwindow import Window, run, RealtimeClock
from gillcup_graphics.layer import Layer
from gillcup_graphics.rectangle import Rectangle

clock = RealtimeClock()


def makeColorrect(parent, i, speed, color):
    colorrect = Rectangle(parent, position=(.5, .5),
            anchor=(.5, .5), color=color)
    colorrect.scale = 0, 0, 0
    colorrect.opacity = 0
    anim = gillcup.Animation(colorrect, 'rotation', speed, time=1,
            timing='infinite')
    anim |= gillcup.Animation(colorrect, 'scale', .5, .5, .5,
            delay=i, time=5, easing='sine.out')
    anim |= gillcup.Animation(colorrect, 'opacity', 1 - i / 15,
            delay=i, time=5, easing='cubic.out')
    clock.schedule(anim)
    return colorrect


def demo():
    rootLayer = Layer()

    makeColorrect(rootLayer, 0, 90, (.5, .5, .5))
    makeColorrect(rootLayer, 1, -90, (1, 0, 0))
    makeColorrect(rootLayer, 2, 80, (1, 1, 0))
    makeColorrect(rootLayer, 3, -80, (0, 1, 0))
    makeColorrect(rootLayer, 4, 70, (1, 0, 1))
    makeColorrect(rootLayer, 5, -70, (0, 0, 1))
    makeColorrect(rootLayer, 6, 60, (0, 1, 1))
    makeColorrect(rootLayer, 7, -60, (.5, .5, .5))

    Window(rootLayer, resizable=True)

    run()


demo()
