
from contextlib import contextmanager

import pyglet
from pyglet.gl import *

from gillcup.graphics.baselayer import BaseLayer
from gillcup.graphics import helpers
from gillcup.pygrendertexture.RenderTextureManager import RenderTextureManager

white = (GLfloat * 3)(1, 1, 1)

class Layer(BaseLayer):
    _opacity_data = None

    def __init__(self, parent=None, **kwargs):
        self.pixelization = kwargs.pop('pixelization', 1)
        super(Layer, self).__init__(parent, **kwargs)
        self.children = []

    def draw(self, **kwargs):
        gl.glTranslatef(*helpers.extend_tuple(self.anchorPoint))
        self.children = [
                c for c in self.children if not c.do_draw(**kwargs)
            ]

    def getDrawContext(self, window=None, **kwargs):
        if window:
            if self.opacity < 0.999 or self.pixelization > 1:
                if self._opacity_data:
                    rendermanager, rendertexture = self._opacity_data
                else:
                    rendermanager = RenderTextureManager(window)
                    rendertexture = rendermanager.Create(
                            width=window.width/self.pixelization,
                            height=window.height/self.pixelization,
                            alpha=True,
                        )
                    self._opacity_data = rendermanager, rendertexture
                @contextmanager
                def cm(*args, **kwargs):
                    glPushMatrix()
                    glPushMatrix()
                    rendertexture.StartRender()
                    glClearColor(0, 0, 0, 0)
                    glClear(GL_COLOR_BUFFER_BIT)
                    glPopMatrix()
                    yield kwargs
                    rendertexture.EndRender()
                    glLoadIdentity()
                    # Enable these for rougher pixelization
                    #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    #glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    rendertexture.SetAsActive(0)
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
                    glDisable(GL_TEXTURE_2D)
                    rendertexture.SetAsInactive(0)
                    glPopMatrix()
                return cm()
            else:
                if self._opacity_data:
                    self._opacity_data = None
        return helpers.nullContextManager(**kwargs)
