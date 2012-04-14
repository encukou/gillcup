"""Tests for the transformation module
"""

import math

from gillcup_graphics.transformation import MatrixTransformation


def almost_equal(a, b):
    """Return true if the numbers a and b are very near each other"""
    return abs(a - b) < 0.00001


def sequences_almost_equal(a_seq, b_seq):
    """Return true if corresponding contents of lists a, b are alost_equal"""
    print a_seq, b_seq
    if len(a_seq) != len(b_seq):
        return False
    return all(almost_equal(a, b) for a, b in zip(a_seq, b_seq))


def matrix_almost_equal(matrix, *args):
    """Return true if elements of matrix are almost equal to args"""
    print '---'
    print matrix
    print args
    return sequences_almost_equal(matrix, args)


def is_identity(matrix):
    """Return true if given matrix is the identity matrix"""
    return matrix_almost_equal(matrix,
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1,)


def pytest_funcarg__matrix(request):
    """Funcarg factory for a matrix"""
    return MatrixTransformation()


def distort(matrix):
    """Mangle the given matrix in some way"""
    matrix.translate(5, 6, 7)
    matrix.rotate(5, 1, 2, 3)
    matrix.scale(2, 3, 4)


def test_identity(matrix):
    """Ensure the matrix is identity by default"""
    assert is_identity(matrix)


def test_translate(matrix):
    """Test general translation works"""
    matrix.translate(5, 6, 7)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            5, 6, 7, 1,
        )


def test_translate_x(matrix):
    """Test x-axis translation works"""
    matrix.translate(4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            4, 0, 0, 1,
        )
    matrix.translate(x=4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            8, 0, 0, 1,
        )


def test_translate_y(matrix):
    """Test y-axis translation works"""
    matrix.translate(0, 4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 4, 0, 1,
        )
    matrix.translate(y=4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 8, 0, 1,
        )


def test_translate_z(matrix):
    """Test z-axis translation works"""
    matrix.translate(0, 0, 4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 4, 1,
        )
    matrix.translate(z=4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 8, 1,
        )


def test_rotate_z(matrix):
    """Test z-axis rotation works"""
    matrix.rotate(180)
    assert matrix_almost_equal(matrix,
            -1, 0, 0, 0,
            0, -1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    matrix.rotate(90)
    assert matrix_almost_equal(matrix,
            0, -1, 0, 0,
            1, 0, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    matrix.rotate(45)
    assert matrix_almost_equal(matrix,
            math.sqrt(2) / 2, -math.sqrt(2) / 2, 0, 0,
            math.sqrt(2) / 2, math.sqrt(2) / 2, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )


def test_rotate_y(matrix):
    """Test y-axis rotation works"""
    matrix.rotate(180, 0, 1, 0)
    assert matrix_almost_equal(matrix,
            -1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, -1, 0,
            0, 0, 0, 1,
        )
    matrix.rotate(90, 0, 1, 0)
    assert matrix_almost_equal(matrix,
            0, 0, 1, 0,
            0, 1, 0, 0,
            -1, 0, 0, 0,
            0, 0, 0, 1,
        )
    matrix.rotate(45, 0, 1, 0)
    assert matrix_almost_equal(matrix,
            math.sqrt(2) / 2, 0, math.sqrt(2) / 2, 0,
            0, 1, 0, 0,
            -math.sqrt(2) / 2, 0, math.sqrt(2) / 2, 0,
            0, 0, 0, 1,
        )


def test_rotate_arbitrary(matrix):
    """Test general rotation works"""
    matrix.rotate(45, 1, 0.5, 1)
    assert matrix_almost_equal(matrix,
            1, 0.8535534, -0.06066, 0,
            -0.56066, 0.78033, 0.8535534, 0,
            0.6464466, -0.56066, 1, 0,
            0, 0, 0, 1,
        )


def test_scale(matrix):
    """Test general scaling works"""
    matrix.scale(5, 6, 7)
    assert matrix_almost_equal(matrix,
            5, 0, 0, 0,
            0, 6, 0, 0,
            0, 0, 7, 0,
            0, 0, 0, 1,
        )


def test_scale_x(matrix):
    """Test x-axis scaling works"""
    matrix.scale(4)
    assert matrix_almost_equal(matrix,
            4, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    matrix.scale(x=4)
    assert matrix_almost_equal(matrix,
            16, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )


def test_scale_y(matrix):
    """Test y-axis scaling works"""
    matrix.scale(1, 4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 4, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    matrix.scale(y=4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 16, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )


def test_scale_z(matrix):
    """Test z-axis scaling works"""
    matrix.scale(1, 1, 4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 4, 0,
            0, 0, 0, 1,
        )
    matrix.scale(z=4)
    assert matrix_almost_equal(matrix,
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 16, 0,
            0, 0, 0, 1,
        )


def test_push_pop(matrix):
    """Test that a pop restores state"""
    matrix.push()
    distort(matrix)
    matrix.pop()
    assert is_identity(matrix)


def test_state(matrix):
    """Test the ``state`` context manager"""
    with matrix.state:
        distort(matrix)
    assert is_identity(matrix)


def test_reset(matrix):
    """Test the matrix is identity after a reset"""
    distort(matrix)
    matrix.reset()
    assert is_identity(matrix)


def test_premultiply_range(matrix):
    """Test premultiplication with a range of numbers"""
    matrix.premultiply(range(16))
    assert matrix_almost_equal(matrix, *range(16))


def test_premultiply_rotate_translate(matrix):
    """Test premultiplication with literal affine matrices"""
    matrix.premultiply((
            0, 0, 1, 0,
            0, 1, 0, 0,
            1, 0, 0, 0,
            0, 0, 0, 1,
        ))
    matrix.premultiply((
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            3, 4, 5, 1,
        ))
    assert matrix_almost_equal(matrix,
            0, 0, 1, 0,
            0, 1, 0, 0,
            1, 0, 0, 0,
            5, 4, 3, 1,
        )


def test_premultiply_random(matrix):
    """Test premultiplication with (fixed) random numbers"""
    matrix.premultiply((
            309, 223, 296, 639,
            132, 737, 406, 731,
            534, 748, 442, 133,
            901, 862, 439, 605,
        ))
    matrix.premultiply((
            450, 526, 880, 995,
            655, 278, 232, 983,
            484, 286, 594, 334,
            327, 158, 564, 939,
        ))
    assert matrix_almost_equal(matrix,
            1574897, 2003942, 1172521, 1391071,
            1248662, 1371833, 840829, 1247334,
            805438, 1050934, 668554, 799414,
            1269114, 1420657, 822449, 967558,
        )


def test_inverse(matrix):
    """Test taking the inverse of an affine matrix"""
    matrix.premultiply((
            30, 22, 96, 0,
            12, 77, 20, 0,
            34, 48, 42, 0,
            91, 62, 43, 1,
        ))
    assert sequences_almost_equal(matrix.inverse, (
            -0.018347588, -0.029724060, 0.056091657, 0,
            -0.001420042, 0.016169114, -0.004453768, 0,
            0.016475714, 0.005583347, -0.016507988, 0,
            1.049217363, 1.462320478, -4.118363724, 1,
        ))
