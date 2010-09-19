
from nose.tools import raises, assert_equal

from gillcup.timer import Timer
from gillcup.action import FunctionAction

def test_timer_advance():
    timer = Timer()
    assert_equal(timer.time, 0)
    timer.advance(1)
    assert_equal(timer.time, 1)
    timer.advance(1.5)
    assert_equal(timer.time, 2.5)

@raises(ValueError)
def test_timer_no_past_advance():
    timer = Timer()
    timer.advance(-1)

def test_action():
    timer = Timer()
    rv = []
    def callback():
        rv.append(timer.time)
    action = FunctionAction(callback)
    timer.advance(1)
    timer.schedule(2, action)
    assert_equal(rv, [])
    timer.advance(1)
    assert_equal(rv, [])
    timer.advance(20)
    assert_equal(rv, [3])
    timer.advance(1)
    assert_equal(rv, [3])

@raises(ValueError)
def test_timer_no_past_schedule():
    timer = Timer()
    action = FunctionAction(lambda: None)
    timer.schedule(-2, action)

def test_action_chain():
    raise NotImplementedError

def test_action_chain_multiple():
    raise NotImplementedError

def test_animated_object_float():
    raise NotImplementedError

def test_animated_object_tuple():
    raise NotImplementedError
