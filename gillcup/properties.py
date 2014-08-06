import weakref

from gillcup.expressions import Constant, Box


class AnimatedProperty:
    def __init__(self, *default, name=None):
        self._boxes = {}
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
            return _get_box(self, instance)

    def __set__(self, instance, value):
        prop_size = len(self._default)
        exp = _coerce(value, prop_size)
        box = _get_box(self, instance)
        box.value = exp


def _get_box(prop, instance):
    try:
        return prop._boxes[id(instance)]
    except KeyError:
        weakref.finalize(instance, prop._boxes.pop, id(instance), None)
        name = '{0} of {1!r}'.format(prop.name, instance)
        box = Box(name, prop._default)
        prop._boxes[id(instance)] = box
        return box


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
        # Can't assign expressions directly to properties, because the
        # intended behavior is ambiguous -- if we say:
        #   item1.position = item2.position
        # where position is animated, would that mean:
        # * linking the properties together, so setting item2.position would
        #   update item1.position?
        #   (And if so, would it work in the opposite direction?)
        # * setting just the expression, so the current animation would
        #   continue on both but
        # * just use the current value of item2.position as a constant?
        # We'll want to provide ways to explicitly say any of the above,
        # ant maaaybe if after some time it becomes clear that one of them
        # is sufficiently more right than the others, also do it here.
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
        box = _get_box(self._parent, instance)
        new = box.value.replace(self._index, _coerce(value, 1))
        box.value = new
