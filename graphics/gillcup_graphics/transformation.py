
"""Transformation objects

A graphic object's transform method takes a Transformation object and updates
it with its transformation. For drawing, use a GlTransformation object, which
will update the OpenGL state directly. For hit tests, use a
MatrixTransformation object.
"""

from __future__ import division

# The more crazy matrix stuff is partly based on the GameObjects library by
#  Will McGugan, which is today, unfortunately, without a licence, but
#  the author wishes it to be used without restrictions:
# http://www.willmcgugan.com/blog/tech/2007/6/7/game-objects-commandments/
#   #comment146

from math import sin, cos, pi
import contextlib

from pyglet import gl

tau = 2 * pi
deg_to_rad = tau / 360


class BaseTransformation(object):
    """Base for all transformations: contains common functionality

    Transformations are based on a 3D affine transformation matrix (a 4x4
    matrix where the last column is [0 0 0 1])
    """
    @property
    @contextlib.contextmanager
    def state(self):
        """Context manager wrapping push() and pop()"""
        self.push()
        try:
            yield
        finally:
            self.pop()

    def reset(self):
        """Reset the matrix to identity"""
        raise NotImplementedError

    def push(self):
        """Push the matrix state: the corresponding pop() will return here

        You probably want to use ``state`` instead.
        """
        raise NotImplementedError

    def pop(self):
        """Restore matrix saved by the corresponding push() call"""
        raise NotImplementedError

    def translate(self, x=0, y=0, z=0):
        """Premultiply a translation matrix to self, in situ"""
        raise NotImplementedError

    def rotate(self, angle, x=0, y=0, z=1):
        """Premultiply a rotation matrix to self, in situ"""
        raise NotImplementedError

    def scale(self, x=1, y=1, z=1):
        """Premultiply a scaling matrix to self, in situ"""
        raise NotImplementedError

    def premultiply(self, values):
        """Premultiply the given matrix to self, in situ

        :param values: An iterable of 16 matrix elements in row-major (C) order
        """
        raise NotImplementedError


class GlTransformation(BaseTransformation):
    """OpenGL implementation: affects the OpenGL state directly
    """
    def reset(self):
        gl.glLoadIdentity()

    def push(self):
        gl.glPushMatrix()

    def pop(self):
        gl.glPopMatrix()

    def translate(self, x=0, y=0, z=0):
        gl.glTranslatef(x, y, z)

    def rotate(self, angle, x=0, y=0, z=1):
        gl.glRotatef(angle, x, y, z)

    def scale(self, x=1, y=1, z=1):
        gl.glScalef(x, y, z)

    def premultiply(self, values):
        gl.glMultMatrixf(*values)


