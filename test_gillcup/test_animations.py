from gillcup.animations import anim


def test_anim_basic(clock):
    animation = anim(1, 3, 2, clock)
    assert animation == 1
    clock.advance_sync(1)
    assert animation == 2
    clock.advance_sync(1)
    assert animation == 3
    clock.advance_sync(1)
    assert animation == 3


def test_anim_basic_vector(clock):
    animation = anim((1, 2), (3, 4), 2, clock)
    assert animation == (1, 2)
    clock.advance_sync(1)
    assert animation == (2, 3)
    clock.advance_sync(1)
    assert animation == (3, 4)


def test_anim_delay(clock):
    animation = anim(1, 3, 2, clock, delay=1)
    assert animation == 1
    clock.advance_sync(1)
    assert animation == 1
    clock.advance_sync(1)
    assert animation == 2
    clock.advance_sync(1)
    assert animation == 3
    clock.advance_sync(1)
    assert animation == 3


def test_anim_infinite(clock):
    animation = anim(1, 3, 2, clock, infinite=True)
    assert animation == 1
    clock.advance_sync(1)
    assert animation == 2
    clock.advance_sync(1)
    assert animation == 3
    clock.advance_sync(1)
    assert animation == 4
    clock.advance_sync(1)
    assert animation == 5


def test_anim_delay_infinite(clock):
    animation = anim(1, 3, 2, clock, delay=1, infinite=True)
    assert animation == 0
    clock.advance_sync(1)
    assert animation == 1
    clock.advance_sync(1)
    assert animation == 2
    clock.advance_sync(1)
    assert animation == 3
    clock.advance_sync(1)
    assert animation == 4
    clock.advance_sync(1)
    assert animation == 5
