"""Tests for the gillcup.clock module"""

import asyncio

import pytest

from gillcup.clocks import Subclock, coroutine


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
    clock.sleep(100)
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
    clock.sleep(100)
    lst = []
    clock.schedule(10, append_const(lst, 'a'))
    clock.schedule(30, append_const(lst, 'd'))
    clock.schedule(10, append_const(lst, 'b'))
    clock.schedule(10, append_const(lst, 'c'))
    clock.speed = 10
    clock.advance_sync(0)
    assert lst == []
    assert clock.time == 0
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']
    assert clock.time == 10
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c']
    assert clock.time == 20
    clock.advance_sync(1)
    assert lst == ['a', 'b', 'c', 'd']
    assert clock.time == 30
    clock.speed = -1
    with pytest.raises(ValueError):
        clock.advance_sync(4)
    assert clock.time == 30


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


def test_future_delay(clock):
    """Test that Gillcup futures can be waited for"""
    assert clock.time == 0
    clock.advance_sync(clock.sleep(1))
    clock.sleep(100)
    assert clock.time == 1


def test_asyncio_future_delay(clock):
    """Test that futures can be waited for"""
    assert clock.time == 0
    aio_future = asyncio.Future()
    sleep_future = clock.sleep(1)
    clock.sleep(100)
    sleep_future.add_done_callback(lambda f: aio_future.set_result(None))
    clock.advance_sync(aio_future)
    assert clock.time == 1


def test_advance_to_end(clock):
    """Test that advance(None) works"""
    assert clock.time == 0
    clock.sleep(10)
    clock.sleep(100)
    clock.advance_sync(None)
    assert clock.time == 100


def test_end_category(clock):
    """Test work scheduled for the current time is done when advance() finishes
    """
    lst = []
    assert clock.time == 0
    aio_future = asyncio.Future()
    sleep_future = clock.sleep(1)
    aio_future.add_done_callback(lambda f: clock.sleep(1))
    aio_future.add_done_callback(lambda f: lst.append('done'))
    sleep_future.add_done_callback(lambda f: aio_future.set_result(None))
    clock.advance_sync(aio_future)
    assert clock.time == 1
    assert lst == ['done']


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
    @coroutine
    def advance():
        print("Advancing!")
        yield 0.1
        yield from clock.advance(1)
    future = clock.task(advance())
    clock.advance_sync(1)
    with pytest.raises(RuntimeError):
        future.result()


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


def test_clock_speedup(clock):
    """Test Clock.speed works"""
    clock.speed = 2
    clock.task(clock.sleep(1))
    assert clock.time == 0
    clock.advance_sync(2)


def test_subclock_speedup(clock):
    """Test Subclock.speed works when set as attribute"""
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


@coroutine
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


@coroutine
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


@coroutine
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


@coroutine
def delaying_task(lst):
    for i in range(100):
        yield
    lst.append('X')


def test_delaying_task(clock):
    lst = []
    clock.task(appending_task(lst))
    clock.task(delaying_task(lst))
    clock.advance_sync(1)
    assert lst == [0, 'X', 1]
