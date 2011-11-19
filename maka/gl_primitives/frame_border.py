'''
Created on Nov 15, 2011

@author: sean
'''

from OpenGL import GL
from PySide import QtCore

def draw_border_line(start, stop, inc, nlines, grad_start=.3, grad_stop=.1, bevel=QtCore.QPoint(0, 0)):
    
    grad_step = (grad_stop - grad_start) / nlines
    grad = grad_start
    
    r, g, b, a = GL.glGetFloatv(GL.GL_CURRENT_COLOR)
    
    GL.glBegin(GL.GL_LINES)
    
    for _ in range(nlines):
        GL.glColor(r, g, b, a * grad)
        GL.glVertex2f(start.x(), start.y())
        GL.glVertex2f(stop.x(), stop.y())
        
        start += inc + bevel
        stop += inc - bevel
        grad += grad_step 
    
    GL.glColor(r, g, b, a)
    GL.glEnd()
    
def draw_frame_border(w, h):
    
    viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
    GL.glViewport(0, 0, w, h)

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glPushMatrix()
    GL.glLoadIdentity()
    GL.glOrtho(0, w, 0, h, -1, 1)
    
    
    p = QtCore.QPoint
    
    nlines = 1
    grad_start = 1.0
    grad_stop = .0
    
    #Bottom
    draw_border_line(p(0, 0), p(w, 0), p(0, 1), nlines, grad_start, grad_stop, bevel=p(1, 0))
    #Left
    draw_border_line(p(0, 0), p(0, h), p(1, 0), nlines, grad_start, grad_stop, bevel=p(0, 1))
    
    nlines = 2
    grad_start = 1.0
    grad_stop = .0
    #Top
    draw_border_line(p(0, h), p(w, h), p(0, -1), nlines, grad_start, grad_stop, bevel=p(1, 0))
    #Right
    draw_border_line(p(w , 0), p(w, h), p(-1, 0), nlines, grad_start, grad_stop, bevel=p(0, 1))

    GL.glPopMatrix()
    GL.glViewport(*viewport)

