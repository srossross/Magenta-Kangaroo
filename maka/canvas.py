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

from contextlib import contextmanager
import time
from maka.util import gl_begin
from PySide.QtGui import QMenu, QAction

SIZE = 100


@contextmanager
def matrix(mat_type):
    GL.glMatrixMode(mat_type)
    GL.glPushMatrix()
    yield
    GL.glMatrixMode(mat_type)
    GL.glPopMatrix()
    
    
class Tool(QtCore.QObject):
    
    def __init__(self, key):
        super(QtCore.QObject, self).__init__()
        self.key = key
        
    def _mousePressEvent(self, qgl_widget, event):
        pass

    def _mouseMoveEvent(self, qgl_widget, event):
        pass

    def _mouseReleaseEvent(self, qgl_widget, event):
        pass
    
    def _paintGL(self, qgl_widget):
        pass
    
class PanTool(Tool):
    
    def _mousePressEvent(self, qgl_widget, event):
        
        if (event.buttons() & Qt.LeftButton):
            self.orig = qgl_widget.mapToGL(event.pos())

    def _mouseMoveEvent(self, qgl_widget, event):
        
        if (event.buttons() & Qt.LeftButton):
            new = qgl_widget.mapToGL(event.pos())
            
            delta_x = new.x() - self.orig.x()
            delta_y = new.y() - self.orig.y()
            
            qgl_widget.bounds.translate(-delta_x, -delta_y) 
            
            qgl_widget.updateGL()
            

class ZoomTool(Tool):
    start_point = QtCore.QPointF(0, 0)
    current_point = QtCore.QPointF(0, 0)
    
    _paint = False
    
    def _mousePressEvent(self, qgl_widget, event):
        if event.modifiers() & Qt.ControlModifier:
            return
        
        self._paint = True
        self.start_point = qgl_widget.mapToGL(event.pos())
    
    def modify(self, qgl_widget, start, curr):
        
        bounds = qgl_widget.bounds
        aspect = abs(bounds.width() / bounds.height())
        
        dx = curr.x() - start.x()
        dy = curr.y() - start.y()
        
        if abs(dx) < abs(dy * aspect):
            sign = -1 if dy < 0 else 1
            curr.setY(start.y() + sign * abs(dx) / aspect)
        else:
            sign = -1 if (dx) < 0 else 1
            curr.setX(start.x() + sign * abs(dy) / aspect)
            
    def _mouseMoveEvent(self, qgl_widget, event):
        
        start = self.start_point
        curr = qgl_widget.mapToGL(event.pos())
        
        if event.modifiers() & Qt.ShiftModifier:
            self.modify(qgl_widget, start, curr)
                
        self.current_point = curr    
        qgl_widget.update()
    
    def _mouseReleaseEvent(self, qgl_widget, event):
        self._paint = False
        
        start = self.start_point
        end = qgl_widget.mapToGL(event.pos())
        
        if event.modifiers() & Qt.ControlModifier:
            x, y = qgl_widget.bounds.x(), qgl_widget.bounds.y()
            width, height = qgl_widget.bounds.width(), qgl_widget.bounds.height()
                                
            rect = QtCore.QRectF(2 * x - end.x(), 2 * y - end.y(), width * 2, height * 2)
        else:
            if event.modifiers() & Qt.ShiftModifier:
                self.modify(qgl_widget, start, end)
    
            x = start.x()
            y = start.y()
            width = end.x() - start.x()
            height = end.y() - start.y()
            
            if (width * qgl_widget.bounds.width()) < 0:
                width *= -1 
                x = end.x()
            if (height * qgl_widget.bounds.height()) < 0:
                height *= -1 
                y = end.y()
            
            if width == 0 or height == 0:
                return
            
            rect = QtCore.QRectF(x, y, width, height)

        self.animation = QtCore.QPropertyAnimation(qgl_widget, "bounds")
        
        self.animation.setDuration(1000);
        self.animation.setStartValue(qgl_widget.bounds)
        self.animation.setEndValue(rect)
        
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        self.animation.start()

        
        qgl_widget.update()

    def _paintGL(self, qgl_widget):
        
        if not self._paint:
            return 
        
        with matrix(GL.GL_PROJECTION):
            rect = qgl_widget.bounds
            GLU.gluOrtho2D(rect.left(), rect.right(), rect.bottom(), rect.top())

            with gl_begin(GL.GL_LINES):
                pass
