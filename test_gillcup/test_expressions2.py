import itertools
import inspect
import math
import textwrap

import pytest

from gillcup.expressions import Constant, Value, Concat, Interpolation
from gillcup.expressions import Progress, dump, simplify


def test_value_simplification():
    exp = Value(1)
    exp.fix()
    print(dump(exp))
    assert isinstance(simplify(exp), Constant)


def test_progress_simplification(clock):
    exp = Progress(clock, 1)
    clock.advance_sync(1)
    print(dump(exp))
    assert isinstance(simplify(exp), Constant)
