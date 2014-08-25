import contextlib

import pytest

from gillcup.properties import AnimatedProperty, link
from gillcup.expressions import Progress, Constant


class BeeperBase:
    def __repr__(self):
        return '<test beeper>'

    @contextlib.contextmanager
    def extra_behavior(self, behavior_type):
        """Wraps test code that uses special AnimatedProperty features

        Usage is similar to :func:`pytest.raises`.

        See :meth:`NaïveBeeper.extra_behavior` code for possible values of
        behavior_type, and their explanations
        """
        yield


class Beeper(BeeperBase):
    """The basic beeper"""
    volume = AnimatedProperty(name='volume')
    pitch = AnimatedProperty(1, lambda inst: 440, name='pitch')
    position = x, y, z = AnimatedProperty(3, name='position: x y z')


class MultichannelBeeper(BeeperBase):
    """A Beeper that emits 3 simultaneous tones

    Not good programming practice!
    This is just to test that ``volume`` and ``pitch`` work exactly the same
    when they are a top-level property as when they are a component.
    """
    volumes = volume, vol2, vol3 = AnimatedProperty(
        3, name='volumes:volume vol2 vol3')
    pitches = pitch, pitch2, pitch3 = AnimatedProperty(
        3, lambda inst: 440, name='pitches: pitch pitch2 pitch3')
    position = x, y, z = AnimatedProperty(3, name='position: x y z')


class FactorizedBeeper(BeeperBase):
    """A beeper that uses factories for the properties"""
    volume = AnimatedProperty(1, lambda inst: 0, name='volume')
    pitch = AnimatedProperty(1, lambda inst: Constant(440),
                             name='pitch')
    position = x, y, z = AnimatedProperty(3, lambda inst: (0, 0, 0),
                                          name='position: x y z')


class NaïveBeeper(BeeperBase):
    """A Beeper that uses simple values/expressions instead of AnimatedProperty

    This is here to test that AnimatedProperty behaves like a simple attribute
    wherever possible.
    """
    volume = 0
    pitch = 440
    position = x, y, z = 0, 0, 0

    @contextlib.contextmanager
    def extra_behavior(self, behavior_type):
        if behavior_type == 'link function':
            # The link() function can be used on an AnimatedProperty value
            with pytest.raises(TypeError) as e:
                yield
            assert str(e.value) == "<class 'int'> can't be linked"
        elif behavior_type == 'link method':
            # AnimatedProperty values have a link() method
            with pytest.raises(AttributeError) as e:
                yield
            assert str(e.value) == "'int' object has no attribute 'link'"
        elif behavior_type == 'anim method':
            # AnimatedProperty values have an anim() method
            with pytest.raises(AttributeError) as e:
                yield
            assert str(e.value).endswith("' object has no attribute 'anim'")
        elif behavior_type == 'syncs-components':
            # Tuple AnimatedProperty values sync with their components
            with pytest.raises(AssertionError) as e:
                yield
        elif behavior_type == 'is-expression':
            # AnimatedProperty values are always expressions
            with pytest.raises(AssertionError) as e:
                yield
        elif behavior_type == 'tuple immutable':
            # Tuple AnimatedProperty values sync with their components
            with pytest.raises(TypeError) as e:
                yield
            assert str(e.value) == (
                "'tuple' object does not support item assignment")
        else:
            raise LookupError(behavior_type)


beeper_subclasses = [Beeper, MultichannelBeeper, NaïveBeeper, FactorizedBeeper]


@pytest.fixture(params=beeper_subclasses,
                ids=[c.__name__ for c in beeper_subclasses])
def beeper_class(request):
    return request.param


@pytest.fixture
def beeper(beeper_class):
    return beeper_class()


def test_defaults(beeper):
    assert beeper.volume == 0
    assert beeper.pitch == 440
    assert beeper.position == (0, 0, 0)
    assert beeper.x == beeper.y == beeper.z == 0


def test_setting_scalar(beeper):
    beeper.volume = 50
    assert beeper.volume == 50
    with beeper.extra_behavior('is-expression'):
        assert beeper.volume == (50,)


