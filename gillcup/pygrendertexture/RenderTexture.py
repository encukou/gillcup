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
# File: Base class for the render texture type
#

from pyglet.gl import *
import logging
import ctypes
import exceptions

# Exception that is thrown when a texture unit is requested, but
#   the hardware doesn't support it.
class RenderTexture_TextureUnitOutOfRange(exceptions.Exception):
    pass

# Exception that is thrown if a function is called on an
#   uninitialized texture
class RenderTexture_TextureUninitalized(exceptions.Exception):
    pass


# the render target base class
class RenderTexture(object):
    # constructor
    #
    # window - Pyglet window class
    # info - one or more of the following:
    #   width - the width of the texture to create
    #   height - the height of the texture to create
    #   bitspercolourcomponent - the number of bits for R,G,B or A
    #   alpha - whether there should be an alpha component
    #   depthbufferbits - the number of bits for the depth buffer
    #   depthtexture - whether it should be a pure depth texture
    #   numtextureunits - the number of available texture units, defaults to 1
    #
    def __init__(self,window,**info):
        # get the logger
        self._log = logging.getLogger()

        # store the window dimensions
        self.windowwidth = window.width
        self.windowheight = window.height

        # get the number of available texture units
        if info.has_key("textureunits"):
            self._numtextureunits = info["textureunits"]
        else:
            self._numtextureunits = 1

        # get the dimensions
        if info.has_key("width"):
            self.width = info["width"]
        else:
            self.width = self.windowwidth
        if info.has_key("height"):
            self.height = info["height"]
        else:
            self.height = self.windowheight

        # start with viewport dimensions set to the full texture
        self._viewportwidth = self.width
        self._viewportheight = self.height
        self.maxtextureu = 1.0
        self.maxtexturev = 1.0

        # is it a power of 2?
        if not (self._IsValuePowerofTwo(self.width)) or not (self._IsValuePowerofTwo(self.height)):
            self.ispoweroftwo = False
            self._CalcPowerofTwo()
        else:
            self.ispoweroftwo = True

        # get the bits per colour
        if info.has_key("bitspercolourcomponent"):
            self._bitspercolour = info["bitspercolourcomponent"]
        else:
            self._bitspercolour = 8

        # get the size of the depth buffer
        if info.has_key("depthbufferbits"):
            self._depthbufferbits = info["depthbufferbits"]
        else:
            self._depthbufferbits = 16

        # do we want alpha?
        if info.has_key("alpha"):
            self.alpha = info["alpha"]
        else:
            self.alpha = False

        # basic attributes
        self._target = GL_TEXTURE_2D
        self._texture = GLuint(0)

        # work out the internal formats
        self._depthtexture = False;
        if info.has_key("depthtexture") and info["depthtexture"]==True:
            self._internalcolourformat = GL_DEPTH_COMPONENT
            self._baseformat = GL_DEPTH_COMPONENT
            self._depthtexture = True
        else:
            # work out the internal format
            self._internalcolourformat = self._GetColourFormat()

            # and the base format
            self._baseformat = GL_RGB
            if self.alpha == True:
              self._baseformat = GL_RGBA

    def __del__(self):
        self.Destroy()

    def _IsValuePowerofTwo(self,value):
        if value & (value - 1 ) == 0:
            return True
        else:
            return False

    def _CalcPowerofTwo(self):
        # get next higher power of two
        def GetNext(present):
            for bit in range(1,15):
                val = 1 << bit
                if present < val:
                    return val
            self.log.warn("RenderTexture::_CalcPowerofTwo::GetNext - Value out of range, returning next highest.")
            return val

        # reset the size of the texture to power of two values
        if not self._IsValuePowerofTwo(self.width):
            self.width = GetNext(self.width)
            self.maxtextureu = float(self._viewportwidth)/float(self.width)
        if not self._IsValuePowerofTwo(self.height):
            self.height = GetNext(self.height)
            self.maxtexturev = float(self._viewportheight)/float(self.height)

    def _GetColourFormat(self):
        if self.alpha == True:
            if self._bitspercolour == 16:
                return GL_RGBA16
            elif self._bitspercolour == 12:
                return GL_RGBA12
            elif self._bitspercolour == 4:
                return GL_RGBA4
            else:
                return GL_RGBA8
        else:
            if self._bitspercolour == 16:
                return GL_RGB16
            elif self._bitspercolour == 12:
                return GL_RGB12
            elif self._bitspercolour == 4:
                return GL_RGB4
            else:
                return GL_RGB8

    def _CheckTextureUnit(self,unit):
        if unit >= self._numtextureunits:
            raise RenderTexture_TextureUnitOutOfRange

    def _IsInitialised(self):
        if self._texture == GLuint(0):
            raise RenderTexture_TextureUninitalized

    # StartRender: Begin rendering to the texture
    def StartRender(self):
        self._IsInitialised()
        glPushAttrib(GL_VIEWPORT_BIT)
        glViewport(0,0,self._viewportwidth,self._viewportheight)

    # EndRender: End rendering to the texture
    def EndRender(self):
        glPopAttrib()

    # SetAsActive: Activate the texture for rendering with
    #
    # unit - the texture unit to use
    #
    def SetAsActive(self,unit=0):
        pass

    # SetAsInactive: Deactivate the texture
    #
    # unit - the texture unit to use
    #
    def SetAsInactive(self,unit=0):
        pass

    # Destroy: Clean up the OpenGL resources associated with the texture
    def Destroy(self):
        pass
