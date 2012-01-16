
import pyglet
from pyglet.gl import *

from gillcup_graphics.base import GraphicsObject

vertices = (GLfloat * 8)(
        0, 0,
        1, 0,
        1, 1,
        0, 1,
    )

class Rectangle(GraphicsObject):
    def draw(self, transformation, **kwargs):
        transformation.scale(self.width, self.height, 1)
        color = self.color + (self.opacity, )
        glColor4fv((GLfloat * 4)(*color))
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glDrawArrays(GL_QUADS, 0, 4)
