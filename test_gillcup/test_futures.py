import asyncio

import pytest

import gillcup.futures


@pytest.fixture(params=('asyncio', 'gillcup'))
def future_type(request):
    return request.param


@pytest.fixture
def asyncio_future():
    return asyncio.Future()


@pytest.fixture
def future(asyncio_future, future_type, clock):
    if future_type == 'asyncio':
        return asyncio_future
    elif future_type == 'gillcup':
        return gillcup.futures.Future(clock, asyncio_future)
    else:
        raise ValueError(future_type)


def test_ground_state(future):
    assert not future.done()
    assert not future.cancelled()
    with pytest.raises(asyncio.InvalidStateError):
        future.result()
    with pytest.raises(asyncio.InvalidStateError):
        future.exception()


def test_done_result(future):
    future.set_result('ok')
    assert future.done()
    assert not future.cancelled()
    assert future.result() == 'ok'
    assert future.exception() is None


def test_done_exception(future):
    future.set_exception(RuntimeError('bad'))
    assert future.done()
    assert not future.cancelled()
    with pytest.raises(RuntimeError) as exc_info:
        future.result()
    assert str(exc_info.value) == 'bad'
    assert future.exception() is exc_info.value


def test_done_cancel(future):
    future.cancel()
    assert future.done()
    assert future.cancelled()
    with pytest.raises(asyncio.CancelledError) as exc_info:
        future.result()
    with pytest.raises(asyncio.CancelledError) as exc_info:
        future.exception()


def test_wrapped(future, asyncio_future, future_type, clock):
    if future_type == 'gillcup':
        assert clock.wait_for(future) is future
        assert future._wrapped is asyncio_future


def test_scheduling(future, clock):
    flag = False

    def callback(fut):
        assert fut is future
        nonlocal flag
        flag = True

    future.add_done_callback(callback)
    future.set_result(None)
    assert not flag
    clock.advance_sync(0)
    assert flag


def test_unscheduling(future, future_type, clock):
    flag = False
    callback = lambda: None
    callback2 = lambda: None
    future.add_done_callback(callback)
    assert future.remove_done_callback(callback) == 1
    future.add_done_callback(callback)
    future.add_done_callback(callback)
    future.add_done_callback(callback2)
    assert future.remove_done_callback(callback) == 2
    assert future.remove_done_callback(callback2) == 1
