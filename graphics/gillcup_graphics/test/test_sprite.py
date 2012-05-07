"""Tests for the objects module
"""

from __future__ import division

import pyglet

from gillcup_graphics.objects import Sprite

# pylint: disable=W0611
from gillcup_graphics.test.util import resource_path
from gillcup_graphics.test.testlayer import pytest_funcarg__layer


def test_simple_sprite(layer):
    """Test if a sprite renders correctly"""
    Sprite(layer,
        pyglet.image.load(resource_path('northpole.png')),
        size=(1, 1))
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005
