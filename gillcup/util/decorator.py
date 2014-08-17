class reify:
    def __init__(self, func, name=None):
        self.func = func
        self.name = name or func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.name, value)
            return value
