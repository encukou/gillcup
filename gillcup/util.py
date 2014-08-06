import inspect


KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY


def fix_public_signature(func):
    """Remove private arguments from the signature of a function

    Private arguments are keyword-only, and prefixed by an underscore.
    """
    old_signature = inspect.signature(func)
    new_signature = old_signature.replace(parameters=[
        p for name, p in old_signature.parameters.items()
        if not (p.name.startswith('_') and p.kind == KEYWORD_ONLY)
    ])
    func.__signature__ = new_signature
    return func


def autoname(cls):
    """Decorator that automatically names class items with autoname properties

    An autoname property is a descriptor thet has the
    "_gillcup_autoname_property" attribute
    set to where the name should be stored, like this::

        >>> class MyDescriptor:
        ...     _gillcup_autoname_property = 'name'
        ...
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
