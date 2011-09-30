'''
Created on Jul 21, 2011

@author: sean
'''
from contextlib import contextmanager
from OpenGL import GL
import pyopencl as cl #@UnresolvedImport

@contextmanager
def client_state(state):
    GL.glEnableClientState(state)
    yield
    GL.glDisableClientState(state)

@contextmanager
def acquire_gl_objects(queue, objects):
    cl.enqueue_acquire_gl_objects(queue, objects)
    yield None
    cl.enqueue_release_gl_objects(queue, objects)

def gl_context_mgr(ctx):
    ctx.makeCurrent()
    yield None
    ctx.doneCurrent()

@contextmanager
def gl_begin(item):
    GL.glBegin(GL.GL_QUADS)
    yield
    GL.glEnd()

@contextmanager
def gl_matrix():
    GL.glPushMatrix()
    yield
    GL.glPopMatrix()
    
    

def bring_to_front():
    try:
        from appscript import Application
        Application('Python').activate()
    except ImportError:
        from subprocess import Popen
        import sys, os
        if sys.platform == 'darwin' and os.path.exists('/usr/bin/osascript'):
            Popen('/usr/bin/osascript -e \'tell application "Python"\nactivate\nend tell\'', shell=True)
    return
