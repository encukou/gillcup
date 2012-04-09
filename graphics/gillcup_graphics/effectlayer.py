
import pyglet
from pyglet import gl

from gillcup import properties
from gillcup_graphics.layer import Layer
from gillcup_graphics.offscreen import fbo


class EffectLayer(Layer):
    def __init__(self,
            parent=None,
            opacity=1,
            mosaic=(1, 1),
            color=(1, 1, 1),
            **kwargs):
        super(EffectLayer, self).__init__(parent, **kwargs)
        self.opacity = opacity
        self.mosaic = mosaic
        self.color = color

    opacity = properties.AnimatedProperty(1)
    mosaic = mosaic_x, mosaic_y = properties.ScaleProperty(2)
    color = red, green, blue = properties.ScaleProperty(3)

    _opacity_data = None

    def need_offscreen(self):
        return (not all(0.99 < n < 1.01 for n in self.mosaic) or
                self.opacity < 0.99 or
                not all(0.99 < c < 1.01 for c in self.color)
            )

    def draw(self, window, transformation, **kwargs):
        if window and self.need_offscreen():
            parent_texture_size = kwargs.get('parent_texture_size')
            if parent_texture_size:
                parent_width, parent_height = parent_texture_size
            else:
                parent_width = window.width
                parent_height = window.height
            width = max(1, int(parent_width / self.mosaic_x))
            height = max(1, int(parent_height / self.mosaic_y))

            if self._opacity_data:
                framebuffer, w, h = self._opacity_data
            else:
                framebuffer = w = h = None
            if (w, h) != (width, height):
                if framebuffer:
                    framebuffer.destroy()
                framebuffer = fbo.FBO(width, height)
                self._opacity_data = framebuffer, width, height
            kwargs['parent_texture_size'] = width, height

            with framebuffer.bind_draw() as parent_framebuffer:
                gl.glClearColor(0, 0, 0, 0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)

                with transformation.state:
                    super(EffectLayer, self).draw(window=window,
                        transformation=transformation, **kwargs)

            self.blit_buffer(
                    framebuffer=framebuffer,
                    parent_framebuffer=parent_framebuffer,
                    width=width,
                    height=height,
                    parent_width=parent_width,
                    parent_height=parent_height,
                    window=window,
                    transformation=transformation,
                    **kwargs)

        else:
            if self._opacity_data:
                framebuffer, w, h = self._opacity_data
                framebuffer.destroy()
                self._opacity_data = None
            super(EffectLayer, self).draw(window=window,
                transformation=transformation, **kwargs)

    def blit_buffer(self, framebuffer, parent_framebuffer,
            width, height, parent_width, parent_height,
            **kwargs):
        gl.glViewport(0, 0, parent_width, parent_height)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,
            gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glBindTexture(gl.GL_TEXTURE_2D, framebuffer.texture_id)
        gl.glEnable(gl.GL_TEXTURE_2D)

        gl.glColor4fv((gl.GLfloat * 4)(*self.color + (self.opacity, )))
        gl.glBlendFunc(gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)  # premultipl.
        gl.glBegin(gl.GL_TRIANGLE_STRIP)
        gl.glTexCoord2f(0, 0)
        gl.glVertex2i(0, 0)
        gl.glTexCoord2f(0, parent_height)
        gl.glVertex2i(0, parent_height)
        gl.glTexCoord2f(parent_width, 0)
        gl.glVertex2i(parent_width, 0)
        gl.glTexCoord2f(parent_width, parent_height)
        gl.glVertex2i(parent_width, parent_height)
        gl.glEnd()
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
            gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
            gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        gl.glViewport(0, 0, parent_width, parent_height)

    def _blit_buffer_direct(self, framebuffer, parent_framebuffer,
            width, height, parent_width, parent_height,
            transformation, **kwargs):
        # XXX: Use this instead of blit_buffer when we don't need
        # colorizing/opacity
        transformation.reset()
        gl.glViewport(0, 0, width, height)
        gl.glBindFramebufferEXT(gl.GL_READ_FRAMEBUFFER_EXT,
            framebuffer.framebuffer_id)
        gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0_EXT)

        gl.glBindFramebufferEXT(gl.GL_DRAW_FRAMEBUFFER_EXT,
            parent_framebuffer.framebuffer_id)
        gl.glBlitFramebufferEXT(0, 0, width, height, 0, 0,
            parent_width, parent_height,
            gl.GL_COLOR_BUFFER_BIT, gl.GL_NEAREST)
        gl.glDisable(gl.GL_TEXTURE_2D)
