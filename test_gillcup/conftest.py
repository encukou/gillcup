import textwrap

import pytest
from hypothesis import settings

from gillcup.clocks import Clock, Subclock
from gillcup.expressions import dump


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def subclock():
    return Subclock()


@pytest.yield_fixture
def check_dump():

    def check_dump(expression, expected):
        dumped = dump(expression)
        print(dumped)
        expected = textwrap.dedent(expected.strip('\n').rstrip())
        assert dumped == expected

    yield check_dump


settings.register_profile("ci", settings(
    max_examples=1000,
    stateful_step_count=500,
))

settings.register_profile("thorough", settings(
    max_examples=10000,
    stateful_step_count=1000,
    timeout=-1,
))
