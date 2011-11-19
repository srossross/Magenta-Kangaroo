'''
Created on Nov 15, 2011

@author: sean
'''

from PySide import QtCore
from OpenGL import GL
from math import radians, sin, cos

class RoundedRect(QtCore.QRectF):
    def __init__(self, rect, radius):
        super(RoundedRect, self).__init__(rect)
        self.radius = radius
        
        self._fill_list = None
        self._outline_list = None
        
    
    @property
    def fill_list(self):
        if self._fill_list is None:
            _fill_list = GL.glGenLists(1)
            GL.glNewList(_fill_list, GL.GL_COMPILE_AND_EXECUTE)
            self._fill()
            self._fill_list = _fill_list
            GL.glEndList()
        return self._fill_list

    @property
    def outline_list(self):
        if self._outline_list is None:
            _outline_list = GL.glGenLists(1)
            GL.glNewList(_outline_list, GL.GL_COMPILE_AND_EXECUTE)
            
            self._draw_outline()
        
            self._outline_list = _outline_list
            GL.glEndList()
            
        return self._outline_list
        
    def _fill(self):
        r = self.radius
        
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        GL.glVertex2f(self.right() - r, self.top() + r)
        for deg in range(0, 90 + 10, 10):
            i0 = radians(deg)
            GL.glVertex2f(self.right() - r + r * cos(i0), self.top() + r - r * sin(i0))
            
        GL.glEnd()
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        GL.glVertex2f(self.left() + r, self.top() + r)
        for deg in range(90, 180 + 10, 10):
            i0 = radians(deg)
            GL.glVertex2f(self.left() + r + r * cos(i0), self.top() + r - r * sin(i0))

        GL.glEnd()
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        GL.glVertex2f(self.left() + r, self.bottom() - r)
        for deg in range(180, 270 + 10, 10):
            i0 = radians(deg)
            GL.glVertex2f(self.left() + r + r * cos(i0), self.bottom() - r - r * sin(i0))

        GL.glEnd()
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        GL.glVertex2f(self.right() - r, self.bottom() - r)
        for deg in range(270, 360 + 10, 10):
            i0 = radians(deg)
            GL.glVertex2f(self.right() - r + r * cos(i0), self.bottom() - r - r * sin(i0))
        GL.glEnd()

        GL.glBegin(GL.GL_QUADS)
        
        GL.glVertex2f(self.right() - r, self.top() + r)
        GL.glVertex2f(self.right() - r, self.top())
        GL.glVertex2f(self.left() + r, self.top())
        GL.glVertex2f(self.left() + r, self.top() + r)
        
        GL.glVertex2f(self.right() - r, self.top() + r)
        GL.glVertex2f(self.right(), self.top() + r)
        GL.glVertex2f(self.right(), self.bottom() - r)
        GL.glVertex2f(self.right() - r, self.bottom() - r)
        
        GL.glVertex2f(self.left() + r, self.bottom() - r)
        GL.glVertex2f(self.left(), self.bottom() - r)
        GL.glVertex2f(self.left(), self.top() + r)
        GL.glVertex2f(self.left() + r, self.top() + r)
        
        
        GL.glVertex2f(self.right() - r, self.bottom() - r)
        GL.glVertex2f(self.right() - r, self.bottom())
        GL.glVertex2f(self.left() + r, self.bottom())
        GL.glVertex2f(self.left() + r, self.bottom() - r)

        GL.glVertex2f(self.right() - r, self.bottom() - r)
        GL.glVertex2f(self.right() - r, self.top() + r)
        GL.glVertex2f(self.left() + r, self.top() + r)
        GL.glVertex2f(self.left() + r, self.bottom() - r)

        GL.glEnd()

    def fill(self):
        fill_list = self.fill_list
        GL.glCallList(fill_list)
    
    def _draw_outline(self):
        GL.glBegin(GL.GL_LINES)
        
        r = self.radius

        GL.glVertex2f(self.left() + r, self.top())
        GL.glVertex2f(self.right() - r, self.top())

        GL.glVertex2f(self.left() + r, self.bottom())
        GL.glVertex2f(self.right() - r, self.bottom())

        GL.glVertex2f(self.left(), self.top() + r)
        GL.glVertex2f(self.left(), self.bottom() - r)

        GL.glVertex2f(self.right(), self.top() + r)
        GL.glVertex2f(self.right(), self.bottom() - r)

        for deg in range(0, 90, 10):
            i0 = radians(deg)
            i1 = radians(deg + 10)
            GL.glVertex2f(self.right() - r + r * cos(i0), self.top() + r - r * sin(i0))
            GL.glVertex2f(self.right() - r + r * cos(i1), self.top() + r - r * sin(i1))

        for deg in range(90, 180, 10):
            i0 = radians(deg)
            i1 = radians(deg + 10)
            GL.glVertex2f(self.left() + r + r * cos(i0), self.top() + r - r * sin(i0))
            GL.glVertex2f(self.left() + r + r * cos(i1), self.top() + r - r * sin(i1))

        for deg in range(180, 270, 10):
            i0 = radians(deg)
            i1 = radians(deg + 10)
            GL.glVertex2f(self.left() + r + r * cos(i0), self.bottom() - r - r * sin(i0))
            GL.glVertex2f(self.left() + r + r * cos(i1), self.bottom() - r - r * sin(i1))

        for deg in range(270, 360, 10):
            i0 = radians(deg)
            i1 = radians(deg + 10)
            GL.glVertex2f(self.right() - r + r * cos(i0), self.bottom() - r - r * sin(i0))
            GL.glVertex2f(self.right() - r + r * cos(i1), self.bottom() - r - r * sin(i1))

        
        GL.glEnd()
        
    def draw_outline(self):
        ol_list = self.outline_list
        GL.glCallList(ol_list)

