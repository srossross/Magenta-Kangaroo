'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtCore
from PySide.QtCore import Property, QObject
from PySide.QtGui import QActionGroup, QAction, QMenu, QColor, QColorDialog
from PySide.QtGui import QWidget, QPalette, QWhatsThis, QCursor
from PySide.QtOpenGL import QGLBuffer
from OpenGL import GL
import opencl as cl
import clyther as cly
from contextlib import contextmanager
from maka.plot.line_types import LineType, LineTypeStore


class LinePlot(QWidget):
    '''
    A basic line plot. 
    '''

    def __init__(self, data, rqueue=None, color='black', name=None,
                 thickness=1, plot_type=None, parent=None, clarray=None):
        QWidget.__init__(self, parent=parent)

        if plot_type is None:
            plot_type = LineType(self)
        self._plot_type = plot_type
        self._plot_types = {type(plot_type):plot_type}

        if name: self.setObjectName(name)

        self.vtx_array = data

        self.queue = cl.Queue(data.context)

        self._rqueue = rqueue
        
        self._state = "normal"
        
        self._actions = {'visible':QAction("Visible", self, checkable=True, checked=True),
                        }
        
        self._menus = {}
        
        self._line_type_menu, self._line_type_group = LineTypeStore.type_menu()
        self._line_type_group.triggered.connect(self.change_plot_type)
        
        for action in self._line_type_group.actions():
            data = action.data()
            if data == self._plot_type.__class__:
                action.setChecked(True)
            
        self._menus['line_type_menu'] = self._line_type_menu
        
        self._line_thickness = thickness
        
        self.color = color
    
    @property
    def gl_context(self):
        return self.parent().parent().context()
    
    @QtCore.Slot(QObject)
    def change_plot_type(self, action):
        ptype = action.data()
        if ptype not in self._plot_types:
            self._plot_types[ptype] = ptype(self)
        self._plot_type = self._plot_types[ptype]
    
    @QtCore.Slot()
    def _show_info(self):
        self.parent().parent().mapFromGlobaQCursor.pos()
        QWhatsThis.showText(QCursor.pos(), "This is a plot!!!\n\nPlease leave me alone", self)
    
    def _get_color(self):
        return self.palette().color(QPalette.WindowText)
        
    def _set_color(self, qcolor):
        
        if qcolor is not None:
            palette = self.palette()
            palette.setColor(QPalette.WindowText, qcolor)
            self.setPalette(palette)


    color = QtCore.Property(QColor, _get_color, _set_color)

    def _get_thickness(self):
        return self._line_thickness
        
    def _set_thickness(self, style):
        self._line_thickness = style
    
    thickness = QtCore.Property(float, _get_thickness, _set_thickness)
    
    @property
    def plot_type(self):
        return self._plot_type

    @plot_type.setter
    def plot_type(self, value):
        self._plot_type = value
        for action in self._line_type_group.actions():
            data = action.data()
            if data == self._plot_type.__class__:
                action.setChecked(True)

    def sample(self):
        return self.plot_type.sample()
    
    def saveState(self, settings):
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue('visible', self.visible)
        settings.setValue('color', self.color)
        settings.setValue('plot_type_name', self.plot_type.type_name())
        
        self.plot_type.saveState(settings)
        
        settings.endGroup()

    
    def restoreState(self, settings):
        
        settings.beginGroup(str(self.objectName()))

        self.visible = settings.value('visible', self.visible)
        self.color = settings.value('color', self.color)
        
        plot_type_name = settings.value('plot_type_name', self.plot_type.type_name())
        
        if plot_type_name in self._plot_types:
            self.plot_type = self._plot_types[plot_type_name]
        else:
            self.plot_type = LineTypeStore.plot_types[plot_type_name](self)
        
        self.plot_type.restoreState(settings)
        
        settings.endGroup()
    
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
        return self.vtx_array.size

    @contextmanager
    def glctx(self):
        self.gl_context.makeCurrent()
        yield None
        self.gl_context.doneCurrent()

    def process(self):

        clbuffer1 = self.vtx_array

        with cl.gl.acquire(self.queue, [clbuffer1]):
            pass
#            for segment in self._pipe_segments:
#                segment.compute(self.queue)

        return self.queue

    def draw(self):
        if self.visible:
            self.plot_type.draw(self.vtx_array)
        
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
        for menu in self._menus.values():
            yield menu
        for menu in self.plot_type._menus.values():
            yield menu
    
    def _get_line_style(self):
        import pdb;pdb.set_trace()
        
    def _set_line_style(self, style):
        import pdb;pdb.set_trace()
        
        self._line_style = style
        
        for action in self._style_action_group.actions():
            if action.data() == style:
                action.setChecked(True)
                break
        else:
            self._style_actions[-1][0].setChecked(True)

    line_style = Property(str, _get_line_style, _set_line_style)

#class VertexArray(object):
#    '''
#    Wrapper around an openGL VBO. 
#    
#    :param ctx: openCL context 
#    :param vbo: openGL vbo id
#     
#    use::
#        
#        vbo = VertexArray(ctx, )
#        
#        with vbo:
#            ...
#        
#            
#    '''
#    def __init__(self, ctx, qvbo):
#        self.qvbo = qvbo
#        self.ctx = ctx
#        self._cl_buffer = None
#
#    def __enter__(self):
#        self.qvbo.bind()
##        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
#        GL.glVertexPointer(2, GL.GL_FLOAT, 0, None)
#
#    def __exit__(self, *args):
#        self.qvbo.release()
#        pass
#
#    @property
#    def size(self):
#        return self.qvbo.size() // (2 * 4)
#    @property
#    def cl_buffer(self):
#
#        if self._cl_buffer is None:
#            with self:
#                self._cl_buffer = cl.GLBuffer(self.ctx, cl.mem_flags.READ_WRITE, int(self.qvbo.bufferId()))
#
#        return self._cl_buffer
