"""Tests for the gillcup.animations module"""

from __future__ import unicode_literals, division, print_function

import math
import weakref
import gc

from pytest import raises

from gillcup import (Clock, AnimatedProperty, TupleProperty, Animation,
        animation, effect)
from gillcup import easing as easing_mod


class ToneWithProperties(object):
    """Test class with some animated properties"""
    pitch = AnimatedProperty(440)
    volume = AnimatedProperty(0)
    x, y, z = position = TupleProperty(0, 0, 0)


def pytest_generate_tests(metafunc):
    """Let Tone be injected in all tests!"""
    if "Tone" in metafunc.funcargnames:
        metafunc.parametrize("Tone", [ToneWithProperties])


def test_animation(Tone):
    """Test a simple animation"""
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
    clock.schedule(Animation(tone, 'pitch', 480, time=4))
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 460
    tone.pitch = 500
    assert tone.pitch == 500
    del tone.pitch
    assert tone.pitch == 440

    with raises(ValueError):
        Animation(tone, 'pitch', 450, target=460)


def test_animation_scheduling(Tone):
    """Test the scheduling of animations"""
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


def test_tuple_property(Tone):
    """Test animating a TupleProperty"""
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


def test_target_animation(Tone):
    """Test animating the targer of an animation... Meta!"""
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'volume', 2, time=2, dynamic=True)
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


def test_tuple_target_animation(Tone):
    """Test animating the targer of a TupleAnimation"""
    clock = Clock()
    tone = Tone()
    action = Animation(tone, 'position', 2, 4, 6, time=2, dynamic=True)
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


def test_additive_animation(Tone):
    """Test the animation.Add flavor of animation"""
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


def test_multiplicative_animation(Tone):
    """Test the animation.Multiply flavor of animation"""
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


def test_computed_animation(Tone):
    """Test the animation.Computed flavor of animation"""
    def _compute(t):
        return math.sin(t) + 440
    clock = Clock()
    tone = Tone()
    action = animation.Computed(tone, 'pitch', func=_compute, time=2)
    clock.schedule(action)
    clock.advance(0)
    assert tone.pitch == 440
    clock.advance(1)
    assert tone.pitch == 440 + math.sin(0.5)
    clock.advance(1)
    assert tone.pitch == 440 + math.sin(1)
    clock.advance(1)
    assert tone.pitch == 440 + math.sin(1)


def test_delay(Tone):
    """Test the delay argument"""
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


def test_infinite_timing(Tone):
    """Test timing='infinite'"""
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


def test_absolute_timing(Tone):
    """Test timing='absolute'"""
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


def test_custom_timing(Tone):
    """Test custom timing"""
    clock = Clock()
    tone = Tone()
    clock.advance(1)
    action = Animation(tone, 'pitch', 450, time=1,
            timing=lambda t, s, d: (t - s) / d / 2)
    clock.schedule(action)
    clock.advance(0)
    assert tone.pitch == 440
    clock.advance(1)
    assert tone.pitch == 445
    clock.advance(1)
    assert tone.pitch == 450
    clock.advance(1)
    assert tone.pitch == 455


def test_easing(Tone):
    """Test all kinds of easing functions"""
    easings = []
    for easing in ['linear', 'quadratic', 'cubic', 'quartic', 'quintic',
            'sine', 'exponential', 'circular']:
        easings.append(easing)
        for mod in [''] + '.in_ .out .in_out .out_in'.split():
            easings.append(easing + mod)
        easings.append(getattr(easing_mod, easing))
    for easing in (easing_mod.linear, easing_mod.exponential,
            easing_mod.bounce(2)):
        easings.append(easing)
        for mod in 'in_ out in_out out_in'.split():
            easings.append(getattr(easing, mod))
    for easing in easings:
        print(easing)
        clock = Clock()
        tone = Tone()
        action = Animation(tone, 'pitch', 450, time=2, easing=easing)
        clock.schedule(action)
        for dummy in range(21):
            clock.advance(0.05)
            assert 440 < tone.pitch < 450
        clock.advance(1)
        assert tone.pitch == 450
    for parameter in 0.5, 1, 2, 3:
        for easing in easings + [
                easing_mod.bounce(parameter),
                easing_mod.overshoot(parameter),
                easing_mod.elastic(parameter),
            ]:
            print(easing)
            clock = Clock()
            tone = Tone()
            action = Animation(tone, 'pitch', 450, time=1, easing=easing)
            clock.schedule(action)
            assert tone.pitch == 440
            clock.advance(1)
            assert tone.pitch == 450
    assert easing_mod.circular(2) == 1  # possible sqrt of neg. number


def test_easing_normalization():
    """Test easingfunc normalization works as advertised"""
    for base_func in (lambda t: t * 4 + 3), (lambda t: t):
        f = easing_mod.normalized(base_func)
        assert [t / 16 for t in range(20)] == [f(t / 16) for t in range(20)]


def test_simple_resource_freeing(Tone):
    """Assert unneeded animations don't linger around"""
    clock = Clock()
    tone = Tone()
    anim = Animation(tone, 'pitch', 450, time=1)
    clock.schedule(anim)
    ref = weakref.ref(anim)
    del anim
    clock.advance(1)
    gc.collect()
    assert tone.pitch == 450
    assert ref() is None


def test_resource_freeing_of_parent(Tone):
    """Assert unneeded animations don't linger around if shadowed"""
    clock = Clock()
    tone = Tone()
    anim = Animation(tone, 'pitch', 450, time=1)
    clock.schedule(anim)
    clock.schedule(Animation(tone, 'pitch', 460, time=1))
    ref = weakref.ref(anim)
    del anim
    clock.advance(1)
    gc.collect()
    assert tone.pitch == 460
    assert ref() is None


def test_resource_freeing_of_add_parent(Tone):
    """Assert unneeded animations don't linger around if shadowed by Add"""
    clock = Clock()
    tone = Tone()
    anim = Animation(tone, 'pitch', 450, time=1)
    clock.schedule(anim)
    clock.schedule(animation.Add(tone, 'pitch', 50, time=10))
    ref = weakref.ref(anim)
    del anim
    clock.advance(1)
    gc.collect()
    assert tone.pitch == 455
    assert ref() is None


def test_effect_apply(Tone):
    """Test direct application of an Effect"""
    tone = Tone()
    assert tone.pitch == 440
    effect.ConstantEffect(450).apply_to(tone, 'pitch')
    assert tone.pitch == 450
