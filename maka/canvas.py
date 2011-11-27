'''
Created on Jul 21, 2011

@author: sean
'''
from __future__ import division
from OpenGL import GL, GLU
from PySide import QtCore, QtGui
from PySide.QtCore import Qt, Property, QRect, QPoint, QTimer
from PySide.QtGui import QMenu, QAction, QColor, QProgressBar, QRegion
from PySide.QtGui import QWidget
from maka.util import matrix, gl_begin, gl_disable, gl_enable, \
    gl_attributes
from maka.tools.controllers import PanControl, SelectionControl, ZoomControl
from maka.marker_animation import MarkerAnimation
from maka.canvas_base import CanvasBase
from maka.tools.legend import Legend
from maka.tools.axes import Axes

SIZE = 100

def move_to(method, marker):
    
    @QtCore.Slot()
    def move_to_slot():
        method(marker)
    
    return move_to_slot
    
class Canvas(CanvasBase):
    '''
    Canvas for 2D plotting. add this to a PlotWidget
    
    :param parent:
    :param aspect
    :param name:
    :param background_color:  
    '''
    
    def _get_xoff(self):
        return self._bounds.topLeft()
    
    def _set_xoff(self, value):
        self._bounds.translate(value)
        self.bounds_changed.emit()
        self.require_redraw.emit()
    
    offset = QtCore.Property(QtCore.QPointF, _get_xoff, _set_xoff)
        
    def _get_bounds(self):
        return self._bounds
    
    def _set_bounds(self, value):
        self._bounds = value
        self.bounds_changed.emit()
        self.require_redraw.emit()
        
     
    bounds = QtCore.Property(QtCore.QRectF, _get_bounds, _set_bounds)
    
    bounds_changed = QtCore.Signal() 
    
    def data_space(self):
        '''
        Set the openGL projection matrix to view the data in self.bounds. 
        '''
        rect = self.bounds
        GLU.gluOrtho2D(rect.left(), rect.right(), rect.top(), rect.bottom())
        
    def mapToGL(self, point):
        '''
        Map a point in local screen space to openGL coordinates. (index space)
        '''
        with matrix(GL.GL_MODELVIEW):
            self.data_space()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            
            x, y, _ = GLU.gluUnProject(point.x() , viewport[3] - (point.y() - 2 * viewport[1]), -1)

        return QtCore.QPointF(x, y)

    def mapToScreen(self, point):
        '''
        Map a point in openGL coordinates (index space) to local screen space.
        '''
        with matrix(GL.GL_MODELVIEW):
            self.data_space()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            x, y, _ = GLU.gluProject(point.x(), point.y(), -1)
            
        screen_point = QtCore.QPoint(x, viewport[3] - (y - 2 * viewport[1]))
        
        return screen_point

    def copy(self):
        new_canvas = Canvas(self.parent(), self.aspect, self.objectName(), self.background_color)
        
        for plot in self.plots:
            new_canvas.add_plot(plot)
            
        new_canvas.markers = self.markers
            
        new_canvas._bounds = self._bounds
        new_canvas._initial_bounds = self._initial_bounds

        return new_canvas
        
    def __init__(self, parent, aspect= -1, name='Magenta Canvas', background_color=None, start_busy=False):

        super(Canvas, self).__init__(parent, name , background_color)
        
        self._busy = False
        self.timer = QTimer()
        self.timer.setInterval(1000 // 30)
        self.timer.timeout.connect(self.reqest_redraw)
        self._progress_bar = None
        self.busy = start_busy
        
        self.setObjectName(name)

        self.aspect = aspect
        self.plots = []
    
        self._bounds = QtCore.QRectF(-1, -1, 2, 2)
        self._initial_bounds = QtCore.QRectF(-1, -1, 2, 2)
        
        
        self.save_act = save_act = QAction("Save As...", self)
        save_act.triggered.connect(self.save_as)
        
        self.drop_marker_act = drop_marker_act = QAction("Drop Marker", self)
        self.show_markers_act = show_markers_act = QAction("Visible", self)
        
        self.remove_marker_act = QAction("Remove Marker", self)
        self.remove_marker_act.setEnabled(False)
        self.remove_marker_act.triggered.connect(self.remove_marker)
        show_markers_act.setCheckable(True)
        show_markers_act.setChecked(True)
        
        drop_marker_act.triggered.connect(self.drop_marker)
        
        self._save = False

        self.markers = {}
        
        controllers = [PanControl('pan', key=Qt.Key_P, canvas=self),
                       SelectionControl('select', key=Qt.Key_S, canvas=self),
                       ZoomControl('zoom', key=Qt.Key_Z, canvas=self)]
        
        self._init_controllers(controllers, 'pan')
        
        self._init_tools([Axes(self, title=name), Legend(self)])
#        self._init_tools([])
        
    def saveState(self, settings):
        '''
        Save this canvases state. 
        
        :param settings: a QSettings object
        '''
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue('bounds', self._bounds)
        settings.setValue('background_color', self.background_color)
        
        settings.beginWriteArray("markers")
        
        for i, (key, value) in enumerate(self.markers.items()):
            settings.setArrayIndex(i)
            settings.setValue("key", key)
            settings.setValue("value", value)
            
        settings.endArray()
        
        for plot in self.plots:
            plot.saveState(settings)
            
        settings.endGroup()

    def restoreState(self, settings):
        '''
        Restore this canvases state. 
        
        :param settings: a QSettings object
        '''
        settings.beginGroup(str(self.objectName()))
        
        self._bounds = settings.value('bounds', self._bounds)
        self.background_color = settings.value('background_color', self.background_color)
        
        size = settings.beginReadArray("markers")
        
        for i in range(size):
            settings.setArrayIndex(i)
            key = settings.value("key")
            value = settings.value("value")
            self.markers[key] = value
            
        settings.endArray()
        
        for plot in self.plots:
            plot.restoreState(settings)

        settings.endGroup()
    
    @property
    def markers_visible(self):
        return self.show_markers_act.isChecked()
    
    @QtCore.Slot()
    def remove_marker(self):
        marker = self.remove_marker_act.data()
        self.markers.pop(marker, None)
        self.require_redraw.emit()
        
    @QtCore.Slot(bool)
    def drop_marker(self):
        '''
        Add a marker at the current mouse position.
        '''
        
        tmp_marker_name = "Marker %i" % (len(self.markers),)
        
        self.marker_animation = MarkerAnimation(tmp_marker_name, self.drop_here, self)
        self.marker_animation.start()
        
        global_pos = self.mapToGlobal(self.drop_here)
        
        dialog = QtGui.QDialog()
        dialog.setWindowOpacity(.8)
        dialog.move(global_pos)
        layout = QtGui.QVBoxLayout()
        dialog.setLayout(layout)
        text = QtGui.QLineEdit(dialog)
        
        text.setText(tmp_marker_name)
        layout.addWidget(text)
        bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
        layout.addWidget(bbox)
        dialog.setModal(True)
        dialog.setWindowTitle("Drop Marker")
        
        bbox.accepted.connect(dialog.accept)
        bbox.rejected.connect(dialog.reject)
        
        result = dialog.exec_()
        
        if result == QtGui.QDialog.Accepted:
            self.marker_animation.accept(text.text())
        else:
            self.marker_animation.reject()
        
    def add_plot(self, plot):
        '''
        Add a plot to the canvas
        '''
        plot.process()
        plot.changed.connect(self.reqest_redraw)
        self.plots.append(plot)
        
        if plot.parent() is None:
            plot.setParent(self)
    
    def initializeGL(self):
         
        for tool in self.tools:
            tool.initializeGL()
    
    def resizeGL(self, w, h):
        '''
        
        '''
        GL.glViewport(0, 0, w, h)
            
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        self.projection(w / h)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        self.update_render_target(w, h)
        
        for tool in self.tools:
            tool.resizeGL(w, h)
        
    def projection(self, screen_aspect, near= -1, far=1):
        '''
        not used
        '''
        
        left = -1
        right = 1
        top = -1
        bottom = 1
        
        if self.aspect == screen_aspect:
            pass
        elif screen_aspect > self.aspect:
            left = -1 * screen_aspect
            right = 1 * screen_aspect
        else:
            top = -1 / screen_aspect
            bottom = 1 / screen_aspect
            
        GL.glOrtho(left, right, top, bottom, near, far)
    
    @property
    def viewport(self):
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        return QRect(viewport[0], viewport[1], viewport[2], viewport[3])
    
    def drawBusy(self, painter):
        if painter is None or not self.visible:
            return 
        
        painter.save()
        
        magenta = QColor(Qt.magenta)
        magenta.setAlphaF(.4)
        painter.setBrush(magenta)
        
        if self._progress_bar is None:
            self._progress_bar = QProgressBar()
        bar = self._progress_bar    
        
        viewport = self.viewport
        painter.drawRect(self.viewport)
        
        bar.setMinimum(0)
        bar.setMaximum(0)
        bar.setValue(0)
        
        x = (viewport.width() - bar.width()) / 2
        y = (viewport.height() - bar.height()) / 2
        
        rf = QWidget.RenderFlags(QWidget.DrawChildren)
        bar.render(painter, QPoint(x, y), QRegion(bar.rect()), rf)
        
        painter.restore()
        
        painter.beginNativePainting()
        painter.endNativePainting()
    
    
    def draw_plots(self, painter):
        qs = [plot.queue for plot in self.plots]

        for q in qs:
            q.finish()

        with matrix(GL.GL_PROJECTION):
            self.data_space()
        
            with matrix(GL.GL_MODELVIEW):
                
                for plot in self.plots:
                    plot.draw()
                
            self.draw_markers()
            
        self.controller._paintGL(self)
        
    def paintGL(self, painter):
        '''
        Draw the current scene to OpenGL
        '''
        
        with gl_attributes():

            bg = self.background_color
            GL.glClearColor(bg.redF(), bg.greenF(), bg.blueF(), bg.alphaF())
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            
            if self.busy:
                self.drawBusy(painter)
            else:
                self.draw_plots(painter)
                
        for tool in self.tools:
                tool.paintGL(painter)
    
        painter.beginNativePainting()
        painter.endNativePainting()

    def draw_markers(self):
        '''
        Draw the current markers
        '''
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
        '''
        Set the bounds of the canvas with optional animation.
        '''
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
        if event.key() == Qt.Key_Escape:
            event.ignore()
            return 
        
        elif event.key() == Qt.Key_R:
            self.setBounds(self._initial_bounds, animate=True)
        else:
            for controller_name, controller in self.controllers.items():
                if controller.key == event.key():
                    self.current_controller = controller_name
                    return
        
        event.ignore()
        
    def toolTipEvent(self, event):
        
        glob_point = event.globalPos()
        
        if self.markers_visible:
            for name in self.markers_at(event.pos()):
                space = QtCore.QPoint(32, 32) 
                rect = QtCore.QRect(event.pos() - space, event.pos() + space)
                QtGui.QToolTip.showText(glob_point, name, self.parent(), rect)
                return True
        
        event.ignore()
        return False
    
#    def mousePressEvent(self, event):
#        self.controller._mousePressEvent(self, event)
#            
#    def mouseReleaseEvent(self, event):
#        self.controller._mouseReleaseEvent(self, event)
#    
#    def mouseMoveEvent(self, event):
#        self.controller._mouseMoveEvent(self, event)
        
    def move_to_marker(self, name):
        '''
        Move the bounds to the marker.
        '''
        marker = self.markers[name]
        
        rect = QtCore.QRectF(self.bounds)
        
        x = marker.x() - self.bounds.width() / 2
        y = marker.y() - self.bounds.height() / 2
        rect.moveTo(x, y)
        self.setBounds(rect, animate=True)
        
    @QtCore.Slot(object)
    def move_to_canvas(self, canvas):
        pass

    @QtCore.Slot(object)
    def copy_to_canvas(self, data):
        '''
        Copy the plot object to a new canvas
        '''
        
        plot_idx, canvas_name = data
        if canvas_name is None:
            canvas_name = self.parent().new_canvas(show=False)
            
            if canvas_name is None:
                return 
            
        self.parent().canvases[canvas_name].add_plot(self.plots[plot_idx])
        
#        print "set_current_canvas", canvas_name
        self.parent().set_current_canvas(canvas_name)

    def _ctx_markers(self, event, menu):
        '''
        Add marker actions to a context menu
        '''
        self.drop_here = drop_here = event.pos()
        
        markers = QMenu("Marker")
        menu.addMenu(markers)
        markers.addAction(self.drop_marker_act)
        makers_under = list(self.markers_at(drop_here))
        if makers_under:
            self.remove_marker_act.setEnabled(True)
            self.remove_marker_act.setData(makers_under[0])
        else:
            self.remove_marker_act.setEnabled(False)
            self.remove_marker_act.setData(None)
        markers.addAction(self.remove_marker_act)
        markers.addSeparator()
        markers.addAction(self.show_markers_act)
        go_to = QMenu("Go To")
        markers.addMenu(go_to)
        for marker in self.markers.keys():
            action = QAction(marker, self)
            action.triggered.connect(move_to(self.move_to_marker, marker))
            go_to.addAction(action)
        
        menu.addMenu(self.bg_color_menu)

    def _ctx_plots(self, event, menu):
        '''
        Add plot actions to a context menu
        '''
        menu.addSeparator()
        for i, plot in enumerate(self.plots):
        
            
            title = QMenu(str(plot.objectName()) if plot.objectName() else "Plot %i" % i)
            menu.addMenu(title)
            
            for action in plot.actions:
                title.addAction(action)
            for sub_menu in plot.menus:
                title.addMenu(sub_menu)
        menu.addSeparator()
#            move_to_menu = QMenu("Move To")
#            copy_to_menu = QMenu("Copy To")
#            for canvas_name in self.parent().canvases:
#                if canvas_name == self.objectName():
#                    continue
#                
#                move_act = SAction(canvas_name, self, (i, canvas_name))
#                move_act.triggered_data.connect(self.move_to_canvas)
#                copy_act = SAction(canvas_name, self, (i, canvas_name))
#                copy_act.triggered_data.connect(self.copy_to_canvas)
#                
#                move_to_menu.addAction(move_act)
#                copy_to_menu.addAction(copy_act)
#            move_to_menu.addSeparator()
#            move_to_menu.addAction(SAction('New Canvas ...', self, (i, None)))
#            copy_to_menu.addSeparator()
#            copy_to_menu.addAction(SAction('New Canvas ...', self, (i, None)))
#            title.addMenu(move_to_menu)
#            title.addMenu(copy_to_menu)
        
    def _ctx_parent(self, event, menu):
        '''
        Add PlotWidget actions to a context menu
        '''
        if self.parent():
            menu.addSeparator()

            for sub_menu in self.parent().ctx_menu_items['menus']:
                menu.addMenu(sub_menu)
            for action in self.parent().ctx_menu_items['actions']:
                menu.addAction(action)

    def _ctx_tools(self, event, menu):
        
        for tool in self.tools:
            menu.addMenu(tool.menu)
            
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        menu.addMenu(self.controller_menu)
        
        self._ctx_markers(event, menu)
        
        self._ctx_plots(event, menu)
        self._ctx_tools(event, menu)

        self._ctx_parent(event, menu)
                    
        p = event.globalPos()
        menu.exec_(p)
        
        event.accept()
        
        self.require_redraw.emit()
    
    def mapToGlobal(self, pos):
        return self.parent().mapToGlobal(pos)
    
        
    def isBusy(self):
        return self._busy

    def setBusy(self, value):
        self._busy = value
        self.require_redraw.emit()
        
        if value:
            self.timer.start(1000 // 30)
        else:
            self.timer.stop()
    
    busy = Property(bool, isBusy, setBusy)

