import pytest

from gillcup import Clock, Action
from gillcup.chaining import WaitForAny, WaitForAll
from gillcup import actions

class TimeAppendingAction(Action):
    def __init__(self, lst, *args):
        super(TimeAppendingAction, self).__init__(*args)
        self.list = lst

    def __call__(self):
        super(TimeAppendingAction, self).__call__()
        self.list.append(self.clock.time)

def test_wait_for_any():
    clock = Clock()
    lst = []
    action1 = Action(clock, 2)
    action2 = Action(clock, 3)
    action3 = Action(clock, 4)
    WaitForAny(action1, action2, action3).chain(TimeAppendingAction(lst))
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == [2]
    clock.advance(1)
    assert lst == [2]
    clock.advance(1)
    assert lst == [2]

def test_wait_for_any_add():
    clock = Clock()
    lst = []
    action1 = Action(clock, 2)
    action2 = Action(clock, 3)
    action3 = Action(clock, 4)
    waiter = WaitForAny()
    waiter.chain(TimeAppendingAction(lst))
    waiter.add(action1, action2, action3)
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == [2]
    clock.advance(1)
    assert lst == [2]
    clock.advance(1)
    assert lst == [2]

def test_wait_for_all():
    clock = Clock()
    lst = []
    action1 = Action(clock, 2)
    action2 = Action(clock, 3)
    action3 = Action(clock, 4)
    WaitForAll(action1, action2, action3).chain(TimeAppendingAction(lst))
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == [4]
    clock.advance(1)
    assert lst == [4]

def test_mismatched_clocks():
    for Wait in WaitForAny, WaitForAll:
        clock1 = Clock()
        clock2 = Clock()
        Wait(Action(clock1), Action(clock2))
        with pytest.raises(ValueError):
            clock1.advance(1)
            clock2.advance(1)
