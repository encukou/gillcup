
import pyglet
from pyglet import gl

from gillcup_graphics.base import GraphicsObject


vertices = (gl.GLfloat * 8)(
        0, 0,
        1, 0,
        1, 1,
        0, 1,
    )


class Rectangle(GraphicsObject):
    def draw(self, transformation, **kwargs):
        transformation.scale(self.width, self.height, 1)
        color = self.color + (self.opacity, )
        gl.glColor4fv((gl.GLfloat * 4)(*color))
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, vertices)
        gl.glDrawArrays(gl.GL_QUADS, 0, 4)