#
#                    GL.glVertex2f(self.start_point.x(), self.start_point.y());
#                    GL.glVertex2f(self.start_point.x(), self.current_point.y());
#                    GL.glVertex2f(self.current_point.x(), self.current_point.y());
#                    GL.glVertex2f(self.current_point.x(), self.start_point.y());
#                    GL.glVertex2f(self.start_point.x(), self.start_point.y());
#                    
            with gl_begin(GL.GL_QUADS):
#                    GL.glColor(0, 0, 0, 255)
#                    GL.glLineWidth(2)
                GL.glColor4ub(34, 140, 150, 140);
                GL.glVertex2f(self.start_point.x(), self.start_point.y());
                GL.glVertex2f(self.start_point.x(), self.current_point.y());
                GL.glVertex2f(self.current_point.x(), self.current_point.y());
                GL.glVertex2f(self.current_point.x(), self.start_point.y());
                GL.glVertex2f(self.start_point.x(), self.start_point.y());

    

class SelectionTool(Tool):
    def _mouseMoveEvent(self, qgl_widget, event):
        with matrix(GL.GL_MODELVIEW):
            rect = qgl_widget.bounds
            GLU.gluOrtho2D(rect.left(), rect.right(), rect.bottom(), rect.top())
            
            with matrix(GL.GL_PROJECTION):
                viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
                GLU.gluPickMatrix(event.pos().x(), viewport[3] - event.pos().y(), 4, 4, viewport)
            
                GL.glSelectBuffer(SIZE)
                GL.glRenderMode(GL.GL_SELECT)
        
                GL.glInitNames();
                
                name = 0
    
                GL.glPushName(name);
        
                pmap = {}
                
                for plot in qgl_widget.plots:
                    name += 1
                    GL.glPopName()
                    GL.glPushName(name)
                    plot.draw()
                    pmap[name] = plot
                    
                GL.glPopName()
                GL.glFlush()
                
                hits = GL.glRenderMode(GL.GL_RENDER)
                
                require_update = False
                for _, _, names in hits:
                    for name in names:
                        plot = pmap.pop(name)
                        if plot:
                            require_update |= bool(plot.over(True))
                            
                for plot in pmap.values():
                        if plot:
                            require_update |= bool(plot.over(False))
                        
        if require_update:
            qgl_widget.updateGL()
            
            
