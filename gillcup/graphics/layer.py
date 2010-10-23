
from contextlib import contextmanager

import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.graphics import helpers
from gillcup.pygrendertexture.RenderTextureManager import RenderTextureManager

white = (GLfloat * 3)(1, 1, 1)

class Layer(BaseLayer):
    """A container for graphics objects

    :param pixelization: The side lengths of a "pixel" for a mosaic effect.

    See the :py:class:`base class <gillcup.graphics.baselayer.BaseLayer>`
    for functionality common to all graphics objects, particularly additional
    attributes and __init__ arguments.

    Setting opacity (or pixelization) to a non-trivial value will cause the
    contents of a Layer to be rendered in an off-screen buffer, which may hurt
    performance.

    A Layer may be the parent of other graphics objects.
    """
    _opacity_data = None

    def __init__(self, parent=None, **kwargs):
        self.pixelization = kwargs.pop('pixelization', (1, 1))
        super(Layer, self).__init__(parent, **kwargs)
        self.children = []

    def draw(self, **kwargs):
        color = self.getColor(kwargs)
        if color != (1, 1, 1):
            kwargs['color'] = color
        gl.glTranslatef(*helpers.extend_tuple(self.anchorPoint))
        self.children = [
                c for c in self.children if not c.do_draw(**kwargs)
            ]

    def needOffscreen(self):
        pixelization = helpers.extend_tuple_copy(self.pixelization)
        return self.opacity < 0.999 or pixelization != (1, 1, 1)

    def getDrawContext(self, kwargs):
        window = kwargs.get('window', None)
        if window and self.needOffscreen():
            pixelization = helpers.extend_tuple_copy(self.pixelization)
            parent_texture = kwargs.get('parent_texture')
            if parent_texture:
                parent_width = parent_texture.width
                parent_height = parent_texture.height
            else:
                parent_width = window.width
                parent_height = window.height
            pix_x, pix_y, dummy = pixelization
            width = max(1, int(parent_width/pix_x))
            height = max(1, int(parent_height/pix_y))
            if self._opacity_data:
                rendermanager, rendertexture, w, h = self._opacity_data
            else:
                w, h = 0, 0
            if (w, h) != (width, height):
                rendermanager = RenderTextureManager(window)
                rendertexture = rendermanager.Create(
                        width=width,
                        height=height,
                        alpha=True,
                    )
                self._opacity_data = rendermanager, rendertexture, width, height
            kwargs['parent_texture'] = rendertexture
            @contextmanager
            def cm(*args, **kwargs):
                glPushMatrix()
                if parent_texture:
                    parent_texture.EndRender()
                rendertexture.StartRender()
                glClearColor(0, 0, 0, 0)
                glClear(GL_COLOR_BUFFER_BIT)
                glPopMatrix()
                yield kwargs
                rendertexture.EndRender()
                if parent_texture:
                    parent_texture.StartRender()
                glLoadIdentity()
                if parent_texture:
                    parent_texture.SetAsInactive(0)
                rendertexture.SetAsActive(0)
                try:
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                    glColor4fv((GLfloat * 4)(1, 1, 1, self.opacity))
                    glEnable(GL_TEXTURE_2D)
                    glBegin(GL_QUADS)
                    glTexCoord2f(0, 0)
                    glVertex2i(0, 0)
                    glTexCoord2f(rendertexture.maxtextureu, 0 )
                    glVertex2i(window.width, 0)
                    glTexCoord2f(rendertexture.maxtextureu, rendertexture.maxtexturev)
                    glVertex2i(window.width, window.height)
                    glTexCoord2f(0, rendertexture.maxtexturev)
                    glVertex2i(0, window.height)
                    glEnd()
                finally:
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glDisable(GL_TEXTURE_2D)
                rendertexture.SetAsInactive(0)
                if parent_texture:
                    parent_texture.SetAsActive(0)
            return cm()
        elif self._opacity_data:
                self._opacity_data = None
        return helpers.nullContextManager(**kwargs)
