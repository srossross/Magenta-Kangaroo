'''
Created on Nov 25, 2011

@author: sean
'''
import opencl as cl
from PySide.QtCore import Slot, Property, QObject, Qt
from PySide.QtGui import QMenu, QAction, QActionGroup, QPixmap, QPainter, QIcon
from PySide.QtGui import QWidgetAction, QLineEdit, QSlider, QWidget, QVBoxLayout, QIntValidator
from PySide.QtGui import QColor, QColorDialog, QPen

from maka.util import client_state, gl_disable, gl_enable, \
    gl_attributes
from OpenGL import GL
from contextlib import contextmanager

QObjectType = type(QObject)

@contextmanager
def bind_array(memobj):
    vbo = cl.gl.get_gl_name(memobj)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    GL.glVertexPointer(2, GL.GL_FLOAT, 0, None)
    
    yield

    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)


class LineTypeStore(object):

    plot_types = {}
    
    @classmethod
    def register(cls, subclass):
        if subclass.type_name():
            cls.plot_types[subclass.type_name()] = subclass
            return subclass
    
    @classmethod
    def type_menu(cls):
        menu = QMenu("Type")
        group = QActionGroup(menu)
        group.setExclusive(True)
        for name, cls in cls.plot_types.items():
            action = QAction(name, menu)
            action.setData(cls)
            action.setCheckable(True)
            
            menu.addAction(action)
            group.addAction(action)
            
        return menu, group

    
class LinePlotType(QObject):
    
    @staticmethod
    def type_name():
        return None
    
    def sample(self):
        pixmap = QPixmap(32, 32)
        return pixmap
    
    def _init_line_color(self):
        
        color_menu = QMenu("color")
        
        self._color_actions = [(QAction("red", self), QColor(Qt.red)),
                               (QAction("green", self), QColor(Qt.green)),
                               (QAction("blue", self), QColor(Qt.blue)),
                               (QAction("Other ...", self), None)]
        
        self._menus['color'] = color_menu
        
        self._color_action_group = action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        for action, color in self._color_actions:
            
            action.setData(color)
            color_menu.addAction(action)
            action_group.addAction(action)
            action.setCheckable(True)
            
        action_group.triggered.connect(self.change_color)
        
        for action in action_group.actions():
            if action.data() == self.color:
                action.setChecked(True)
                break
        

    @Slot(QObject)
    def change_color(self, action):
        
        color = action.data()
        
        if color is None:
            color = QColorDialog.getColor(self.color)
        
        if not color.isValid():
            return
         
        self.color = color

    def _get_color(self):
        return self.parent().color
        
    def _set_color(self, qcolor):
        
        if qcolor is not None:
            self.parent().color = qcolor
    
        for action in self._color_action_group.actions():
            if action.data() == qcolor:
                action.setChecked(True)
                break
        else:
            self._color_actions[-1][0].setChecked(True)
        
    color = Property(QColor, _get_color, _set_color)


    def saveState(self, settings):
        pass
    
    def restoreState(self, settings):
        pass