def test_setting_vector(beeper):
    beeper.position = 1, 2, 3
    assert beeper.position == (1, 2, 3)
    with beeper.extra_behavior('syncs-components'):
        assert beeper.x == 1
        assert beeper.y == 2
        assert beeper.z == 3


def test_setting_component(beeper):
    beeper.x = 1
    beeper.y = 2
    beeper.z = 3
    with beeper.extra_behavior('syncs-components'):
        assert beeper.position == (1, 2, 3)
    assert beeper.x == 1
    assert beeper.y == 2
    assert beeper.z == 3


def test_separate_instances_vector(beeper):
    beeper2 = Beeper()
    beeper2.x = 5
    assert beeper2.position == (5, 0, 0)
    assert beeper.position == (0, 0, 0)


def test_property_naming(check_dump):
    class Foo:
        namedprop = AnimatedProperty(1, lambda inst: 5, name='namedprop')
        unnamedprop = AnimatedProperty(1, lambda inst: 5)

        def __repr__(self):
            return '<a Foo>'

    assert Foo.namedprop.name == 'namedprop'
    assert Foo.unnamedprop.name == '<unnamed property>'

    foo = Foo()

    assert foo.namedprop.pretty_name == '<a Foo>.namedprop value'
    assert foo.unnamedprop.pretty_name == '<a Foo>.<unnamed property> value'

    check_dump(foo.namedprop, """
        <a Foo>.namedprop value <5.0>:
          Constant <5.0>
    """)

    check_dump(foo.unnamedprop, """
        <a Foo>.<unnamed property> value <5.0>:
          Constant <5.0>
    """)


def test_iadd(beeper):
    beeper.volume += 3
    assert beeper.volume == 3


def test_set_progress(beeper, clock):
    beeper.volume = Progress(clock, 2) * 100
    assert beeper.volume == 0
    clock.advance_sync(1)
    assert beeper.volume == 50
    clock.advance_sync(1)
    assert beeper.volume == 100


def test_add_progress(beeper, clock):
    beeper.pitch += Progress(clock, 2) * 20
    assert beeper.pitch == 440
    clock.advance_sync(1)
    assert beeper.pitch == 450
    clock.advance_sync(1)
    assert beeper.pitch == 460


def test_set_to_property(beeper):
    beeper.volume = beeper.pitch
    assert beeper.volume == 440
    assert beeper.pitch == 440


def test_set_to_property_animated(beeper, clock):
    beeper.pitch += Progress(clock, 2) * 20
    beeper.volume = beeper.pitch
    assert beeper.volume == 440
    assert beeper.pitch == 440
    clock.advance_sync(1)
    assert beeper.volume == 450
    assert beeper.pitch == 450
    clock.advance_sync(1)
    assert beeper.volume == 460
    assert beeper.pitch == 460


def test_set_to_property_divergent(beeper, clock):
    beeper.volume = beeper.pitch
    beeper.pitch += Progress(clock, 2) * 20
    assert beeper.volume == 440
    assert beeper.pitch == 440
    clock.advance_sync(1)
    assert beeper.volume == 440
    assert beeper.pitch == 450
    clock.advance_sync(1)
    assert beeper.volume == 440
    assert beeper.pitch == 460


def test_set_to_property_linked_method(beeper, clock):
    with beeper.extra_behavior('link method'):
        beeper.volume.link(beeper.pitch)
        beeper.pitch += Progress(clock, 2) * 20
        assert beeper.volume == 440
        assert beeper.pitch == 440
        clock.advance_sync(1)
        assert beeper.volume == 450
        assert beeper.pitch == 450
        clock.advance_sync(1)
        assert beeper.volume == 460
        assert beeper.pitch == 460


def test_set_to_property_linked_function(beeper, clock):
    with beeper.extra_behavior('link function'):
        beeper.volume = link(beeper.pitch)
        beeper.pitch += Progress(clock, 2) * 20
        assert beeper.volume == 440
        assert beeper.pitch == 440
        clock.advance_sync(1)
        assert beeper.volume == 450
        assert beeper.pitch == 450
        clock.advance_sync(1)
        assert beeper.volume == 460
        assert beeper.pitch == 460


