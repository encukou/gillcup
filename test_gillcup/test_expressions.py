import pytest

from gillcup.expressions import Constant


def test_simple_value():
    exp = Constant(3)
    assert tuple(exp) == (3, )
    assert float(exp) == 3.0
    assert int(exp) == 3

    assert exp == 3
    assert exp != 4
    assert exp < 4
    assert exp > 2
    assert exp <= 3
    assert exp >= 3

    assert exp == (3,)
    assert exp != (4,)
    assert exp < (4,)
    assert exp > (2,)
    assert exp <= (3,)
    assert exp >= (3,)


def test_tuple_value():
    exp = Constant(3, 4, 5)
    assert tuple(exp) == (3, 4, 5)
    with pytest.raises(ValueError):
        float(exp)
    with pytest.raises(ValueError):
        int(exp)

    assert exp == (3, 4, 5)
    assert exp != (3, 5, 5)
    assert exp < (3, 4, 6)
    assert exp > (3, 4, 4)
    assert exp <= (3, 5, 5)
    assert exp >= (3, 2, 5)
