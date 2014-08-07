import pytest

from gillcup.properties import AnimatedProperty, link
from gillcup.expressions import Progress


class Buzzer:
    volume = AnimatedProperty(0, name='volume')
    pitch = AnimatedProperty(440, name='pitch')
    position = x, y, z = AnimatedProperty(0, 0, 0, name='position: x y z')

    def __repr__(self):
        return '<test buzzer>'


class MultichannelBuzzer:
    """A Buzzer that emits 3 simultaneous tones

    Not good programming practice!
    This is just to test that ``volume`` and ``pitch`` work exactly the same
    when they are a top-level property as when they are a component.
    """
    volumes = volume, vol2, vol3 = AnimatedProperty(
        0, 0, 0, name='volumes:volume vol2 vol3')
    pitches = pitch, pitch2, pitch3 = AnimatedProperty(
        440, 440, 440, name='pitches: pitch pitch2 pitch3')
    position = x, y, z = AnimatedProperty(0, 0, 0, name='position: x y z')

    def __repr__(self):
        return '<test buzzer>'


@pytest.fixture(params=[Buzzer, MultichannelBuzzer])
def buzzer_class(request):
    return request.param


@pytest.fixture
def buzzer(buzzer_class):
    return buzzer_class()


def test_defaults(buzzer):
    assert buzzer.volume == 0
    assert buzzer.pitch == 440
    assert buzzer.position == (0, 0, 0)
    assert buzzer.x == buzzer.y == buzzer.z == 0


def test_setting_scalar(buzzer):
    buzzer.volume = 50
    assert buzzer.volume == 50
    assert buzzer.volume == (50,)


def test_setting_vector(buzzer):
    buzzer.position = 1, 2, 3
    assert buzzer.position == (1, 2, 3)
    assert buzzer.x == 1
    assert buzzer.y == 2
    assert buzzer.z == 3


def test_separate_instances_vector(buzzer):
    buzzer2 = Buzzer()
    buzzer2.x = 5
    assert buzzer2.position == (5, 0, 0)
    assert buzzer.position == (0, 0, 0)


def test_property_naming(check_dump):
    class Foo:
        namedprop = AnimatedProperty(5, name='namedprop')
        unnamedprop = AnimatedProperty(5)

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


def test_iadd(buzzer):
    buzzer.volume += 3
    assert buzzer.volume == 3


def test_set_progress(buzzer, clock):
    buzzer.volume = Progress(clock, 2) * 100
    assert buzzer.volume == 0
    clock.advance_sync(1)
    assert buzzer.volume == 50
    clock.advance_sync(1)
    assert buzzer.volume == 100


def test_add_progress(buzzer, clock):
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.pitch == 460


def test_set_to_property(buzzer):
    buzzer.volume = buzzer.pitch
    assert buzzer.volume == 440
    assert buzzer.pitch == 440


def test_set_to_property_animated(buzzer, clock):
    buzzer.pitch += Progress(clock, 2) * 20
    buzzer.volume = buzzer.pitch
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 450
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 460
    assert buzzer.pitch == 460


def test_set_to_property_divergent(buzzer, clock):
    buzzer.volume = buzzer.pitch
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 440
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 440
    assert buzzer.pitch == 460


def test_set_to_property_linked_method(buzzer, clock):
    buzzer.volume.link(buzzer.pitch)
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 450
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 460
    assert buzzer.pitch == 460


def test_set_to_property_linked_function(buzzer, clock):
    buzzer.volume = link(buzzer.pitch)
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 450
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 460
    assert buzzer.pitch == 460


def test_set_to_expression_with_linked_property(buzzer, clock):
    buzzer.volume = link(buzzer.pitch)
    buzzer.pitch += Progress(clock, 2) * 20
    assert buzzer.volume == 440
    assert buzzer.pitch == 440
    clock.advance_sync(1)
    assert buzzer.volume == 450
    assert buzzer.pitch == 450
    clock.advance_sync(1)
    assert buzzer.volume == 460
    assert buzzer.pitch == 460


