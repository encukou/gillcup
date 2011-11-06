import pytest

from gillcup import Clock, Action, actions

class TimeAppendingAction(Action):
    def __init__(self, lst, *args):
        super(TimeAppendingAction, self).__init__(*args)
        self.list = lst

    def __call__(self):
        self.list.append(self.clock.time)
        super(TimeAppendingAction, self).__call__()

def test_scheduling():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst)
    clock.schedule(action, 1)
    clock.advance(1)
    assert lst == [1]
    TimeAppendingAction(lst, clock, 1)
    clock.advance(1)
    assert lst == [1, 2]

def test_double_schedule():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    with pytest.raises(RuntimeError):
        clock.schedule(action, 1)

def test_double_run():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    clock.advance(1)
    with pytest.raises(RuntimeError):
        action()

def test_simple_chaining():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    action.chain(TimeAppendingAction(lst), 1)
    clock.advance(1)
    assert lst == [1]
    clock.advance(1)
    assert lst == [1, 2]

def test_delayed_chaining():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    clock.advance(1)
    assert lst == [1]
    action.chain(TimeAppendingAction(lst), 1)
    assert lst == [1]
    clock.advance(1)
    assert lst == [1, 2]
    action.chain(TimeAppendingAction(lst), 1)
    assert lst == [1, 2]
    clock.advance(1)
    assert lst == [1, 2, 3]

def test_function_caller():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    action = action.chain(actions.FunctionCaller(lst.append, 'a'), 1)
    action = action.chain(TimeAppendingAction(lst), 1)
    clock.advance(1)
    assert lst == [1]
    clock.advance(1)
    assert lst == [1, 'a']
    clock.advance(1)
    assert lst == [1, 'a', 3]

def test_delay():
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    action = action.chain(actions.Delay(1))
    action = action.chain(TimeAppendingAction(lst))
    clock.advance(1)
    assert lst == [1]
    clock.advance(1)
    assert lst == [1, 2]

def test_sequence():
    clock = Clock()
    lst = []
    action = actions.Sequence(
            TimeAppendingAction(lst),
            actions.Delay(1),
            TimeAppendingAction(lst),
            actions.Delay(1),
            TimeAppendingAction(lst),
        )
    action.chain(TimeAppendingAction(lst))
    clock.schedule(action)
    clock.advance(2)
    assert lst == [0, 1, 2, 2]

def test_parallel():
    clock = Clock()
    lst = []
    action = actions.Parallel(
            TimeAppendingAction(lst),
            TimeAppendingAction(lst),
            actions.Sequence(actions.Delay(1), TimeAppendingAction(lst)),
            actions.Sequence(actions.Delay(2), TimeAppendingAction(lst)),
        )
    action.chain(TimeAppendingAction(lst))
    clock.schedule(action)
    clock.advance(2)
    assert lst == [0, 0, 1, 2, 2]
