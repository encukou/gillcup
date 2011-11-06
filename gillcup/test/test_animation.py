import pytest

from gillcup import Clock, AnimatedProperty, Animation, actions

class Tone(object):
    pitch = AnimatedProperty(440)
    volume = AnimatedProperty(0)

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
