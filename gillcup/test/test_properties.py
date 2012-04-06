"""Tests for the gillcup.properties module"""

from pytest import raises

from gillcup import Clock, Animation
from gillcup.properties import VectorProperty, ScaleProperty


class Box(object):
    """A Test class with some properties"""
    position = VectorProperty(3)
    size = ScaleProperty(3)


def test_defaults():
    """Test ScaleProperty and VectorProperty defaults"""
    box = Box()
    assert box.position == (0, 0, 0)
    assert box.size == (1, 1, 1)


def test_vector_assignment():
    """Test assigning to a VectorProperty"""
    box = Box()
    box.position = 1,
    assert box.position == (1, 0, 0)
    box.position = 1, 2
    assert box.position == (1, 2, 0)
    box.position = 1,
    assert box.position == (1, 0, 0)
    box.position = 1, 2, 3
    assert box.position == (1, 2, 3)
    with raises(TypeError):
        box.position = 4
    with raises(ValueError):
        box.position = 1, 2, 3, 4


def test_scale_assignment():
    """Test assigning to a ScaleProperty"""
    box = Box()
    box.size = 2,
    assert box.size == (2, 2, 2)
    box.size = 2, 3
    assert box.size == (2, 3, 1)
    box.size = 2,
    assert box.size == (2, 2, 2)
    box.size = 2, 3, 4
    assert box.size == (2, 3, 4)
    box.size = 5
    assert box.size == (5, 5, 5)


def test_vector_animation():
    """Test animating a VectorProperty"""
    box = Box()
    clock = Clock()
    clock.schedule(Animation(box, 'position', 1))
    clock.advance(1)
    assert box.position == (1, 0, 0)
    clock.schedule(Animation(box, 'position', 1, 2))
    clock.advance(1)
    assert box.position == (1, 2, 0)
    clock.schedule(Animation(box, 'position', 1))
    clock.advance(1)
    assert box.position == (1, 0, 0)
    clock.schedule(Animation(box, 'position', 1, 2, 3))
    clock.advance(1)
    assert box.position == (1, 2, 3)
    with raises(ValueError):
        Animation(box, 'position', 1, 2, 3, 4)


def test_scale_animation():
    """Test animating a ScaleProperty"""
    box = Box()
    clock = Clock()
    clock.schedule(Animation(box, 'size', 2))
    clock.advance(1)
    assert box.size == (2, 2, 2)
    clock.schedule(Animation(box, 'size', 2, 3))
    clock.advance(1)
    assert box.size == (2, 3, 1)
    clock.schedule(Animation(box, 'size', 2))
    clock.advance(1)
    assert box.size == (2, 2, 2)
    clock.schedule(Animation(box, 'size', 2, 3, 4))
    clock.advance(1)
    assert box.size == (2, 3, 4)
    with raises(ValueError):
        Animation(box, 'size', 1, 2, 3, 4)
