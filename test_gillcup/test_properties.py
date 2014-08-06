import textwrap

import pytest

from gillcup.properties import AnimatedProperty
from gillcup.expressions import Box, Progress, dump


class Buzzer:
    volume = AnimatedProperty(0)
    pitch = AnimatedProperty(440)
    position = x, y, z = AnimatedProperty(0, 0, 0)


@pytest.fixture
def buzzer():
    return Buzzer()


def test_defaults(buzzer):
    assert buzzer.volume == 0
    assert buzzer.pitch == 440
    assert buzzer.position == (0, 0, 0)
    assert buzzer.x == buzzer.y == buzzer.z == 0


def test_setting_scalar(buzzer):
    buzzer.volume = 50
    assert buzzer.volume == 50
    assert buzzer.volume == (50,)


def test_setting_vector(buzzer):
    buzzer.position = 1, 2, 3
    assert buzzer.position == (1, 2, 3)
    assert buzzer.x == 1
    assert buzzer.y == 2
    assert buzzer.z == 3


def test_props_are_boxes(buzzer):
    assert isinstance(buzzer.volume, Box)
    buzzer.volume = 50
    assert isinstance(buzzer.volume, Box)
    buzzer.volume == (50,)
    assert isinstance(buzzer.volume, Box)


def test_attempt_setting_expression(buzzer):
    with pytest.raises(TypeError):
        buzzer.volume = buzzer.pitch


def test_separate_instances_scalar(buzzer):
    buzzer2 = Buzzer()
    buzzer2.volume = 50
    assert buzzer2.volume == 50
    assert buzzer.volume == 0


def test_separate_instances_vector(buzzer):
    buzzer2 = Buzzer()
    buzzer2.x = 5
    assert buzzer2.position == (5, 0, 0)
    assert buzzer.position == (0, 0, 0)


def test_property_naming():
    class Foo:
        namedprop = AnimatedProperty(5, name='namedprop')
        unnamedprop = AnimatedProperty(5)

        def __repr__(self):
            return '<a Foo>'

    assert Foo.namedprop.name == 'namedprop'
    assert Foo.unnamedprop.name == '<unnamed property>'

    foo = Foo()

    assert foo.namedprop.pretty_name == 'namedprop of <a Foo>'
    assert foo.unnamedprop.pretty_name == '<unnamed property> of <a Foo>'

    assert dump(foo.namedprop) == textwrap.dedent("""
        namedprop of <a Foo> <5.0>:
          Constant <5.0>
    """).strip()

    assert dump(foo.unnamedprop) == textwrap.dedent("""
        <unnamed property> of <a Foo> <5.0>:
          Constant <5.0>
    """).strip()


def test_iadd(buzzer):
    buzzer.volume += 3
    assert buzzer.volume == 3


def test_set_progress(buzzer, clock):
    buzzer.volume = Progress(clock, 2) * 100
    assert buzzer.volume == 0
    clock.advance_sync(1)
    assert buzzer.volume == 50
    clock.advance_sync(1)
    assert buzzer.volume == 100


def test_add_progress(buzzer, clock):
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.pitch == 460


def test_set_to_property(buzzer):
    buzzer.volume = buzzer.pitch
    assert buzzer.volume == 440
    assert buzzer.pitch == 440


def test_set_to_property_animated(buzzer, clock):
    buzzer.pitch += Progress(clock, 2) * 20
    buzzer.volume = buzzer.pitch
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 450
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 460
    assert buzzer.pitch == 460


def test_set_to_property_divergent(buzzer, clock):
    buzzer.volume = buzzer.pitch
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 440
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 440
    assert buzzer.pitch == 460


def test_set_to_property_linked(buzzer, clock):
    buzzer.volume.link(buzzer.pitch)
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 450
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 460
    assert buzzer.pitch == 460
