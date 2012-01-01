import math

import pytest

from gillcup import (Clock, AnimatedProperty, TupleProperty, Animation,
        actions, animation)
from gillcup import easing as easing_mod

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
    base_action = Animation(tone, 'pitch', 420, delay=3, time=2)
    action = animation.Add(tone, 'pitch', 20, time=2)
    clock.schedule(base_action)
    clock.schedule(action)
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 460
    clock.advance(1)
    assert tone.pitch == 460
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 440

def test_multiplicative_animation():
    clock = Clock()
    tone = Tone()
    base_action = Animation(tone, 'pitch', 220, time=2, delay=3)
    action = animation.Multiply(tone, 'pitch', 2, time=2)
    clock.schedule(base_action)
    clock.schedule(action)
    clock.advance(1)
    assert tone.pitch == 440 * 1.5
    clock.advance(1)
    assert tone.pitch == 440 * 2
    clock.advance(1)
    assert tone.pitch == 440 * 2
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

def test_delay():
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'pitch', 450, time=2, delay=1)
    clock.schedule(action)
    clock.advance(1)
    assert tone.pitch == 440
    clock.advance(1)
    assert tone.pitch == 445
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 450

def test_infinite_timing():
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'pitch', 450, time=1, timing='infinite')
    clock.schedule(action)
    assert tone.pitch == 440
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 460
    clock.advance(1)
    assert tone.pitch == 470
    clock.advance(0.5)
    assert tone.pitch == 475

def test_infinite_timing():
    clock = Clock()
    tone = Tone()
    clock.advance(1)
    action = Animation(tone, 'pitch', 450, time=1, timing='absolute')
    clock.schedule(action)
    clock.advance(0)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 460
    clock.advance(1)
    assert tone.pitch == 470
    clock.advance(0.5)
    assert tone.pitch == 475

def test_easing():
    easings = []
    for easing in 'linear quad cubic quart quint sin exp circ'.split():
        easings.append(easing)
        for mod in [''] + '.in_ .out .in_out .out_in'.split():
            easings.append(easing + mod)
        easings.append(getattr(easing_mod, easing))
    for easing in (easing_mod.linear, easing_mod.exp, easing_mod.bounce(2)):
        easings.append(easing)
        for mod in 'in_ out in_out out_in'.split():
            easings.append(getattr(easing, mod))
    for easing in easings:
        print easing
        clock = Clock()
        tone = Tone()
        action = Animation(tone, 'pitch', 450, time=2, easing=easing)
        clock.schedule(action)
        for i in xrange(20):
            clock.advance(0.05)
            assert 440 < tone.pitch < 450
        clock.advance(1)
        assert tone.pitch == 450