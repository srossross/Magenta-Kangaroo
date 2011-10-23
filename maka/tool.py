'''
Created on Oct 15, 2011

@author: sean
'''

from OpenGL import GL, GLU
from PySide import QtCore
from PySide.QtCore import Qt
from maka.util import gl_begin, matrix, gl_enable, gl_disable, SAction


SIZE = 100

class Tool(QtCore.QObject):
    
    def __init__(self, name, key, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        
        self.key = key
        
        self.setObjectName(name)
        
        self.select_action = SAction(name, parent, name)
        self.select_action.setCheckable(True)
        self.select_action.setChecked(False)
        
        
    def _mousePressEvent(self, canvas, event):
        pass

    def _mouseMoveEvent(self, canvas, event):
        pass

    def _mouseReleaseEvent(self, canvas, event):
        pass
    
    def _paintGL(self, canvas):
        pass
    
class PanTool(Tool):
    
    def _mousePressEvent(self, canvas, event):
        
        if (event.buttons() & Qt.LeftButton):
            self.orig = canvas.mapToGL(event.pos())

    def _mouseMoveEvent(self, canvas, event):
        
        if (event.buttons() & Qt.LeftButton):
            new = canvas.mapToGL(event.pos())
            
            delta_x = new.x() - self.orig.x()
            delta_y = new.y() - self.orig.y()
            
            canvas.bounds.translate(-delta_x, -delta_y) 
            
            canvas.require_redraw.emit()
            

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
            
