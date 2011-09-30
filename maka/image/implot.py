'''
Created on Jul 23, 2011

@author: sean
'''
from PySide import QtCore
from OpenGL import GL
import pyopencl as cl #@UnresolvedImport
import numpy as np
from maka.util import gl_begin

class Texture2D(object):
    def __init__(self, cl_ctx, texture, shape, hostbuf=None, share=True):
        self.texture = texture
        self.cl_ctx = cl_ctx
        self.shape = shape

        devices = cl_ctx.get_info(cl.context_info.DEVICES)
        device = devices[0]

        self.have_image_support = share and device.get_info(cl.device_info.IMAGE_SUPPORT)

        print 'self.have_image_support', self.have_image_support
        if self.have_image_support:
            self._cl_image = cl.GLTexture(cl_ctx, cl.mem_flags.READ_WRITE,
                                          GL.GL_TEXTURE_2D, 0, self.texture, 2)
        else:

            self._cl_image = cl.Buffer(cl_ctx, cl.mem_flags.READ_WRITE, int(np.prod(shape) * 4))
            
            if hostbuf is not None:
                queue = cl.CommandQueue(self.cl_ctx)
                cl.enqueue_copy(queue, self._cl_image, hostbuf)
                queue.finish()

            self._array = np.zeros(shape + [4], dtype=np.uint8)

    @property
    def cl_image(self):
        return self._cl_image

    def __enter__(self):

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        if self.have_image_support:
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, self.shape[1],self.shape[0], 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        else:
            queue = cl.CommandQueue(self.cl_ctx)
            cl.enqueue_copy(queue, self._array, self._cl_image)
            queue.finish()
            
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, self.shape[1], self.shape[0], 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, self._array)

    def __exit__(self, *args):
        pass

from OpenGL.GL import GL_LINEAR as LINEAR, GL_NEAREST as NEAREST

class Interp:
    NEAREST = NEAREST
    LINEAR = LINEAR
    
class ImagePlot(QtCore.QObject):

    changed = QtCore.Signal(QtCore.QObject)

    def __init__(self, gl_context, cl_context, shape, share=True, interp=GL.GL_NEAREST):
        super(ImagePlot, self).__init__()

        self.gl_context = gl_context
        self.cl_context = cl_context

        texture = GL.glGenTextures(1)

        GL.glEnable(GL.GL_TEXTURE_2D);
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)

        GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)

        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, interp)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, interp)

        self.texture = Texture2D(cl_context, texture, shape, share=share)

        self.queue = cl.CommandQueue(self.cl_context)

        self._pipe_segments = []

    def process(self):

        for segment in self._pipe_segments:
            segment.compute(self.queue)

        return self.queue

    def draw(self):

        GL.glColor4ub(255, 0, 0, 255);
        
        with self.texture:
            with gl_begin(GL.GL_QUADS):
                GL.glTexCoord2f(0, 0); GL.glVertex2f(-1, 1);
                GL.glTexCoord2f(1, 0); GL.glVertex2f(1, 1);
                GL.glTexCoord2f(1, 1); GL.glVertex2f(1, -1);
                GL.glTexCoord2f(0, 1); GL.glVertex2f(-1, -1);

