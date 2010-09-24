
"""Easy-to use functions for actually displaying Gillcup animations.

To "run" a layer, call run(layer).
Pass height=n, width=m, or debug=True to change the behavior in obvious ways.
If you want more control, see the other stuff here.
If you want even more control, call timer.advance() and layer.draw() for each
frame yourself.
"""


import pyglet
from pyglet.gl import *

from gillcup.timer import Timer


def createMainWindow(layer, width=768, height=576, debug=False, config_args={},
        **winargs
    ):
    """Make an easy-to-use main window

    A convenience function designed to be easy to use rather than clean.
    """
    config = pyglet.gl.Config(sample_buffers=1, samples=4, **config_args)
    window = pyglet.window.Window(
            config=config,
            width=width,
            height=height,
            **winargs
        )

    try:
        layer.timer.time
    except RuntimeError:
        layer.timer = getMainTimer()

    layer.scaleTo(width / layer.width, height / layer.height)

    if debug:
        fps_display = pyglet.clock.ClockDisplay(format=' ' * 33 + '%(fps).2f')

    @window.event
    def on_draw():
        glEnable(GL_LINE_SMOOTH)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        layer.do_draw(window=window)
        if debug:
            fps_display.draw()
            layer.dump()

    pyglet.clock.set_fps_limit(60)

    window.run = pyglet.app.run
    window.draw = on_draw

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    return window


def getClockTimer(speed=1):
    """Return a timer that advances with the Pyglet clock.

    This creates a new timer every time. You'll usually want
    getMainTimer() instead.
    """
    rv = Timer()
    pyglet.clock.schedule(lambda dt: rv.advance(dt * speed))
    return rv


mainTimer = None

def getMainTimer():
    """Return a singleton timer that advances with the Pyglet clock"""
    global mainTimer
    if mainTimer is None:
        mainTimer = Timer()
        pyglet.clock.schedule(mainTimer.advance)
    return mainTimer


def run(layer, *args, **kwargs):
    """Call createMainWindow() and run a main loop with it"""
    window = createMainWindow(layer, *args, **kwargs)
    window.run()
    if kwargs.get('debug'):
        layer.dump()
