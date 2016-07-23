from math import isnan, isinf, isclose
import operator

from hypothesis import note, assume, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule

from gillcup.expressions import Constant, Value, dump, simplify


def skip_errors(func, error_class):
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except error_class:
            assume(False)
    return wrapped


BINARY_OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '**': skip_errors(operator.pow, ValueError),
    '/': skip_errors(operator.truediv, ZeroDivisionError),
    '//': skip_errors(operator.floordiv, ZeroDivisionError),
    '%': skip_errors(operator.mod, ZeroDivisionError),
    '==': operator.eq,
    '!=': operator.ne,
    '>': operator.gt,
    '<': operator.lt,
    '>=': operator.ge,
    '<=': operator.le,
}

UNARY_OPERATORS = {
    '+': operator.pos,
    '-': operator.neg,
}

_global_token = 0
class ValueSetting:
    """Represents setting a Value to a concrete number

    Like a namedtuple, but hashable (uses a globally unique token to
    disambiguate).
    """
    __slots__ = ['value', 'number', 'token']
    def __init__(self, value, number):
        global _global_token
        self.value = value
        self.number = number
        self.token = _global_token
        _global_token += 1

    def __repr__(self):
        return "<{}: set {} to {}>".format(self.token, id(self.value),
                                           self.number)

    def __hash__(self):
        return hash(self.token)

    def __eq__(self, other):
        return hash(self.token == other.token)

    def __lt__(self, other):
        return hash(self.token < other.token)


class Expressions(RuleBasedStateMachine):
    trees = Bundle('expressions')

    @rule(target=trees, x=st.floats())
    def constant(self, x):
        return Constant(x), {frozenset(): x}

    @rule(target=trees, nums=st.lists(st.floats(), min_size=1))
    def value(self, nums):
        val = Value(0)
        return val, {frozenset([ValueSetting(val, x)]): x for x in nums}

    @rule(target=trees, left=trees, right=trees,
          operator=st.sampled_from(BINARY_OPERATORS))
    def binop(self, operator, left, right):
        op = BINARY_OPERATORS[operator]
        left_expr, left_xmap = left
        right_expr, right_xmap = right
        new_expected_map = {}
        for (l_settings, l_expected), (r_settings, r_expected) in zip(
                left_xmap.items(), right_xmap.items()):
            combined = l_settings | r_settings
            if len({id(s.value) for s in combined}) == len(combined):
                try:
                    result = op(l_expected, r_expected)
                except (ArithmeticError, OverflowError):
                    result = float('nan')
                if isinstance(result, complex):
                    result = float('nan')
                new_expected_map[combined] = result
        return op(left_expr, right_expr), new_expected_map

    @rule(target=trees, node=trees,
          operator=st.sampled_from(UNARY_OPERATORS))
    def unop(self, operator, node):
        op = UNARY_OPERATORS[operator]
        expr, expected_map = node
        new_expected_map = {}
        for settings, expected in expected_map.items():
            try:
                result = op(expected)
            except (ArithmeticError, OverflowError):
                result = float('nan')
            if isinstance(result, complex):
                result = float('nan')
            new_expected_map[settings] = result
        return op(expr), new_expected_map

    @rule(target=trees, node=trees.filter(lambda t: t[1]), index=st.integers())
    def trim(self, node, index):
        expr, expected_map = node
        settings, expected = sorted(expected_map.items())[index % len(expected_map)]
        return expr, {settings: expected}

    @rule(target=trees, node=trees)
    def simplify(self, node):
        expr, expected_map = node
        expr = simplify(expr)
        note(dump(expr))
        return expr, expected_map

    @rule(tree=trees)
    def check_equiv(self, tree):
        got, expected_map = tree
        for settings, expected_value in expected_map.items():
            note('settings: {}'.format(settings))
            note('expected: {}'.format(expected_value))
            for setting in settings:
                setting.value.set(setting.number)
            note(dump(got,show_ids=True))
            if isnan(expected_value) or isinf(expected_value):
                assert isnan(got) or isinf(got)
            else:
                assert isclose(float(got), expected_value, abs_tol=1e-09)


TestExpressions = Expressions.TestCase
