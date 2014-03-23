import itertools
import inspect
import math

import pytest

from gillcup.expressions import Constant, Value, dump


try:
    import numpy
except ImportError:
    numpy = None



def pytest_generate_tests(metafunc):
    if {'args', 'formula'} <= set(metafunc.fixturenames):
        def _gen():
            for formula in [
                lambda a, b: a + b,
                lambda a, b: a - b,
                lambda a, b: a * b,
                lambda a, b: a / b,
                lambda a: +a,
                lambda a: -a,
                lambda a, b: (a + b) * (a - b),
                lambda a, b: a + b - a - b,
                lambda a, b: a * b / a * b + 1,
                lambda a: 2 + a + 2 + 3,
                lambda a: a + Constant(2) + 3,
                lambda a: 2 - a - 2 - 3,
                lambda a: a - Constant(2) - 3,
                lambda a: 2 * a * 2 * 3,
                lambda a: a * Constant(2) * 3,
                lambda a: 2 / a / 2 / 3,
                lambda a: a / Constant(2) / 3,
            ]:
                numbers = -3, 0, 3, float('inf'), float('nan')
                count = len(inspect.signature(formula).parameters)
                get_combs = itertools.combinations_with_replacement
                for args in get_combs(numbers, count):
                    yield args, formula
        argvalues = list(_gen())
        ids = ['{} ({})'.format(
                inspect.getsource(formula).split(':', 1)[1].strip().rstrip(','),
                ', '.join(str(a) for a in args))
               for args, formula in argvalues]
        metafunc.parametrize('args,formula', argvalues, ids=ids)


@pytest.fixture(params=['numpy', 'py'])
def maybe_numpy(request):
    if request.param == 'numpy':
        if numpy:
            return numpy
        else:
            raise pytest.skip('no numpy')
    else:
        return None


@pytest.fixture(params=['add', 'mul', 'sub', 'truediv', 'pos', 'neg'])
def op(request):
    # would be nice to use the operator module, but we need inspect.signature
    return dict(
        add=lambda a, b: a + b,
        mul=lambda a, b: a * b,
        sub=lambda a, b: a - b,
        truediv=lambda a, b: a / b,
        pos=lambda a: +a,
        neg=lambda a: -a,
    )[request.param]


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


def check_formula(numpy, formula, expected_args, got_args):
    if numpy:
        expected = formula(*(numpy.array(a) for a in expected_args))
    else:
        try:
            expected = formula(*expected_args)
        except ZeroDivisionError:
            print('cannot check zero division without numpy')
            return
    got = formula(*got_args)
    print(dump(got))
    if math.isnan(got):
        assert math.isnan(expected)
    else:
        assert expected == got


def test_formula_values(formula, args, maybe_numpy):
    values = tuple(Value(a) for a in args)
    check_formula(maybe_numpy, formula, args, values)
    for value in values:
        value.set(value + 1)
    check_formula(maybe_numpy, formula, [a + 1 for a in args], values)


def test_tuples(op):
    num_args = len(inspect.signature(op).parameters)
    if num_args == 1:
        assert op(Value(1, 2)) == (op(1), op(2))
    elif num_args == 2:
        assert op(Value(1, 2), Value(3, 4)) == (op(1, 3), op(2, 4))
    else:
        raise ValueError(num_args)
