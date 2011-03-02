
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
    :param fontSize: The size of the font used. Increase if your label looks
            pixelated.
    :param charactersDisplayed: The number of characters to be displayed
            (or None to display them all)

    See the :py:class:`base class <gillcup.graphics.baselayer.BaseLayer>`
    for functionality common to all graphics objects, particularly additional
    attributes and __init__ arguments.
    """
    # XXX: Setting a size does not work
    def __init__(self,
            parent,
            text,
            fontSize=72,
            fontName=None,
            charactersDisplayed=None,
            **kwargs
        ):
        kwargs.setdefault('size', (None, None))
        super(Text, self).__init__(parent, **kwargs)
        self.text = text
        self.fontName = fontName
        self.fontSize = fontSize
        self.sprite = pyglet.text.Label(
                text,
                font_name=fontName,
                font_size=fontSize,
            )
        self.charactersDisplayed = charactersDisplayed
        self.setSize()

    def draw(self, opacity=1, **kwargs):
        if self.fontName:
            self.sprite.font_name = self.fontName
        self.sprite.font_size = self.fontSize
        color = self.getColor(kwargs) + (self.opacity * opacity, )
        self.sprite.color = [int(a * 255) for a in color]
        text = self.text
        if self.charactersDisplayed is not None:
            text = text[:int(self.charactersDisplayed)]
        self.sprite.text = text
        self.sprite.draw()
        self.sprite.text = self.text

    def setSize(self):
        width, height, dummy = helpers.extend_tuple_copy(self.size)
        self.sprite.width = width
        self.sprite.height = height

    def getRealSize(self):
        self.sprite.text = self.text
        return (self.sprite.content_width, self.sprite.content_height)

    def _relativePoint(self, x, y):
        width, height = self.getRealSize()
        x, y = width * x, height * y
        return int(x), int(y)

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
