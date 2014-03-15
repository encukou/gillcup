"""Tests for the gillcup.clock module"""

from pytest import raises

from gillcup.clock import Clock, Subclock


def dummy_function():
    """Helper function; does nothing"""
    pass


def append_const(lst, value):
    """Helper callback; returns func that appends a constant to list"""
    def _append():
        lst.append(value)
    return _append


def append_time(lst, clock):
    """Helper callback; returns func that appends clock's time to list"""
    def _append():
        lst.append(clock.time)
    return _append


def test_clock():
    """Test that simple clock advancement works"""
    clock = Clock()
    assert clock.time == 0
    clock.advance(1)
    assert clock.time == 1


def test_scheduling():
    """Test that simple scheduling works"""
    clock = Clock()
    lst = []
    clock.schedule(1, append_const(lst, 'a'))
    clock.schedule(3, append_const(lst, 'd'))
    clock.schedule(1, append_const(lst, 'b'))
    clock.schedule(1, append_const(lst, 'c'))
    clock.advance(0)
    assert lst == []
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
    clock.advance(1)
    assert lst == ['a', 'b', 'c', 'd']


def test_speed():
    """Test that the speed property works"""
    clock = Clock()
    lst = []
    clock.schedule(10, append_const(lst, 'a'))
    clock.schedule(30, append_const(lst, 'd'))
    clock.schedule(10, append_const(lst, 'b'))
    clock.schedule(10, append_const(lst, 'c'))
    clock.speed = 10
    clock.advance(0)
    assert lst == []
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
    clock.advance(1)
    assert lst == ['a', 'b', 'c']
    clock.advance(1)
    assert lst == ['a', 'b', 'c', 'd']
    clock.speed = -1
    with raises(ValueError):
        clock.advance(4)


def test_negative_dt():
    """Test that negative advancements are blocked"""
    clock = Clock()
    with raises(ValueError):
        clock.advance(-1)
    with raises(ValueError):
        clock.schedule(-1, dummy_function)


def test_zero_dt():
    """Test that a zero advancement triggers immediate events"""
    clock = Clock()
    lst = []
    clock.schedule(0, append_const(lst, 'a'))
    clock.advance(0)
    assert lst == ['a']


def test_integer_times():
    """Test that we keep to int arithmetic as much as we can

    Ensure that even if the clock advances by float ticks, events scheduled
    at integer times get fired with clock.time being an integer.
    """
    clock = Clock()
    lst = []
    clock.schedule(1, append_time(lst, clock))
    clock.schedule(2, append_time(lst, clock))
    clock.schedule(3, append_time(lst, clock))
    for dummy in range(30):
        clock.advance(0.3)
    assert lst == [1, 2, 3]
    for time in lst:
        assert type(time) == int


def test_recursive_advance():
    """Test that calling advance() from within advance() is blocked"""
    clock = Clock()
    clock.schedule(0, lambda: clock.advance(1))
    with raises(RuntimeError):
        clock.advance(0)


def test_subclock():
    """Test Sublock works"""
    clock = Clock()
    subclock = Subclock(clock)
    subclock.advance(1)
    assert clock.time == 0
    assert subclock.time == 1
    clock.advance(1)
    assert clock.time == 1
    assert subclock.time == 2
    subclock.speed = 2
    clock.advance(1)
    assert clock.time == 2
    assert subclock.time == 4

    lst = []

    def _append_const(lst, value):
        def _append():
            print(value, clock.time, subclock.time)
            lst.append(value)
        return _append

    subclock.schedule(1, _append_const(lst, 'a'))
    clock.schedule(1, _append_const(lst, 'b'))
    subclock.schedule(2, _append_const(lst, 'c'))
    clock.advance(1)
    assert lst == ['a', 'b', 'c']


def test_subclock_speedup():
    """Test Sublock.speed works when set as attribute"""
    clock = Clock()
    subclock = Subclock(clock)
    assert subclock.time == 0
    clock.advance(1)
    assert subclock.time == 1
    subclock.speed = 2
    clock.advance(1)
    assert subclock.time == 3


def test_subclock_speed_arg():
    """Test Sublock.speed works when passed as argument"""
    clock = Clock()
    subclock = Subclock(clock, speed=2)
    assert subclock.time == 0
    clock.advance(1)
    assert subclock.time == 2
