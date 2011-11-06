import math

import pytest

from gillcup import (Clock, AnimatedProperty, TupleProperty, Animation,
        actions, animation)

class Tone(object):
    pitch = AnimatedProperty(440)
    volume = AnimatedProperty(0)
    x, y, z = position = TupleProperty(3, (0, 0, 0))

def test_effect():
    clock = Clock()
    tone = Tone()
    clock.schedule(Animation(tone, 'pitch', 450, time=5))
    assert tone.pitch == 440
    clock.advance(1)
    assert tone.pitch == 442
    clock.advance(3)
    assert tone.pitch == 448
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 450
    tone.pitch = 440
    assert tone.pitch == 440
    clock.schedule(Animation(tone, 'pitch', 450, time=2))
    clock.advance(1)
    assert tone.pitch == 445
    clock.advance(1)
    assert tone.pitch == 450

def test_effect_scheduling():
    clock = Clock()
    tone = Tone()
    tone.volume = 60
    action = Animation(tone, 'pitch', 450, time=5)
    action += Animation(tone, 'volume', 0, time=2)
    clock.schedule(action)
    assert tone.pitch == 440 and tone.volume == 60
    clock.advance(1)
    assert tone.pitch == 442 and tone.volume == 60
    clock.advance(3)
    assert tone.pitch == 448 and tone.volume == 60
    clock.advance(1)
    assert tone.pitch == 450 and tone.volume == 60
    clock.advance(1)
    assert tone.pitch == 450 and tone.volume == 30
    clock.advance(1)
    assert tone.pitch == 450 and tone.volume == 0
    clock.advance(1)
    assert tone.pitch == 450 and tone.volume == 0

def test_tuple_property():
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'x', 2, time=2)
    action |= Animation(tone, 'y', 4, time=2)
    action |= Animation(tone, 'z', 6, time=2)
    action += Animation(tone, 'position', 0, 0, 0, time=2)
    clock.schedule(action)
    assert (tone.x, tone.y, tone.z) == tone.position == (0, 0, 0)
    clock.advance(1)
    assert (tone.x, tone.y, tone.z) == tone.position == (1, 2, 3)
    clock.advance(1)
    assert (tone.x, tone.y, tone.z) == tone.position == (2, 4, 6)
    clock.advance(1)
    assert (tone.x, tone.y, tone.z) == tone.position == (1, 2, 3)
    clock.advance(1)
    assert (tone.x, tone.y, tone.z) == tone.position == (0, 0, 0)
    tone.position = 1, 2, 0
    assert (tone.x, tone.y, tone.z) == tone.position == (1, 2, 0)
    tone.z = 3
    assert (tone.x, tone.y, tone.z) == tone.position == (1, 2, 3)

def test_target_animation():
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'volume', 2, time=2)
    action.chain(Animation(action, 'target', 0, time=2))
    clock.schedule(action)
    clock.advance(1)
    assert tone.volume == 1
    clock.advance(1)
    assert tone.volume == 2
    clock.advance(1)
    assert tone.volume == 1
    clock.advance(1)
    assert tone.volume == 0

def test_tuple_target_animation():
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'position', 2, 4, 6, time=2)
    action.chain(Animation(action, 'target', -2, -4, -6, time=2))
    clock.schedule(action)
    clock.advance(1)
    assert tone.position == (1, 2, 3)
    clock.advance(1)
    assert tone.position == (2, 4, 6)
    clock.advance(1)
    assert tone.position == (0, 0, 0)
    clock.advance(1)
    assert tone.position == (-2, -4, -6)

def test_additive_animation():
    clock = Clock()
    tone = Tone()
    base_action = Animation(tone, 'pitch', 440)
    action = animation.Add(tone, 'pitch', 20, time=2)
    clock.schedule(base_action)
    clock.schedule(action)
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 460
    clock.advance(1)
    assert tone.pitch == 460
    clock.schedule(Animation(base_action, 'target', 420, time=2))
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 440

def test_multiplicative_animation():
    clock = Clock()
    tone = Tone()
    base_action = Animation(tone, 'pitch', 440)
    action = animation.Multiply(tone, 'pitch', 2, time=2)
    clock.schedule(base_action)
    clock.schedule(action)
    clock.advance(1)
    assert tone.pitch == 440 * 1.5
    clock.advance(1)
    assert tone.pitch == 440 * 2
    clock.advance(1)
    assert tone.pitch == 440 * 2
    clock.schedule(Animation(base_action, 'target', 220, time=2))
    clock.advance(1)
    assert tone.pitch == 330 * 2
    clock.advance(1)
    assert tone.pitch == 220 * 2

def test_computed_animation():
    clock = Clock()
    tone = Tone()
    def compute(t):
        return math.sin(t) + 440
    action = animation.Computed(tone, 'pitch', func=compute, time=2)
    clock.schedule(action)
    clock.advance(0)
    assert tone.pitch == 440
    clock.advance(1)
    assert tone.pitch == 440 + math.sin(0.5)
    clock.advance(1)
    assert tone.pitch == 440 + math.sin(1)
    clock.advance(1)
    assert tone.pitch == 440 + math.sin(1)
