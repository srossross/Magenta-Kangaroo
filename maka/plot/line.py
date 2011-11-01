'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtCore
from PySide.QtGui import QAction, QMenu, QColor, QColorDialog
from PySide.QtGui import QWidget, QPalette, QWhatsThis, QApplication, QCursor
from OpenGL import GL
from OpenGL.raw.GL.VERSION.GL_1_5 import glBufferData as rawGlBufferData
import pyopencl as cl #@UnresolvedImport
from contextlib import contextmanager
from maka.util import acquire_gl_objects, client_state, SAction, gl_enable, \
    gl_disable


class LinePlot(QWidget):
    '''
    A basic line plot. 
    '''

    def _init_line_color(self, color):
        
        color_menu = QMenu("Line Color")
        
        self._color_actions = [SAction("red", self, QColor(255, 0, 0)),
            SAction("green", self, QColor(0, 255, 0)),
            SAction("blue", self, QColor(0, 0, 255)),
            SAction("Other ...", self, None)]
        
        self._menus['color'] = color_menu
        
        for action in self._color_actions:
            
            if action is self._color_actions[-1]:
                color_menu.addSeparator()
                
            color_menu.addAction(action)
            action.setCheckable(True)
            action.triggered_data.connect(self.change_color)
        
        self.change_color(color=color)

    def __init__(self, gl_context, cl_context, size, color=QColor(0, 0, 0), name=None,
                 line_style='solid', thickness=1,
                 parent=None):
        QWidget.__init__(self, parent=parent)

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
        
#        self.setWhatsThis("This is a plot!!!\n\nPlease leave me alone")
#        
        whats_this_act = QAction("Info ...", self)
        whats_this_act.triggered.connect(self._show_info)

        self._actions = {'visible':QAction("Visible", self, checkable=True, checked=True),
                         'edit':QAction("Edit Plot", self),
                         'what': whats_this_act
                        }
        
        self._menus = {}
        
        
        
        self._init_line_color(color)
        
        self._init_line_style(line_style)
        
        self._line_thickness = thickness
        
    @QtCore.Slot()
    def _show_info(self):
        self.parent().parent().mapFromGlobaQCursor.pos()
        QWhatsThis.showText(QCursor.pos(), "This is a plot!!!\n\nPlease leave me alone", self)
    
    def _get_color(self):
        return self.palette().color(QPalette.WindowText)
        
    def _set_color(self, qcolor):
        print "color.setter", qcolor
        palette = self.palette()
        palette.setColor(QPalette.WindowText, qcolor)
        self.setPalette(palette)
    
    color = QtCore.Property(QColor, _get_color, _set_color)

    def _get_line_style(self):
        return self._line_style
        
    def _set_line_style(self, style):
        self._line_style = style
    
    line_style = QtCore.Property(str, _get_line_style, _set_line_style)

    def _get_thickness(self):
        return self._line_thickness
        
    def _set_thickness(self, style):
        self._line_thickness = style
    
    thickness = QtCore.Property(float, _get_thickness, _set_thickness)
    
    def saveState(self, settings):
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue('visible', self.visible)
        settings.setValue('color', self.color)
        settings.setValue('line_style', self._line_style)
        
        settings.endGroup()

    
    def restoreState(self, settings):
        settings.beginGroup(str(self.objectName()))

        self.visible = settings.value('visible', self.visible)
        self.color = settings.value('color', self.color)
        self._line_style = settings.value('line_style', self._line_style)
        
        settings.endGroup()
    
    def _init_line_style(self, line_style):
        
        self._line_style = line_style
        
        self._line_styles = {'solid': None,
                             'long dash': 0x00FF,
                             'short dash': 0xAAAA,
                             'dot': 0x1111,
                             }
        

        style_menu = QMenu("Line Style")
        
        self._style_actions = [SAction("solid", self, 'solid'),
                               SAction("long dash", self, 'long dash'),
                               SAction("short dash", self, 'short dash'),
                               SAction("dot", self, 'dot'),
                               SAction("Other ...", self, None)]
        
        
        self._menus['style'] = style_menu
        
        for action in self._style_actions:
            
            if action is self._color_actions[-1]:
                style_menu.addSeparator()
                
            style_menu.addAction(action)
            action.setCheckable(True)
            action.triggered_data.connect(self.change_line_style)
        
        self.change_line_style(style=line_style)
        
        
    @QtCore.Slot(object)
    def change_line_style(self, style):
        
        if style is None:
            print "Not implemented yet"
            pass
#            color = QColorDialog.getColor(QtCore.Qt.green)
#            print color
        
        have_color = False
        for action in self._style_actions:
            action.setChecked(False)
            if action.data == style:
                action.setChecked(True)
                have_color = True
                
        if not have_color:
            other = self._style_actions[-1]
            other.setChecked(True)
            
        self._line_style = style
        
        self.changed.emit(self)
    
    @QtCore.Slot(object)
    def change_color(self, color):
        
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
                
                with gl_disable(GL.GL_DEPTH_TEST), gl_enable(GL.GL_BLEND), gl_enable(GL.GL_LINE_SMOOTH):
                    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

                    GL.glColor(self.color.red(), self.color.green(), self.color.blue(), self.color.alpha())
                    
                    line_width = self.thickness if self.state == 'normal' else self.thickness * 3.5
                    GL.glLineWidth(line_width)
                    
                    if self.stipple_pattern is not None:
                        GL.glEnable(GL.GL_LINE_STIPPLE)
                        GL.glLineStipple(1, self.stipple_pattern)
                        
                    GL.glDrawArrays(GL.GL_LINE_STRIP, 0, self.size)
                    
                    if self.stipple_pattern is not None:
                        GL.glDisable(GL.GL_LINE_STIPPLE)
            
    @property
    def stipple_pattern(self):
        return self._line_styles[self._line_style]
        
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

