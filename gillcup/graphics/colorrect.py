
import pyglet
from pyglet.gl import *

from gillcup.graphics.layer import Layer
from gillcup.graphics import helpers

vertices = [
        0, 0,
        1, 0,
        1, 1,
        0, 1,
    ]
vertices_gl = (GLfloat * len(vertices))(*vertices)


class ColorRect(Layer):
    """ColorRect without animatable properties"""
    def __init__(self, parent, size=(1, 1), color=(.5, .5, .5), **kwargs):
        super(ColorRect, self).__init__(parent, **kwargs)
        self.size = size
        self.color = color

    def drawContent(self):
        # XXX: Take opacity into account
        glScalef(*helpers.extend_tuple(*self.size, default=1))
        glColor3fv((GLfloat * 3)(*helpers.extend_tuple_copy(*self.color)))
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices_gl)
        glDrawArrays(GL_QUADS, 0, len(vertices) // 2)
