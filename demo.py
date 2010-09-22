
from __future__ import division

from gillcup.graphics import mainwindow
from gillcup.graphics.layer import Layer
from gillcup.graphics.colorrect import ColorRect

def makeColorrect(parent, i, speed, color):
    colorrect = ColorRect(parent, position=(.5, .5), anchorPoint=(.5, .5), color=color)
    colorrect.rotateBy(speed, time=1, infinite=True)
    colorrect.scaleTo(0)
    colorrect.scaleTo(.5, time=5, dt=i, easing='sin out')
    colorrect.opacity = 0
    colorrect.fadeTo(1 - i / 15, time=5 + i, dt=i, easing='cubic out')
    return colorrect

def demo():
    print 'Amazing, is it not?'
    layer = Layer(timer=mainwindow.getMainTimer())
    layer.scaleTo(768. / 576, 1)
    makeColorrect(layer, 0, 90, (.5, .5, .5))
    makeColorrect(layer, 1, -90, (1, 0, 0))
    makeColorrect(layer, 2, 80, (1, 1, 0))
    makeColorrect(layer, 3, -80, (0, 1, 0))
    makeColorrect(layer, 4, 70, (1, 0, 1))
    makeColorrect(layer, 5, -70, (0, 0, 1))
    makeColorrect(layer, 6, 60, (0, 1, 1))
    makeColorrect(layer, 7, -60, (.5, .5, .5))
    mainwindow.run(layer, debug=True)

if __name__ == '__main__':
    demo()
