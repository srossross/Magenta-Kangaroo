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
from PySide.QtGui import QWidget, QActionGroup, QApplication, QAction
from maka.util import matrix, gl_enable
import numpy as np
import os
from maka.tools.controllers import NoControl

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
        
        self.bg_color_menu = bg_color_menu = QMenu("Background Color")
        
        self._color_actions = _color_actions = [
            (QAction("white", self), QColor(255, 255, 255)),
            (QAction("black", self), QColor(0, 0, 0)),
            (QAction("grey", self), QColor(128, 128, 128)),
            (QAction("Other ...", self), None)]
        
        self._color_action_group = action_group = QActionGroup(self)
        self._color_action_group.setExclusive(True)
        
        for action, color in _color_actions:
            action.setData(color)
            action_group.addAction(action)
            if action is _color_actions[-1]:
                bg_color_menu.addSeparator()
            bg_color_menu.addAction(action)
            action.setCheckable(True)
            
        action_group.triggered.connect(self.change_bg_color)

        if background_color is not None:
            self.background_color = background_color

    def _init_tools(self, tools):
        self.tools = list(tools)
    
    def _init_controllers(self, controllers, initial_control='no_control'):
        '''
        Initialize interaction controllers and associated actions. 
        '''
        self._current_controller = None
        
        self.controllers = {'no_control': NoControl('no_control', key=None, canvas=self), }
        
        self.controllers.update({controller.objectName():controller for controller in controllers})
        
        self.controller_menu = QMenu("Interaction")
        self.controller_action_group = QActionGroup(self)
        
        self.controller_action_group.setExclusive(True)
        
        self.controller_action_group.triggered.connect(self._action_changed)
#        controller.select_action.toggled_data.connect(self.set_controller)
        
        for controller in self.controllers.values():
#            controller.select_action.toggled_data.connect(self.set_controller)
            self.controller_menu.addAction(controller.select_action)
            self.controller_action_group.addAction(controller.select_action)
            if controller.objectName() == initial_control:
                controller.select_action.setChecked(True)

#        self.current_controller = initial_control
        
    @QtCore.Slot(QtCore.QObject)
    def _action_changed(self, action):
        pass
    def copy(self):
        pass
        
    def __init__(self, parent, name, background_color):

        QWidget.__init__(self, parent)
        
        self._visible = False
        self._focus = False
        
        self.setObjectName(name)

        self._save = False
        self.render_target = None
        
        self._init_background_color(background_color)
        
    def isVisible(self):
        return self._visible
    
    def setVisible(self, value):
        self._visible = bool(value)
    
    visible = QtCore.Property(bool, isVisible, setVisible)

    def hasFocus(self):
        return self._focus
    
    def setFocus(self, value):
        self._focus = bool(value)
    
    focus = QtCore.Property(bool, hasFocus, setFocus)
    
    def projection(self, screen_aspect, near= -1, far=1):
        GL.glOrtho(-1, 1, -1, 1, near, far)
            
    MY_EVENTS = [QEvent.MouseMove, QEvent.KeyPress, QEvent.KeyRelease, QEvent.MouseButtonDblClick, QEvent.MouseButtonPress,
                 QEvent.MouseButtonRelease, QEvent.ContextMenu, QEvent.Enter, QEvent.Leave
                 ]
    
#    def eventFilter(self, obj, event):
#        print 'eventFilter:', event.type(), type(self), repr(self.objectName()), type(obj), repr(obj.objectName())
#        if event.type() in self.MY_EVENTS and self.isVisible() and self.hasFocus():
##            print 'sendEvent:', event.type(), type(self), repr(self.objectName())
##            import pdb;pdb.set_trace()
##            for controll in self.controllers.values():
#            return QtGui.QApplication.sendEvent(self, event)
##            QWidget.eventFilter( )
#        else:
#            return False
        
    def event(self, event):
        '''
        Overload the event method to add a toolTipEvent for the canvas.
        '''
        
        if event.type() in self.MY_EVENTS:
            for tool in self.tools:
                tool.event(event)
            
            if self.controller.event(event):
                return True
            
        if event.type() == QtCore.QEvent.ToolTip:
            return self.toolTipEvent(event)
        else:
            super(CanvasBase, self).event(event)
            return event.isAccepted()

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

        for action in self._color_action_group.actions():
            if action.data() == color:
                action.setChecked(True)
                break
        else:
            self._color_actions[-1][0].setChecked(True)
        
    @QtCore.Slot(QtCore.QObject)
    def change_bg_color(self, action):
        '''
        Cange the background color prompting with a color dialog if param `color` is None. 
        '''
        color = action.data()
        if color is None:
            color = QColorDialog.getColor(self.background_color)
            
        if not color.isValid():
            return
         
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
        return self.controller.objectName()
#    
    def _set_current_controller(self, value):
        self.controllers[value].select_action.setChecked(True)
#
    current_controller = QtCore.Property(str, _get_current_controller, _set_current_controller)

    @property
    def controller(self):
        return self.controller_action_group.checkedAction().parent()
        
#        return self.controllers[self.current_controller]

    controller_changed = QtCore.Signal(bool, str)
    
#    @QtCore.Slot(bool, object)
#    def set_controller(self, enabled, name):
#        '''
#        Set the current controller 
#        '''
#        raise
#        self._current_controller = name
#        
#        for controller in self.controllers.values():
#            controller.select_action.blockSignals(True) # Otherwise stackoverflow
#            enabled = controller.objectName() == name
#            controller.select_action.setChecked(enabled)
#            if enabled: 
#                controller.enable(self.parent())
#            else:
#                controller.disable(self.parent())
#            
#            controller.select_action.blockSignals(False)
        
    @QtCore.Slot(QtCore.QObject)
    def reqest_redraw(self, plot=None):
        '''
        
        '''
        self.require_redraw.emit()

#    def enable(self):
#        self.controllers[self.current_controller].enable(self.parent())

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
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def render_to_texture(self, painter):
        '''
        Render the current state to a texture.
        '''
        with matrix(GL.GL_PROJECTION), matrix(GL.GL_MODELVIEW):
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            screen_aspect = self.render_target_size[0] / self.render_target_size[1]
            self.projection(screen_aspect)
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            self.paintGL(painter)
        
        GL.glFlush()
        
        w, h = self.render_target_size
        with gl_enable(GL.GL_TEXTURE_2D):
        
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 0, 0, w, h, 0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            
        return self.render_target

    @QtCore.Slot(object)
    def move_to_canvas(self, canvas):
        pass

    require_redraw = QtCore.Signal() 
    
    def initializeGL(self):
        pass
