"""Brute-force check that a Slice of a Concat simplifies correctly"""

from gillcup.expressions import Value, Concat, simplify


def generate_splits(n, _start=0):
    """Generate all "splits" of range(n)

    A "split" of a sequence is a tuple of tuples whose concatenation yields
    that sequence.
    (see test_generate_splits_3 for an example)
    """
    if _start >= n:
        yield ()
    elif _start >= n - 1:
        yield (_start,),
    else:
        for split in generate_splits(n, _start + 1):
            yield ((_start,),) + split
            yield (((_start,) + split[0]),) + split[1:]


def test_generate_splits_0():
    assert list(generate_splits(0)) == [
        (),
    ]


def test_generate_splits_1():
    assert list(generate_splits(1)) == [
        ((0,),),
    ]


def test_generate_splits_3():
    # start ignoring PEP8Bear because this is more readable when aligned
    assert list(generate_splits(3)) == [
        ((0,), (1,), (2,),),
        ((0,    1,), (2,),),
        ((0,), (1,    2,),),
        ((0,    1,    2,),),
    ]
    # stop ignoring


def pytest_generate_tests(metafunc):
    if {'start', 'stop', 'tuples'} <= set(metafunc.fixturenames):
        def _gen():
            for n in (0, 1, 5):
                for splits in generate_splits(n):
                    for start in range(-1, n + 2):
                        for stop in range(start, n + 2):
                            yield start, stop, splits
        argvalues = list(_gen())
        ids = ['<{}>[{}:{}]'.format('|'.join(','.join(str(n) for n in t)
                                             for t in tp),
                                    start, stop)
               for start, stop, tp in argvalues]
        metafunc.parametrize(['start', 'stop', 'tuples'], argvalues, ids=ids)


def test_slice_of_concat_simplification(start, stop, tuples):
    expected = sum(tuples, ())[start:stop]
    exp = Concat(*(Value(*t) for t in tuples))[start:stop]
    assert exp.get() == expected
    assert simplify(exp).get() == expected
