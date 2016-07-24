def autoname_property(attrname):
    """Decorator for creating autoname properties, for use with @autoname

    :param name: Name of the attribute that should hold the property's name

    See :func:`autoname` for usage.

    Under the covers this sets the :token:`_gillcup_autoname_property`
    attribute on the decorated object. This is an implementation detail.
    """
    if not isinstance(attrname, str):
        raise TypeError(
            'Attribute names must be strings. '
            'Did you forget to call @autoname_property with the attrname?')

    def decorator(cls):
        cls._gillcup_autoname_property = attrname
        return cls

    return decorator


def autoname(cls):
    """Decorator that automatically names class items with autoname properties
    An autoname property is made with the :func:`autoname_property` decorator,
    like this::

        >>> @autoname_property('name')
        ... class MyDescriptor:
        ...     def __get__(self, instance, owner=None):
        ...         if instance is None:
        ...             return self
        ...         else:
        ...             return '<{} of {}>'.format(self.name, instance)

        >>> @autoname
        ... class Spaceship:
        ...     position = MyDescriptor()
        ...     velocity = MyDescriptor()

        >>> Spaceship().position
        '<position of <...Spaceship object at ...>>'
        >>> Spaceship().velocity
        '<velocity of <...Spaceship object at ...>>'
    """
    for name, value in cls.__dict__.items():
        name_prop = getattr(type(value), '_gillcup_autoname_property', None)
        if name_prop is not None:
            setattr(value, name_prop, name)
    return cls
