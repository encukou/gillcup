
from __future__ import division

import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.action import FunctionAction
from gillcup.graphics import helpers


class Text(BaseLayer):
    """A line of text.

    :param text: The text to display
    :param fontName: The font to display the text with

    These arguments become animable attributes:

    :param color: The color of the text.
    :param size: The size of the text label. If one dimension is zero, it is
            calculated from the other so that aspect ratio is preserved.
    :param fontSize: The size of the font used. Increase if your label looks
            pixelated.

    See the :py:class:`base class <gillcup.graphics.baselayer.BaseLayer>`
    for functionality common to all graphics objects, particularly additional
    attributes and __init__ arguments.
    """
    def __init__(self,
            parent,
            text,
            fontSize=72,
            fontName=None,
            **kwargs
        ):
        kwargs.setdefault('size', (0, 1))
        super(Text, self).__init__(parent, **kwargs)
        self.text = text
        self.fontName = fontName
        self.fontSize = fontSize
        self.sprite = pyglet.text.Label(text)

    def draw(self, **kwargs):
        if self.fontName:
            self.sprite.font_name = self.fontName
        self.sprite.font_size = self.fontSize
        width, height, dummy = helpers.extend_tuple_copy(self.size)
        c_width = self.sprite.content_width
        c_height = self.sprite.content_height
        if not width:
            scale_x = scale_y = height / c_height
        elif not height:
            scale_x = scale_y = width / c_width
        else:
            scale_x = width / c_width
            scale_y = height / c_height
        glScalef(scale_x, scale_y, 1)
        color = self.getColor(kwargs) + (self.opacity, )
        self.sprite.color = [int(a * 255) for a in color]
        self.sprite.draw()
        from gillcup.graphics.colorrect import vertices_gl
        glColor4fv((GLfloat * 4)(1, 1, 1, 0.2))
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices_gl)
        glDrawArrays(GL_QUADS, 0, 4)

    def getRealSize(self):
        width, height, dummy_z = helpers.extend_tuple_copy(self.size)
        c_width = self.sprite.content_width
        c_height = self.sprite.content_height
        if not width:
            return height * c_width / c_height, height
        elif not height:
            return width, width * c_height / c_width
        else:
            return width, height

    def _relativePoint(self, x, y):
        width, height = self.getRealSize()
        print width, height
        return width * x, height * y

    def relativeAnchorSetter(self, x, y):
        return FunctionAction(self.setRelativeAnchor, x, y)

    def setRelativeAnchor(self, x, y, dt=0):
        if dt:
            self.apply(self.relativeAnchorSetter(x, y), dt=dt)
        else:
            self.setDynamicAttribute(
                    'anchorPoint',
                    lambda: self._relativePoint(x, y),
                )
