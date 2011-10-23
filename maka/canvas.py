'''
Created on Jul 21, 2011

@author: sean
'''

from OpenGL import GL, GLU
from PIL.Image import fromarray #@UnresolvedImport
from PySide import QtCore, QtGui
from PySide.QtCore import Qt, QObject
from PySide.QtGui import QMenu, QAction, QColor, QColorDialog, QToolBar
from maka.util import matrix, gl_begin, gl_disable, gl_enable, SAction
import numpy as np
import os
from maka.tool import PanTool, SelectionTool, ZoomTool
from PySide.QtGui import *

SIZE = 100
class Canvas(QObject):

    def _get_xoff(self):
        return self._bounds.topLeft()
    
    def _set_xoff(self, value):
        self._bounds.translate(value)
        self.require_redraw.emit()
        
    def _get_bounds(self):
        return self._bounds
    
    def _set_bounds(self, value):
        self._bounds = value
        self.require_redraw.emit()
    
    offset = QtCore.Property(QtCore.QPointF, _get_xoff, _set_xoff) 
    bounds = QtCore.Property(QtCore.QRectF, _get_bounds, _set_bounds) 
    
    def data_space(self):
        rect = self.bounds
        GLU.gluOrtho2D(rect.left(), rect.right(), rect.top(), rect.bottom())
        
    def mapToGL(self, point):
        with matrix(GL.GL_MODELVIEW):
            self.data_space()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            
            x, y, _ = GLU.gluUnProject(point.x() , viewport[3] - (point.y() - 2 * viewport[1]), -1)

        return QtCore.QPointF(x, y)

    def mapToScreen(self, point):
        with matrix(GL.GL_MODELVIEW):
            self.data_space()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            x, y, _ = GLU.gluProject(point.x(), point.y(), -1)
            
        screen_point = QtCore.QPoint(x, viewport[3] - (y - 2 * viewport[1]))
        
        return screen_point


    def _init_background_color(self, background_color):
        
        self.background_color = background_color
        self.bg_color_menu = bg_color_menu = QMenu("Background Color")
        
        self._color_actions = [
            SAction("white", self, QColor(255, 255, 255)),
            SAction("black", self, QColor(0, 0, 0)),
            SAction("grey", self, QColor(128, 128, 128)),
            SAction("Other ...", self, None)]
        
        for action in self._color_actions:
            if action is self._color_actions[-1]:
                bg_color_menu.addSeparator()
            bg_color_menu.addAction(action)
            action.setCheckable(True)
            action.triggered_data.connect(self.change_bg_color)


    def _init_tools(self):
        
        self._current_tool = None
        
        self.tools = {'pan':PanTool('pan', key=Qt.Key_P, parent=self.parent()),
                      'select':SelectionTool('select', key=Qt.Key_S, parent=self.parent()),
                      'zoom':ZoomTool('zoom', key=Qt.Key_Z, parent=self.parent())}
        
        self.tool_menu = QMenu("Interaction")
        
        for tool in self.tools.values():
            tool.select_action.toggled_data.connect(self.set_tool)
            self.tool_menu.addAction(tool.select_action)

        self.current_tool = 'pan'
        
    def __init__(self, parent, aspect= -1, name='Magenta Canvas', background_color=QtGui.QColor(255, 255, 255, 255)):

        QObject.__init__(self, parent)
        
        self.setObjectName(name)

        self.aspect = aspect
        self.plots = []
        self._cl_context = None
    
        self._bounds = QtCore.QRectF(-1, -1, 2, 2)
        self._initial_bounds = QtCore.QRectF(-1, -1, 2, 2)
        
        
        self.save_act = save_act = QAction("Save As...", self)
        save_act.triggered.connect(self.save_as)
        
        self.drop_marker_act = drop_marker_act = QAction("Drop Marker", self)
        self.show_markers_act = show_markers_act = QAction("Visible", self)
        show_markers_act.setCheckable(True)
        show_markers_act.setChecked(True)
        
        drop_marker_act.triggered.connect(self.drop_marker)
        
        self._save = False

        self.markers = {"Center" : QtCore.QPointF(0, 0)}
        
        self.render_target = None
        
        self._init_background_color(background_color)
        
        self._init_tools()
        
    tool_changed = QtCore.Signal(bool, str)
    
    @QtCore.Slot(bool, object)
    def set_tool(self, enabled, name):

        self._current_tool = name
        
        for tool in self.tools.values():
            tool.select_action.blockSignals(True)
            tool.select_action.setChecked(tool.objectName() == name)
            tool.select_action.blockSignals(False)

    
    def _get_current_tool(self):
        return self._current_tool
    
    def _set_current_tool(self, value):
        self.set_tool(True, value)

    current_tool = QtCore.Property(str, _get_current_tool, _set_current_tool)
            
    @QtCore.Slot(bool, object)
    def change_bg_color(self, color=None):
        
        if color is None:
            color = QColorDialog.getColor(self.background_color)
            
        if not color.isValid():
            return
         
        have_color = False
        for action in self._color_actions:
            action.setChecked(False)
            if action.data == color:
                action.setChecked(True)
                have_color = True
                
        if not have_color:
            other = self._color_actions[-1]
            other.setChecked(True)
            
        self.background_color = color
