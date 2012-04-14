"""Utilities for interfacing gillcup_graphics with the rest of the world

"""

from __future__ import division

import pyglet
from pyglet import gl

import gillcup
from gillcup_graphics.transformation import GlTransformation

run = pyglet.app.run


class Window(pyglet.window.Window):  # pylint: disable=W0223
    """A main window

    Just a convenience subclass of pyglet.window.Window that shows a Layer
    """
    def __init__(self, layer, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.layer = layer
        self.on_resize(self.width, self.height)

    def manual_draw(self):
        """Draw the contents outside of the main loop"""
        self.on_draw()
        self.flip()

    def on_draw(self):  # pylint: disable=W0221
        gl.glClearColor(0, 0, 0, 0)
        self.clear()
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glViewport(0, 0, self.width, self.height)
        transformation = GlTransformation()
        transformation.reset()
        self.layer.do_draw(window=self, transformation=transformation)

    def on_resize(self, width, height):
        super(Window, self).on_resize(width, height)
        layer = self.layer
        layer.scale = width / layer.width, height / layer.height, 1


class RealtimeClock(gillcup.Clock):
    """A Clock tied to the system time
    """
    def __init__(self):
        super(RealtimeClock, self).__init__()
        pyglet.clock.schedule(self.advance)
