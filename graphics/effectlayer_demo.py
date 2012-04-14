from __future__ import division

import math

import gillcup

from gillcup_graphics import Window, run, RealtimeClock, Layer, EffectLayer
from gillcup_graphics import Rectangle

clock = RealtimeClock()


def makeColorrect(parent, i, speed, color):
    colorrect = Rectangle(parent, position=(.5, .5),
            anchor=(.5, .5), color=color)
    colorrect.scale = 0, 0, 0
    colorrect.opacity = 1
    anim = gillcup.Animation(colorrect, 'rotation', speed, time=1,
            timing='infinite')
    anim |= gillcup.Animation(colorrect, 'scale', .5, .5, .5,
            delay=i, time=5, easing='sine.out')
    anim |= gillcup.Animation(colorrect, 'opacity', 1 - i / 7,
            delay=i, time=.05, easing='cubic.out')
    clock.schedule(anim)
    return colorrect


def demo():
    rootLayer = EffectLayer()
    rootLayer.mosaic = 10, 10

    fooLayer = EffectLayer(rootLayer)

    makeColorrect(fooLayer, 0, 90, (.5, .5, .5))
    makeColorrect(fooLayer, 1, -90, (1, 0, 0))
    makeColorrect(fooLayer, 2, 80, (1, 1, 0))
    makeColorrect(fooLayer, 3, -80, (0, 1, 0))
    makeColorrect(fooLayer, 4, 70, (1, 0, 1))
    makeColorrect(fooLayer, 5, -70, (0, 0, 1))
    makeColorrect(fooLayer, 6, 60, (0, 1, 1))
    makeColorrect(fooLayer, 7, -60, (.5, .5, .5))

    clock.schedule(gillcup.Animation(rootLayer, 'mosaic', 1, 1, time=10))
    clock.schedule(5 + gillcup.Animation(fooLayer, 'color', 0, 1, 0,
            timing=lambda t, s, d: (0.5 + math.sin(t - s) * 0.5) ** 5))

    Window(rootLayer, resizable=True)

    run()


demo()
