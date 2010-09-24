

"""A Sprite layer, displaying an image

Currently, 3 methods of specifying the image exist:
- Passing a Pyglet sprite in the 'sprite' argument to __init__
- Passing a filename in the 'filename' argument to __init__
    (any image type loadable by Pyglet will do)
- Passing 'filename' and 'pkg' attributes will call
    pkg_resources.resource_filename(pkg, filename)

Other methods are possible by overriding the loadSprite classmethod.
"""

from __future__ import division

import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.graphics import helpers

class Sprite(BaseLayer):
    def __init__(self, parent, color=(1, 1, 1), **kwargs):
        self.sprite = self.loadSprite(kwargs)
        self.color = color
        super(Sprite, self).__init__(parent, **kwargs)

    @classmethod
    def loadSprite(cls, kwargs):
        sprite = kwargs.pop('sprite', None)
        if sprite:
            return sprite
        else:
            pkg = kwargs.pop('pkg', None)
            filename = kwargs.pop('filename')
            if pkg:
                import pkg_resources
                filename = pkg_resources.resource_filename(pkg, filename)
            return pyglet.sprite.Sprite(pyglet.image.load(filename))

    def draw(self, **kwargs):
        self.sprite.opacity = self.opacity * 255
        self.sprite.color = tuple(
                int(c * 255) for c
                in helpers.extend_tuple_copy(self.color)
            )
        size = helpers.extend_tuple_copy(self.size)
        glScalef(
                size[0] / self.sprite.width,
                size[1] / self.sprite.height,
                1,
            )
        self.sprite.draw()