class MakaCanvasWidget(QtOpenGL.QGLWidget):

    def _get_xoff(self):
        return self._bounds.topLeft()
    
    def _set_xoff(self, value):
        self._bounds.translate(value)
        self.update()
        
    def _get_bounds(self):
        return self._bounds
    
    def _set_bounds(self, value):
        self._bounds = value
        self.update()
    
    offset = QtCore.Property(QtCore.QPointF, _get_xoff, _set_xoff) 
    bounds = QtCore.Property(QtCore.QRectF, _get_bounds, _set_bounds) 
    
    def mapToGL(self, point):
        with matrix(GL.GL_MODELVIEW):
            rect = self.bounds
            GLU.gluOrtho2D(rect.left(), rect.right(), rect.bottom(), rect.top())
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            x, y, _ = GLU.gluUnProject(point.x(), viewport[3] - point.y(), -1)
#            x, y, _ = GLU.gluUnProject(point.x(), point.y(), -1)
        return QtCore.QPointF(x, y)

    def __init__(self, parent=None, aspect= -1):
        
        QtOpenGL.QGLWidget.__init__(self, QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)

        self.setWindowTitle("Sample Buffers")

        self.aspect = aspect
        self.plots = []
        self._cl_context = None
    
        self.setFocusPolicy(Qt.ClickFocus)
        
        self._bounds = QtCore.QRectF(-1, -1, 2, 2)
        self._initial_bounds = QtCore.QRectF(-1, -1, 2, 2)
        
        self.setMouseTracking(True)
        
        self._mouse_down = False
        
        
        self.tools = {'pan':PanTool(key=Qt.Key_P),
                      'selection': SelectionTool(key=Qt.Key_S),
                      'zoom': ZoomTool(key=Qt.Key_Z)}

        self.current_tool = 'pan'
        
        self.save_act = save_act = QAction("Save As...", self)
        
        save_act.triggered.connect(self.save_as)
        self._save = False

    @QtCore.Slot(bool)
    def save_as(self, checked=False):
        
        self.makeCurrent()
        
        print self.size().width(), self.size().height()
        pixmap = GL.glReadPixels(0, 0, self.size().width(), self.size().height(), GL.GL_BGRA, GL.GL_UNSIGNED_BYTE)
        
        import numpy as np
        a = np.frombuffer(pixmap, dtype=np.uint8)
        b = a.reshape([self.size().height(), self.size().width(), 4])
        
        import os
        path = os.path.expanduser('~')
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Image", path, "Image Files (*.png *.jpg *.bmp, *.tiff)")
#        
        from PIL.Image import fromarray
        
        image = fromarray(b, mode='RGBA')
        
        image.save(open(fileName[0], 'w'), )
        
    @property
    def tool(self):
        return self.tools[self.current_tool]
        
                
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
        print "initializeGL"
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        
    def resizeGL(self, w, h):
        print "resizeGL"
        aspect = self.aspect
        if aspect < 0:
            GL.glViewport(0, 0, w, h)
        elif w > h * aspect:
            GL.glViewport((w - h * aspect) / 2, 0, h * aspect, h)
        else:
            GL.glViewport(0, (h - w / aspect) / 2, w, w / aspect)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GL.glClearColor(1.0, 1.0, 1.0, 1.0)
        
    def paintGL(self):
        print "paintGL"
        if self._save == True:
            import pdb;pdb.set_trace()
        qs = [plot.queue for plot in self.plots]

        for q in qs:
            q.finish()
        
        with matrix(GL.GL_PROJECTION):
            rect = self.bounds
            GLU.gluOrtho2D(rect.left(), rect.right(), rect.bottom(), rect.top())
        
            with matrix(GL.GL_MODELVIEW):
                
                GL.glClear(GL.GL_COLOR_BUFFER_BIT)
                
                for plot in self.plots:
                    plot.draw()
                
        self.tool._paintGL(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.animation = QtCore.QPropertyAnimation(self, "bounds")
            
            self.animation.setDuration(500);
            self.animation.setStartValue(self.bounds)
            self.animation.setEndValue(self._initial_bounds)
            
            self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
            self.animation.start()
            
            self.animation.finished.connect(self.waa)
        else:
            for tool_name, tool in self.tools.items():
                if tool.key == event.key():
                    print "setting current tool to", tool_name
                    self.current_tool = tool_name
            return
        
        self.updateGL()
    
    @QtCore.Slot()
    def waa(self):
        print "finished"
    
    def mousePressEvent(self, event):
        self.tool._mousePressEvent(self, event)
            
    def mouseReleaseEvent(self, event):
        self.tool._mouseReleaseEvent(self, event)
        
    def mouseMoveEvent(self, event):
        self.tool._mouseMoveEvent(self, event)
                            
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        menu.addAction(self.save_act)
        for i, plot in enumerate(self.plots):
        
            menu.addSeparator()
            
            title = QMenu(str(plot.objectName()) if plot.objectName() else "Plot %i" % i)
            menu.addMenu(title)
            
            for action in plot.actions:
                title.addAction(action)

        p = self.mapToGlobal(event.pos())
        menu.exec_(p)
        
        event.accept()
        self.update()

