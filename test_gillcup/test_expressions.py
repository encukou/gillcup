import itertools
import inspect
import math
import textwrap
import contextlib

import pytest

from gillcup.expressions import Constant, Value, Concat, Interpolation, Slice
from gillcup.expressions import Sum, Difference, Product, Quotient, Neg, Box
from gillcup.expressions import Progress, dump, simplify


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

    assert not exp == (3, 0)
    assert exp != (3, 0)
    assert exp < (3, 0)
    assert exp > (2, 99)
    assert exp <= (3, 0)
    assert exp >= (2, 99)

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

    assert not exp == 3
    assert exp != 3
    assert exp < 4
    assert exp > 3
    assert exp <= 4
    assert exp >= 3

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
    assert simplify(exp) == 6
    assert isinstance(simplify(exp), Constant)


def test_value_fix_1():
    exp = Value(6)
    exp.fix()
    assert exp == 6
    with pytest.raises(ValueError):
        exp.set(4)
    assert exp == 6
    assert simplify(exp) == 6
    assert isinstance(simplify(exp), Constant)


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
        with pytest.raises(ValueError):
            op(Value(1), (2, 3))
        with pytest.raises(ValueError):
            op((1, 2), Value(3))
    else:
        raise ValueError(num_args)  # extend the test if this happens


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
        assert isinstance(simplify(got), Constant)


def check_dump(expression, expected):
    dumped = dump(expression)
    print(dumped)
    expected = textwrap.dedent(expected.strip('\n').rstrip())
    assert dumped == expected


