import pytest

from gillcup.expressions import Constant, Value


@pytest.mark.parametrize('exp', [Constant(3), Value(3)])
def test_simple_value(exp):
    assert tuple(exp) == (3, )
    assert float(exp) == 3.0
    assert int(exp) == 3
    assert repr(exp) == '<3.0>'

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


@pytest.mark.parametrize('exp', [Constant(3, 4, 5), Value(3, 4, 5)])
def test_tuple_value(exp):
    assert tuple(exp) == (3, 4, 5)
    with pytest.raises(ValueError):
        float(exp)
    with pytest.raises(ValueError):
        int(exp)
    assert repr(exp) == '<3.0, 4.0, 5.0>'

    assert exp == (3, 4, 5)
    assert exp != (3, 5, 5)
    assert exp < (3, 4, 6)
    assert exp > (3, 4, 4)
    assert exp <= (3, 5, 5)
    assert exp >= (3, 2, 5)


def test_value_setting():
    exp = Value(4)
    assert exp == 4
    exp.set(6)
    assert exp == 6

    with pytest.raises(ValueError):
        exp.set(6, 7)
