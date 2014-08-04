import pytest

from gillcup.properties import AnimatedProperty


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
