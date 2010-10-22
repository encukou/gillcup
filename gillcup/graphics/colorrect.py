
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
    """A rectangle of solid color.

    :param color: The color of this rectangle. Becomes an animable attribute.

    See the :py:class:`base class <gillcup.graphics.baselayer.BaseLayer>`
    for functionality common to all graphics objects, particularly additional
    attributes and __init__ arguments.
    """
    def __init__(self, parent, color=(.5, .5, .5), **kwargs):
        super(ColorRect, self).__init__(parent, color=color, **kwargs)

    def draw(self, **kwargs):
        glScalef(*helpers.extend_tuple_copy(self.size))
        color = helpers.extend_tuple_copy(self.color) + (self.opacity, )
        glColor4fv((GLfloat * 4)(*color))
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices_gl)
        glDrawArrays(GL_QUADS, 0, len(vertices) // 2)
