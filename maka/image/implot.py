'''
Created on Jul 23, 2011

@author: sean
'''
from PySide import QtCore
from PySide.QtGui import QAction, QMenu
from OpenGL import GL
import pyopencl as cl #@UnresolvedImport
import numpy as np
from maka.util import gl_begin, gl_enable, gl_disable

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

        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        if self.have_image_support:
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, self.shape[1], self.shape[0], 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        else:
            queue = cl.CommandQueue(self.cl_ctx)
            cl.enqueue_copy(queue, self._array, self._cl_image)
            queue.finish()
            
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, self.shape[1], self.shape[0], 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, self._array)

    def __exit__(self, *args):
        GL.glDisable(GL.GL_TEXTURE_2D)

from OpenGL.GL import GL_LINEAR as LINEAR, GL_NEAREST as NEAREST

class Interp:
    NEAREST = NEAREST
    LINEAR = LINEAR
    
class ImagePlot(QtCore.QObject):

    changed = QtCore.Signal(QtCore.QObject)

    def __init__(self, gl_context, cl_context, shape, share=True, interp=GL.GL_NEAREST, name='Image Plot'):
        super(ImagePlot, self).__init__()

        self.setObjectName(name)
        self.gl_context = gl_context
        self.cl_context = cl_context

        texture = GL.glGenTextures(1)
        self.texture = Texture2D(cl_context, texture, shape, share=share)
        
        self.interp = interp
        with self.texture:
#        GL.glEnable(GL.GL_TEXTURE_2D);
#        GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_BLEND)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, interp)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, interp)


        self.queue = cl.CommandQueue(self.cl_context)

        self._pipe_segments = []
    
        self._visible_act = visible_act = QAction('Visible', self)
        visible_act.setCheckable(True)
        visible_act.setChecked(True)
        
        self._actions = {'visible': self._visible_act}
        
        
        self._colormap_menu = colormap_menu = QMenu('Color Map')
        self._menus = {'colormap': colormap_menu}
        
        jet_action = QAction('jet', self)
        
        
        colormap_menu.addActions([jet_action])
        
    @property
    def visible(self):
        return self._visible_act.isChecked()
    
    @visible.setter
    def visible(self, value):
        self._visible_act.setChecked(bool(value))
    
    def saveState(self, settings):
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue('visible', self.visible)
        
        settings.endGroup()

    
    def restoreState(self, settings):
        settings.beginGroup(str(self.objectName()))

        self.visible = settings.value('visible', self.visible)
        
        settings.endGroup()

    def process(self):

        for segment in self._pipe_segments:
            segment.compute(self.queue)

        return self.queue

    def draw(self):
        
        if not self.visible:
            return
         
        GL.glColor4ub(255, 0, 0, 0);
        
#        with self.texture:
#            with gl_enable(GL.GL_BLEND):
#                GL.glBlendFunc(GL.GL_ONE, GL.GL_ZERO)

        with gl_disable(GL.GL_DEPTH_TEST), self.texture:
#            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_BLEND)
#            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, self.interp)
#            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, self.interp)
#            GL.glBlendFunc(GL.GL_ONE, GL.GL_ZERO)
            
            with gl_begin(GL.GL_QUADS):
                GL.glTexCoord2f(0, 0); GL.glVertex2f(-1, 1);
                GL.glTexCoord2f(1, 0); GL.glVertex2f(1, 1);
                GL.glTexCoord2f(1, 1); GL.glVertex2f(1, -1);
                GL.glTexCoord2f(0, 1); GL.glVertex2f(-1, -1);
    @property
    def actions(self):
        return self._actions.values()
    
    @property
    def menus(self):
        return self._menus.values()
    
    def over(self, test):
        pass
