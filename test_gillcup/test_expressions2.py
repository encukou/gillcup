import contextlib

import pytest

from gillcup.expressions import Constant, Value, Concat, Interpolation, Slice
from gillcup.expressions import Progress, dump, simplify
from gillcup.expressions import Sum, Difference, Product, Quotient, Neg

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
    repl_available = Flag(simplify(exp) is not exp)
    exp.replacement_available.connect(repl_available.set)
    yield exp
    print(dump(simplify(exp)))
    assert exp == simplify(exp)
    assert isinstance(simplify(exp), Constant), type(exp.replacement)
    assert repl_available


def test_value_simplification():
    with reduce_to_const(Value(1)) as exp:
        exp.fix()


def test_progress_simplification(clock):
    with reduce_to_const(Progress(clock, 1)):
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
    with reduce_to_const(Concat(v1, v2, v3)) as exp:
        v1.fix()
        v2.fix()
        assert len(exp.children) == 2
        v3.fix()


@pytest.mark.parametrize(['start', 'end'], [
    (None, None), (0, 1), (0, -1), (-1, None), (0, 0), (3, 2)])
def test_slice_simplification(start, end):
    val = Value(1, 2, 3, 4)
    with reduce_to_const(Slice(val, slice(start, end))):
        val.fix()


def test_neg_simplification():
    val = Value(1, 2, 3, 4)
    with reduce_to_const(Neg(val)):
        val.fix()


@pytest.mark.parametrize('op', [Sum, Difference, Product, Quotient])
def test_reduce_simplification(op):
    v1 = Value(1)
    v2 = Value(2)
    v3 = Value(3)
    with reduce_to_const(op([v1, v2, v3])) as exp:
        v1.fix()
        v2.fix()
        assert len(exp.children) == 2
        v3.fix()
