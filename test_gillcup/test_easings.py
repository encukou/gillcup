import collections

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
