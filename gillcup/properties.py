import weakref

from gillcup.expressions import Constant


class AnimatedProperty:
    def __init__(self, *default):
        self._instance_expressions = {}
        self._default = Constant(*default)

    def __iter__(self):
        for index in range(len(self._default)):
            yield _ComponentProperty(self, index)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            try:
                return self._instance_expressions[id(instance)]
            except KeyError:
                exp = self._instance_expressions[id(instance)] = self._default
                _make_slot(self._instance_expressions, instance)
                return exp

    def __set__(self, instance, value):
        _make_slot(self._instance_expressions, instance)
        prop_size = len(self._default)
        self._instance_expressions[id(instance)] = _coerce(value, prop_size)


def _make_slot(dct, instance):
    if id(instance) not in dct:
        weakref.finalize(instance, dct.pop, id(instance), None)


def _coerce(value, size):
    try:
        value.get
    except AttributeError:
        try:
            it = iter(value)
        except TypeError:
            value = (float(value), ) * size
        else:
            value = tuple(it)
            assert len(value) == size
        return Constant(*value)
    else:
        raise TypeError('Bad type %s - setting Expressions is not supported' %
                        type(value))


class _ComponentProperty:
    def __init__(self, parent, index):
        self._parent = parent
        self._index = index

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            return self._parent.__get__(instance, owner)[self._index]

    def __set__(self, instance, value):
        orig = self._parent.__get__(instance)
        new = orig.replace(self._index, _coerce(value, 1))
        _make_slot(self._parent._instance_expressions, instance)
        self._parent._instance_expressions[id(instance)] = new
