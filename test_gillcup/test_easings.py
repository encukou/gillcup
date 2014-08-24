import collections
import inspect

import pytest

from gillcup import easings

ε = 0.00000001

other_easings = collections.OrderedDict(
    ('{name}({args})'.format(
        name=easing.__name__,
        args=', '.join('{}={}'.format(*item) for item in args.items())),
     easing.parametrized(**args)) for easing, args in [
        (easings.elastic, dict(period=0.1)),
        (easings.elastic, dict(amplitude=0.5, period=0.1)),
        (easings.elastic, dict(amplitude=2, period=0.1)),
        (easings.elastic, dict(period=0.5)),
        (easings.elastic, dict(amplitude=0.5, period=0.5)),
        (easings.elastic, dict(amplitude=2, period=0.5)),
        (easings.elastic, dict(amplitude=0.5)),
        (easings.elastic, dict(amplitude=2)),
        (easings.back, dict(amount=1.5)),
        (easings.back, dict(amount=2)),
        (easings.bounce, dict(amplitude=1.5)),
        (easings.bounce, dict(amplitude=2)),
        (easings.expo, dict(exponent=2)),
        (easings.expo, dict(exponent=50)),
        (easings.power, dict(exponent=1/4)),
        (easings.power, dict(exponent=50)),
        (easings.cubic_bezier, dict(x1=1, y1=1.75, x2=0, y2=0.57)),
    ])


std_easing_names = [n for n in easings.standard_easings if '.' not in n]


@pytest.fixture(
    params=([easings.standard_easings[n] for n in std_easing_names] +
            list(other_easings.values())),
    ids=std_easing_names + list(other_easings.keys()),
)
def easing(request):
    return request.param


@pytest.fixture(params=['in_', 'out', 'in_out', 'out_in'])
def any_easing(easing, request):
    return getattr(easing, request.param)


@pytest.fixture(params=['in_out', 'out_in'])
def combo_easing(easing, request):
    return getattr(easing, request.param)


def test_easing_limits(any_easing):
    assert abs(any_easing(0) - 0) < ε
    assert abs(any_easing(1) - 1) < ε


def test_combo_midpoints(combo_easing):
    assert abs(combo_easing(0.5) - 0.5) < ε


def test_self_is_in(easing):
    assert easing is easing.in_


def test_in_out_mirroring(easing):
    for i in range(-5, 50):
        t = i / 42
        assert abs(easing(t) - (1 - easing.out(1 - t))) < ε


def test_inout_compliance(easing):
    for i in range(21):
        t = i / 42
        t2 = t * 2
        assert abs(easing.in_out(t) - easing(t2) / 2) < ε
        assert abs(easing.in_out(t + 0.5) - 0.5 - easing.out(t2) / 2) < ε


def test_outin_compliance(easing):
    for i in range(21):
        t = i / 42
        t2 = t * 2
        assert abs(easing.out_in(t) - easing.out(t2) / 2) < ε
        assert abs(easing.out_in(t + 0.5) - 0.5 - easing.in_(t2) / 2) < ε


def test_parametrized_bind_expo():
    expo1 = easings.expo.p(exponent=4)
    expo2 = easings.expo.p(4)
    for i in range(21):
        t = i / 42
        assert abs(expo1(t) - expo2(t)) < ε


def test_parametrized_bind_bad():
    with pytest.raises(TypeError):
        easings.linear.p(0)


def test_parametrized_bind_noop():
    easings.linear.p()


def test_parametrized_bind_special():
    @easings.easing
    def special_func(t, pos=0, *args, kwd=0, **kwargs):
        if t == 42:
            return pos, args, kwd, kwargs
        return t
    assert special_func.p()(42) == (0, (), 0, {})
    assert special_func.p(1)(42) == (1, (), 0, {})
    assert special_func.p(pos=1)(42) == (1, (), 0, {})
    with pytest.raises(TypeError):
        special_func.p(1, 2)(42)  # *args not supported
    assert special_func.p(kwd=1)(42) == (0, (), 1, {})
    assert special_func.p(kwd=1, pos=2)(42) == (2, (), 1, {})
    assert special_func.p(kwd=1, pos=2, z=3)(42) == (2, (), 1, {'z': 3})


def check_linear(func):
    for n in 0, .25, .5, .75, 1:
        assert func(n) == n


def test_parametrized_normalization():
    @easings.easing
    def special_func(t, start=0):
        return t + start
    check_linear(special_func)
    check_linear(special_func.p(3))
    check_linear(special_func.out.p(3))
    check_linear(special_func.p(3).out)
    check_linear(special_func.p(3).in_out)
    check_linear(special_func.in_out.p(3))


def assert_sigs_equal(a, b):
    sig_a = inspect.signature(a)
    sig_b = inspect.signature(b)
    print(sig_a)
    print(sig_b)
    assert sig_a == sig_b


def test_parametrized_signature():
    @easings.easing
    def special_func(t, pos=0, *args, kwd=0, **kwargs):
        if t == 42:
            return pos, args, kwd, kwargs
        return t
    assert_sigs_equal(special_func.p, lambda pos=0, *, kwd=0, **kwargs: None)


def test_parametrized_signature_lie(recwarn):
    def special_func(t, pos=0, *args, kwd=0, **kwargs):
        if t == 42:
            return pos, args, kwd, kwargs
        return t
    special_func.__signature__ = inspect.signature(lambda **kwargs: None)
    special_func = easings.easing(special_func)
    w = recwarn.pop(easings.ParametrizationWarning)
    assert 'could not process function signature' in str(w.message)
    assert special_func.p(kwd=1, pos=2, z=3)(42) == (2, (), 1, {'z': 3})
    with pytest.raises(TypeError):
        assert special_func.p(1)


def test_variant_names(recwarn):
    assert easings.expo.__name__ == 'expo'
    assert easings.expo.out.__name__ == 'expo.out'
    assert easings.expo.in_out.__name__ == 'expo.in_out'
    assert easings.expo.p(4).__name__ == 'expo.p(exponent=4)'
    assert easings.expo.p(4).out.__name__ == 'expo.p(exponent=4).out'
    assert easings.expo.out.p(4).__name__ == 'expo.p(exponent=4).out'
