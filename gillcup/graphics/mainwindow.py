import pyglet
from pyglet.gl import *

from gillcup.timer import Timer


def createMainWindow(layer, width=768, height=576, debug=False, config_args={},
        **winargs
    ):
    config = pyglet.gl.Config(sample_buffers=1, samples=4, **config_args)
    window = pyglet.window.Window(
            config=config,
            width=width,
            height=height,
            **winargs
        )

    layer.scaleTo(width, height)

    if debug:
        fps_display = pyglet.clock.ClockDisplay(format=' ' * 33 + '%(fps).2f')

    @window.event
    def on_draw():
        glEnable(GL_LINE_SMOOTH)
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        layer.do_draw()
        if debug:
            fps_display.draw()
            layer.dump()

    pyglet.clock.set_fps_limit(60)

    window.run = pyglet.app.run
    window.draw = on_draw

    return window


def getClockTimer(speed=1):
    rv = Timer()
    pyglet.clock.schedule(lambda dt: rv.advance(dt * speed))
    return rv


mainTimer = None

def getMainTimer():
    global mainTimer
    if mainTimer is None:
        mainTimer = Timer()
        pyglet.clock.schedule(mainTimer.advance)
    return mainTimer


def run(layer, *args, **kwargs):
    window = createMainWindow(layer, *args, **kwargs)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    window.run()
    if kwargs.get('debug'):
        layer.dump()
