'''
Created on Oct 18, 2011

@author: sean
'''
from __future__ import division
from PySide import QtOpenGL
from collections import OrderedDict
from PySide.QtGui import QPixmap, QColor, QFont, QFontMetrics, QToolBar
from PySide.QtCore import Qt, QPropertyAnimation
from OpenGL import GL, GLU, GLUT
from maka.canvas import Canvas
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport
import numpy as np
import os
import pyopencl as cl #@UnresolvedImport
from maka.util import gl_begin, matrix, gl_enable, gl_disable
from PySide import QtCore
from numpy import clip

def draw_plot():
    
#    GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    
    with gl_begin(GL.GL_QUADS):
        GL.glTexCoord2f(0, 0)
        GL.glVertex(-0.25, -0.25, 0)
        
        GL.glTexCoord2f(1, 0)
        GL.glVertex(0.25, -0.25, 0)

        GL.glTexCoord2f(1, 1)
        GL.glVertex(0.25, 0.25, 0)

        GL.glTexCoord2f(0, 1)
        GL.glVertex(-0.25, 0.25, 0)

def draw_plot_reflection():
    
#    GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    
    with gl_disable(GL.GL_DEPTH_TEST):
        with gl_enable(GL.GL_BLEND):
#            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ZERO)
            
            with gl_begin(GL.GL_QUADS):
                GL.glColor(1, 1, 1, 0)
                GL.glTexCoord2f(0, .5)
                GL.glVertex(-0.25, -0.25 / 2 - .51, 0)
                
#                GL.glColor(1, 1, 1, 0)
                GL.glTexCoord2f(1, .5)
                GL.glVertex(0.25, -0.25 / 2 - .51, 0)
        
                GL.glColor(1, 1, 1, 0.15)
                GL.glTexCoord2f(1, 1)
                GL.glVertex(0.25, 0.25 - .51, 0)
        
#                GL.glColor(1, 1, 1, 0.5)
                GL.glTexCoord2f(0, 1)
                GL.glVertex(-0.25, 0.25 - .51, 0)
                
#            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
            

