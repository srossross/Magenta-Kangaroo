'''
Created on Jul 21, 2011

@author: sean
'''
from contextlib import contextmanager
from OpenGL import GL
import pyopencl as cl #@UnresolvedImport
import sys

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


old_excepthook = None 

execption_type = None
execption_value = None
execption_traceback = None

execption_application = None

def new_excepthook(type, value, traceback):
    
    global execption_type, execption_value, execption_traceback
    execption_type, execption_value, execption_traceback = type, value, traceback
    
    if execption_application is not None:
        print "Exception Occurred: Exiting application"
        execption_application.exit(1)
    else:
        old_excepthook(type, value, traceback)
    
def execute(app, *args, **kwargs):
    
    epic_fail = kwargs.pop('epic_fail', False)
    
    if epic_fail:
        debug_execute(app, *args, **kwargs)
        return 0
    else:
        return app.exec_(*args, **kwargs)
        
def debug_execute(app, *args, **kwargs):
    
    global old_excepthook, execption_application
    
    execption_application = app
    
    old_excepthook = sys.excepthook
     
    sys.excepthook = new_excepthook
    
    try:
        result = app.exec_(*args, **kwargs)
    except:
        sys.excepthook = old_excepthook
        raise 
    
    sys.excepthook = old_excepthook
    
    print "result", result
    if result:
        raise execption_type, execption_value, execption_traceback


