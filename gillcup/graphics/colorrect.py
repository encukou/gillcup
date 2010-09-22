
import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.graphics import helpers

vertices = [
        0, 0,
        1, 0,
        1, 1,
        0, 1,
    ]
vertices_gl = (GLfloat * len(vertices))(*vertices)


class ColorRect(BaseLayer):
    """ColorRect without animatable properties"""
    def __init__(self, parent, size=(1, 1), color=(.5, .5, .5), **kwargs):
        super(ColorRect, self).__init__(parent, **kwargs)
        self.size = size
        self.color = color

    def draw(self, **kwargs):
        glScalef(*helpers.extend_tuple(self.size, default=1))
        color = helpers.extend_tuple_copy(self.color) + (self.opacity, )
        glColor4fv((GLfloat * 4)(*color))
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices_gl)
        glDrawArrays(GL_QUADS, 0, len(vertices) // 2)
