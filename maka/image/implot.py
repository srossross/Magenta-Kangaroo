'''
Created on Jul 23, 2011

@author: sean
'''
from PySide import QtCore
from PySide.QtGui import QAction, QActionGroup, QMenu
from OpenGL import GL
import pyopencl as cl #@UnresolvedImport
import numpy as np
from maka.util import gl_begin, gl_enable, gl_disable
from maka.image.color_map import COLORMAPS

class Texture2D(object):
    def __init__(self, cl_ctx, texture, shape, hostbuf=None, share=True):
        self.texture = texture
        self.cl_ctx = cl_ctx
        self.shape = shape

        devices = cl_ctx.get_info(cl.context_info.DEVICES)
        
        device = devices[0]

        self.have_image_support = share and device.get_info(cl.device_info.IMAGE_SUPPORT)

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
            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, interp)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, interp)


        self.queue = cl.CommandQueue(self.cl_context)

        self._pipe_segments = []
    
        self._visible_act = visible_act = QAction('Visible', self)
        visible_act.setCheckable(True)
        visible_act.setChecked(True)
        
        self._actions = {'visible': self._visible_act}
        
        self._init_colormaps()
    
    def sample(self):
        return None
    def _init_colormaps(self):
        
        self._colormap_menu = colormap_menu = QMenu('Color Map')
        self._menus = {'colormap': colormap_menu}
        
        self._colormap_actions = []
        self._colormap_action_group = action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        for name, cdict in COLORMAPS.items():
            caction = QAction(name, self)
            caction.setData(cdict)
            caction.setCheckable(True)
            self._colormap_actions.append(caction)
            action_group.addAction(caction)
            
        action_group.triggered.connect(self.colormap_triggered)
        
        self.cdict = None
        
        colormap_menu.addActions(self._colormap_actions)
        
    @QtCore.Slot(QAction)
    def colormap_triggered(self, action):
        self.cdict = action.data()
        
        
    @property
    def visible(self):
        return self._visible_act.isChecked()
    
    @visible.setter
    def visible(self, value):
        self._visible_act.setChecked(bool(value))
    
    @property
    def color_map_name(self):
        for cname, item in COLORMAPS.items():
            if self.color_map._cdict == item:
                color_map_name = cname
                break
        else:
            color_map_name = None
            
        return color_map_name
        
    def saveState(self, settings):
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue('visible', self.visible)
        settings.setValue('color_map', self.color_map_name)
        
        settings.endGroup()

    
    def restoreState(self, settings):
        settings.beginGroup(str(self.objectName()))

        self.visible = settings.value('visible', self.visible)
        
        color_map_name = settings.value('color_map', None)
        
        cdict = COLORMAPS.get(color_map_name)
        
        if cdict is not None:
            self.cdict = cdict
#            self.colormap_triggered(cdict)
        
        settings.endGroup()
    
    def _get_cdict(self):
        return self._color_map._cdict

    def _set_cdict(self, value):
        if value is not None:
            self.color_map.set_cdict(value)
            self.color_map.compute(self.queue)
            
            for action in self._colormap_action_group.actions():
                if action.data() == value:
                    action.setChecked(True)
                    break
            else:
                pass
                    
    cdict = QtCore.Property(object, _get_cdict, _set_cdict)
    
    @property
    def color_map(self):
        return self._color_map
    
    @color_map.setter
    def color_map(self, value):
        self._color_map = value
    
    def process(self):

        for segment in self._pipe_segments:
            segment.compute(self.queue)
            
        if self.color_map is not None:
            self.color_map.compute(self.queue)

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
            GL.glColor(1, 1, 1, 1)
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
