from gillcup import Clock

def test_clock():
    clock = Clock()
    assert clock.time == 0
    clock.advance(1)
    assert clock.time == 1
