'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtCore, QtOpenGL
from OpenGL import GL
import pyopencl as cl #@UnresolvedImport
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport

class MakaCanvasWidget(QtOpenGL.QGLWidget):

    def __init__(self, parent=None, aspect= -1):
        QtOpenGL.QGLWidget.__init__(self, QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)

        self.setWindowTitle("Sample Buffers")

        self.aspect = aspect
        self.plots = []
        self._cl_context = None

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

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        qs = [plot.queue for plot in self.plots]

        for q in qs:
            q.finish()

        for plot in self.plots:
            plot.draw()
