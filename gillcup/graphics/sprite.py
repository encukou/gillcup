
from __future__ import division

import weakref

import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.graphics import helpers

class Sprite(BaseLayer):
    """An image

    See :py:meth:`loadSprite` for keyword arguments to pass for loading images.

    :param color: The color of this rectangle. Becomes an animable attribute.
    :param size: The size of this sprite, (width, height). By default, the
            size of the image.

    See the :py:class:`base class <gillcup.graphics.baselayer.BaseLayer>`
    for functionality common to all graphics objects, particularly additional
    attributes and __init__ arguments.
    """
    def __init__(self, parent, **kwargs):
        self.sprite = self.loadSprite(kwargs)
        kwargs.setdefault('size', (self.sprite.width, self.sprite.height))
        super(Sprite, self).__init__(parent, **kwargs)

    spriteCache = weakref.WeakValueDictionary()

    @classmethod
    def loadSprite(cls, kwargs):
        """Load an image to use given __init__'s kwargs

        Currently, 3 methods of specifying the image exist:

        - Passing a Pyglet sprite in the 'sprite' argument to __init__
        - Passing a filename in the 'filename' argument to __init__
            (any image type loadable by Pyglet will do)
        - Passing 'filename' and 'pkg' attributes will call
            pkg_resources.resource_filename(pkg, filename)

        The 'region' argument can be specified to only use a specific region
        of the loaded image.
        The 'trim' argument will use a region 1px smaller on each side
        (used to prevent antialiasing errors).

        Used arguments are removed from kwargs.

        Returns a Pyglet sprite.
        """
        sprite = kwargs.pop('sprite', None)
        if sprite:
            return sprite
        else:
            pkg = kwargs.pop('pkg', None)
            filename = kwargs.pop('filename')
            key = pkg, filename
            if kwargs.pop('trim', False):
                region = 'trim'
            else:
                region = kwargs.pop('region', None)
            try:
                return cls.spriteCache[key, region]
            except KeyError:
                if pkg:
                    import pkg_resources
                    filename = pkg_resources.resource_filename(pkg, filename)
                image = pyglet.image.load(filename)
                if region is 'trim':
                    region = 1, 1, image.width - 2, image.height - 2
                if region:
                    image = image.get_texture().get_region(*region)
                sprite = pyglet.sprite.Sprite(image)
                cls.spriteCache[key, region] = sprite
                return sprite

    def draw(self, **kwargs):
        self.sprite.opacity = self.opacity * 255
        self.sprite.color = tuple( int(c * 255) for c in self.getColor(kwargs))
        size = helpers.extend_tuple_copy(self.size)
        glScalef(
                size[0] / self.sprite.width,
                size[1] / self.sprite.height,
                1,
            )
        self.sprite.draw()
