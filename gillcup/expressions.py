import functools

@functools.total_ordering
class Expression:
    """A dynamic numeric value.

    This is a base class, do not use it directly.
    """

    def __len__(self):
        return len(self.get())

    def __iter__(self):
        return iter(self.get())

    def __float__(self):
        value = self.get()
        try:
            [number] = value
        except ValueError:
            raise ValueError('need one component, not {}'.format(len(self)))
        return float(number)

    def __int__(self):
        return int(float(self))

    def __repr__(self):
        return '<{}>'.format(', '.join(str(n) for n in self))

    def get(self):
        """Return the value of this expression, as a tuple"""
        raise NotImplementedError()

    def __eq__(self, other):
        return self.get() == _as_tuple(other)

    def __lt__(self, other):
        return self.get() < _as_tuple(other)


def _as_tuple(value):
    if isinstance(value, Expression):
        return value.get()
    try:
        iterator = iter(value)
    except TypeError:
        return (value, )
    else:
        return tuple(float(v) for v in iterator)


class Constant(Expression):
    def __init__(self, *value):
        self._value = tuple(float(v) for v in value)

    def get(self):
        return self._value


class Value(Expression):
    def __init__(self, *value):
        self._value = tuple(float(v) for v in value)
        self._size = len(self._value)

    def __len__(self):
        return self._size

    def get(self):
        return self._value

    def set(self, *value):
        value = tuple(float(v) for v in value)
        if len(value) != self._size:
            raise ValueError('Mismatched vector size: {} != {}'.format(
                len(value), self._size))
        self._value = value
