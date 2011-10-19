'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtCore
from PySide.QtGui import QAction, QMenu, QColor, QColorDialog
from OpenGL import GL
from OpenGL.raw.GL.VERSION.GL_1_5 import glBufferData as rawGlBufferData
import pyopencl as cl #@UnresolvedImport
from contextlib import contextmanager
from maka.util import acquire_gl_objects, client_state, SAction


class LinePlot(QtCore.QObject):
    '''
    A basic line plot. 
    '''
    def __init__(self, gl_context, cl_context, size, color=QColor(0, 0, 0), name=None):
        super(LinePlot, self).__init__()
        self._size = size

        if name: self.setObjectName(name)

        self.gl_context = gl_context
        self.cl_context = cl_context

        vbo = GL.glGenBuffers(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        rawGlBufferData(GL.GL_ARRAY_BUFFER, self.size * 2 * 4, None, GL.GL_STATIC_DRAW)

        self.vtx_array = VertexArray(self.cl_context, vbo)

        self.queue = cl.CommandQueue(self.cl_context)

        self._pipe_segments = []
        
        self._state = "normal"
        
        self._actions = {'visible':QAction("Visible", self, checkable=True, checked=True),
                         'edit':QAction("Edit Plot", self),
                        }
        
        color_menu = QMenu("Color")
        
        self._color_actions = [
                               SAction("red", self, QColor(255, 0, 0)),
                               SAction("green", self, QColor(0, 255, 0)),
                               SAction("blue", self, QColor(0, 0, 255)),
                               SAction("Other ...", self, None),
                               ]
        
        self._menus = {'color': color_menu}
        
        for action in self._color_actions[:-1]:
            color_menu.addAction(action)
            action.setCheckable(True)
            action.triggered_data.connect(self.change_color)
        
        color_menu.addSeparator() 
        action = self._color_actions[-1]
        color_menu.addAction(action)
        action.setCheckable(True)
        action.triggered_data.connect(self.change_color)
            
        self.change_color(color=color)
        
        
    @QtCore.Slot(bool, object)
    def change_color(self, checked=False, color=None):
        
        if color is None:
            color = QColorDialog.getColor(QtCore.Qt.green)
            print color
        
        have_color = False
        for action in self._color_actions:
            action.setChecked(False)
            if action.data == color:
                action.setChecked(True)
                have_color = True
                
        if not have_color:
            other = self._color_actions[-1]
            other.setChecked(True)
            
        
        self.color = color
    
    @property
    def visible(self):
        return self._actions['visible'].isChecked()
    
    @visible.setter
    def visible(self, value):
        self._actions['visible'].setChecked(bool(value))
        
    @property
    def state(self):
        return self._state
    
    state_changed = QtCore.Signal(str)
    
    @state.setter
    def state(self, value):
        if self._state != value:
            self.state_changed.emit(value)
        self._state = value
        
    
    def add_pipe_segment(self, segment):
        self._pipe_segments.append(segment)
        segment.changed.connect(self.segment_changed)

    @QtCore.Slot(QtCore.QObject)
    def segment_changed(self, segment):

        self.process()

        self.changed.emit(self)

    changed = QtCore.Signal(QtCore.QObject)

    @property
    def size(self):
        return self._size

    @contextmanager
    def glctx(self):
        self.gl_context.makeCurrent()
        yield None
        self.gl_context.doneCurrent()

    def process(self):

        clbuffer1 = self.vtx_array.cl_buffer

        with acquire_gl_objects(self.queue, [clbuffer1]):
            for segment in self._pipe_segments:
                segment.compute(self.queue)

        return self.queue

    def draw(self):
        if self.visible:
            with client_state(GL.GL_VERTEX_ARRAY), self.vtx_array:
                
                GL.glEnable(GL.GL_BLEND)
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

                GL.glEnable(GL.GL_LINE_SMOOTH)
                GL.glDisable(GL.GL_DEPTH_TEST)

                GL.glColor(self.color.red(), self.color.green(), self.color.blue(), self.color.alpha())
                
                line_width = 1 if self.state == 'normal' else 3.5
                
                GL.glLineWidth(line_width)
                GL.glDrawArrays(GL.GL_LINE_STRIP, 0, self.size)
            
    def over(self, value):
        if self._state == value:
            return False
        
        self.state = 'hover' if value else 'normal'
        
        return True
        
    @property
    def actions(self):
        return self._actions.values()

    @property
    def menus(self):
        return self._menus.values()
    
        
class VertexArray(object):
    '''
    Wrapper around an openGL VBO. 
    
    :param ctx: openCL context 
    :param vbo: openGL vbo id
     
    use::
        
        vbo = VertexArray(ctx, )
        
        with vbo:
            ...
        
            
    '''
    def __init__(self, ctx, vbo):
        self.vbo = vbo
        self.ctx = ctx
        self._cl_buffer = None

    def __enter__(self):
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, None)

    def __exit__(self, *args):
        pass

    @property
    def cl_buffer(self):

        if self._cl_buffer is None:
            with self:
                self._cl_buffer = cl.GLBuffer(self.ctx, cl.mem_flags.READ_WRITE, int(self.vbo))

        return self._cl_buffer

