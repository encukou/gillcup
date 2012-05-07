"""Tests for the objects module
"""

from __future__ import division

import pyglet

from gillcup_graphics.objects import Text

# pylint: disable=W0611
from gillcup_graphics.test.util import resource_path
from gillcup_graphics.test.testlayer import pytest_funcarg__layer


# Add a test font to Pyglet's registry
pyglet.font.add_file(resource_path('testfont.ttf'))


def test_simple_text(layer):
    """Test if a text renders correctly"""
    Text(layer, 'a', font_name='testfont',
        scale=(0.005, 0.005), position=(0.5, 0.35), relative_anchor=(0.5, 0))
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005
