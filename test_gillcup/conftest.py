import textwrap

import pytest

from gillcup.clock import Clock, Subclock
from gillcup.expressions import dump


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def subclock():
    return Subclock()


@pytest.yield_fixture
def check_dump():
    called = False

    def check_dump(expression, expected):
        nonlocal called
        called = True
        dumped = dump(expression)
        print(dumped)
        expected = textwrap.dedent(expected.strip('\n').rstrip())
        assert dumped == expected

    yield check_dump
    assert called, 'check_dump was not called'
