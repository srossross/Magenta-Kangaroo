'''
Created on Jul 21, 2011

@author: sean
'''
from __future__ import division

from OpenGL import GL
from PIL.Image import fromarray #@UnresolvedImport
from PySide import QtCore, QtGui
from PySide.QtCore import QEvent
from PySide.QtGui import QMenu, QColor, QColorDialog, QPalette
from PySide.QtGui import QWidget
from maka.util import matrix, gl_enable, SAction
import numpy as np
import os
from maka.controllers import NoControl

SIZE = 100


class CanvasBase(QWidget):
    '''
    Canvas for 2D plotting. add this to a PlotWidget
    
    :param parent:
    :param aspect
    :param name:
    :param background_color:  
    '''
    
    def _init_background_color(self, background_color):
        '''
        Initialize the background color and associated actions.
        
        :param background_color: initial color. note that style overrides this selection.
        '''
        
        if background_color is not None:
            self.background_color = background_color
#            self.palette().setColor(QPalette.Window, background_color)
        
        self.bg_color_menu = bg_color_menu = QMenu("Background Color")
        
        self._color_actions = [
            SAction("white", self, QColor(255, 255, 255)),
            SAction("black", self, QColor(0, 0, 0)),
            SAction("grey", self, QColor(128, 128, 128)),
            SAction("Other ...", self, None)]
        
        for action in self._color_actions:
            if action is self._color_actions[-1]:
                bg_color_menu.addSeparator()
            bg_color_menu.addAction(action)
            action.setCheckable(True)
            action.triggered_data.connect(self.change_bg_color)

    def _init_controllers(self, controllers, initial_control='no_control'):
        '''
        Initialize interaction controllers and associated actions. 
        '''
        self._current_controller = None
        
        self.controllers = {'no_control': NoControl('no_control', key=None, canvas=self), }
        
        self.controllers.update({controller.objectName():controller for controller in controllers})
        
        self.controller_menu = QMenu("Interaction")
        
        for controller in self.controllers.values():
            controller.select_action.toggled_data.connect(self.set_controller)
            self.controller_menu.addAction(controller.select_action)

        self.current_controller = initial_control
        
    def copy(self):
        pass
        
    def __init__(self, parent, name, background_color=None):

        QWidget.__init__(self, parent)
        
        self.setObjectName(name)

        self._save = False
        self.render_target = None
        
        self._init_background_color(background_color)
        
        self._init_controllers()
        
    MY_EVENTS = [QEvent.MouseMove, QEvent.KeyPress, QEvent.KeyRelease, QEvent.MouseButtonDblClick, QEvent.MouseButtonPress,
                 QEvent.MouseButtonRelease, QEvent.ContextMenu,
                 ]
    
    def eventFilter(self, obj, event):
        if event.type() in self.MY_EVENTS:
            self.event(event)
            return event.isAccepted()
        else:
            return QtCore.QObject.eventFilter(self, obj, event)
        
    def event(self, event):
        '''
        Overload the event method to add a toolTipEvent for the canvas.
        '''
        if event.type() == QtCore.QEvent.ToolTip:
            return self.toolTipEvent(event)
        else:
            return super(CanvasBase, self).event(event)

    @property
    def background_color(self):
        '''
        get/set the background_color from the palette
        '''
        return self.palette().color(QPalette.Window)
        
    @background_color.setter
    def background_color(self, color):
        '''
        get/set the background_color from the palette
        '''
        palette = self.palette()
        palette.setColor(QPalette.Window, color)
        self.setPalette(palette)

        
    @QtCore.Slot(bool, object)
    def change_bg_color(self, color=None):
        '''
        Cange the background color prompting with a color dialog if param `color` is None. 
        '''
        if color is None:
            color = QColorDialog.getColor(self.background_color)
            
        if not color.isValid():
            return
         
        have_color = False
        for action in self._color_actions:
            action.setChecked(False)
            if action.data == color:
                action.setChecked(True)
                have_color = True
                
        if not have_color:
            other = self._color_actions[-1]
            other.setChecked(True)
            
        self.background_color = color

    @QtCore.Slot(bool)
    def save_as(self, checked=False):
        '''
        FIXME: save to an image
        '''
        self.makeCurrent()
        
        pixmap = GL.glReadPixels(0, 0, 1000, 1000, GL.GL_BGRA, GL.GL_UNSIGNED_BYTE)
        
        a = np.frombuffer(pixmap, dtype=np.uint8)
        b = a.reshape([1000, 1000, 4])
        
        path = os.path.expanduser('~')
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Image", path, "Image Files (*.png *.jpg *.bmp, *.tiff)")
        
        image = fromarray(b, mode='RGBA')
        
        image.save(open(fileName[0], 'w'),)
        
    def _get_current_controller(self):
        return self._current_controller
    
    def _set_current_controller(self, value):
        self.set_controller(True, value)

    current_controller = QtCore.Property(str, _get_current_controller, _set_current_controller)

    @property
    def controller(self):
        return self.controllers[self.current_controller]
        
    @QtCore.Slot(QtCore.QObject)
    def reqest_redraw(self, plot):
        '''
        
        '''
        self.require_redraw.emit()

    def enable(self):
        self.controllers[self.current_controller].enable(self.parent())

    def update_render_target(self, w, h):
        '''
        Create a texture that maps to the pixels of the screen
        '''
        if self.render_target is not None:
            GL.glDeleteTextures([self.render_target])
            
        self.render_target = GL.glGenTextures(1)
        self.render_target_size = w, h
        
        with gl_enable(GL.GL_TEXTURE_2D):
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, w, h, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP);

    def render_to_texture(self):
        '''
        Render the current state to a texture.
        '''
        with matrix(GL.GL_PROJECTION), matrix(GL.GL_MODELVIEW):
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            self.paintGL()
        
        GL.glFlush()
        
        w, h = self.render_target_size
        with gl_enable(GL.GL_TEXTURE_2D):
        
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 0, 0, w, h, 0)
            
        return self.render_target

    @QtCore.Slot(object)
    def move_to_canvas(self, canvas):
        pass

    require_redraw = QtCore.Signal() 
