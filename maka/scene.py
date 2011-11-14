'''
Created on Jul 21, 2011

@author: sean
'''
from __future__ import division
from OpenGL import GL, GLU
from PIL.Image import fromarray #@UnresolvedImport
from PySide import QtCore, QtGui
from PySide.QtCore import Qt, QEvent
from PySide.QtGui import QMenu, QAction, QColor, QColorDialog, QPalette
from PySide.QtGui import QWidget
from maka.util import matrix, gl_begin, gl_disable, gl_enable, SAction
import numpy as np
import os
from maka.controllers import PanControl, SelectionControl, ZoomControl
from maka.marker_animation import MarkerAnimation
from maka.canvas_base import CanvasBase

SIZE = 100


class Scene(CanvasBase):
    '''
    Scene for 3D plotting. Add this to a PlotWidget
    
    :param parent:
    :param aspect
    :param name:
    :param background_color:  
    '''
    
    def mapToGL(self, point):
        '''
        Map a point in local screen space to openGL coordinates. (index space)
        '''
        with matrix(GL.GL_MODELVIEW):
            self.data_space()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            
            x, y, _ = GLU.gluUnProject(point.x() , viewport[3] - (point.y() - 2 * viewport[1]), -1)

        return QtCore.QPointF(x, y)

    def mapToScreen(self, point):
        '''
        Map a point in openGL coordinates (index space) to local screen space.
        '''
        with matrix(GL.GL_MODELVIEW):
            self.data_space()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            x, y, _ = GLU.gluProject(point.x(), point.y(), -1)
            
        screen_point = QtCore.QPoint(x, viewport[3] - (y - 2 * viewport[1]))
        
        return screen_point

    def copy(self):
        return Scene(self.parent(), self.objectName(), background_color=self.background_color)
    
    def __init__(self, parent, name='Magenta Scene', background_color=None):

        CanvasBase.__init__(self, parent, name, background_color)

        self.save_act = save_act = QAction("Save As...", self)
        save_act.triggered.connect(self.save_as)
        
        self.render_target = None
        
        self._init_background_color(background_color)
        
        self._init_controllers([])
        
    def saveState(self, settings):
        '''
        Save this canvases state. 
        
        :param settings: a QSettings object
        '''
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue('background_color', self.background_color)

        settings.endGroup()

    def restoreState(self, settings):
        '''
        Restore this canvases state. 
        
        :param settings: a QSettings object
        '''
        settings.beginGroup(str(self.objectName()))
        
        self.background_color = settings.value('background_color', self.background_color)
        
        settings.endGroup()
    
    controller_changed = QtCore.Signal(bool, str)
    
    def projection(self, screen_aspect, near= -1, far=1):
        GLU.gluPerspective(45.0, screen_aspect, 0.15, 30.0)

    def resizeGL(self, w, h):
        '''
        '''
        GL.glViewport(0, 0, w, h)
            
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        self.projection(w / h)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        self.update_render_target(w, h)
        
    def paintGL(self):
        '''
        Draw the current scene to OpenGL
        '''
        bg = self.background_color
        GL.glClearColor(bg.redF(), bg.greenF(), bg.blueF(), bg.alphaF())
        
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        #TODO: insert code here
                    
        self.controller._paintGL(self)
        
    def keyPressEvent(self, event):
        
        if event.key() == Qt.Key_Escape:
            event.ignore()
            return 
        
    def toolTipEvent(self, event):
        
        glob_point = event.globalPos()
        
        return False
    
    def mousePressEvent(self, event):
        
        self.controller._mousePressEvent(self, event)
            
    def mouseReleaseEvent(self, event):
        
        self.controller._mouseReleaseEvent(self, event)
    
    def mouseMoveEvent(self, event):
        
        self.controller._mouseMoveEvent(self, event)
        
    def _ctx_parent(self, event, menu):
        '''
        Add PlotWidget actions to a context menu
        '''
        if self.parent():
            menu.addSeparator()

            for sub_menu in self.parent().ctx_menu_items['menus']:
                menu.addMenu(sub_menu)
            for action in self.parent().ctx_menu_items['actions']:
                menu.addAction(action)

                
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        menu.addMenu(self.controller_menu)
        
        self._ctx_parent(event, menu)
                    
        p = event.globalPos()
        menu.exec_(p)
        
        event.accept()
        
        self.require_redraw.emit()
    
    require_redraw = QtCore.Signal() 
    
