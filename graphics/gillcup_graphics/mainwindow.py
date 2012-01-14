
from __future__ import division

import pyglet
from pyglet.gl import *

import gillcup
from gillcup_graphics.transformation import GlTransformation

run = pyglet.app.run

class Window(pyglet.window.Window):
    """A main window

    Just a convenience subclass of pyglet.window.Window that shows a Layer
    """
    def __init__(self, layer, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.layer = layer

    def on_draw(self):
        glClearColor(0, 0, 0, 0)
        self.clear()
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClear(GL_COLOR_BUFFER_BIT)
        transformation = GlTransformation()
        transformation.reset()
        self.layer.do_draw(window=self, transformation=transformation)

    def on_resize(self, width, height):
        super(Window, self).on_resize(width, height)
        layer = self.layer
        layer.scale = width / layer.width, height / layer.height, 1

class RealtimeClock(gillcup.Clock):
    def __init__(self):
        super(RealtimeClock, self).__init__()
        pyglet.clock.schedule(self.advance)
