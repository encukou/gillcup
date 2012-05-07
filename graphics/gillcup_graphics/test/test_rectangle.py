"""Test the Rectangle class
"""

from __future__ import division

from gillcup_graphics import Rectangle

# pylint: disable=W0611
from gillcup_graphics.test.testlayer import pytest_funcarg__layer


def test_basic_rectangle(layer):
    """The simplest graphics test possible"""
    Rectangle(layer)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity == 0


def test_small_rectangle(layer):
    """Test if ``size`` and ``position`` work"""
    Rectangle(layer, position=(0.1, 0.1), size=(0.8, 0.8))
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_scale(layer):
    """Test if ``scale`` and ``position`` work"""
    Rectangle(layer, position=(0.1, 0.1), scale=(0.8, 0.8))
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_color(layer):
    """Test if ``color`` works"""
    Rectangle(layer, color=(0.3, 0.4, 0.5))
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_opacity(layer):
    """Test if ``opacity`` works"""
    Rectangle(layer, opacity=0.9)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_anchors(layer):
    """Test if ``anchor`` works"""
    kwargs = dict(position=(0.5, 0.5), size=(0.5, 0.5))
    Rectangle(layer, anchor=(0, 0), color=(0, 0, 1), **kwargs)
    Rectangle(layer, anchor=(0.25, 0.25), color=(0, 1, 0), **kwargs)
    Rectangle(layer, anchor=(0.5, 0.5), color=(1, 0, 0), **kwargs)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_anchors_with_scale(layer):
    """Test if ``anchor`` works"""
    kwargs = dict(position=(0.5, 0.5), scale=(0.5, 0.5))
    Rectangle(layer, anchor=(0, 0), color=(0, 0, 1), **kwargs)
    Rectangle(layer, anchor=(0.25, 0.25), color=(0, 1, 0), **kwargs)
    Rectangle(layer, anchor=(0.5, 0.5), color=(1, 0, 0), **kwargs)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_relative_anchors(layer):
    """Test if ``relative_anchor`` works"""
    kwargs = dict(position=(0.5, 0.5), size=(0.5, 0.5))
    Rectangle(layer, relative_anchor=(0, 0), color=(0, 0, 1), **kwargs)
    Rectangle(layer, relative_anchor=(0.25, 0.25), color=(0, 1, 0), **kwargs)
    Rectangle(layer, relative_anchor=(0.5, 0.5), color=(1, 0, 0), **kwargs)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_relative_anchors_with_scale(layer):
    """Test if ``relative_anchor`` works"""
    kwargs = dict(position=(0.5, 0.5), scale=(0.5, 0.5))
    Rectangle(layer, relative_anchor=(0, 0), color=(0, 0, 1), **kwargs)
    Rectangle(layer, relative_anchor=(0.25, 0.25), color=(0, 1, 0), **kwargs)
    Rectangle(layer, relative_anchor=(0.5, 0.5), color=(1, 0, 0), **kwargs)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005


def test_rectangle_rotation(layer):
    """Test if ``rotation`` works"""
    Rectangle(layer, rotation=45)
    dissimilarity = layer.dissimilarity()
    assert dissimilarity < 0.005
