import itertools
import inspect
import math
import textwrap

import pytest

from gillcup.expressions import Constant, Value, Concat
from gillcup.expressions import dump


try:
    import numpy
except ImportError:
    numpy = None


def get_lambda_source(f):
    return inspect.getsource(f).split(':', 1)[1].strip().rstrip(',')


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
        ids = ['{} ({})'.format(get_lambda_source(formula),
                                ', '.join(str(a) for a in args))
               for args, formula in argvalues]
        metafunc.parametrize(['args', 'formula'], argvalues, ids=ids)


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

    assert exp


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

    assert exp


def test_value_setting():
    exp = Value(4)
    assert exp == 4
    exp.set(6)
    assert exp == 6

    with pytest.raises(ValueError):
        exp.set(6, 7)


def test_value_fix_0():
    exp = Value(4)
    exp.fix(6)
    assert exp == 6
    with pytest.raises(ValueError):
        exp.set(4)
    assert exp == 6
    assert exp.simplify() == 6
    assert isinstance(exp.simplify(), Constant)


def test_value_fix_1():
    exp = Value(6)
    exp.fix()
    assert exp == 6
    with pytest.raises(ValueError):
        exp.set(4)
    assert exp == 6
    assert exp.simplify() == 6
    assert isinstance(exp.simplify(), Constant)


def test_constant_zero_size():
    assert Constant() == ()
    assert tuple(Constant()) == ()

    with pytest.raises(ValueError):
        float(Constant())

    assert not Constant()


def test_value_zero_size():
    assert Value() == ()
    assert tuple(Value()) == ()

    with pytest.raises(ValueError):
        float(Value())

    assert not Value()


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
    return got


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
        assert op(Value(1, 2), 3) == (op(1, 3), op(2, 3))
        assert op(3, Value(1, 2)) == (op(3, 1), op(3, 2))
    else:
        raise ValueError(num_args)


def test_bad_lengths(op):
    num_args = len(inspect.signature(op).parameters)
    if num_args == 1:
        pass
    elif num_args == 2:
        with pytest.raises(ValueError):
            op(Value(1, 2), Value(3))
        with pytest.raises(ValueError):
            op(Value(1), Value(2, 3))
        with pytest.raises(ValueError):
            op(Value(1, 2), (3,))
        with pytest.raises(ValueError):
            op((3,), Value(1, 2))
    else:
        raise ValueError(num_args)


def test_constant_propagation(formula, args, maybe_numpy):
    values = tuple(Constant(a) for a in args)
    got = check_formula(maybe_numpy, formula, args, values)
    if got:
        assert isinstance(got, Constant)


def test_fixed_falue_constant_propegation(formula, args, maybe_numpy):
    values = tuple(Value(a) for a in args)
    for value in values:
        value.fix()
    got = check_formula(maybe_numpy, formula, args, values)
    if got:
        assert isinstance(got.simplify(), Constant)


def check_dump(expression, expected):
    print(dump(expression))
    expected = textwrap.dedent(expected.strip('\n').rstrip())
    assert dump(expression) == expected


def test_dump():
    val = Value(3) + 1
    check_dump(val + 4 * val + 5, """
        + <25.0>:
          + <20.0>:
            + <4.0>:  (&1)
              Value <3.0>
              Constant <1.0>
            * <16.0>:
              + <4.0>  (*1)
              Constant <4.0>
          Constant <5.0>
    """)


def test_index_get():
    val = Value(1, 2, 3)

    assert val[1] == 2
    assert val[2] == 3
    assert val[-2] == 2
    assert val[-3] == 1
    assert val[:-1] == (1, 2)
    assert val[-1:] == (3, )
    with pytest.raises(IndexError):
        val[3]
    with pytest.raises(IndexError):
        val[-80]
    assert val[1:1] == ()
    assert val[2:1] == ()
    with pytest.raises(TypeError):
        val[None]

    first_item = val[0]
    last_item = val[-1]
    first_two = val[:2]

    assert first_item == 1
    assert last_item == 3
    assert first_two == (1, 2)

    val.set(2, 3, 4)
    assert first_item == 2
    assert last_item == 4
    assert first_two == (2, 3)

    assert len(val[1]) == 1
    assert len(val[:1]) == 1
    assert len(val[1:]) == 2
    assert len(val[:]) == 3
    assert len(val[:-1]) == 2


def test_concat():
    val = Value(3)
    cat = Concat(val, 2, Value(5, 4))
    assert cat == (3, 2, 5, 4)
    val.set(8)
    assert cat == (8, 2, 5, 4)


def test_concat_simplification():
    val1 = Value(1)
    val2 = Value(4, 5)
    cat = Concat(val1, 2, 3, val2)
    assert cat == (1, 2, 3, 4, 5)
    check_dump(cat, """
        Concat <1.0, 2.0, 3.0, 4.0, 5.0>:
          Value <1.0>
          Constant <2.0, 3.0>
          Value <4.0, 5.0>
    """)
    val1.fix()
    val2.fix()
    check_dump(cat.simplify(), 'Constant <1.0, 2.0, 3.0, 4.0, 5.0>')


def test_replace_slice():
    val = Value(1, 2, 3)
    val = val.replace(1, 0)
    assert val == (1, 0, 3)
    val = val.replace(slice(1, None), -1)
    assert val == (1, -1, -1)
    val = val.replace(slice(1), (2, 3))
    assert val == (2, 3, -1, -1)
    val = val.replace(slice(0, -1), ())
    assert val == -1

    assert val.replace(slice(None, None), ()) == ()


def test_constant_slice_simplification():
    const = Constant(0, 1, 2)
    check_dump(const[:-1], 'Constant <0.0, 1.0>')
    check_dump(const[1:], 'Constant <1.0, 2.0>')
    check_dump(const[1], 'Constant <1.0>')


def test_concat_simplification():
    exp = Concat(Constant(0, 1), Constant(2, 3))
    check_dump(exp.simplify(), 'Constant <0.0, 1.0, 2.0, 3.0>')


def test_slice_replace_simplification():
    val = Value(0, 1, 2)
    val = val.replace(0, 1)
    val = val.replace(1, 1)
    val = val.replace(2, 1)

    check_dump(val, 'Constant <1.0, 1.0, 1.0>')


def test_slice_replace_simplification2():
    val = Value(0, 1, 2)
    val = val.replace(1, val[1] + 3)
    val = val.replace(0, val[0] + 3)
    val = val.replace(2, val[2] + 3)

    check_dump(val.simplify(), """
        Concat <3.0, 4.0, 5.0>:
          + <3.0>:
            [0:1] <0.0>:
              Value <0.0, 1.0, 2.0>  (&1)
            Constant <3.0>
          + <4.0>:
            [1:2] <1.0>:
              Value <0.0, 1.0, 2.0>  (*1)
            Constant <3.0>
          + <5.0>:
            [2:3] <2.0>:
              Value <0.0, 1.0, 2.0>  (*1)
            Constant <3.0>
    """)