def test_dump():
    val = Value(3) + 1
    check_dump(val - 4 * val - 5, """
        - <-17.0>:
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


def test_basic_slice_simplification():
    val = Value(1, 2, 3)
    assert val[:] is val
    check_dump(val[:-1][:-1], """
        [0:1] <1.0>:
          Value <1.0, 2.0, 3.0>
    """)
    check_dump(val[1:][:-1], """
        [1:2] <2.0>:
          Value <1.0, 2.0, 3.0>
    """)
    check_dump(val[1:30][1:], """
        [2:3] <3.0>:
          Value <1.0, 2.0, 3.0>
    """)
    check_dump(val[:-1][:30], """
        [0:2] <1.0, 2.0>:
          Value <1.0, 2.0, 3.0>
    """)


def test_concat():
    val = Value(3)
    cat = Concat(val, 2, Value(5, 4))
    assert cat == (3, 2, 5, 4)
    val.set(8)
    assert cat == (8, 2, 5, 4)


def test_simple_concat_simplification():
    exp = Concat(Constant(0, 1), Constant(2, 3))
    check_dump(simplify(exp), 'Constant <0.0, 1.0, 2.0, 3.0>')


def test_complex_concat_simplification():
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
    check_dump(simplify(cat), 'Constant <1.0, 2.0, 3.0, 4.0, 5.0>')


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

    check_dump(simplify(val), """
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


def test_interpolation():
    val1 = Value(0, 1, 5, 1)
    val2 = Value(10, 1, 0, 2)
    t = Value(0)
    exp = Interpolation(val1, val2, t)
    assert exp == simplify(exp) == (0, 1, 5, 1)

    t.set(1)
    assert exp == simplify(exp) == (10, 1, 0, 2)

    t.set(0.5)
    assert exp == simplify(exp) == (5, 1, 2.5, 1.5)


def test_interpolation_ramps():
    t = Value(0)
    for x in range(-2, 5):
        exp = Interpolation(0, x, t)
        for i in range(-10, 20):
            t.set(i / 10)
            assert exp == simplify(exp) == t * x


def test_interpolation_simplification():
    val1 = Value(0, 1, 5, 1)
    val2 = Value(10, 1, 0, 2)
    assert simplify(Interpolation(val1, val2, 0)) is val1
    assert simplify(Interpolation(val1, val2, 1)) is val2


def test_interpolation_dump():
    val1 = Value(0, 0)
    val2 = Value(2, 10)
    exp = Interpolation(val1, val2, Value(0.5))
    check_dump(exp, """
        Interpolation <1.0, 5.0>:
          start <0.0, 0.0>:
            Value <0.0, 0.0>
          end <2.0, 10.0>:
            Value <2.0, 10.0>
          t <0.5>:
            Value <0.5>
    """)


def test_progress_clamped(clock):
    exp = Progress(clock, 2, delay=1)
    assert exp == 0
    clock.advance_sync(1)
    assert exp == 0
    clock.advance_sync(1)
    assert exp == 0.5
    clock.advance_sync(1)
    assert exp == 1
    assert isinstance(simplify(exp), Constant)


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


def test_concat_empty_exp_removal():
    exp = Concat(Value(), Value(1), Value(2, 3))
    check_dump(exp, """
        Concat <1.0, 2.0, 3.0>:
          Value <1.0>
          Value <2.0, 3.0>
    """)


@pytest.mark.parametrize('i', [0, 1, 2])
def test_concat_of_slice_simplification_0(i):
    val = Value(0, 1, 2)
    exp = Concat(val[0], val[1], val[2])
    val.fix()
    exp = simplify(exp[i])
    check_dump(exp, "Constant <%s.0>" % i)


def test_concat_of_slice_simplification_1():
    exp = Concat(Value(0, 1), Value(2))
    exp = simplify(exp[1])
    check_dump(exp, """
        [1:2] <1.0>:
          Value <0.0, 1.0>
    """)


def test_concat_of_slice_simplification_2():
    exp = Value(0, 1, 2)
    exp = Concat(exp[0], exp[1], exp[2])
    exp = simplify(exp)
    check_dump(exp, "Value <0.0, 1.0, 2.0>")


@pytest.mark.parametrize(['start', 'end', 'dump'], [
    (0, 1, """
        [0:1] <0.0>:
          Value <0.0, 1.0, 2.0>
    """),
    (0, 2, """
        [0:2] <0.0, 1.0>:
          Value <0.0, 1.0, 2.0>
    """),
    (0, 3, """
        Value <0.0, 1.0, 2.0>
    """),
    (0, 4, """
        Concat <0.0, 1.0, 2.0, 3.0>:
          Value <0.0, 1.0, 2.0>
          [0:1] <3.0>:
            Value <3.0, 4.0, 5.0>
    """),
    (1, 5, """
        Concat <1.0, 2.0, 3.0, 4.0>:
          [1:3] <1.0, 2.0>:
            Value <0.0, 1.0, 2.0>
          [0:2] <3.0, 4.0>:
            Value <3.0, 4.0, 5.0>
    """),
    (2, 100, """
        Concat <2.0, 3.0, 4.0, 5.0>:
          [2:3] <2.0>:
            Value <0.0, 1.0, 2.0>
          Value <3.0, 4.0, 5.0>
    """),
])
def test_slice_of_concat_simplification_3(start, end, dump):
    val = Concat(Value(0, 1, 2), Value(3, 4, 5))

    check_dump(simplify(val[start:end]), dump)


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


@pytest.mark.parametrize('cls', [Sum, Difference, Product, Quotient])
def test_reduce_simplification(cls):
    v1 = Value(1)
    v2 = Value(2)
    v3 = Value(3)
    with reduce_to_const(cls([v1, v2, v3])) as exp:
        v1.fix()
        v2.fix()
        assert len(exp.children) == 2
        v3.fix()


def get_depth(exp):
    depths = [get_depth(c) for c in exp.children]
    if depths:
        return 1 + max(depths)
    else:
        return 1


def check_depth(exp, depth):
    print(dump(exp))
    assert get_depth(exp) == depth


def test_addition_depth():
    exp = Value(0)
    for i in range(10):
        exp = exp + 1
    check_depth(exp, 2)


def test_subtraction_depth():
    exp = Value(0)
    for i in range(10):
        exp = exp - 1
    check_depth(exp, 2)


def test_slicing_depth():
    exp = Value(0, 0, 0)
    for i in range(10):
        exp = exp.replace(1, exp[1] - 1)
    check_depth(exp, 4)


def test_elementwise_manipulation_depth():
    exp = Value(0, 0, 0)
    for i in range(10):
        exp = exp.replace(i % 3, exp[i % 3] - i)
    check_depth(exp, 4)


def test_box():
    name = 'Boxed variable'
    val = Value(0, 0, 0)
    exp = Box(name, val)
    assert exp == (0, 0, 0)
    assert exp.pretty_name == name
    val.fix(3, 3, 3)
    assert exp == (3, 3, 3)
    exp.value = Value(6, 6, 6)
    assert exp == (6, 6, 6)


def test_box_recursion():
    val = Value(0, 0, 0)
    exp = Box('Box with itself inside', val)
    exp.value = exp
    with pytest.raises(RuntimeError):
        exp.get()
    check_dump(exp, """
        Box with itself inside <RuntimeError while getting value>:  (&1)
          Box with itself inside <RuntimeError while getting value>  (*1)
    """)
