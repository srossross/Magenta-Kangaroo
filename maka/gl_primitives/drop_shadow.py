'''
Created on Nov 15, 2011

@author: sean
'''

from OpenGL import GL

def draw_quad(left, right, top, bottom):
    
    GL.glBegin(GL.GL_QUADS)
    
    GL.glVertex2f(left, top)
    GL.glVertex2f(left, bottom)
    GL.glVertex2f(right, bottom)
    GL.glVertex2f(right, top)
    
    GL.glEnd()

def drop_shadow(rect):
    viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
    
    GL.glMatrixMode(GL.GL_PROJECTION)
    for i in range(0, 10):
        shift = i
        GL.glViewport(rect.left() + shift, rect.top() - shift, rect.width() + shift, rect.height() - shift)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glColor(0, 0, 0, .02)
        draw_quad(-1, 1, -1, 1)
        GL.glPopMatrix()
        
    GL.glViewport(*viewport)
