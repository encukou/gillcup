"""Offscreen rendering via the OpenGL framebuffer object extension
"""

import ctypes
import contextlib

import pyglet
from pyglet import gl


class _FakeTopFBO(object):
    framebuffer_id = depthbuffer_id = texture_id = ctypes.c_uint(0)


class FBO(object):
    """Stackable helper for using Frame Buffer Objects (FBOs)"""

    _bind_stack = [_FakeTopFBO()]
    data = None

    @staticmethod
    def supported():
        """Check that FBOs are supported"""
        return (
                gl.gl_info.have_extension("GL_EXT_framebuffer_object") and
                gl.gl_info.have_extension("GL_ARB_draw_buffers"))

    def __init__(self, width, height):
        """Creates a FBO"""
        self.initialized = False

        assert self.supported()

        self.width = width
        self.height = height

        self.framebuffer_id = ctypes.c_uint(0)
        self.depthbuffer_id = ctypes.c_uint(0)
        self.texture_id = ctypes.c_uint(0)

        # Frame buffer
        gl.glGenFramebuffersEXT(
                1,  # number of buffers created
                ctypes.byref(self.framebuffer_id),  # dest. id
            )

        self.initialized = True

        with self._bound_context(gl.GL_FRAMEBUFFER_EXT):
            # Depth buffer
            gl.glGenRenderbuffersEXT(
                    1,  # no. of buffers created
                    ctypes.byref(self.depthbuffer_id),  # dest. id
                )
            gl.glBindRenderbufferEXT(
                    gl.GL_RENDERBUFFER_EXT,  # target
                    self.depthbuffer_id,  # id
                )
            gl.glRenderbufferStorageEXT(
                    gl.GL_RENDERBUFFER_EXT,  # target
                    gl.GL_DEPTH_COMPONENT,  # internal format
                    self.width, self.height,  # size
                )
            gl.glFramebufferRenderbufferEXT(
                    gl.GL_FRAMEBUFFER_EXT,  # target
                    gl.GL_DEPTH_ATTACHMENT_EXT,  # attachment point
                    gl.GL_RENDERBUFFER_EXT,  # renderbuffer target
                    self.depthbuffer_id,  # renderbuffer id
                )

            # Target Texture
            gl.glGenTextures(
                    1,  # no. of textures
                    ctypes.byref(self.texture_id),  # dest. id
                )
            gl.glBindTexture(
                    gl.GL_TEXTURE_2D,  # target
                    self.texture_id,  # texture id
                )

            # Black magic (props to pyprocessing!)
            # (nearest works, as well as linear)
            gl.glTexParameteri(
                    gl.GL_TEXTURE_2D,  # target
                    gl.GL_TEXTURE_MAG_FILTER,  # property name
                    gl.GL_LINEAR,  # value
                )
            gl.glTexParameteri(
                    gl.GL_TEXTURE_2D,  # target
                    gl.GL_TEXTURE_MIN_FILTER,  # property name
                    gl.GL_LINEAR,  # value
                )

            # Attach texture to FBO
            gl.glTexImage2D(
                    gl.GL_TEXTURE_2D,  # target
                    0,  # mipmap level (0=default)
                    gl.GL_RGBA8,  # internal format
                    self.width, self.height,  # size
                    0,  # border
                    gl.GL_RGBA,  # format
                    gl.GL_UNSIGNED_BYTE,  # type
                    None,  # data
                )
            gl.glFramebufferTexture2DEXT(
                    gl.GL_FRAMEBUFFER_EXT,  # target
                    gl.GL_COLOR_ATTACHMENT0_EXT,  # attachment point
                    gl.GL_TEXTURE_2D,  # texture target
                    self.texture_id,  # tex id
                    0,  # mipmap level
                )

            # sanity check
            status = gl.glCheckFramebufferStatusEXT(gl.GL_FRAMEBUFFER_EXT)
            assert status == gl.GL_FRAMEBUFFER_COMPLETE_EXT

    @contextlib.contextmanager
    def _bound_context(self, target):
        """Nestable context for glBindFramebufferEXT with given target

        The value is the framebuffer in the outer context
        """
        assert self.initialized
        parent_fb = self._bind_stack[-1]
        gl.glBindFramebufferEXT(target, self.framebuffer_id)
        self._bind_stack.append(self)
        try:
            yield parent_fb
        finally:
            me = self._bind_stack.pop()
            assert me is self
            gl.glBindFramebufferEXT(target, parent_fb.framebuffer_id)

    @contextlib.contextmanager
    def bind_draw(self):
        """Context for drawing into the FBO"""
        with self._bound_context(gl.GL_FRAMEBUFFER_EXT) as parent_fb:
            # Set viewport to the size of the texture
            gl.glPushAttrib(gl.GL_VIEWPORT_BIT)
            try:
                gl.glViewport(0, 0, self.width, self.height)
                yield parent_fb
            finally:
                # Restore old viewport!
                gl.glPopAttrib()

    def get_image_data(self):
        """Return a pyglet image with the contents of the FBO."""
        # props to pyprocessing!
        self.data = (ctypes.c_ubyte * (self.width * self.height * 4))()

        gl.glGetTexImage(
                gl.GL_TEXTURE_2D,  # target
                0,  # mipmap level
                gl.GL_RGBA,  # format
                gl.GL_UNSIGNED_BYTE,  # type,
                self.data,  # image data
            )

        return pyglet.image.ImageData(self.width, self.height,
                'RGBA', self.data)

    def destroy(self):
        """Free memory"""
        if self.initialized:
            byref = ctypes.byref
            if self.framebuffer_id:
                gl.glDeleteFramebuffersEXT(1, byref(self.framebuffer_id))
            if self.depthbuffer_id:
                gl.glDeleteRenderbuffersEXT(1, byref(self.depthbuffer_id))
            if self.texture_id:
                gl.glDeleteTextures(1, byref(self.texture_id))
        self.initialized = False

    def __del__(self):
        self.destroy()
