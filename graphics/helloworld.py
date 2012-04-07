import gillcup

from gillcup_graphics.mainwindow import Window, run, RealtimeClock
from gillcup_graphics.layer import Layer
from gillcup_graphics.text import Text
from gillcup_graphics.rectangle import Rectangle

clock = RealtimeClock()



def hello():
    rootLayer = Layer()
    Text(rootLayer, 'Hello, World!',
        relative_anchor=(0.5, 0.75),
        position=(0.5, 0.75),
        scale=(0.001, 0.001))

    Window(rootLayer, resizable=True)

    run()


hello()
