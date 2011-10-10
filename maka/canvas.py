'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtCore, QtOpenGL, QtGui
from OpenGL import GL
from OpenGL import GLU
import pyopencl as cl #@UnresolvedImport
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport
from PySide.QtCore import Qt

class MakaCanvasWidget(QtOpenGL.QGLWidget):

    def __init__(self, parent=None, aspect= -1):
        QtOpenGL.QGLWidget.__init__(self, QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)

        self.setWindowTitle("Sample Buffers")

        self.aspect = aspect
        self.plots = []
        self._cl_context = None
    
        self.setFocusPolicy(Qt.ClickFocus)
        
        self.x_offset = 0
        self.y_offset = 0
        
        self.setMouseTracking(True)
        
        self._mouse_down = False
        
        print "add buttons"
        self._layout = QtGui.QVBoxLayout(self)
        
        self.b1 = QtGui.QPushButton("Button1")
        self._layout.addWidget(self.b1)
        self.b2 = QtGui.QPushButton("Button2")
        self._layout.addWidget(self.b2)
        self.b3 = QtGui.QPushButton("Button3")
        self._layout.addWidget(self.b3)
        
        self.setLayout(self._layout)
        
    def add_plot(self, plot):

        plot.process()
        plot.changed.connect(self.reqest_redraw)
        self.plots.append(plot)

    @QtCore.Slot(QtCore.QObject)
    def reqest_redraw(self, plot):
        self.updateGL()

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

    def initializeGL(self):

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)

    def resizeGL(self, w, h):
        aspect = self.aspect
        if aspect < 0:
            GL.glViewport(0, 0, w, h)
        elif w > h * aspect:
            GL.glViewport((w - h * aspect) / 2, 0, h * aspect, h)
        else:
            GL.glViewport(0, (h - w / aspect) / 2, w, w / aspect)

    def paintGL(self):
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        
        GL.glTranslate(self.x_offset, self.y_offset, 0)
        
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        qs = [plot.queue for plot in self.plots]

        for q in qs:
            q.finish()

        for plot in self.plots:
            plot.draw()
    
    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Left:
            self.x_offset -= .01
        elif event.key() == Qt.Key_Right:
            self.x_offset += .01
        elif event.key() == Qt.Key_Up:
            self.y_offset += .01
        elif event.key() == Qt.Key_Down:
            self.y_offset -= .01
            
        elif event.key() == Qt.Key_F:
            print "F pressed"
            if self.isFullScreen():
                print "showNormal"
                self.showNormal()
            else:
                print "showFullScreen"
                self.showFullScreen()
        else:
            print event.text() , "pressed"
        self.updateGL()
        
    def mousePressEvent(self, event):
        
        self._orig_x, self._orig_y, _ = GLU.gluUnProject(event.pos().x(), event.pos().y(), 0)
        
        self._mouse_down = True
        print "self._orig_y", self._orig_y
        
    def mouseReleaseEvent(self, event):
        self._mouse_down = False
        
    def mouseMoveEvent(self, event):
        
        if not self._mouse_down:
            print "moving", event.pos()
            return
        
        x, y, z = GLU.gluUnProject(event.pos().x(), event.pos().y(), 0)
        
        delta_x = x - self._orig_x
        self.x_offset += delta_x

        delta_y = y - self._orig_y
        self.y_offset += delta_y
        print "y_offset = %10.7f delta_y = %10.7f orig = %10.7f  new = %10.7f" % (self.y_offset, delta_y, self._orig_y, y)
        
        self.updateGL()
        
        