#        self.req

    @property
    def markers_visible(self):
        return self.show_markers_act.isChecked()
    
    @QtCore.Slot(bool)
    def remove_marker(self, marker):
        self.markers.pop(marker, None)
        self.require_redraw.emit()
        
    @QtCore.Slot(bool)
    def drop_marker(self):
        
        point = self.mapToGL(self.drop_here)
        
        global_pos = self.mapToGlobal(self.drop_here)
        dialog = QtGui.QDialog()
        dialog.setWindowOpacity(.8)
        dialog.move(global_pos)
        layout = QtGui.QVBoxLayout()
        dialog.setLayout(layout)
        text = QtGui.QLineEdit(dialog)
        text.setText("Marker %i" % (len(self.markers),))
        layout.addWidget(text)
        bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addWidget(bbox)
        dialog.setModal(True)
        dialog.setWindowTitle("Drop Marker")
        
        bbox.accepted.connect(dialog.accept)
        bbox.rejected.connect(dialog.reject)
        
        result = dialog.exec_()
        
        if result == QtGui.QDialog.Accepted:
            self.markers[text.text()] = point
            self.require_redraw.emit()
        
    @QtCore.Slot(bool)
    def save_as(self, checked=False):
        
        self.makeCurrent()
        
        orig_size = self.size()
        
        pixmap = GL.glReadPixels(0, 0, 1000, 1000, GL.GL_BGRA, GL.GL_UNSIGNED_BYTE)
        
        a = np.frombuffer(pixmap, dtype=np.uint8)
        b = a.reshape([1000, 1000, 4])
        
        path = os.path.expanduser('~')
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Save Image", path, "Image Files (*.png *.jpg *.bmp, *.tiff)")
        
        image = fromarray(b, mode='RGBA')
        
        image.save(open(fileName[0], 'w'),)
        
    @property
    def tool(self):
        return self.tools[self.current_tool]
        
    def add_plot(self, plot):
        plot.process()
        plot.changed.connect(self.reqest_redraw)
        self.plots.append(plot)

    @QtCore.Slot(QtCore.QObject)
    def reqest_redraw(self, plot):
        self.updateGL()

    def resizeGL(self, w, h):
        
        aspect = self.aspect
        
        if aspect < 0:
            GL.glViewport(0, 0, w, h)
        elif w > h * aspect:
            GL.glViewport((w - h * aspect) / 2, 0, h * aspect, h)
        else:
            GL.glViewport(0, (h - w / aspect) / 2, w, w / aspect)
            
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        self.update_render_target(w, h)
            
    def update_render_target(self, w, h):
        if self.render_target is not None:
            GL.glDeleteTextures([self.render_target])
            
        self.render_target = GL.glGenTextures(1)
        self.render_target_size = w, h
        
        with gl_enable(GL.GL_TEXTURE_2D):
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, w, h, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, None)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP);
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP);

    def render_to_texture(self):
        
        with matrix(GL.GL_PROJECTION), matrix(GL.GL_MODELVIEW):
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            self.paintGL()
        
        GL.glFlush()
        
        w, h = self.render_target_size
        with gl_enable(GL.GL_TEXTURE_2D):
        
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 0, 0, w, h, 0)
            
        return self.render_target

    def paintGL(self):
        bg = self.background_color
        GL.glClearColor(bg.redF(), bg.greenF(), bg.blueF(), bg.alphaF())
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        qs = [plot.queue for plot in self.plots]

        for q in qs:
            q.finish()
        
        with matrix(GL.GL_PROJECTION):
            self.data_space()
        
            with matrix(GL.GL_MODELVIEW):
                
                for plot in self.plots:
                    plot.draw()
                
            self.draw_markers()
            
        self.tool._paintGL(self)
        
    def draw_markers(self):
        if not self.markers_visible:
            return 
        
        _maxSize = GL.glGetFloatv(GL.GL_POINT_SIZE_MAX_ARB)
        _minSize = GL.glGetFloatv(GL.GL_POINT_SIZE_MIN_ARB)
        
        plot_widget = self.parent()
        
        with gl_disable(GL.GL_DEPTH_TEST), gl_disable(GL.GL_LIGHTING), \
             gl_enable(GL.GL_TEXTURE_2D), gl_enable(GL.GL_POINT_SPRITE), \
             gl_enable(GL.GL_BLEND):

            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

            GL.glDepthMask(0)
            
            GL.glBindTexture(GL.GL_TEXTURE_2D, plot_widget.drop_pin_tex)
    
            GL.glTexEnvi(GL.GL_POINT_SPRITE, GL.GL_COORD_REPLACE, GL.GL_TRUE)
            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_REPLACE)
            GL.glPointParameteri(GL.GL_POINT_SPRITE_COORD_ORIGIN, GL.GL_LOWER_LEFT)
            
            GL.glPointSize(_maxSize)
            
            GL.glColor4f(1.0, 1.0, 1.0, 1.0)
            
            with gl_begin(GL.GL_POINTS):
                for marker in self.markers.values():
                    GL.glVertex3f(marker.x(), marker.y(), -1)
    
    def setBounds(self, rect, animate=False):
        
        if animate:
            self.animation = QtCore.QPropertyAnimation(self, "bounds")
            
            self.animation.setDuration(1000);
            self.animation.setStartValue(self.bounds)
            self.animation.setEndValue(rect)
            
            self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
            self.animation.start()
        else:
            self.bounds = rect
        
        self.require_redraw.emit()
            
        
    def markers_at(self, atpoint):
        '''
        :param point: point in screen space
        '''
        for name, marker in self.markers.items():
            point = self.mapToScreen(marker)
            if (point - atpoint).manhattanLength() < 64:
                
                yield name
                
                
    def keyPressEvent(self, event):
        
        if event.key() == Qt.Key_R:
            self.setBounds(self._initial_bounds, animate=True)
        else:

            for tool_name, tool in self.tools.items():
                if tool.key == event.key():
                    self.current_tool = tool_name
            return
        
    
    def toolTipEvent(self, event):
        
        glob_point = event.globalPos()
        
        if self.markers_visible:
            for name in self.markers_at(event.pos()):
                space = QtCore.QPoint(32, 32) 
                rect = QtCore.QRect(event.pos() - space, event.pos() + space)
                QtGui.QToolTip.showText(glob_point, name, self.parent(), rect)
                return True
        
        return False
    
    def mousePressEvent(self, event):
        
        self.tool._mousePressEvent(self, event)
            
    def mouseReleaseEvent(self, event):
        
        self.tool._mouseReleaseEvent(self, event)
    
    def mouseMoveEvent(self, event):
        
        self.tool._mouseMoveEvent(self, event)
        
    def move_to_marker(self, name):
        
        marker = self.markers[name]
        