class PlotWidget(QtOpenGL.QGLWidget):
    
    def __init__(self, parent=None, aspect= -1, name='Magenta Plot'):
        
        QtOpenGL.QGLWidget.__init__(self, parent=parent)
        self.setObjectName(name)
        
        self._canvases = OrderedDict()
        
        self._current_canvas = None
        
        self._view_state_choices = ['carousel', 'single_canvas']
        self._view_state = 'single_canvas'
        
        self.drop_pin = QPixmap("resources/images/drop-pin-large2.png")
        
        self.aspect = aspect
        
        self.setFocusPolicy(Qt.ClickFocus)
        self.setMouseTracking(True)
        self.angle_off = 0.0
        
        self.eye = -0.2 
        self.tgt = 0.05
        
        self._plot_position = 0.0
        self._perspective_transition = 1.0
        
        self._cl_context = None
        
    def _get_pos(self):
        return self._plot_position
    
    def _set_pos(self, value):
        self._plot_position = value
        self.update()

    def _get_per(self):
        return self._perspective_transition
    
    def _set_per(self, value):
        self._perspective_transition = value
        self.update()
     
    plot_position = QtCore.Property(float, _get_pos, _set_pos)
    perspective_transition = QtCore.Property(float, _get_per, _set_per)
    
    @property
    def carousel_state(self):
        return self._view_state == 'carousel'

    def set_carousel_state(self):
        self._view_state = 'carousel'

    @property
    def single_canvas_state(self):
        return self._view_state == 'single_canvas'

    def set_single_canvas_state(self):
        self._view_state = 'single_canvas'
        self.current_canvas.resizeGL(self.size().width(), self.size().height())
    
    @property
    def current_canvas(self):
        return self._canvases[self._current_canvas]
    
    def add_canvas(self, canvas):
        
        self._canvases[canvas.objectName()] = canvas
        canvas.require_redraw.connect(self.update)
        
        if self._current_canvas is None:
            self._current_canvas = canvas.objectName()
    
    def remove_canvas(self, id):
        canvas = self._canvases.pop(id)
        canvas.require_redraw.disconnect(self.update)
        
    def resizeGL(self, w, h):
        '''
        '''
        self.aspect = aspect = w / h
        
        if self.carousel_state:
            GL.glViewport(0, 0, w, h)
            
            for canvas in self._canvases.values():
                canvas.update_render_target(w, h)

            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GLU.gluPerspective(45.0, 1.0 * w / h, 0.5, 10.0)
            
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            GLU.gluLookAt(0.0, self.eye, 1.8,
                          0.0, self.tgt, 0.0,
                          0.0, 1.0, 0.0)
        else:
            self.current_canvas.resizeGL(w, h)
        
    def initializeGL(self):
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        self.drop_pin_tex = self.bindTexture(self.drop_pin.toImage())
        
    @QtCore.Slot()
    def rotate(self):
        self.angle_off += 1
        self.update()
        
    def paintGL(self):
        if self.carousel_state:
            self.draw_carousel()
        else:
            self.current_canvas.paintGL()
    
    def set_fog_params(self):
        GL.glFogfv(GL.GL_FOG_COLOR, (.0, .0, .0))
        GL.glFogi(GL.GL_FOG_MODE, GL.GL_LINEAR)
        GL.glFogf(GL.GL_FOG_START, 1)
        GL.glFogf(GL.GL_FOG_END, 2.5)

    def interpolate_matricies(self):
        per = self.perspective_transition
        projection_1 = np.array(GL.glGetDouble(GL.GL_PROJECTION_MATRIX)) 

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluOrtho2D(-0.25, 0.25, -0.25, 0.25)
        projection_2 = np.array(GL.glGetDouble(GL.GL_PROJECTION_MATRIX)) 
        GL.glLoadIdentity()
        GL.glLoadMatrixd(((1 - per) * projection_1) + (per * projection_2))
        
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        
        GLU.gluLookAt(0.0, (1.0 - per) * self.eye, 1.8 - (0.1 * abs(per)),
                      0.0, (1.0 - per) * self.tgt, 0.0,
                      0.0, 1.0, 0.0)


    def draw_carousel(self):
        
        canvas_textures = OrderedDict((name, canvas.render_to_texture()) for name, canvas in self._canvases.items())
        
        GL.glInitNames()
        

        with matrix(GL.GL_PROJECTION), matrix(GL.GL_MODELVIEW):
            
            per = self.perspective_transition
            if per != 0.0:
                self.interpolate_matricies()
                bg = self.current_canvas.background_color
                GL.glClearColor(per * bg.redF(), per * bg.greenF(), per * bg.blueF(), 0)
            else:
                GL.glClearColor(.0, .0, .0, 0)
                
            GL.glEnable(GL.GL_DEPTH_TEST)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            
            GL.glDepthMask(True)
            
            font = QFont("Helvetica", 24)
    
            font.setBold(True)  
            
            fm = QFontMetrics(font)
            fw = fm.width(self._current_canvas)
            fh = fm.height()
            
            GL.glColor(1, 1, 1, 0)
            self.renderText(self.size().width() / 2 - fw / 2, self.size().height() - fh, self._current_canvas, font)
            
            global_pos = self.plot_position
            
            with gl_enable(GL.GL_FOG):
                self.set_fog_params()
                
#                for draw in [draw_plot_reflection, draw_plot]:
                for i, name in enumerate(self._canvases.keys()):
                    pos = i - global_pos
                    if abs(pos) < 1:
                        current_z = (1 - abs(pos)) * 0.75 
                        current_x = (pos) * 0.50 
                        current_angle = (pos) * -45.0
                    else:
                        current_z = 0.0 
                        direction = (-1 if pos < 0 else 1)
                        current_x = direction * 0.40 + 0.10 * pos 
                        current_angle = -direction * 45
    
                    with matrix(GL.GL_MODELVIEW):
                        GL.glTranslatef(current_x, 0.0, current_z)
                        GL.glRotate(current_angle, 0, 1, 0)
                        
                        with gl_enable(GL.GL_TEXTURE_2D):
                            GL.glBindTexture(GL.GL_TEXTURE_2D, canvas_textures[name])
                            GL.glPushName(i)
                            draw_plot()
