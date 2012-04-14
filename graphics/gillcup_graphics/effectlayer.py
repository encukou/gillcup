# Encoding: UTF-8
"""A Layer that provides some bling

With EffectLayer, it is possible to colorize, fade, or pixelate groups of
graphics objects.

This wors by rendering the layer's contents to a texture, and then drawing the
texture with effects applied.
Currently, the framebuffer object OpenGL extension to work.
"""

from pyglet import gl

from gillcup import properties
from gillcup_graphics import Layer
from gillcup_graphics.offscreen import fbo

from gillcup_graphics.mainwindow import Window


class EffectLayer(Layer):
    """A Layer that can colorie, fade, or pixelate its contents as a whole
    """
    opacity = properties.AnimatedProperty(1,
        docstring="""Opacity of this layer""")
    mosaic = mosaic_x, mosaic_y = properties.ScaleProperty(2,
        docstring=u"""Pixelation of this layer

        For example, if mosaic=(2, 4), the layer will be drawn using 2×4 blocks
        """)

    _opacity_data = None

    def need_offscreen(self):
        """

        Off-screen rendering is only done if needed, i.e. if ``color``,
        ``opacity`` or ``mosaic`` don't have their default values.

        Subclasses should extend this method if they need off-screen
        rendering in more circumstances.
        """
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
            width = max(1, int(parent_width / max(1, self.mosaic_x)))
            height = max(1, int(parent_height / max(1, self.mosaic_y)))

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

    def blit_buffer(self, framebuffer, parent_width, parent_height, **kwargs):
        """Draw the texture into the parent scene

        .. warning:

            This method's arguments are not part of the API yet and may change
            at any time.
        """
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


class RecordingLayer(EffectLayer):
    """A layer that records its contents as an image

    After this layer is drawn, the picture is available in the ``last_image``
    attribute as a pyglet ImageData object.
    """
    last_image = None

    def need_offscreen(self):
        return True

    def blit_buffer(self, framebuffer, **kwargs):
        self.last_image = framebuffer.get_image_data()
        super(RecordingLayer, self).blit_buffer(framebuffer=framebuffer,
            **kwargs)

    def get_image(self, width, height):
        """Draw this layer in a new invisible window and return the ImageData
        """
        window = Window(self, width=width, height=height, visible=False)
        window.manual_draw()
        return self.last_image
