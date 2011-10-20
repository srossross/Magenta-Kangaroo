'''
Created on Oct 18, 2011

@author: sean
'''

from PySide import QtOpenGL
from collections import OrderedDict
from PySide.QtGui import QPixmap
from PySide.QtCore import Qt
from OpenGL import GL, GLU, GLUT
from maka.canvas import Canvas
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport
import numpy as np
import os
import pyopencl as cl #@UnresolvedImport
from maka.util import gl_begin, matrix, gl_enable
from PySide import QtCore
#from OpenGL.GL import *
#from OpenGL.GLU import *
#
#from OpenGL.GL.ARB.framebuffer_object import *
#from OpenGL.GL.EXT.framebuffer_object import *

def drawQuad():

    with gl_begin(GL.GL_QUADS):
        GL.glVertex2f(-0.25, -0.25)
        GL.glVertex2f(0.25, -0.25)
        GL.glVertex2f(0.25, 0.25)
        GL.glVertex2f(-0.25, 0.25)


class PlotWidget(QtOpenGL.QGLWidget):
    
    def __init__(self, parent=None, aspect= -1, name='Magenta Plot'):
        
        QtOpenGL.QGLWidget.__init__(self, parent=parent)
        self.setObjectName(name)
        
        self._canvases = OrderedDict(Default=Canvas(self, name='Default'))
        self._current_canvas = 'Default'
        
        self._view_state_choices = ['carousel', 'single_canvas']
#        self._view_state = 'single_canvas'
        self._view_state = 'carousel'
        
        self.drop_pin = QPixmap("resources/images/drop-pin-large2.png")
        
        self.aspect = aspect
        
        self.setFocusPolicy(Qt.ClickFocus)
        self.setMouseTracking(True)
    
        self.rendertarget = None
    @property
    def in_carousel_state(self):
        return self._view_state == 'carousel'
    
    @property
    def current_canvas(self):
        return self._canvases[self._current_canvas]
    
    def add_canvas(self, canvas):
        self._canvases[canvas.objectName()] = canvas

    def resizeGL(self, w, h):
        aspect = self.aspect
        if aspect < 0:
            GL.glViewport(0, 0, w, h)
        elif w > h * aspect:
            GL.glViewport((w - h * aspect) / 2, 0, h * aspect, h)
        else:
            GL.glViewport(0, (h - w / aspect) / 2, w, w / aspect)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        
        if 0:
            print 'glOrtho', -1.0, 1.0, -1.0, 1.0, -1.0, 20.0
            GL.glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 20.0)
        else:
            print 'GLU.gluPerspective', 45.0, 1.0 * w / h, 1.0, 100.0
            GLU.gluPerspective(45.0, 1.0 * w / h, 1.0, 100.0)
        
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        
#        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        
        if self.rendertarget is not None:
            GL.glDeleteTextures([self.rendertarget])
        self.rendertarget = GL.glGenTextures(1)
        
        with gl_enable(GL.GL_TEXTURE_2D):
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.rendertarget)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, w, h, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP);
#
#        GL.glMatrixMode(GL.GL_PROJECTION)
#        GL.glLoadIdentity()
        

        
#        GLU.gluPerspective(45, w, h, 1, 500)
        
#        GL.glMatrixMode(GL.GL_MODELVIEW)
#        GL.glLoadIdentity()
        
    def initializeGL(self):
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        self.drop_pin_tex = self.bindTexture(self.drop_pin.toImage())
        from PySide.QtCore import QTimer
        self.timer = QTimer()
        self.timer.setInterval(25)
        self.timer.setSingleShot(False)
        self.timer.start()
        
        self.angle_off = 0.0
        self.timer.timeout.connect(self.rotate)
#        self.fbo = glGenFramebuffers(1)
    
    @QtCore.Slot()
    def rotate(self):
        self.angle_off += 1
        self.update()
        
    def paintGL(self):
        
        
        if self.in_carousel_state:
            self.draw_carousel()
        else:
            self.current_canvas.paintGL()

    def draw_carousel(self):
        name = 'Default'
        canvas = self._canvases[name]

        with matrix(GL.GL_PROJECTION), matrix(GL.GL_MODELVIEW):
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            canvas.paintGL()
        
        GL.glFlush()
        
        with gl_enable(GL.GL_TEXTURE_2D):
        
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.rendertarget)
            GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 0, 0, self.size().width(), self.size().height(), 0)
        
        GL.glClearColor(.0, .0, .0, 0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        GL.glDepthMask(True)
        
        with matrix(GL.GL_PROJECTION):
            GL.glLoadIdentity()
            
            if 0:
                GL.glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 20.0)
            else:
                GLU.gluPerspective(45.0, 1.0 , 1.0, 100.0)

            with matrix(GL.GL_MODELVIEW):
                GL.glLoadIdentity()
                
                GLU.gluLookAt(0.0, -.25, 1.8,
                              0.0, 0.25, 0.0,
                              0.0, 1.0, 0.0)

                with gl_enable(GL.GL_TEXTURE_2D):
                    GL.glBindTexture(GL.GL_TEXTURE_2D, self.rendertarget)
                    
                    for angle in [0, 60, 120, 180, 240, 300]:
                        with matrix(GL.GL_MODELVIEW):
                            angle = angle + self.angle_off
                            GL.glRotate(angle, 0, 1, 0)
                            GL.glTranslatef(0.0, 0.0, 0.75)
                            GL.glRotate(-angle, 0, 1, 0)
                            
                            with gl_begin(GL.GL_QUADS):
                                GL.glTexCoord2f(0, 0)
                                GL.glVertex(-0.25, -0.25, 0)
                                
                                GL.glTexCoord2f(1, 0)
                                GL.glVertex(0.25, -0.25, 0)
            
                                GL.glTexCoord2f(1, 1)
                                GL.glVertex(0.25, 0.25, 0)
            
                                GL.glTexCoord2f(0, 1)
                                GL.glVertex(-0.25, 0.25, 0)
                
    #        GLU.gluPerspective
    #        GLUT.glutSolidTeapot(.5)
    #        GLUT.glutWireTeapot(.5)
            
#                GL.glColor4f(1.0, 0.0, 0.0, 1.0)
#                GL.glTranslatef(0.25, 0.0, 0.0)
#                drawQuad()
#            
#                GL.glColor4f(0.0, 1.0, 0.0, 1.0)
#                GL.glTranslatef(-0.25, 0.0, -0.5)
#                drawQuad()
#            
#                GL.glColor4f(0.0, 0.0, 1.0, 1.0)
#                GL.glTranslatef(-0.25, 0.0, -1)
#                drawQuad()
                    
        GL.glFlush()

    
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