def test_set_to_expression_with_linked_property(beeper, clock):
    with beeper.extra_behavior('link function'):
        beeper.volume = link(beeper.pitch)
        beeper.pitch += Progress(clock, 2) * 20
        assert beeper.volume == 440
        assert beeper.pitch == 440
        clock.advance_sync(1)
        assert beeper.volume == 450
        assert beeper.pitch == 450
        clock.advance_sync(1)
        assert beeper.volume == 460
        assert beeper.pitch == 460


def test_recursive_link(beeper, beeper_class, clock):
    if beeper_class == MultichannelBeeper:
        # TODO: This gets rather nasty with component property; fix!
        raise pytest.xfail(
            'INTERNALERROR> RuntimeError: maximum recursion depth exceeded')
    with beeper.extra_behavior('link function'):
        beeper.volume = link(beeper.volume)
        with pytest.raises(RuntimeError):
            beeper.volume.get()
        assert str(beeper.volume) == '<RuntimeError while getting value>'


def test_link_dump_method(beeper, beeper_class, clock, check_dump):
    # The dump is different for normal properties and for components
    with beeper.extra_behavior('link method'):
        beeper.volume.link(beeper.pitch)
        if beeper_class == MultichannelBeeper:
            check_dump(beeper.volume, """
                <test beeper>.volume (volumes[0]) value <440.0>:
                  <test beeper>.volumes value <440.0, 0.0, 0.0>:
                    Concat <440.0, 0.0, 0.0>:
                      linked <test beeper>.pitch (pitches[0]) <440.0>:
                        <test beeper>.pitches value <440.0, 440.0, 440.0>:
                          Constant <440.0, 440.0, 440.0>
                      Constant <0.0, 0.0>
            """)
        else:
            check_dump(beeper.volume, """
                <test beeper>.volume value <440.0>:
                  linked <test beeper>.pitch <440.0>:
                    Constant <440.0>
            """)


def test_link_dump_function(beeper, beeper_class, clock, check_dump):
    # The dump is different for normal properties and for components
    with beeper.extra_behavior('link function'):
        beeper.volume = link(beeper.pitch) + 4
        if beeper_class == MultichannelBeeper:
            check_dump(beeper.volume, """
                <test beeper>.volume (volumes[0]) value <444.0>:
                  <test beeper>.volumes value <444.0, 0.0, 0.0>:
                    Concat <444.0, 0.0, 0.0>:
                      + <444.0>:
                        linked <test beeper>.pitch (pitches[0]) <440.0>:
                          <test beeper>.pitches value <440.0, 440.0, 440.0>:
                            Constant <440.0, 440.0, 440.0>
                        Constant <4.0>
                      Constant <0.0, 0.0>
            """)
        else:
            check_dump(beeper.volume, """
                <test beeper>.volume value <444.0>:
                  + <444.0>:
                    linked <test beeper>.pitch <440.0>:
                      Constant <440.0>
                    Constant <4.0>
            """)


def test_link_function_idempotent(beeper, clock):
    with beeper.extra_behavior('link function'):
        linked = link(beeper.volume)
        assert linked is link(linked)


def test_default_naming():
    class Foo:
        bar = b, a, r = AnimatedProperty(3)

    assert Foo.bar.name == '<unnamed property>'
    assert Foo.b.name == '<unnamed property>[0]'
    assert Foo.a.name == '<unnamed property>[1]'
    assert Foo.r.name == '<unnamed property>[2]'


def test_single_name():
    class Foo:
        bar = b, a, r = AnimatedProperty(3, name='bar')

    assert Foo.bar.name == 'bar'
    assert Foo.b.name == 'bar[0]'
    assert Foo.a.name == 'bar[1]'
    assert Foo.r.name == 'bar[2]'


@pytest.mark.parametrize('name', ['bar:x y z', 'bar: x y z', 'bar:x,y,z',
                                  'bar : x  y  z', 'bar  :  x , y , z'])
def test_component_naming(name):
    class Foo:
        bar = b, a, r = AnimatedProperty(3, name=name)

    assert Foo.bar.name == 'bar'
    assert Foo.b.name == 'x'
    assert Foo.a.name == 'y'
    assert Foo.r.name == 'z'


