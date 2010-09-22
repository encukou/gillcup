# Corkscrew Library v1.00
# Title: Render to Texture Library (pygRenderTexture)
# 
# Copyright (C) 2009 Gregory Austwick
#
#  This software is provided 'as-is', without any express or implied
#  warranty.  In no event will the authors be held liable for any damages
#  arising from the use of this software.
#
#  Permission is granted to anyone to use this software for any purpose,
#  including commercial applications, and to alter it and redistribute it
#  freely, subject to the following restrictions:
#
#  1. The origin of this software must not be misrepresented; you must not
#     claim that you wrote the original software. If you use this software
#     in a product, an acknowledgment in the product documentation would be
#     appreciated but is not required.
#  2. Altered source versions must be plainly marked as such, and must not be
#     misrepresented as being the original software.
#  3. This notice may not be removed or altered from any source distribution.
#
# Gregory Austwick (greg@gregs.me.uk)
#
# File: Manager for creation of render targets
#

import GLRenderTexture , FBO
import pyglet.gl.gl_info
from pyglet.gl import *
import ctypes
import exceptions

# Exception that is thrown when a depth texture is requested, but
#   the hardware doesn't support it.
class RenderTexture_DepthTexturesUnavailable(exceptions.Exception):
    pass

# Exception that is thrown if there was a problem creating a render target
class RenderTexture_CreationFailed(exceptions.Exception):
    pass

# The manager class
class RenderTextureManager:
    # Constructor
    #
    # window - Pyglet window class
    #
    def __init__(self,window):
        self._window = window
        self.useFBO = False
        self.depthtexturesavailable = False
        self.numtextureunits = GLint(1)
        self.RescanExtensions()


    # Create: Create a new texture
    #
    # info - one or more of the following:
    #   width - the width of the texture to create
    #   height - the height of the texture to create
    #   bitspercolourcomponent - the number of bits for R,G,B or A
    #   alpha - whether there should be an alpha component
    #   depthbufferbits - the number of bits for the depth buffer
    #   depthtexture - whether it should be a pure depth texture
    #
    # Note: texture dimensions are rounded up to the next power of two
    #
    # Returns the texture object
    #
    def Create(self,**info):
        rendertex = None

        # is it a depth texture?
        if info.has_key("depthtexture") and info["depthtexture"]==True:
            if self.depthtexturesavailable == False:
                raise RenderTexture_DepthTexturesUnavailable

        # add on the number of textures
        info["textureunits"] = self.numtextureunits.value

        # decide what kind of render texture to make
        if self.useFBO==True:
            rendertex = FBO.FBO( self._window , **info )
        else:
            rendertex = GLRenderTexture.GLRenderTexture( self._window , **info )

        # did that work?
        if rendertex._texture == GLuint(0):
            raise RenderTexture_CreationFailed

        return rendertex

    # RescanExtensions: Checks whether certain texture types can be used 
    def RescanExtensions(self):
        if pyglet.gl.gl_info.have_extension('GL_EXT_framebuffer_object'):
            self.useFBO = True
        if pyglet.gl.gl_info.have_extension('GL_ARB_depth_texture'):
            self.depthtexturesavailable = True
        if pyglet.gl.gl_info.have_extension('GL_ARB_multitexture'):
            glGetIntegerv( GL_MAX_TEXTURE_UNITS_ARB , ctypes.byref( self.numtextureunits ) )

    # ForceNOFBO: Do not create FBO textures 
    def ForceNoFBO(self):
        self.useFBO = False
        