from math import isnan, isclose
import operator

from hypothesis import note
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule

from gillcup.expressions import Constant, Value, dump


OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
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
        return "<set {} to {}>".format(id(self.value), self.number)

    def __hash__(self):
        return hash(self.token)


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
          operator=st.sampled_from(OPERATORS))
    def operate(self, operator, left, right):
        op = OPERATORS[operator]
        left_value, left_keys = left
        right_value, right_keys = right
        return op(left_value, right_value), {
            l_settings | r_settings: op(l_expected, r_expected)
            for (l_settings, l_expected), (r_settings, r_expected)
            in zip(left_keys.items(), right_keys.items())
            if len({id(s.value) for s in l_settings | r_settings}) ==
               len({l_settings | r_settings})}

    @rule(tree=trees)
    def check_equiv(self, tree):
        got, expected_values = tree
        for settings, expected_value in expected_values.items():
            note('settings: {}'.format(settings))
            note('expected: {}'.format(expected_value))
            for setting in settings:
                setting.value.set(setting.number)
            note(dump(got,show_ids=True))
            if isnan(expected_value):
                assert isnan(got)
            else:
                assert isclose(float(got), expected_value, abs_tol=1e-09)


TestExpressions = Expressions.TestCase
