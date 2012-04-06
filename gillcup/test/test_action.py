"""Tests for the gillcup.action module"""

from pytest import raises, mark

from gillcup import Clock, Action, actions


class TimeAppendingAction(Action):
    """Action that appends the current time to a list when triggered"""
    def __init__(self, lst, *args, **kwargs):
        super(TimeAppendingAction, self).__init__(*args, **kwargs)
        self.list = lst

    def __call__(self):
        self.list.append(self.clock.time)
        super(TimeAppendingAction, self).__call__()


def test_scheduling():
    """Test basic scheduling of actions"""
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst)
    clock.schedule(action, 1)
    clock.advance(1)
    assert lst == [1]
    TimeAppendingAction(lst, clock, 1)
    clock.advance(1)
    assert lst == [1, 2]
    with raises(ValueError):
        TimeAppendingAction(lst, dt=1)


def test_double_schedule():
    """Test scheduling an Action twice is blocked"""
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    with raises(RuntimeError):
        clock.schedule(action, 1)


def test_double_run():
    """Test running an Action twice is blocked"""
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    clock.advance(1)
    with raises(RuntimeError):
        action()


def test_simple_chaining():
    """Test basic chaining"""
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    action.chain(TimeAppendingAction(lst), 1)
    clock.advance(1)
    assert lst == [1]
    clock.advance(1)
    assert lst == [1, 2]


def test_delayed_chaining():
    """Test chaining with a delay"""
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
    """Test the FunctionCaller action"""
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst, clock, 1)
    action = action.chain(actions.FunctionCaller(lst.append, 'a'), 1)
    action = action.chain(TimeAppendingAction(lst), 1)  # pylint: disable=E1101
    clock.advance(1)
    assert lst == [1]
    clock.advance(1)
    assert lst == [1, 'a']
    clock.advance(1)
    assert lst == [1, 'a', 3]


def test_delay():
    """Test the Delay action"""
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
    """Test the Sequence action (explicit instantiation)"""
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
    """Test the Parallel action (explicit instantiation)"""
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


def test_sequence_operator():
    """Test the Sequence action (via + operator)"""
    clock = Clock()
    lst = []
    action = TimeAppendingAction(lst) + 1 + TimeAppendingAction(lst)
    action = 1 + action + 1 + (lambda: lst.append('a'))
    action += lambda: lst.append('b')
    action.chain(lambda: lst.append('end'))
    clock.schedule(action)
    assert lst == []
    clock.advance(2)
    assert lst == [1, 2]
    clock.advance(2)
    assert lst == [1, 2, 'a', 'b', 'end']
    with raises(TypeError):
        action += None
    with raises(TypeError):
        action = None + action


def test_parallel_operator():
    """Test the Parallel action (via | operator)"""
    clock = Clock()
    lst = []
    action = 0.5 + TimeAppendingAction(lst) | 1 + TimeAppendingAction(lst)
    action = 2 + TimeAppendingAction(lst) | action | (lambda: lst.append('a'))
    action |= 3 + TimeAppendingAction(lst)
    action.chain(lambda: lst.append('end'))
    action = 23 | action
    action.chain(lambda: lst.append('real end'))
    clock.schedule(action)
    assert lst == []
    clock.advance(3)
    assert lst == ['a', 0.5, 1, 2, 3, 'end']
    clock.advance(20)
    assert lst == ['a', 0.5, 1, 2, 3, 'end', 'real end']
    with raises(TypeError):
        action |= None
    with raises(TypeError):
        action = None | action


def test_chain_on_expired():
    """Test that stuff chained on an expired action is scheduled"""
    clock = Clock()
    lst = []
    action = actions.Delay(3)
    clock.schedule(action)
    action.chain(lambda: lst.append('a'), 1)
    clock.advance(1)
    assert lst == []
    action.chain(lambda: lst.append('b'), 1)
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == []
    clock.advance(1)
    assert lst == ['a', 'b']
    action.chain(lambda: lst.append('c'), 1)
    clock.advance(0)
    assert lst == ['a', 'b']
    clock.advance(1)
    assert lst == ['a', 'b', 'c']


@mark.parametrize(('maker'), [
        lambda g: Action.coerce(g()),
        lambda g: actions.process_generator(g)(),
    ])
def test_generator(maker):
    """Test actions.Generator"""
    clock = Clock()
    lst = []
    def _generator():
        yield 1
        lst.append('a')
        yield 1
        lst.append('b')
        yield TimeAppendingAction(lst)
        yield 1
    action = maker(_generator)
    clock.schedule(action)
    action.chain(TimeAppendingAction(lst))
    assert lst == []
    clock.advance(1)
    assert lst == ['a']
    clock.advance(1)
    assert lst == ['a', 'b', 2]
    clock.advance(1)
    assert lst == ['a', 'b', 2, 3]