@LineTypeStore.register
class LineType(LinePlotType):
    
    def __init__(self, parent, line_style='solid'):
        
        LinePlotType.__init__(self, parent=parent)
        
        self._menus = {}
        self._init_line_style(line_style)
        self._init_line_color()
    
    @staticmethod
    def type_name():
        return 'line'
    
    @property
    def thickness(self):
        return self.parent().thickness
    
    def _init_line_style(self, line_style):
        
        self._line_style = line_style
        
        self._line_styles = {'solid': None,
                             'long dash': 0x00FF,
                             'short dash': 0xAAAA,
                             'dot': 0x1111,
                             }

        style_menu = QMenu("Line Style")
        
        self._style_action_group = action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        self._style_actions = [(QAction("solid", self), 'solid'),
                               (QAction("long dash", self), 'long dash'),
                               (QAction("short dash", self), 'short dash'),
                               (QAction("dot", self), 'dot'),
                               (QAction("Other ...", self), None)]
        
        self._menus['style'] = style_menu
        
        for action, style in self._style_actions:
            
            action_group.addAction(action)
            style_menu.addAction(action)
            action.setCheckable(True)
            action.setData(style)
            
        action_group.triggered.connect(self.change_line_style)
        
        self.line_style = line_style
        
    def _get_line_style(self):
        return self._line_style
        
    def _set_line_style(self, style):
        self._line_style = style
        
        for action in self._style_action_group.actions():
            if action.data() == style:
                action.setChecked(True)
                break
        else:
            self._style_actions[-1][0].setChecked(True)

    line_style = Property(str, _get_line_style, _set_line_style)

    @Slot(QObject)
    def change_line_style(self, action):
        
        style = action.data()
        
        if style is None:
            print "Not implemented yet"
            pass

        self.line_style = style
    
    @property
    def stipple_pattern(self):
        return self._line_styles[self._line_style]

    @property
    def state(self):
        return self.parent().state
    
    @property
    def size(self):
        return self.parent().size
    
    def sample(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        pen = QPen(self.color)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawLine(0, 16, 32, 16)
        painter.end()
        return pixmap

    def draw(self, vtx_array):
        with client_state(GL.GL_VERTEX_ARRAY), bind_array(vtx_array):
            
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


class ScatterSprite(object):
    
    symbols_dict = {}
    
    def __init__(self):
        pass
    
    @property
    def symbols(self):
        return self.symbols_dict.keys()
    
    def draw_x(self, painter, color, symbol):
        size = painter.viewport().size().width()
        
        painter.drawLine(0, 0, size, size)
        painter.drawLine(0, size, size, 0)
        
    symbols_dict['x'] = draw_x

    def draw_plus(self, painter, color, symbol):
        size = painter.viewport().size().width()
        
        painter.drawLine(0, size // 2, size, size // 2)
        painter.drawLine(size // 2, 0, size // 2, size)
        
    symbols_dict['+'] = draw_plus

    def draw_left(self, painter, color, symbol):
        size = painter.viewport().size().width()
        
        tq = size - size // 4
        painter.drawLine(tq, 0, 0, size // 2)
        painter.drawLine(0, size // 2, tq, size)
        
    symbols_dict['<'] = draw_left

    def draw_right(self, painter, color, symbol):
        size = painter.viewport().size().width()
        
        tq = size // 4
        painter.drawLine(tq, 0,
                         size, size // 2)
        painter.drawLine(size, size // 2,
                         tq, size)
        
    symbols_dict['>'] = draw_right

    def draw_o(self, painter, color, symbol):
        size = painter.viewport().size().width()
        painter.drawEllipse(0, 0, size, size)
        
    symbols_dict['o'] = draw_o
    
    def draw(self, painter, color, symbol):
        self.symbols_dict[symbol](self, painter, color, symbol)
    
    def create(self, point_size, color, symbol):
        
        size = point_size
        
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        
        try:
            
            painter.setRenderHint(painter.Antialiasing, True)
            painter.setRenderHint(painter.TextAntialiasing, True)
            
            painter.setBrush(Qt.NoBrush)
            painter.setPen(color)
            
            self.draw(painter, color, symbol)
        except:
            painter.end()
            raise
        
        painter.end()
    
        return pixmap
    
#    pixmap.save('PX.png', 'PNG')
    

@LineTypeStore.register
class ScatterType(LinePlotType):
    
    def __init__(self, parent, color=Qt.black, point_size=12, symbol='x'):
        
        LinePlotType.__init__(self, parent=parent)
        
        self.scatter_sprite = ScatterSprite()
        
        self._symbol = symbol
        self._point_size = point_size
        self._texture_id = None
        
        self._menus = {}
        
        self._init_size_menu()
        self._init_symbol_menu()
        self._init_line_color()
        
        self._color_action_group.triggered.connect(self.invalidate)
    
    def _init_symbol_menu(self):
        self._menus['symbol'] = menu = QMenu('symbol')
        
        self._symbol_act_group = group = QActionGroup(self)
        group.setExclusive(True)
        
        for symbol in self.scatter_sprite.symbols:
            action = QAction(self)
            action.setCheckable(True)
            action.setData(symbol)
            pixmap = self.scatter_sprite.create(32, Qt.black, symbol)
            action.setIcon(QIcon(pixmap))
            menu.addAction(action)
            group.addAction(action)
            
        self._symbol_act_group.triggered.connect(self.change_symbol)
    
    
    def _init_size_menu(self):
        
        self._menus['size'] = size_menu = QMenu("size")
        
        self.widget = widget = QWidget()
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)
        self.line_edit = le = QLineEdit(widget)
        le.setValidator(QIntValidator(2, 32, le))
        layout.addWidget(le)
        self.slider = sl = QSlider(Qt.Horizontal, widget)
        sl.setMaximum(32)
        sl.setMinimum(2)
        
        le.setText(str(self.point_size))
        sl.setValue(self.point_size)
        
        le.textEdited.connect(self.setPointSize)
        sl.valueChanged.connect(self.setPointSize)
        
        layout.addWidget(sl)
        
        wa = QWidgetAction(size_menu)
        wa.setDefaultWidget(widget)
        
        size_menu.addAction(wa)
    
    @Slot(QObject)
    def invalidate(self, action=None):
        self._texture_id = None
        self.parent().changed.emit(self.parent())
    
    def getSymbol(self):
        return self._symbol
    
    def setSymbol(self, value):
        
        self._symbol = value
        
        for action in self._symbol_act_group.actions():
            if action.data() == value:
                action.setChecked(True)
                break
            
        self.invalidate()
    
    symbol = Property(str, getSymbol, setSymbol)
    
    @Slot(QObject)
    def change_symbol(self, action):
        print "change_symbol", action.data()
        self.symbol = action.data()
        
    def getPointSize(self):
        return self._point_size
    
    @Slot(object)
    def setPointSize(self, size):
        self._point_size = int(size)
        
        self.slider.setValue(int(size))
        self.line_edit.setText(str(size))
        
        self.invalidate()
    
    point_size = Property(int, getPointSize, setPointSize)
    
    def sample(self):
        return self.scatter_sprite.create(32, self.color, self.symbol)

    def bind_texture(self):
        if self._texture_id is None:
            pixmap = self.scatter_sprite.create(self.point_size, self.color, self.symbol)
            self._texture_id = self.parent().gl_context.bindTexture(pixmap)
        else:
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture_id)
            
    @staticmethod
    def type_name():
        return 'scatter'

    def draw(self, vtx_array):
        
        with gl_attributes():
    
            GL.glEnable(GL.GL_TEXTURE_2D)
            
            with gl_disable(GL.GL_DEPTH_TEST), gl_disable(GL.GL_LIGHTING), \
                 gl_enable(GL.GL_TEXTURE_2D), gl_enable(GL.GL_POINT_SPRITE), \
                 gl_enable(GL.GL_BLEND):
                
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
                
                self.bind_texture()
                
                GL.glTexEnvi(GL.GL_POINT_SPRITE, GL.GL_COORD_REPLACE, GL.GL_TRUE)
                GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)
                GL.glPointParameteri(GL.GL_POINT_SPRITE_COORD_ORIGIN, GL.GL_LOWER_LEFT)
                
                GL.glPointSize(self.point_size)
                
                GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
                
                with bind_array(vtx_array):
                    GL.glDrawArrays(GL.GL_POINTS, 0, vtx_array.size)
                    
                GL.glBindTexture(GL.GL_TEXTURE_2D, 0)


    def saveState(self, settings):
        settings.beginGroup("scatter")
        
        settings.setValue('size', self.point_size)
        settings.setValue('symbol', self.symbol)
        
        settings.endGroup()

    
    def restoreState(self, settings):
        
        settings.beginGroup("scatter")
        
        self.point_size = settings.value('size', self.point_size)
        self.symbol = settings.value('symbol', self.symbol)
        
        settings.endGroup()

