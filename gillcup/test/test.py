
from nose.tools import raises, assert_equal

from gillcup.timer import Timer
from gillcup.action import FunctionAction, EffectAction
from gillcup.animatedobject import AnimatedObject
from gillcup.effect import InterpolationEffect

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

def test_animated_object_float():
    timer = Timer()
    obj = AnimatedObject()
    obj.attr = 1
    eff = InterpolationEffect(3, 2)
    eff.start(timer, obj, 'attr')
    assert_equal(obj.attr, 1)
    timer.advance(1)
    assert_equal(obj.attr, 2)
    timer.advance(1)
    assert_equal(obj.attr, 3)
    timer.advance(1)
    assert_equal(obj.attr, 3)

def test_animated_object_tuple():
    timer = Timer()
    obj = AnimatedObject()
    obj.attr = 1, 2, 3
    eff = InterpolationEffect((3, 2, 1), 2)
    eff.interpolate = lambda a, b, t: tuple(
                eff.interpolateScalar(aa, bb, t) for aa, bb in zip(a, b)
            )
    eff.start(timer, obj, 'attr')
    assert_equal(obj.attr, (1, 2, 3))
    timer.advance(1)
    assert_equal(obj.attr, (2, 2, 2))
    timer.advance(1)
    assert_equal(obj.attr, (3, 2, 1))
    timer.advance(1)
    assert_equal(obj.attr, (3, 2, 1))

def test_action_chain():
    timer = Timer()
    rv = []
    def callback():
        rv.append(timer.time)
    action = FunctionAction(callback)
    obj = AnimatedObject()
    obj.attr = 1
    eff = InterpolationEffect(3, 2)
    eff.chain(action)
    eff.start(timer, obj, 'attr')
    timer.advance(1)
    assert_equal(rv, [])
    timer.advance(2)
    assert_equal(rv, [2])
    timer.advance(1)
    assert_equal(rv, [2])

def test_action_chain_multiple():
    timer = Timer()
    rv = []
    def callback():
        rv.append(timer.time)
    action = FunctionAction(callback)
    obj = AnimatedObject()
    obj.attr = 1
    eff1 = InterpolationEffect(3, 2)
    eff2 = InterpolationEffect(1, 2)
    eff1.chain(EffectAction(eff2, obj, 'attr'))
    eff1.start(timer, obj, 'attr')
    assert_equal(obj.attr, 1)
    timer.advance(1)
    assert_equal(obj.attr, 2)
    timer.advance(1)
    assert_equal(obj.attr, 3)
    timer.advance(1)
    assert_equal(obj.attr, 2)
    timer.advance(1)
    assert_equal(obj.attr, 1)
    timer.advance(1)
    assert_equal(obj.attr, 1)
