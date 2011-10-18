'''
Created on Oct 15, 2011

@author: sean
'''

from OpenGL import GL, GLU
from PySide import QtCore
from PySide.QtCore import Qt
from maka.util import gl_begin, matrix, gl_enable, gl_disable


SIZE = 100

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

        if (not (event.buttons() & Qt.LeftButton)) or (event.modifiers() & Qt.ControlModifier):
            self._paint = False
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
        
        if not (event.buttons() & Qt.LeftButton):
            self._paint = False
            return 
        
        if self._paint:
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
            qgl_widget.data_space()
            
#            rect = qgl_widget.bounds
#            GLU.gluOrtho2D(rect.left(), rect.right(), rect.bottom(), rect.top())

#            with gl_begin(GL.GL_LINES):
#                pass
#
#                    GL.glVertex2f(self.start_point.x(), self.start_point.y());
#                    GL.glVertex2f(self.start_point.x(), self.current_point.y());
#                    GL.glVertex2f(self.current_point.x(), self.current_point.y());
#                    GL.glVertex2f(self.current_point.x(), self.start_point.y());
#                    GL.glVertex2f(self.start_point.x(), self.start_point.y());
#                    
            with gl_disable(GL.GL_BLEND), gl_disable(GL.GL_DEPTH_TEST):

                GL.glBlendFunc(GL.GL_ONE, GL.GL_ZERO)
#                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
#                GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
                GL.glDepthMask(0)
    
                with gl_begin(GL.GL_QUADS):
                    GL.glColor4ub(139, 0, 139, 255)
                    GL.glVertex3f(self.start_point.x(), self.start_point.y(), -1)
                    GL.glVertex3f(self.start_point.x(), self.current_point.y(), -1 )
                    GL.glVertex3f(self.current_point.x(), self.current_point.y(), -1)
                    GL.glVertex3f(self.current_point.x(), self.start_point.y(), -1)
                    GL.glVertex3f(self.start_point.x(), self.start_point.y(), -1)

    

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
            
