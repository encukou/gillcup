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
# File: FrameBuffer Object render texture class
#
# Note: for function reference, see RenderTexture.py
#

from pyglet.gl import *
from RenderTexture import RenderTexture
import ctypes

class FBO(RenderTexture):
    def __init__(self,window,**info):
        super( FBO , self ).__init__(window,**info)

        # create an FBO
        self._fbo = GLuint(0)
        glGenFramebuffersEXT( 1 , ctypes.byref(self._fbo) )

        # create a texture
        glGenTextures( 1 , ctypes.byref(self._texture) )
        glBindTexture( self._target , self._texture )

        # setup the texture
        glTexImage2D(self._target , 0 , self._internalcolourformat ,
            self.width , self.height , 0 , self._baseformat , GL_UNSIGNED_BYTE , 0)
        glTexParameteri(self._target,GL_TEXTURE_MAG_FILTER , GL_LINEAR)
        glTexParameteri(self._target,GL_TEXTURE_MIN_FILTER , GL_LINEAR)

        # the depth render buffer
        self._depth = GLuint(0)

        # bind and attach the texture to the FBO
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT , self._fbo)
        if self._depthtexture == True:
            glFramebufferTexture2DEXT( GL_FRAMEBUFFER_EXT , GL_DEPTH_ATTACHMENT_EXT ,
                GL_TEXTURE_2D , self._texture , 0 )

            glDrawBuffer(GL_NONE)
            glReadBuffer(GL_NONE)
        else:
            glFramebufferTexture2DEXT( GL_FRAMEBUFFER_EXT , GL_COLOR_ATTACHMENT0_EXT ,
                GL_TEXTURE_2D , self._texture , 0 )

            # create depth render buffer
            glGenRenderbuffersEXT( 1 , ctypes.byref(self._depth) )
            glBindRenderbufferEXT( GL_RENDERBUFFER_EXT , self._depth )
            glRenderbufferStorageEXT( GL_RENDERBUFFER_EXT , self._GetDepthFormat() ,
                self.width , self.height )

            # and attach it to the FBO
            glFramebufferRenderbufferEXT( GL_FRAMEBUFFER_EXT , GL_DEPTH_ATTACHMENT_EXT ,
                GL_RENDERBUFFER_EXT , self._depth)

    def _GetDepthFormat(self):
        if self._depthbufferbits == 32:
            return GL_DEPTH_COMPONENT32
        elif self._depthbufferbits == 24:
            return GL_DEPTH_COMPONENT24
        else:
            return GL_DEPTH_COMPONENT16

    def StartRender(self):
        # anything to do?
        self._IsInitialised()

        # switch to framebuffer
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT , self._fbo)

        # switch viewport
        super( FBO , self ).StartRender()

    def EndRender(self):
        # anything to do?
        self._IsInitialised()

        # return to normal rendering
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT , 0)

        # and set the viewport back to the dimensions of the screen
        super( FBO , self ).EndRender()

    def SetAsActive(self,unit):
        # sanity checks
        self._IsInitialised()
        self._CheckTextureUnit(unit)

        # simply bind our texture
        if self._numtextureunits > 1:
            glActiveTextureARB(GL_TEXTURE0_ARB + unit)
        glBindTexture( self._target , self._texture )

    def SetAsInactive(self,unit):
        # sanity checks
        self._IsInitialised()
        self._CheckTextureUnit(unit)

        # unbind the texture
        if self._numtextureunits > 1:
            glActiveTextureARB(GL_TEXTURE0_ARB + unit)
        glBindTexture( self._target , 0 )

    def Destroy(self):
        # delete the buffers
        if self._fbo != GLuint(0):
            glDeleteFramebuffersEXT(1,ctypes.byref(self._fbo))
            if self._depth != GLuint(0):
                glDeleteRenderbuffersEXT(1,ctypes.byref(self._depth))
            glDeleteTextures(1 , ctypes.byref(self._texture))
            self._fbo = GLuint(0)
        
    