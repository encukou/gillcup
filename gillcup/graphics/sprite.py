
import pyglet
from pyglet.gl import *

from gillcup.graphics.layer import Layer
from gillcup.graphics import helpers

class Sprite(Layer):
    handlesOpacity = True

    def __init__(self, parent, spriteFilename='', size=(1, 1), **kwargs):
        super(Sprite, self).__init__(parent, **kwargs)
        self.sprite = pyglet.sprite.Sprite(pyglet.image.load(spriteFilename))
        self.size = size

    def draw(self):
        self.sprite.opacity = self.opacity * 255
        self.sprite.color = tuple(
                int(c * 255) for c
                in helpers.extend_tuple_copy(*self.color)
            )
        glScalef(
                self.size[0] / self.sprite.width,
                self.size[1] / self.sprite.height,
                1,
            )
        self.sprite.draw()