#        print "move_to_marker", checked, marker
        
        rect = QtCore.QRectF(self.bounds)
        
        x = marker.x() - self.bounds.width() / 2
        y = marker.y() - self.bounds.height() / 2
        rect.moveTo(x, y)
        self.setBounds(rect, animate=True)
        
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        menu.addMenu(self.tool_menu)
        
        self.drop_here = drop_here = event.pos()
        
        markers = QMenu("Marker")
        menu.addMenu(markers)
        markers.addAction(self.drop_marker_act)
        
        makers_under = list(self.markers_at(drop_here))
        
        if makers_under:
            remove_marker_act = SAction("Remove %r" % makers_under[0], self, makers_under[0])
            remove_marker_act.setEnabled(True)
            remove_marker_act.triggered_data.connect(self.remove_marker)
        else:
            remove_marker_act = QAction("Remove Marker", self)
            remove_marker_act.setEnabled(False)

        markers.addAction(remove_marker_act)
        
        markers.addSeparator()
        markers.addAction(self.show_markers_act)

        go_to = QMenu("Go To")
        markers.addMenu(go_to)
        
        for marker in self.markers.keys():
            action = SAction(marker, self, data=marker)
            action.triggered_data.connect(self.move_to_marker)
            go_to.addAction(action)
        
        menu.addMenu(self.bg_color_menu)
        
        for i, plot in enumerate(self.plots):
        
            menu.addSeparator()
            
            title = QMenu(str(plot.objectName()) if plot.objectName() else "Plot %i" % i)
            menu.addMenu(title)
            
            for action in plot.actions:
                title.addAction(action)
            for sub_menu in plot.menus:
                title.addMenu(sub_menu)
                
        
        p = self.mapToGlobal(event.pos())
        menu.exec_(p)
        
        event.accept()
        
        self.require_redraw.emit()
    
    
    require_redraw = QtCore.Signal() 
    
    def mapToGlobal(self, pos):
        return self.parent().mapToGlobal(pos)
    
    def busy(self):
        
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glColor4ub(139, 0, 139, 100)
        GL.glBegin(GL.GL_QUADS)
        GL.glVertex3i(-1, -1, -1)
        GL.glVertex3i(1, -1, -1)
        GL.glVertex3i(1, 1, -1)
        GL.glVertex3i(-1, 1, -1)
        GL.glEnd()
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