def test_recursive_link(buzzer, buzzer_class, clock):
    if buzzer_class == MultichannelBuzzer:
        # TODO: This gets rather nasty with component property; fix!
        raise pytest.xfail(
            'INTERNALERROR> RuntimeError: maximum recursion depth exceeded')
    buzzer.volume = link(buzzer.volume)
    with pytest.raises(RuntimeError):
        buzzer.volume.get()
    assert str(buzzer.volume) == '<RuntimeError while getting value>'


def test_link_dump_method(buzzer, buzzer_class, clock, check_dump):
    # The dump is different for normal properties and for components
    buzzer.volume.link(buzzer.pitch)
    if buzzer_class == Buzzer:
        check_dump(buzzer.volume, """
            <test buzzer>.volume value <440.0>:
              linked <test buzzer>.pitch <440.0>:
                Constant <440.0>
        """)
    elif buzzer_class == MultichannelBuzzer:
        check_dump(buzzer.volume, """
            <test buzzer>.volume (volumes[0]) value <440.0>:
              <test buzzer>.volumes value <440.0, 0.0, 0.0>:
                Concat <440.0, 0.0, 0.0>:
                  linked <test buzzer>.pitch (pitches[0]) <440.0>:
                    <test buzzer>.pitches value <440.0, 440.0, 440.0>:
                      Constant <440.0, 440.0, 440.0>
                  Constant <0.0, 0.0>
        """)
    else:
        raise TypeError(buzzer_class)


def test_link_dump_function(buzzer, buzzer_class, clock, check_dump):
    # The dump is different for normal properties and for components
    buzzer.volume = link(buzzer.pitch) + 4
    if buzzer_class == Buzzer:
        check_dump(buzzer.volume, """
            <test buzzer>.volume value <444.0>:
              + <444.0>:
                linked <test buzzer>.pitch <440.0>:
                  Constant <440.0>
                Constant <4.0>
        """)
    elif buzzer_class == MultichannelBuzzer:
        check_dump(buzzer.volume, """
            <test buzzer>.volume (volumes[0]) value <444.0>:
              <test buzzer>.volumes value <444.0, 0.0, 0.0>:
                Concat <444.0, 0.0, 0.0>:
                  + <444.0>:
                    linked <test buzzer>.pitch (pitches[0]) <440.0>:
                      <test buzzer>.pitches value <440.0, 440.0, 440.0>:
                        Constant <440.0, 440.0, 440.0>
                    Constant <4.0>
                  Constant <0.0, 0.0>
        """)
    else:
        raise TypeError(buzzer_class)


def test_link_function_idempotent(buzzer, clock):
    linked = link(buzzer.volume)
    assert linked is link(linked)


def test_default_naming():
    class Foo:
        bar = b, a, r = AnimatedProperty(0, 0, 0)

    assert Foo.bar.name == '<unnamed property>'
    assert Foo.b.name == '<unnamed property>[0]'
    assert Foo.a.name == '<unnamed property>[1]'
    assert Foo.r.name == '<unnamed property>[2]'


def test_single_name():
    class Foo:
        bar = b, a, r = AnimatedProperty(0, 0, 0, name='bar')

    assert Foo.bar.name == 'bar'
    assert Foo.b.name == 'bar[0]'
    assert Foo.a.name == 'bar[1]'
    assert Foo.r.name == 'bar[2]'


@pytest.mark.parametrize('name', ['bar:x y z', 'bar: x y z', 'bar:x,y,z'])
def test_component_naming(name):
    class Foo:
        bar = b, a, r = AnimatedProperty(0, 0, 0, name=name)

    assert Foo.bar.name == 'bar'
    assert Foo.b.name == 'x'
    assert Foo.a.name == 'y'
    assert Foo.r.name == 'z'
