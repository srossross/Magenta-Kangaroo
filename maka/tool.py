'''
Created on Oct 15, 2011

@author: sean
'''

from OpenGL import GL, GLU
from PySide import QtCore
from PySide.QtCore import Qt, QPropertyAnimation
from PySide.QtGui import QCursor
from maka.util import gl_begin, matrix, gl_enable, gl_disable, SAction

from time import time
from numpy import mean
SIZE = 100

class Tool(QtCore.QObject):
    '''
    Base tool class.
    '''
    def __init__(self, name, key, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        
        self.key = key
        
        self.setObjectName(name)
        
        self.select_action = SAction(name, parent, name)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(False)
        self._enabled = False
        
    def _mousePressEvent(self, canvas, event):
        pass

    def _mouseMoveEvent(self, canvas, event):
        pass

    def _mouseReleaseEvent(self, canvas, event):
        pass
    
    def _paintGL(self, canvas):
        pass
    
    def enable(self, plot_widget):
        pass

    def disable(self, plot_widget):
        if self._enabled:
            self._enabled = False
            
class PanTool(Tool):
    
    
    def enable(self, plot_widget):
        if not self._enabled:
            self.plot_widget = plot_widget
            plot_widget.setCursor(Qt.OpenHandCursor)
            self._enabled = True

    def _get_delta(self):
        return self._delta
    
    def _set_delta(self, value):
        self._delta = value
        self.canvas.bounds.translate(-self._delta.x(), -self._delta.y())
        self.canvas.require_redraw.emit()
        
    delta = QtCore.Property(QtCore.QPointF, _get_delta, _set_delta)
    
    def __init__(self, name, key, parent=None):
        Tool.__init__(self, name, key, parent)
        
        self._delta = QtCore.QPointF(0, 0)
        self._deltas = [None, None, None, None, None]
        self._time = 0 
        
        self.animation = QPropertyAnimation(self, 'delta')
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
#        self.animation.start()

        
    def _mousePressEvent(self, canvas, event):
        self._delta = QtCore.QPointF(0, 0)
        self._time = 0 
        if (event.buttons() & Qt.LeftButton):
            self.plot_widget.setCursor(Qt.ClosedHandCursor)
            self.animation.stop()
            self.orig = canvas.mapToGL(event.pos())

    def _mouseMoveEvent(self, canvas, event):
        
        if (event.buttons() & Qt.LeftButton):
            self.animation.stop()
            new = canvas.mapToGL(event.pos())
            
            delta_x = new.x() - self.orig.x()
            delta_y = new.y() - self.orig.y()
            
            self._delta = QtCore.QPointF(delta_x, delta_y)
            self._deltas.pop(0)
            self._deltas.append((self._delta, time()))
            
            self._time = time()
            
            canvas.bounds.translate(-delta_x, -delta_y) 
            
            canvas.require_redraw.emit()
        else:
            self._delta = QtCore.QPointF(0, 0)
            self._time = 0
            
            
    def _mouseReleaseEvent(self, canvas, event):
        self.plot_widget.setCursor(Qt.OpenHandCursor)
        
        deltas = [d for d in self._deltas if d is not None]
        
        if len(deltas) < 2:
            return 
        self._deltas = [None] * 5
        
        fps = 60
        dxy = QtCore.QPointF(mean(list(d[0].x() for d in deltas)), mean(list(d[0].y() for d in deltas)))
        
#        print 'dt', (deltas[-1][1] , deltas[0][1]) , (len(deltas) - 1)
        dt = (deltas[-1][1] - deltas[0][1]) / (len(deltas) - 1)
        
        if dt == 0 or (dxy.manhattanLength() == 0):
            self.animation.stop()
            return
        if ((time() - deltas[-1][1]) > .125):
            self.animation.stop()
            return 
        
        x = (dxy.x() / dt) / fps
        y = (dxy.y() / dt) / fps
        
        
        self.canvas = canvas
        self.animation.setStartValue(QtCore.QPointF(x, y))
        self.animation.setEndValue(QtCore.QPointF(0, 0))
        self.animation.start()
        
        
            

class ZoomTool(Tool):
    start_point = QtCore.QPointF(0, 0)
    current_point = QtCore.QPointF(0, 0)
    
    _paint = False
    
    def _mousePressEvent(self, canvas, event):

        if (not (event.buttons() & Qt.LeftButton)) or (event.modifiers() & Qt.ControlModifier):
            self._paint = False
            return
        
        self._paint = True
        
        self.start_point = canvas.mapToGL(event.pos())
        self.current_point = canvas.mapToGL(event.pos())
    
    def modify(self, canvas, start, curr):
        
        bounds = canvas.bounds
        aspect = abs(bounds.width() / bounds.height())
        
        dx = curr.x() - start.x()
        dy = curr.y() - start.y()
        
        if abs(dx) < abs(dy * aspect):
            sign = -1 if dy < 0 else 1
            curr.setY(start.y() + sign * abs(dx) / aspect)
        else:
            sign = -1 if (dx) < 0 else 1
            curr.setX(start.x() + sign * abs(dy) / aspect)
            
    def _mouseMoveEvent(self, canvas, event):
        
        if not (event.buttons() & Qt.LeftButton):
            self._paint = False
            return 
        
        if self._paint:
            start = self.start_point
            curr = canvas.mapToGL(event.pos())
            
            if event.modifiers() & Qt.ShiftModifier:
                self.modify(canvas, start, curr)
                    
            self.current_point = curr    
        canvas.require_redraw.emit()
    
    def _mouseReleaseEvent(self, canvas, event):
        self._paint = False

        start = self.start_point
        end = canvas.mapToGL(event.pos())
        
        self.start_point = QtCore.QPointF(0, 0)
        self.current_point = QtCore.QPointF(0, 0)
        
        if event.modifiers() & Qt.ControlModifier:
            x, y = canvas.bounds.x(), canvas.bounds.y()
            width, height = canvas.bounds.width(), canvas.bounds.height()
                                
            rect = QtCore.QRectF(2 * x - end.x(), 2 * y - end.y(), width * 2, height * 2)
        else:
            if event.modifiers() & Qt.ShiftModifier:
                self.modify(canvas, start, end)
    
            x = start.x()
            y = start.y()
            width = end.x() - start.x()
            height = end.y() - start.y()
            
            if (width * canvas.bounds.width()) < 0:
                width *= -1 
                x = end.x()
            if (height * canvas.bounds.height()) < 0:
                height *= -1 
                y = end.y()
            
            if width == 0 or height == 0:
                return
            
            rect = QtCore.QRectF(x, y, width, height)

        self.animation = QtCore.QPropertyAnimation(canvas, "bounds")
        
        self.animation.setDuration(1000);
        self.animation.setStartValue(canvas.bounds)
        self.animation.setEndValue(rect)
        
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        self.animation.start()

        
        canvas.require_redraw.emit()

    def _paintGL(self, canvas):
        
        if not self._paint:
            return 
        
        with matrix(GL.GL_PROJECTION):
            canvas.data_space()
            
            GL.glColor(.5, 0, .5, .5)
            
            with gl_enable(GL.GL_LINE_STIPPLE):
                GL.glLineWidth(1.5)
                GL.glLineStipple(1, 0x00FF)
                
                with gl_begin(GL.GL_LINES):
                    GL.glVertex3f(self.start_point.x(), self.start_point.y(), -1)
                    GL.glVertex3f(self.start_point.x(), self.current_point.y(), -1)
    
                    GL.glVertex3f(self.start_point.x(), self.current_point.y(), -1)
                    GL.glVertex3f(self.current_point.x(), self.current_point.y(), -1)
    
                    
                    GL.glVertex3f(self.current_point.x(), self.current_point.y(), -1)
                    GL.glVertex3f(self.current_point.x(), self.start_point.y(), -1)
                    
                    GL.glVertex3f(self.current_point.x(), self.start_point.y(), -1)
                    GL.glVertex3f(self.start_point.x(), self.start_point.y(), -1)

            with gl_disable(GL.GL_DEPTH_TEST):
                GL.glDepthMask(0)
                with gl_enable(GL.GL_BLEND):
                    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
                    with gl_begin(GL.GL_QUADS):
                        GL.glVertex3f(self.start_point.x(), self.start_point.y(), -1)
                        GL.glVertex3f(self.start_point.x(), self.current_point.y(), -1)
                        GL.glVertex3f(self.current_point.x(), self.current_point.y(), -1)
                        GL.glVertex3f(self.current_point.x(), self.start_point.y(), -1)
                        GL.glVertex3f(self.start_point.x(), self.start_point.y(), -1)
        return 
    
    def enable(self, plot_widget):
        if not self._enabled:
            plot_widget.setCursor(Qt.CrossCursor)
            self._enabled = True


class SelectionTool(Tool):
    
    def _mouseMoveEvent(self, canvas, event):
        with matrix(GL.GL_MODELVIEW):
            canvas.data_space()
            
            with matrix(GL.GL_PROJECTION):
                viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
                GLU.gluPickMatrix(event.pos().x(), viewport[3] - event.pos().y(), 4, 4, viewport)
            
                GL.glSelectBuffer(SIZE)
                GL.glRenderMode(GL.GL_SELECT)
        
                GL.glInitNames();
                
                name = 0
    
                GL.glPushName(name);
        
                pmap = {}
                
                for plot in canvas.plots:
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
            canvas.require_redraw.emit()
            
    def enable(self, plot_widget):
        if not self._enabled:
            plot_widget.setCursor(Qt.PointingHandCursor)
            self._enabled = True
