import contextlib

import pytest

from gillcup.expressions import Constant, Value, Concat, Interpolation
from gillcup.expressions import Progress, dump, simplify

class Flag:
    def __init__(self, value=False):
        self.value = value

    def set(self, value=True):
        self.value = value

    def unset(self):
        self.value = False

    def __bool__(self):
        return self.value


@contextlib.contextmanager
def reduce_to_const(exp):
    replacement_available_called = Flag()
    exp.replacement_available.connect(replacement_available_called.set)
    yield
    print(dump(simplify(exp)))
    assert exp == simplify(exp)
    assert isinstance(simplify(exp), Constant), type(exp.replacement)
    assert replacement_available_called


def test_value_simplification():
    exp = Value(1)
    with reduce_to_const(exp):
        exp.fix()


def test_progress_simplification(clock):
    exp = Progress(clock, 1)
    with reduce_to_const(exp):
        clock.advance_sync(1)


@pytest.mark.parametrize('chain_length', [0, 1, 2, 3, 50])
def test_interpolation_chain_simplification(chain_length):
    t = Value(0)
    exp = Interpolation(1, 0, t)
    for i in range(chain_length):
        exp = Interpolation(exp, i + 1, t)
    print(id(exp))
    with reduce_to_const(exp):
        t.fix()


def test_concat_simplification():
    v1 = Value(1)
    v2 = Value(2)
    v3 = Value(3)
    exp = Concat(v1, v2, v3)
    with reduce_to_const(exp):
        v1.fix()
        v2.fix()
        assert len(exp.children) == 2
        v3.fix()
