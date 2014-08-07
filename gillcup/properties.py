import re
import weakref

from gillcup.expressions import Expression, Constant, coerce, simplify


class AnimatedProperty:
    def __init__(self, *default, name=None):
        self._instance_expressions = {}
        self._default = Constant(*default)

        size = len(self._default)
        self.name, component_names = _get_names(name, size)

        self._components = tuple(_ComponentProperty(self, i, name)
                                 for i, name in enumerate(component_names))

    def __iter__(self):
        yield from self._components

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
        self._instance_expressions[id(instance)] = simplify(exp)


def _get_names(name, size):
    component_names = None
    if name:
        name, sep, component_names_str = name.partition(':')
        if sep:
            name = name.strip()
            component_names = re.split('[\s,]', component_names_str.strip())
            if len(component_names) != size:
                raise ValueError(
                    'Bad number of component names: {} != {}'.format(
                        len(component_names), size))

    if not name:
        name = '<unnamed property>'

    if not component_names:
        component_names = ['{}[{}]'.format(name, i) for i in range(size)]

    return name, component_names


def link(prop):
    """Given a property value, returns an expression linked to that value

        >>> from gillcup.expressions import Value
        >>> class Rect:
        ...     width = AnimatedProperty(1)
        ...     height = AnimatedProperty(1)
        >>> rect = Rect()

    Normally, expressions retreived from properties don't reflect later updates
    to the property::

        >>> val = Value(3)
        >>> rect.height = val
        >>> rect.width = rect.height
        >>> rect.width
        <3.0>

        >>> rect.height = 50
        >>> rect.height
        <50.0>
        >>> rect.width
        <3.0>

    However, value changes of the expression the "source" property originally
    contained still take effect::

        >>> val.set(1000)
        >>> rect.width
        <1000.0>

    This means any running animations will continue to run.


    To "link" one property to another, call :func:`link` on the "source"
    property::

        >>> rect.height
        <50.0>
        >>> rect.width = link(rect.height)
        >>> rect.width
        <50.0>

        >>> rect.height = 40
        >>> rect.height
        <40.0>
        >>> rect.width
        <40.0>

    Calling :func:`link` creates an expression that evaluates
    attrubute access of the property.
    This result can be used in more complicated expressions::

        >>> rect.height
        <40.0>
        >>> rect.width = link(rect.height) * 2
        >>> rect.width
        <80.0>

        >>> rect.height += 2
        >>> rect.height
        <42.0>
        >>> rect.width
        <84.0>

    Just beware that you can create loops this way by making a property's value
    depend on itself.
    The infinite recursion will result in a :class:`RuntimeError` being raised
    when the value is accessed (or possibly even earlier)::

        >>> rect.width = link(rect.width)
        >>> int(rect.width)
        Traceback (most recent call last):
            ...
            ...
            ...
        RuntimeError: maximum recursion depth exceeded ...


    Finally, property values have a convenience *method* called :meth:`link`.
    Calling::

        obj.property.link(obj2.prop2)

    is equivalent to::

        obj.property = link(obj2.prop2)
    """
    try:
        func = prop._gillcup_propexp_link
    except AttributeError:
        raise TypeError("{} can't be linked".format(type(prop)))
    else:
        return func()


class _PropertyValue(Expression):
    def __init__(self, prop, instance, expression):
        self._prop = prop
        self._instance = instance
        self.replacement = expression

    def get(self):
        return self.replacement.get()

    @property
    def pretty_name(self):
        return '{0!r}.{1} value'.format(self._instance, self._prop.name)

    @property
    def children(self):
        yield self.replacement

    def _gillcup_propexp_link(self):
        return _Linked(self._prop, self._instance)

    def link(self, source):
        linked = link(source)
        self._prop.__set__(self._instance, linked)


class _Linked(Expression):
    def __init__(self, prop, instance):
        self._prop = prop
        self._instance = instance

    def get(self):
        return self._prop.__get__(self._instance).get()

    @property
    def pretty_name(self):
        return 'linked {0!r}.{1}'.format(self._instance, self._prop.name)

    @property
    def children(self):
        yield simplify(self._prop.__get__(self._instance))

    def _gillcup_propexp_link(self):
        return self


class _ComponentProperty:
    def __init__(self, parent, index, name):
        self._parent = parent
        self._index = index
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            return self._parent.__get__(instance, owner)[self._index]

    def __set__(self, instance, value):
        exp = self._parent.__get__(instance)
        new = exp.replace(self._index, coerce(value, size=1))
        self._parent.__set__(instance, new)
