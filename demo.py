
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
    topLayer = Layer(timer=mainwindow.getMainTimer())
    topLayer.scaleTo(768. / 576, 1)
    makeColorrect(topLayer, 0, 90, (.5, .5, .5))
    makeColorrect(topLayer, 1, -90, (1, 0, 0))
    makeColorrect(topLayer, 2, 80, (1, 1, 0))
    makeColorrect(topLayer, 3, -80, (0, 1, 0))
    makeColorrect(topLayer, 4, 70, (1, 0, 1))
    makeColorrect(topLayer, 5, -70, (0, 0, 1))
    makeColorrect(topLayer, 6, 60, (0, 1, 1))
    makeColorrect(topLayer, 7, -60, (.5, .5, .5))
    opacityLayer = Layer(topLayer,
            position=(.5, .5),
            anchorPoint=(.5, .5),
            scale=(.125, .125),
            opacity=.5,
            pixelization=4,
        )
    opacityLayer.rotateBy(2, time=1, infinite=True)
    ColorRect(opacityLayer, position=(.25, 0), anchorPoint=(.5, .5), color=(0, 0, 0), rotation=45).rotateBy(100, time=1, infinite=True)
    ColorRect(opacityLayer, position=(-.25, 0), anchorPoint=(.5, .5), color=(1, 1, 1), rotation=45).rotateBy(-100, time=1, infinite=True)
    opacityLayer2 = Layer(opacityLayer, opacity=.75)
    ColorRect(opacityLayer2, color=(0, 1, 0), scale=(1, 1), anchorPoint=(.5, .5))
    mainwindow.run(topLayer, debug=True)

if __name__ == '__main__':
    demo()
