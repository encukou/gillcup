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
# File: Basic OpenGL 1.2 render texture class
#
# Note: for function reference, see RenderTexture.py
#

from RenderTexture import RenderTexture
from pyglet.gl import *
import ctypes

class GLRenderTexture(RenderTexture):
    def __init__(self,window,**info):
        super( GLRenderTexture , self ).__init__(window,**info)

        # create and set the texture
        glGenTextures(1,ctypes.byref(self._texture))
        glBindTexture( self._target , self._texture )

        # setup the texture
        glTexImage2D(self._target , 0 , self._internalcolourformat ,
            self.width , self.height , 0 , self._baseformat , GL_UNSIGNED_BYTE , 0)

        glTexParameteri(self._target,GL_TEXTURE_MAG_FILTER , GL_LINEAR)
        glTexParameteri(self._target,GL_TEXTURE_MIN_FILTER , GL_LINEAR)


    def EndRender(self):
        # anything to do?
        self._IsInitialised()

        # finish any rendering
        glFlush()
        
        # copy the texture over
        glBindTexture( self._target , self._texture )
        glCopyTexImage2D( self._target , 0 , self._internalcolourformat , 0 , 0 ,
                    self.width , self.height , 0 )

        # and set the viewport back to the dimensions of the screen
        super( GLRenderTexture , self ).EndRender()

    def SetAsActive(self,unit=0):
        # sanity checks
        self._IsInitialised()
        self._CheckTextureUnit(unit)

        # simply bind our texture
        if self._numtextureunits > 1:
            glActiveTextureARB(GL_TEXTURE0_ARB + unit)
        glBindTexture( self._target , self._texture )

    def SetAsInactive(self,unit=0):
        # sanity checks
        self._IsInitialised()
        self._CheckTextureUnit(unit)

        # unbind the texture
        if self._numtextureunits > 1:
            glActiveTextureARB(GL_TEXTURE0_ARB + unit)
        glBindTexture( self._target , 0 )

    def Destroy(self):
        if self._texture != GLuint(0):
            glDeleteTextures(1 , ctypes.byref(self._texture))
            self._texture = GLuint(0)

