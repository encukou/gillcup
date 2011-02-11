
from math import sin, cos

from pyglet import gl

"""Transformation objects

A graphic object's transform method takes a Transformation object and updates
it with its transformation. For drawing, use a GlTransformation object, which
will update the OpenGL state directly. For hit tests, use a
MatrixTransformation object. For heavy-duty tests, use MatrixTransformation,
but pass the NumPy module to it.
"""

# The more crazy matrix stuff is partly based on the GameObjects library by
#  Will McGugan, which is today, unfortunately, without a licence, but
#  the author wishes it to be used without restrictions:
# http://www.willmcgugan.com/blog/tech/2007/6/7/game-objects-commandments/#comment146


class GlTransformation(object):
    """OpenGL implementation
    """
    def reset(self):
        gl.glLoadIdentity()

    def push(self):
        gl.glPushMatrix()

    def pop(self):
        gl.glPopMatrix()

    def translate(self, x, y, z=0):
        gl.glTranslatef(x, y, z)

    def rotate(self, angle, x=0, y=0, z=1):
        gl.glRotatef(angle, x, y, z)

    def scale(self, x=1, y=1, z=1):
        gl.glScalef(x, y, z)

    def multiply(self, values):
        gl.glMultMatrixf(*matrix)

class MatrixTransformation(object):
    """Implementation that uses tuples. Slow.
    """
    def __init__(self, numpy=None):
        if numpy is None:
            self.identity = (
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1,
                )
        else:
            self.identity = numpy.identity(4)
            self.multiply = lambda other: numpy.dot(other, self.matrix)
            self.getInverse = lambda: numpy.linalg.inv(self.matrix)
        self.reset()
        self.stack = []

    def reset(self):
        self.matrix = self.identity

    def push(self):
        self.stack.append(self.matrix)

    def pop(self):
        self.matrix = self.stack.pop()

    def translate(self, x=0, y=0, z=0):
        self.multiply((
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                x, y, z, 1,
            ))

    def rotate(self, angle, x=0, y=0, z=1):
        c = cos(angle)
        s = sin(angle)
        d = 1 - c
        self.multiply((
                x*x*d+c,   y*x*d+z*s, x*z*d-y*s, 0,
                x*y*d-z*s, y*y*d+c,   y*z*d+x*s, 0,
                x*z*d+y*s, y*z*d-x*s, z*z*d+c,   0,
                0,         0,         0,         1,
            ))

    def scale(self, x=1, y=1, z=1):
        self.multiply((
                x, 0, 0, 0,
                0, y, 0, 0,
                0, 0, z, 0,
                0, 0, 0, 1,
            ))

    def multiply(self, values):
        (
                m1_0,  m1_1,  m1_2,  m1_3,
                m1_4,  m1_5,  m1_6,  m1_7,
                m1_8,  m1_9,  m1_10, m1_11,
                m1_12, m1_13, m1_14, m1_15,
            ) = self.matrix

        (
                m2_0,  m2_1,  m2_2,  m2_3,
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

    def transformPoint(self, x=0, y=0, z=0):
        (
                m1_0,  m1_1,  m1_2,  m1_3,
                m1_4,  m1_5,  m1_6,  m1_7,
                m1_8,  m1_9,  m1_10, m1_11,
                m1_12, m1_13, m1_14, m1_15,
            ) = self.getInverse()
        return (
                x * m1_0 + y * m1_4 + z * m1_8 + m1_12,
                x * m1_1 + y * m1_5 + z * m1_9 + m1_13,
                x * m1_2 + y * m1_6 + z * m1_10 + m1_14, 
            )

    def getInverse(self):
        """Returns the inverse (matrix with the opposite effect) of this
        matrix."""

        (
                i0,  i1,  i2,  i3,
                i4,  i5,  i6,  i7,
                i8,  i9,  i10, i11,
                i12, i13, i14, i15,
            ) = self.matrix

        negpos=[0., 0.]
        temp = i0 * i5 * i10
        negpos[temp > 0.] += temp

        temp = i1 * i6 * i8
        negpos[temp > 0.] += temp

        temp = i2 * i4 * i9
        negpos[temp > 0.] += temp

        temp = -i2 * i5 * i8
        negpos[temp > 0.] += temp

        temp = -i1 * i4 * i10
        negpos[temp > 0.] += temp

        temp = -i0 * i6 * i9
        negpos[temp > 0.] += temp

        det_1 = negpos[0]+negpos[1]

        if (det_1 == 0.) or (abs(det_1 / (negpos[1] - negpos[0])) < \
                             (2. * 0.00000000000000001) ):
            raise ValueError("This Matrix44 can not be inverted")

        det_1 = 1. / det_1

        m = [ (i5*i10 - i6*i9)*det_1,
                  -(i1*i10 - i2*i9)*det_1,
                   (i1*i6 - i2*i5 )*det_1,
                   0.0,
                  -(i4*i10 - i6*i8)*det_1,
                   (i0*i10 - i2*i8)*det_1,
                  -(i0*i6 - i2*i4)*det_1,
                   0.0,
                  (i4*i9 - i5*i8 )*det_1,
                  -(i0*i9 - i1*i8)*det_1,
                   (i0*i5 - i1*i4)*det_1,
                   0.0,
                   0.0, 0.0, 0.0, 1.0 ]

        m[12] = - ( i12 * m[0] + i13 * m[4] + i14 * m[8] )
        m[13] = - ( i12 * m[1] + i13 * m[5] + i14 * m[9] )
        m[14] = - ( i12 * m[2] + i13 * m[6] + i14 * m[10] )

        return tuple(m)
