
import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.graphics import helpers

class Sprite(BaseLayer):
    def __init__(self, parent, spriteFilename='', **kwargs):
        super(Sprite, self).__init__(parent, **kwargs)
        self.sprite = pyglet.sprite.Sprite(pyglet.image.load(spriteFilename))

    def draw(self, **kwargs):
        self.sprite.opacity = self.opacity * 255
        self.sprite.color = tuple(
                int(c * 255) for c
                in helpers.extend_tuple_copy(*self.color)
            )
        size = helpers.extend_tuple_copy(self.size)
        glScalef(
                size[0] / self.sprite.width,
                size[1] / self.sprite.height,
                1,
            )
        self.sprite.draw()
