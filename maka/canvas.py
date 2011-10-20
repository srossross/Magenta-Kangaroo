'''
Created on Jul 21, 2011

@author: sean
'''

from OpenGL import GL, GLU
from PIL.Image import fromarray #@UnresolvedImport
from PySide import QtCore, QtOpenGL, QtGui
from PySide.QtCore import Qt, QObject
from PySide.QtGui import QMenu, QAction
from maka.util import matrix, gl_begin, gl_disable, gl_enable, SAction
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport
import numpy as np
import os
import pyopencl as cl #@UnresolvedImport
from maka.tool import PanTool, SelectionTool, ZoomTool

SIZE = 100
class Canvas(QObject):

    def _get_xoff(self):
        return self._bounds.topLeft()
    
    def _set_xoff(self, value):
        self._bounds.translate(value)
        self.update()
        
    def _get_bounds(self):
        return self._bounds
    
    def _set_bounds(self, value):
        self._bounds = value
        self.update()
    
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
        
        print self.mapToGL(screen_point), point
        return screen_point

    def __init__(self, parent, aspect= -1, name='Magenta Canvas'):
        
        QObject.__init__(self, parent)
        
        
        self.setObjectName(name)

        self.aspect = aspect
        self.plots = []
        self._cl_context = None
    
        self._bounds = QtCore.QRectF(-1, -1, 2, 2)
        self._initial_bounds = QtCore.QRectF(-1, -1, 2, 2)
        
        self._mouse_down = False
        
        
        self.tools = {'pan':PanTool(key=Qt.Key_P),
                      'selection': SelectionTool(key=Qt.Key_S),
                      'zoom': ZoomTool(key=Qt.Key_Z)}

        self.current_tool = 'pan'
        
        self.save_act = save_act = QAction("Save As...", self)
        save_act.triggered.connect(self.save_as)
        
        self.drop_marker_act = drop_marker_act = QAction("Drop Marker", self)
        self.show_markers_act = show_markers_act = QAction("Visible", self)
        show_markers_act.setCheckable(True)
        show_markers_act.setChecked(True)
        
        drop_marker_act.triggered.connect(self.drop_marker)
        
        self._save = False

        self.markers = {"Center" : QtCore.QPointF(0, 0)}
        
    @property
    def markers_visible(self):
        return self.show_markers_act.isChecked()
    
    @QtCore.Slot(bool)
    def remove_marker(self, checked, marker):
        print "remove_marker"
        
    @QtCore.Slot(bool)
    def drop_marker(self, checked=False):
        print "drop_marker"
        
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
            self.update()
        
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

    def paintGL(self):

        GL.glClearColor(1.0, 1.0, 0.5, 0.0)
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
        
        self.update()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self.setBounds(self._initial_bounds, animate=True)
            
        else:
            for tool_name, tool in self.tools.items():
                if tool.key == event.key():
                    print "setting current tool to", tool_name
                    self.current_tool = tool_name
            return
        
    def event(self, event):
        if event.type() == QtCore.QEvent.ToolTip:
            return self.toolTipEvent(event)
        else:
            return QObject.event(self, event)
        
    def markers_at(self, atpoint):
        '''
        :param point: point in screen space
        '''
        for name, marker in self.markers.items():
            point = self.mapToScreen(marker)
            if (point - atpoint).manhattanLength() < 64:
                
                yield name
    
    def toolTipEvent(self, event):
        
        glob_point = event.globalPos()
        
        if self.markers_visible:
            for name in self.markers_at(event.pos()):
                space = QtCore.QPoint(32, 32) 
                rect = QtCore.QRect(event.pos() - space, event.pos() + space)
                QtGui.QToolTip.showText(glob_point, name, self, rect)
                return True
        
        return False
    
    def mousePressEvent(self, event):
        
        self.tool._mousePressEvent(self, event)
            
    def mouseReleaseEvent(self, event):
        
        self.tool._mouseReleaseEvent(self, event)
    
    def mouseMoveEvent(self, event):
        
        self.tool._mouseMoveEvent(self, event)
        
    def move_to_marker(self, checked, name):
        
        marker = self.markers[name]
        
        print "move_to_marker", checked, marker
        
        rect = QtCore.QRectF(self.bounds)
        
        x = marker.x() - self.bounds.width() / 2
        y = marker.y() - self.bounds.height() / 2
        rect.moveTo(x, y)
        self.setBounds(rect, animate=True)
        
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        menu.addAction(self.save_act)
        
        self.drop_here = drop_here = event.pos()
        
        markers = QMenu("Marker")
        menu.addMenu(markers)
        markers.addAction(self.drop_marker_act)
        
        makers_under = list(self.markers_at(drop_here))
        
        if makers_under:
            remove_marker_act = SAction("Remove %r" % makers_under[0], self, makers_under[0])
            remove_marker_act.setEnabled(True)
            remove_marker_act.triggered.connect(self.remove_marker)
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
        
        self.update()

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

