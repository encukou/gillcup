
from __future__ import division

import sys

import pyglet
from pyglet import gl

import gillcup
from gillcup.effect import Effect
from gillcup_graphics.base import GraphicsObject


class Text(GraphicsObject):
    def __init__(self,
            parent,
            text,
            font_size=None,
            font_name=None,
            characters_displayed=None,
            relative_anchor=None,
            **kwargs
        ):
        super(Text, self).__init__(parent, **kwargs)
        if 'size' not in kwargs:
            getattr(type(self), 'size').animate(self, Autosizer(self))
        if 'anchor' not in kwargs:
            getattr(type(self), 'anchor').animate(self, RelativeAnchor(self))
        self.text = text
        self.font_name = font_name
        if font_size is not None:
            self.font_size = font_size
        if relative_anchor is not None:
            self.relative_anchor = relative_anchor
        if characters_displayed is not None:
            self.characters_displayed = characters_displayed
        self.sprite = pyglet.text.Label(
                text,
                font_name=font_name,
                font_size=font_size,
            )

    font_size = gillcup.AnimatedProperty(72)
    characters_displayed = gillcup.AnimatedProperty(sys.maxint)
    relative_anchor = gillcup.TupleProperty(0, 0)
    relative_anchor_x, relative_anchor_y = relative_anchor

    def setup(self):
        if self.font_name:
            self.sprite.font_name = self.font_name
        self.sprite.font_size = self.font_size

    def draw(self, **kwargs):
        self.setup()
        color = self.color + (self.opacity, )
        self.sprite.color = [int(a * 255) for a in color]
        self.sprite.text = self.text[:int(self.characters_displayed)]
        self.sprite.draw()
        self.sprite.text = self.text


class Autosizer(Effect):
    """Put on text.size to reflect the natural size of the label"""
    def __init__(self, text):
        super(Autosizer, self).__init__()
        self.text = text

    @property
    def value(self):
        self.text.setup()
        sprite = self.text.sprite
        sprite.text = self.text.text
        return (sprite.content_width, sprite.content_height)


class RelativeAnchor(Effect):
    """Put on text.anchor to make it respect relative_anchor"""
    def __init__(self, text):
        super(RelativeAnchor, self).__init__()
        self.text = text

    @property
    def value(self):
        return (self.text.width * self.text.relative_anchor_x,
            self.text.height * self.text.relative_anchor_y)