class MatrixTransformation(BaseTransformation):
    """Implementation that uses tuples. Slow.
    """
    def __init__(self):
        super(MatrixTransformation, self).__init__()
        self.matrix = self.identity
        self.stack = []

    identity = (
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )

    def __len__(self):
        return 16

    def __getitem__(self, item):
        try:
            col, row = item
        except TypeError:
            return self.matrix[item]
        else:
            return self.matrix[row * 4 + col]

    def reset(self):
        self.matrix = self.identity

    def push(self):
        self.stack.append(self.matrix)

    def pop(self):
        self.matrix = self.stack.pop()

    def translate(self, x=0, y=0, z=0):
        self.premultiply((
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                x, y, z, 1,
            ))

    def rotate(self, angle, x=0, y=0, z=1):
        c = cos(angle * deg_to_rad)
        s = sin(angle * deg_to_rad)
        d = 1 - c
        xs = x * s
        ys = y * s
        zs = z * s
        xd = x * d
        yd = y * d
        zd = z * d
        self.premultiply((
                x * xd + c,  y * xd + zs, x * zd - ys, 0,
                x * yd - zs, y * yd + c,  y * zd + xs, 0,
                x * zd + ys, y * zd - xs, z * zd + c,  0,
                0, 0, 0, 1,
            ))

    def scale(self, x=1, y=1, z=1):
        self.premultiply((
                x, 0, 0, 0,
                0, y, 0, 0,
                0, 0, z, 0,
                0, 0, 0, 1,
            ))

    def premultiply(self, values):
        (m1_0,  m1_1,  m1_2,  m1_3,
         m1_4,  m1_5,  m1_6,  m1_7,
         m1_8,  m1_9,  m1_10, m1_11,
         m1_12, m1_13, m1_14, m1_15,
        ) = self.matrix

        (m2_0,  m2_1,  m2_2,  m2_3,
         m2_4,  m2_5,  m2_6,  m2_7,
         m2_8,  m2_9,  m2_10, m2_11,
         m2_12, m2_13, m2_14, m2_15,
        ) = values

        self.matrix = (
                m2_0 * m1_0 + m2_1 * m1_4 + m2_2 * m1_8 + m2_3 * m1_12,
                m2_0 * m1_1 + m2_1 * m1_5 + m2_2 * m1_9 + m2_3 * m1_13,
                m2_0 * m1_2 + m2_1 * m1_6 + m2_2 * m1_10 + m2_3 * m1_14,
                m2_0 * m1_3 + m2_1 * m1_7 + m2_2 * m1_11 + m2_3 * m1_15,

                m2_4 * m1_0 + m2_5 * m1_4 + m2_6 * m1_8 + m2_7 * m1_12,
                m2_4 * m1_1 + m2_5 * m1_5 + m2_6 * m1_9 + m2_7 * m1_13,
                m2_4 * m1_2 + m2_5 * m1_6 + m2_6 * m1_10 + m2_7 * m1_14,
                m2_4 * m1_3 + m2_5 * m1_7 + m2_6 * m1_11 + m2_7 * m1_15,

                m2_8 * m1_0 + m2_9 * m1_4 + m2_10 * m1_8 + m2_11 * m1_12,
                m2_8 * m1_1 + m2_9 * m1_5 + m2_10 * m1_9 + m2_11 * m1_13,
                m2_8 * m1_2 + m2_9 * m1_6 + m2_10 * m1_10 + m2_11 * m1_14,
                m2_8 * m1_3 + m2_9 * m1_7 + m2_10 * m1_11 + m2_11 * m1_15,

                m2_12 * m1_0 + m2_13 * m1_4 + m2_14 * m1_8 + m2_15 * m1_12,
                m2_12 * m1_1 + m2_13 * m1_5 + m2_14 * m1_9 + m2_15 * m1_13,
                m2_12 * m1_2 + m2_13 * m1_6 + m2_14 * m1_10 + m2_15 * m1_14,
                m2_12 * m1_3 + m2_13 * m1_7 + m2_14 * m1_11 + m2_15 * m1_15,
            )

    def transform_point(self, x=0, y=0, z=0):
        """Multiply the given vector by this matrix"""
        (   m1_0,  m1_1,  m1_2,  m1_3,
            m1_4,  m1_5,  m1_6,  m1_7,
            m1_8,  m1_9,  m1_10, m1_11,
            m1_12, m1_13, m1_14, m1_15,
        ) = self.inverse
        return (
                x * m1_0 + y * m1_4 + z * m1_8 + m1_12,
                x * m1_1 + y * m1_5 + z * m1_9 + m1_13,
                x * m1_2 + y * m1_6 + z * m1_10 + m1_14,
            )

    @property
    def inverse(self):
        """The inverse (matrix with the opposite effect) of this matrix.

        N.B. Only works with transformation martices (last column is identity)
        """

        (i0,  i1,  i2,  i3,
         i4,  i5,  i6,  i7,
         i8,  i9,  i10, i11,
         i12, i13, i14, i15,
        ) = self.matrix

        negpos = [0, 0]
        temp = i0 * i5 * i10
        negpos[temp > 0] += temp

        temp = i1 * i6 * i8
        negpos[temp > 0] += temp

        temp = i2 * i4 * i9
        negpos[temp > 0] += temp

        temp = -i2 * i5 * i8
        negpos[temp > 0] += temp

        temp = -i1 * i4 * i10
        negpos[temp > 0] += temp

        temp = -i0 * i6 * i9
        negpos[temp > 0] += temp

        det_1 = negpos[0] + negpos[1]

        if (det_1 == 0) or (abs(det_1 / (negpos[1] - negpos[0])) <
                (2 * 0.00000000000000001)):
            raise ValueError("Matrix can not be inverted")

        det_1 = 1 / det_1

        m = [(i5 * i10 - i6 * i9) * det_1,
            -(i1 * i10 - i2 * i9) * det_1,
             (i1 * i6 - i2 * i5 ) * det_1,
            0,
            -(i4 * i10 - i6 * i8) * det_1,
             (i0 * i10 - i2 * i8) * det_1,
            -(i0 * i6 - i2 * i4) * det_1,
            0,
             (i4 * i9 - i5 * i8) * det_1,
            -(i0 * i9 - i1 * i8) * det_1,
             (i0 * i5 - i1 * i4) * det_1,
            0,
            0, 0, 0, 1]

        m[12] = - (i12 * m[0] + i13 * m[4] + i14 * m[8])
        m[13] = - (i12 * m[1] + i13 * m[5] + i14 * m[9])
        m[14] = - (i12 * m[2] + i13 * m[6] + i14 * m[10])

        return tuple(m)
