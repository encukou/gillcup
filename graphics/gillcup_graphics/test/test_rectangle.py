from __future__ import division

from gillcup_graphics.rectangle import Rectangle

from gillcup_graphics.test.recordinglayer import pytest_funcarg__layer


def test_basic_rectangle(layer):
    Rectangle(layer)


def test_small_rectangle(layer):
    Rectangle(layer, position=(0.1, 0.1), size=(0.8, 0.8))


def test_rectangle_scale(layer):
    Rectangle(layer, position=(0.1, 0.1), scale=(0.8, 0.8))


def test_rectangle_color(layer):
    Rectangle(layer, color=(0.3, 0.4, 0.5))


def test_rectangle_opacity(layer):
    Rectangle(layer, opacity=0.9)


def test_rectangle_anchors(layer):
    kwargs = dict(position=(0.5, 0.5), size=(0.5, 0.5))
    Rectangle(layer, anchor=(0, 0), color=(0, 0, 1), **kwargs)
    Rectangle(layer, anchor=(0.25, 0.25), color=(0, 1, 0), **kwargs)
    Rectangle(layer, anchor=(0.5, 0.5), color=(1, 0, 0), **kwargs)


def test_rectangle_relative_anchors(layer):
    kwargs = dict(position=(0.5, 0.5), size=(0.5, 0.5))
    Rectangle(layer, relative_anchor=(0, 0), color=(0, 0, 1), **kwargs)
    Rectangle(layer, relative_anchor=(0.25, 0.25), color=(0, 1, 0), **kwargs)
    Rectangle(layer, relative_anchor=(0.5, 0.5), color=(1, 0, 0), **kwargs)


def test_rectangle_rotation(layer):
    Rectangle(layer, rotation=45)