#                            draw_plot_reflection()
                            GL.glPopName(i)
        
    @property
    def gl_context(self):
        return self.context()

    @property
    def cl_context(self):
        if self._cl_context is None:
            gl_context = self.context()
            gl_context.makeCurrent()
            self._cl_context = cl.Context(properties=get_gl_sharing_context_properties(), devices=[])
            
        return self._cl_context

    def event(self, event):
        if event.type() == QtCore.QEvent.ToolTip:
            return self.toolTipEvent(event)
        else:
            return QtOpenGL.QGLWidget.event(self, event)
        
    def toolTipEvent(self, event):
        if self.carousel_state:
            return False
        else:
            return self.current_canvas.toolTipEvent(event)

    def mousePressEvent(self, event):
        if self.carousel_state:
            return
        else:
            self.current_canvas.mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        if self.carousel_state:
            return
        else:
            self.current_canvas.mouseReleaseEvent(event)
        
    def mouseMoveEvent(self, event):
        
        if self.carousel_state:
            pass
#            print "mouseMoveEvent"
            # FIXME: doesnt work
#            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
#            GLU.gluPickMatrix(event.pos().x(), viewport[3] - event.pos().y(), 4, 4, viewport)
#        
#            GL.glRenderMode(GL.GL_SELECT)
#            GL.glSelectBuffer(20)
#    
#            GL.glInitNames()
#            
#            GL.glFlush()
#            
#            hits = GL.glRenderMode(GL.GL_RENDER)
            
        else:
            self.current_canvas.mouseMoveEvent(event)

    def contextMenuEvent(self, event):        
        if self.carousel_state:
            return
        else:
            self.current_canvas.contextMenuEvent(event)
    
    QtCore.Slot()
    def fin(self):
        print "=========="
        
    def keyPressEvent(self, event):
        if self.carousel_state:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                print "Enter"
                self.per_animation = QPropertyAnimation(self, 'perspective_transition')
                self.per_animation.setDuration(1000);
                self.per_animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
                self.per_animation.setStartValue(self.perspective_transition)
                self.per_animation.setEndValue(1.0)
                self.per_animation.start()
                self.per_animation.finished.connect(self.set_single_canvas_state)
            else:
                names = self._canvases.keys()
                index = names.index(self._current_canvas)

                if event.key() in [Qt.Key_Left, Qt.Key_Right]:
                    if event.key() == Qt.Key_Left:
                        if index == 0:
                            return
                        pos = -1
                    if event.key() == Qt.Key_Right:
                        if index == len(names) - 1:
                            return 
                        pos = 1
                    
                    self._current_canvas = names[index + pos]
                    self.animation = QPropertyAnimation(self, 'plot_position')
                    self.animation.setDuration(1000);
                    self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
                    self.animation.setStartValue(self.plot_position)
                    self.animation.setEndValue(index + pos)
                    self.animation.start()
                    self.animation.finished.connect(self.fin)
        else:
            if event.key() == Qt.Key_Escape:
                
                self.set_carousel_state()
                self.resizeGL(self.size().width(), self.size().height())
                self.per_animation = QPropertyAnimation(self, 'perspective_transition')
                self.per_animation.setDuration(1000)
                self.per_animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
                self.per_animation.setStartValue(self.perspective_transition)
                self.per_animation.setEndValue(0.0)
                self.per_animation.start()
#                self.animation.finished.connect(self.set_single_canvas_state)
#                self.update()
                
            self.current_canvas.keyPressEvent(event)

