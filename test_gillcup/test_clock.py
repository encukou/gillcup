"""Tests for the gillcup.clock module"""

import asyncio

import pytest

import gillcup
from gillcup.clock import Clock, Subclock


@pytest.fixture
def clock():
    return Clock()


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


def test_clock(clock):
    """Test that simple clock advancement works"""
    assert clock.time == 0
    clock.advance_sync(1)
    assert clock.time == 1


def test_scheduling(clock):
    """Test that simple scheduling works"""
    lst = []
    clock.schedule(1, append_const(lst, 'a'))
    clock.schedule(3, append_const(lst, 'd'))
    clock.schedule(1, append_const(lst, 'b'))
    clock.schedule(1, append_const(lst, 'c'))
    clock.advance_sync(0)
    assert lst == []
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c', 'd']


def test_speed(clock):
    """Test that the speed property works"""
    lst = []
    clock.schedule(10, append_const(lst, 'a'))
    clock.schedule(30, append_const(lst, 'd'))
    clock.schedule(10, append_const(lst, 'b'))
    clock.schedule(10, append_const(lst, 'c'))
    clock.speed = 10
    clock.advance_sync(0)
    assert lst == []
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c', 'd']
    clock.speed = -1
    with pytest.raises(ValueError):
        clock.advance_sync(4)


def test_negative_dt(clock):
    """Test that negative advancements are blocked"""
    with pytest.raises(ValueError):
        clock.advance_sync(-1)
    with pytest.raises(ValueError):
        clock.schedule(-1, dummy_function)


def test_zero_dt(clock):
    """Test that a zero advancement triggers immediate events"""
    lst = []
    clock.schedule(0, append_const(lst, 'a'))
    clock.advance_sync(0)
    assert lst == ['a']


def test_integer_times(clock):
    """Test that we keep to int arithmetic as much as we can

    Ensure that even if the clock advances by float ticks, events scheduled
    at integer times get fired with clock.time being an integer.
    """
    lst = []
    clock.schedule(1, append_time(lst, clock))
    clock.schedule(2, append_time(lst, clock))
    clock.schedule(3, append_time(lst, clock))
    for dummy in range(30):
        clock.advance_sync(0.3)
    assert lst == [1, 2, 3]
    for time in lst:
        assert type(time) == int


def test_recursive_advance(clock):
    """Test that calling advance() from within advance() is blocked"""
    @gillcup.coroutine
    def advance():
        print("Advancing!")
        yield from clock.advance(1)
    clock.task(advance())
    with pytest.raises(RuntimeError):
        clock.advance_sync(1)


def test_subclock(clock):
    """Test Sublock works"""
    subclock = Subclock(clock)
    subclock.advance_sync(1)
    assert clock.time == 0
    assert subclock.time == 1
    clock.advance_sync(1)
    assert clock.time == 1
    assert subclock.time == 2
    subclock.speed = 2
    clock.advance_sync(1)
    assert clock.time == 2
    assert subclock.time == 4

    lst = []

    def _append_const(lst, value):
        def _append():
            lst.append(value)
        return _append

    subclock.schedule(1, _append_const(lst, 'a'))
    clock.schedule(1, _append_const(lst, 'b'))
    subclock.schedule(2, _append_const(lst, 'c'))
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']


def test_subclock_speedup(clock):
    """Test Sublock.speed works when set as attribute"""
    subclock = Subclock(clock)
    assert subclock.time == 0
    clock.advance_sync(1)
    assert subclock.time == 1
    subclock.speed = 2
    clock.advance_sync(1)
    assert subclock.time == 3


def test_subclock_speed_arg(clock):
    """Test Sublock.speed works when passed as argument"""
    subclock = Subclock(clock, speed=2)
    assert subclock.time == 0
    clock.advance_sync(1)
    assert subclock.time == 2


@gillcup.coroutine
def appending_task(lst):
    lst.append(0)
    yield 1
    lst.append(1)
    yield 1
    lst.append(2)
    yield 1
    lst.append(3)
    return 'ok'


def test_task(clock):
    lst = []
    future = clock.task(appending_task(lst))
    assert lst == []
    assert not future.done()
    clock.advance_sync(0)
    assert lst == [0]
    clock.advance_sync(1)
    assert lst == [0, 1]
    clock.advance_sync(1)
    assert lst == [0, 1, 2]
    clock.advance_sync(0.5)
    assert lst == [0, 1, 2]
    assert not future.done()
    clock.advance_sync(0.5)
    assert lst == [0, 1, 2, 3]
    assert future.done()
    clock.advance_sync(500)
    assert lst == [0, 1, 2, 3]
    assert future.result() == 'ok'


@gillcup.coroutine
def error_task():
    raise RuntimeError('bad')
    yield


def test_error_task(clock):
    future = clock.task(error_task())
    assert not future.done()
    clock.advance_sync(0)
    assert future.done()
    assert isinstance(future.exception(), RuntimeError)
    assert str(future.exception()) == 'bad'


@gillcup.coroutine
def complex_task(lst):
    try:
        yield from error_task()
    except RuntimeError:
        lst.append('X')
    return (yield from appending_task(lst))


def test_complex_task(clock):
    lst = []
    future = clock.task(complex_task(lst))
    assert not future.done()
    clock.advance_sync(0)
    assert lst == ['X', 0]
    clock.advance_sync(3)
    assert lst == ['X', 0, 1, 2, 3]
    assert future.done()
    assert future.result() == 'ok'


def test_double_complex_task(clock):
    lst = []
    future1 = clock.task(complex_task(lst))
    future2 = clock.task(complex_task(lst))
    assert not future1.done()
    assert not future2.done()
    clock.advance_sync(0)
    assert lst == ['X', 0, 'X', 0]
    clock.advance_sync(3)
    assert lst == ['X', 0, 'X', 0, 1, 1, 2, 2, 3, 3]
    assert future1.done()
    assert future1.result() == 'ok'
    assert future2.done()
    assert future2.result() == 'ok'
