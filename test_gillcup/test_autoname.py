from gillcup.util import autoname


def _simple_repr(self):
    return '<{}>'.format(type(self).__name__.lower())


class NamedProperty:
    _gillcup_autoname_property = 'name'

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        else:
            return '<{} of {}>'.format(self.name, instance)


class NamedPropertyWithDefault(NamedProperty):
    name = '<unnamed>'


def test_autoname():
    @autoname
    class Foo:
        bar = NamedProperty()
        __repr__ = _simple_repr

    assert Foo.bar.name == 'bar'

    inst = Foo()
    assert inst.bar == '<bar of <foo>>'


def test_autoname_override():
    class Foo:
        bar = NamedPropertyWithDefault()
        __repr__ = _simple_repr

    assert Foo.bar.name == '<unnamed>'
    inst = Foo()
    assert inst.bar == '<<unnamed> of <foo>>'

    old_Foo = Foo
    autoname(Foo)
    assert old_Foo is Foo

    assert Foo.bar.name == 'bar'
    inst = Foo()
    assert inst.bar == '<bar of <foo>>'


def test_autoname_no_override_parent():
    class Foo:
        bar = NamedPropertyWithDefault()
        __repr__ = _simple_repr

    @autoname
    class Subclass(Foo):
        pass

    assert Subclass.bar.name == '<unnamed>'
    inst = Subclass()
    assert inst.bar == '<<unnamed> of <subclass>>'
