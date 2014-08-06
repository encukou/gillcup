import textwrap

import pytest

from gillcup.properties import AnimatedProperty
from gillcup.expressions import dump


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