@pytest.mark.parametrize('name', ['bar:x y', 'bar: x,,y z', 'bar:'])
def test_bad_component_naming(name):
    with pytest.raises(ValueError):
        AnimatedProperty(3, name=name)


def test_matched_size_0():
    AnimatedProperty(0, lambda inst: ())


def test_matched_size_1():
    AnimatedProperty(1, lambda inst: 0)


def test_matched_size_3():
    AnimatedProperty(3, lambda inst: (1, 2, 3))


def test_factory():
    class Foo:
        def __init__(self, val):
            self.val = val

        bar = AnimatedProperty(2, lambda inst: (inst.val, inst.val + 1))

    assert Foo(1).bar == (1, 2)
    assert Foo(2).bar == (2, 3)
    assert Foo(1).bar + 2 == (3, 4)


def test_factory_mismatched_size():
    class Foo:
        bar = AnimatedProperty(2, lambda inst: Constant(0))

    with pytest.raises(ValueError):
        Foo().bar


def test_factory_coercion():
    class Foo:
        bar = AnimatedProperty(3, lambda inst: 3)

    assert Foo().bar == (3, 3, 3)


def test_anim_basic(beeper, clock):
    beeper.clock = clock
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(50)
        assert beeper.volume == 50


def test_anim_duration(beeper, clock):
    beeper.clock = clock
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(100, 2)
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 50
        clock.advance_sync(1)
        assert beeper.volume == 100
        clock.advance_sync(1)
        assert beeper.volume == 100


def test_anim_delay(beeper, clock):
    beeper.clock = clock
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(100, 2, delay=1)
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 50
        clock.advance_sync(1)
        assert beeper.volume == 100
        clock.advance_sync(1)
        assert beeper.volume == 100


def test_anim_easing(beeper, clock):
    beeper.clock = clock
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(100, 2, easing='quad')
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 25
        clock.advance_sync(1)
        assert beeper.volume == 100
        clock.advance_sync(1)
        assert beeper.volume == 100


def test_anim_infinite(beeper, clock):
    beeper.clock = clock
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(100, 2, infinite=True)
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 50
        clock.advance_sync(1)
        assert beeper.volume == 100
        clock.advance_sync(1)
        assert beeper.volume == 150


def test_anim_strength(beeper, clock):
    beeper.clock = clock
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(100, 2, strength=0.5)
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 25
        clock.advance_sync(1)
        assert beeper.volume == 50
        clock.advance_sync(1)
        assert beeper.volume == 50


def test_anim_no_clock(beeper):
    with beeper.extra_behavior('anim method'):
        with pytest.raises(TypeError):
            beeper.volume.anim(5)


def test_anim_explicit_clock(beeper, clock):
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim(5, clock=clock)
        assert beeper.volume == 5


def test_anim_in_coroutine(beeper, clock):
    with beeper.extra_behavior('anim method'):
        beeper.volume.anim
        beeper.clock = clock

        def there_and_back():
            yield from beeper.volume.anim(100, 2)
            yield from beeper.volume.anim(0, 2)

        clock.task(there_and_back())

        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 50
        clock.advance_sync(1)
        assert beeper.volume == 100
        clock.advance_sync(1)
        assert beeper.volume == 50
        clock.advance_sync(1)
        assert beeper.volume == 0
        clock.advance_sync(1)
        assert beeper.volume == 0


def test_component_assign(beeper, clock):
    with beeper.extra_behavior('tuple immutable'):
        beeper.position[0] = 5
        assert beeper.position == (5, 0, 0)
        beeper.position[1:] = 6, 7
        assert beeper.position == (5, 6, 7)


def test_anim_component(beeper, clock):
    with beeper.extra_behavior('anim method'):
        print(beeper.position[0])
        beeper.position[0].anim(5, clock=clock)
        assert beeper.position == (5, 0, 0)


def test_anim_components(beeper, clock):
    with beeper.extra_behavior('anim method'):
        beeper.position[0:2].anim((5, 6), clock=clock)
        assert beeper.position == (5, 6, 0)
