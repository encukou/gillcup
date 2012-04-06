
import math

from gillcup_graphics.transformation import MatrixTransformation


def assert_almost_equal(a, b):
    assert abs(a - b) < 0.00001


def assert_sequences_almost_equal(a_seq, b_seq):
    print a_seq, b_seq
    assert len(a_seq) == len(b_seq)
    for a_item, b_item in zip(a_seq, b_seq):
        assert_almost_equal(a_item, b_item)


class TestMatrixTransformation(object):
    def setup(self):
        self.t = MatrixTransformation()

    def assert_matrix(self, *args):
        print '---'
        print self.t.matrix
        print args
        assert_sequences_almost_equal(self.t, args)

    def assert_identity(self):
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )

    def distort(self):
        self.t.translate(5, 6, 7)
        self.t.rotate(5, 1, 2, 3)
        self.t.scale(2, 3, 4)

    def test_identity(self):
        self.assert_identity()

    def test_translate(self):
        self.t.translate(5, 6, 7)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                5, 6, 7, 1,
            )

    def test_translate_x(self):
        self.t.translate(4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                4, 0, 0, 1,
            )
        self.t.translate(x=4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                8, 0, 0, 1,
            )

    def test_translate_y(self):
        self.t.translate(0, 4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 4, 0, 1,
            )
        self.t.translate(y=4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 8, 0, 1,
            )

    def test_translate_z(self):
        self.t.translate(0, 0, 4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 4, 1,
            )
        self.t.translate(z=4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 8, 1,
            )

    def test_rotate_z(self):
        self.t.rotate(180)
        self.assert_matrix(
                -1, 0, 0, 0,
                0, -1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )
        self.t.rotate(90)
        self.assert_matrix(
                0, -1, 0, 0,
                1, 0, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )
        self.t.rotate(45)
        self.assert_matrix(
                math.sqrt(2) / 2, -math.sqrt(2) / 2, 0, 0,
                math.sqrt(2) / 2, math.sqrt(2) / 2, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )

    def test_rotate_y(self):
        self.t.rotate(180, 0, 1, 0)
        self.assert_matrix(
                -1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, -1, 0,
                0, 0, 0, 1,
            )
        return
        self.t.rotate(90, 0, 1, 0)
        self.assert_matrix(
                0, 0, 1, 0,
                0, 1, 0, 0,
                -1, 0, 0, 0,
                0, 0, 0, 1,
            )
        self.t.rotate(45, 0, 1, 0)
        self.assert_matrix(
                math.sqrt(2) / 2, 0, math.sqrt(2) / 2, 0,
                0, 1, 0, 0,
                -math.sqrt(2) / 2, 0, math.sqrt(2) / 2, 0,
                0, 0, 0, 1,
            )

    def test_rotate_arbitrary(self):
        self.t.rotate(45, 1, 0.5, 1)
        self.assert_matrix(
                1, 0.8535534, -0.06066, 0,
                -0.56066, 0.78033, 0.8535534, 0,
                0.6464466, -0.56066, 1, 0,
                0, 0, 0, 1,
            )

    def test_scale(self):
        self.t.scale(5, 6, 7)
        self.assert_matrix(
                5, 0, 0, 0,
                0, 6, 0, 0,
                0, 0, 7, 0,
                0, 0, 0, 1,
            )

    def test_scale_x(self):
        self.t.scale(4)
        self.assert_matrix(
                4, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )
        self.t.scale(x=4)
        self.assert_matrix(
                16, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )

    def test_scale_y(self):
        self.t.scale(1, 4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 4, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )
        self.t.scale(y=4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 16, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            )

    def test_scale_z(self):
        self.t.scale(1, 1, 4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 4, 0,
                0, 0, 0, 1,
            )
        self.t.scale(z=4)
        self.assert_matrix(
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 16, 0,
                0, 0, 0, 1,
            )

    def test_push_pop(self):
        self.t.push()
        self.distort()
        self.t.pop()
        self.assert_identity()

    def test_state(self):
        with self.t.state:
            self.distort()
        self.assert_identity()

    def test_reset(self):
        self.distort()
        self.t.reset()
        self.assert_identity()

    def test_premultiply_range(self):
        self.t.premultiply(range(16))
        self.assert_matrix(*range(16))

    def test_premultiply_rotate_translate(self):
        self.t.premultiply((
                0, 0, 1, 0,
                0, 1, 0, 0,
                1, 0, 0, 0,
                0, 0, 0, 1,
            ))
        self.t.premultiply((
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                3, 4, 5, 1,
            ))
        self.assert_matrix(
                0, 0, 1, 0,
                0, 1, 0, 0,
                1, 0, 0, 0,
                5, 4, 3, 1,
            )

    def test_premultiply_random(self):
        self.t.premultiply((
                309, 223, 296, 639,
                132, 737, 406, 731,
                534, 748, 442, 133,
                901, 862, 439, 605,
            ))
        self.t.premultiply((
                450, 526, 880, 995,
                655, 278, 232, 983,
                484, 286, 594, 334,
                327, 158, 564, 939,
            ))
        self.assert_matrix(
                1574897, 2003942, 1172521, 1391071,
                1248662, 1371833, 840829, 1247334,
                805438, 1050934, 668554, 799414,
                1269114, 1420657, 822449, 967558,
            )

    def test_inverse(self):
        self.t.premultiply((
                30, 22, 96, 0,
                12, 77, 20, 0,
                34, 48, 42, 0,
                91, 62, 43, 1,
            ))
        assert_sequences_almost_equal(self.t.inverse, (
                -0.018347588, -0.029724060, 0.056091657, 0,
                -0.001420042, 0.016169114, -0.004453768, 0,
                0.016475714, 0.005583347, -0.016507988, 0,
                1.049217363, 1.462320478, -4.118363724, 1,
            ))
