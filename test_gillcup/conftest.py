import pytest

from gillcup.clock import Clock, Subclock


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def subclock():
    return Subclock()
