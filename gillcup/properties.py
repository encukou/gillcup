import weakref

from gillcup.expressions import Expression, Constant, coerce


class AnimatedProperty:
    def __init__(self, *default, name=None):
        self._instance_expressions = {}
        self._default = Constant(*default)

        if name is None:
            self.name = '<unnamed property>'
        else:
            self.name = name

    def __iter__(self):
        for index in range(len(self._default)):
            yield _ComponentProperty(self, index)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            try:
                exp = self._instance_expressions[id(instance)]
            except KeyError:
                exp = self._default
            return _PropertyValue(self, instance, exp)

    def __set__(self, instance, value):
        prop_size = len(self._default)
        exp = coerce(value, size=prop_size)
        if id(instance) not in self._instance_expressions:
            weakref.finalize(instance, self._instance_expressions.pop,
                             id(instance), None)
        self._instance_expressions[id(instance)] = exp


class _PropertyValue(Expression):
    def __init__(self, prop, instance, expression):
        self._prop = prop
        self._instance = instance
        self.replacement = expression

    def get(self):
        return self.replacement.get()

    @property
    def pretty_name(self):
        # TODO: Is "snapshot" a good name?
        return 'snapshot of {0} of {1!r}'.format(
            self._prop.name, self._instance)

    @property
    def children(self):
        yield self.replacement


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
        exp = self._parent.__get__(instance)
        new = exp.replace(self._index, coerce(value, size=1))
        self._parent.__set__(instance, new)
