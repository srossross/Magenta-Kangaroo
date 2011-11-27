'''
Created on Oct 18, 2011

@author: sean
'''
from __future__ import division
from PySide import QtOpenGL, QtCore
from collections import OrderedDict
from PySide.QtGui import QPixmap, QFont, QFontMetrics, QAction, QMenu, QInputDialog, QPainter, QApplication
from PySide.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup, QPoint, QPointF, QEvent
from OpenGL import GL, GLU
from maka.canvas import Canvas
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport
import numpy as np
import pyopencl as cl #@UnresolvedImport
from maka.util import gl_begin, matrix, gl_enable, gl_disable, gl_push_all
from contextlib import contextmanager

def draw_plot(trans, screen_aspect):
    '''
    Draw a unit quad (-1,1,-1,1) with a openGL texture.
    trans == 0 if coverflow where the aspect is 1  
    trans == 1 if coverflow where the aspect is the screen coords  
    '''
    
    x = .5
    y = .5
    
    if screen_aspect > 1:
        x = .5 / (1.0 + (1 - trans) * (screen_aspect - 1.0))
    else:
        y = .5 / (1.0 + (1 - trans) * ((1.0 / screen_aspect) - 1.0))
    
    with gl_begin(GL.GL_QUADS):
        GL.glTexCoord2f(0.5 - x, 0.5 - y)
        GL.glVertex(-1, -1, 0)
        
        GL.glTexCoord2f(0.5 + x, 0.5 - y)
        GL.glVertex(1, -1, 0)

        GL.glTexCoord2f(0.5 + x, 0.5 + y)
        GL.glVertex(1, 1, 0)

        GL.glTexCoord2f(0.5 - x, 0.5 + y)
        GL.glVertex(-1, 1, 0)

def draw_plot_reflection():
    '''
    Not quite there yet.
    '''
#    GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_DECAL)
    
    with gl_disable(GL.GL_DEPTH_TEST):
        with gl_enable(GL.GL_BLEND):
#            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ZERO)
            
            with gl_begin(GL.GL_QUADS):
                GL.glColor(1, 1, 1, 0)
                GL.glTexCoord2f(0, .5)
                GL.glVertex(-1, -1 / 2 - .51, 0)
                
#                GL.glColor(1, 1, 1, 0)
                GL.glTexCoord2f(1, .5)
                GL.glVertex(1, -1 / 2 - .51, 0)
        
                GL.glColor(1, 1, 1, 0.15)
                GL.glTexCoord2f(1, 1)
                GL.glVertex(1, 1 - .51, 0)
        
#                GL.glColor(1, 1, 1, 0.5)
                GL.glTexCoord2f(0, 1)
                GL.glVertex(-1, 1 - .51, 0)
                
#            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
            
DISTANCE = 1.8 * 3

EYE = -0.2 * 2
TARGET = 0.05 * 2

z_position = 0.75 * 2

angle = 45.0
one_x = 0.50 * 4
next_x = 0.10 * 4


#DISTANCE = 2.8
class PlotWidget(QtOpenGL.QGLWidget):
    '''
    This is the main plot widget. 
    
    This widget subclasses the `QtOpenGL.QGLWidget` and contains the openGL and openCL contexts. 
    This widget contains canvases. All data is drawn in a canvas. 
    This widget can switch between a coverflow and individual canvas. 
    
    :param parent: parent widget
    :param aspect: TODO
    :param name: object name 
    :param share: another PlotWidget that this will take its openGL context from. 
    '''
    
    COVERFLOW = 'coverflow'
    SINGLE_CANVAS = 'single_canvas'
    def __init__(self, parent=None, aspect= -1, name='Magenta Plot', share=None):
        
        QtOpenGL.QGLWidget.__init__(self, parent=parent, shareWidget=share)
        self.setObjectName(name)
        
        font = QFont('H')
        self.setFont(font)
        self._canvases = OrderedDict()
        
        self._current_canvas_id = None
        
        self._view_state_choices = [self.COVERFLOW, self.SINGLE_CANVAS]
        self._view_state = self.SINGLE_CANVAS
        
        self.drop_pin = QPixmap("resources/images/drop-pin-large2.png")
        
        self.aspect = aspect
        
        self.setFocusPolicy(Qt.ClickFocus)
        self.setMouseTracking(True)
        self.angle_off = 0.0
        
        self.eye = EYE
        self.tgt = TARGET
        
        self._plot_position = 0.0
        self._perspective_transition = 1.0
        
        self._cl_context = None
        
        self.fs = None
        self.windows = []
        
        self.full_screen_action = QAction("Full Screen", self, shortcut='Ctrl+F')
        self.full_screen_action.triggered.connect(self.toggle_full_screen)

        self.new_canvas_action = QAction("New Canvas", self, shortcut='Ctrl+N')
        self.new_canvas_action.triggered.connect(self.new_canvas)

        self.new_window_action = QAction("Open in New Window", self, shortcut='Ctrl+T')
        self.new_window_action.triggered.connect(self.open_new_window)
        
        self._menus = []
        self._actions = [self.new_canvas_action, self.new_window_action, self.full_screen_action, ]
        self.ctx_menu_items = {'menus':self._menus, 'actions':self._actions}
        
    def saveState(self, settings):
        '''
        Save the state of this widget and it's contained canvases.
        
        :param settings: A Qsettings object
        '''
        settings.beginGroup("plot")
        settings.beginGroup(str(self.objectName()))
        
        settings.setValue("view_state", self._view_state)
        settings.setValue("current_canvas", self.current_canvas_id)

        for canvas in self._canvases.values():
            canvas.saveState(settings)

        settings.endGroup()
        settings.endGroup()
        
    def restoreState(self, settings):
        '''
        restore the state of this widget and it's contained canvases.
        
        :param settings: A Qsettings object
        '''

        settings.beginGroup("plot")
        settings.beginGroup(str(self.objectName()))
        
        self._view_state = settings.value("view_state", self._view_state)
        
#        if not self.single_canvas_state:
#            self.removeEventFilter(self.current_canvas)
            
        if self.coverflow_state:
            self._perspective_transition = 0
        else:
            self._perspective_transition = 1
        
        current_canvas = settings.value("current_canvas", self.current_canvas_id)
        if current_canvas in self._canvases:
            self.current_canvas_id = current_canvas
            
        self._plot_position = self._canvases.keys().index(self.current_canvas_id)
            
        
        for canvas in self._canvases.values():
            canvas.restoreState(settings)
            
        settings.endGroup()
        settings.endGroup()
    
    @QtCore.Slot()
    def new_canvas(self, show=True):
        '''
        Create a new canvas. 
        
        :param show: Enter the canvas if show is true.
        
        '''
        name, ok = QInputDialog.getText(self, "New Canvas", "Name:", text="New Canvas")
        
        if not ok:
            return
        
        if name in self._canvases:
            while name in self._canvases:
                name, ok = QInputDialog.getText(self, "New Canvas", "Sorry that name already exists, choose another:", text="New Canvas")
                if not ok:
                    return
                
        if ok:
            canvas = Canvas(parent=self, name=name)
            self.add_canvas(canvas)
            self.update()
            
            if show:
                self.set_current_canvas(name, animate=True)
                
            return name
                
    @QtCore.Slot()
    def open_new_window(self):
        '''
        Toggle in and out of full screen mode.
        '''
        window = PlotWidget(aspect=self.aspect, name=self.objectName(), share=self)
        self.windows.append(window)
            
        window.current_canvas_id = self.current_canvas_id
        for canvas in self._canvases.values():
            new_canvas = canvas.copy()
            window.add_canvas(new_canvas)
        
        window._view_state = self._view_state
        window._cl_context = self._cl_context
        
        window.show()
            
        
    @QtCore.Slot()
    def toggle_full_screen(self):
        '''
        Toggle in and out of full screen mode.
        '''
        if self.fs is not None and self.fs.isVisible():
            self.show()
            self.resizeGL(self.size().width(), self.size().height())
            self.fs.hide()
        else:
            if self.fs is None:
                self.fs = PlotWidget(aspect=self.aspect, name=self.objectName(), share=self)
                
            fs = self.fs
                
            fs.current_canvas_id = self.current_canvas_id
            for canvas in self._canvases.values():
                fs.add_canvas(canvas.copy())
            
            fs._view_state = self._view_state
            fs._cl_context = self._cl_context
            
            fs.showFullScreen()
            fs.resizeGL(fs.size().width(), fs.size().height())
    
    def _get_plot_position(self):
        return self._plot_position
    
    def _set_plot_position(self, value):
        self._plot_position = value
        self.update()

    def _get_perspective_transition(self):
        return self._perspective_transition
    
    def _set_perspective_transition(self, value):
        self._perspective_transition = value
        self.update()
    
    #For animating changing the selected plot.  
    plot_position = QtCore.Property(float, _get_plot_position, _set_plot_position)
    
    #For animating changing between the current canvas and cover flow state
    perspective_transition = QtCore.Property(float, _get_perspective_transition, _set_perspective_transition)
    
    @property
    def canvases(self):
        'return the dict of current canvases'
        return self._canvases
    
    @property
    def coverflow_state(self):
        '''
        Test whether this widget is in coverflow state
        '''
        return self._view_state == 'coverflow'
    
    @QtCore.Slot(str)    
    def state_changed(self, state_name=None):
        
        if self._view_state == self.COVERFLOW:
            for canvas in self._canvases.values():
                canvas.setFocus(False)
                canvas.setVisible(True)
        else:
            for canvas_id, canvas in self._canvases.items():
                if canvas_id == self.current_canvas_id:
                    canvas.setFocus(True)
                    canvas.setVisible(True)
                else:
                    canvas.setFocus(False)
                    canvas.setVisible(False)

    def set_coverflow_state(self):
        '''
        
        Set this widget to be in coverflow state.
        
        No animation.
        '''
#        self.removeEventFilter(self.current_canvas)
        for canvas in self._canvases.values():
            canvas.setFocus(False)
            canvas.setVisible(True)
            
        self.setCursor(Qt.ArrowCursor)
        self._view_state = 'coverflow'

    @property
    def single_canvas_state(self):
        '''
        Test whether this widget is in single canvas state
        '''
        return self._view_state == 'single_canvas'

    def set_single_canvas_state(self):
        '''
        Set this widget to be in single canvas state
        '''

        self._view_state = self.SINGLE_CANVAS
        
        self.current_canvas.resizeGL(self.size().width(), self.size().height())
        
        self.state_changed(self._view_state)
    
    def set_current_canvas(self, name, animate=True, enter_target_canvas=False):
        '''
        Set the current canvas to be `name`.
        
        :param name: the object name of the canvas to set
        :param animate: animate the transition if true
        :param enter_target_canvas: enter canvas if true, else center in coverflow. 
        
        '''
        
#        print "removeEventFilter"
#        self.removeEventFilter(self._canvases[self.current_canvas_id])
        
        self.current_canvas_id = name
        if self.single_canvas_state:
            self._canvases[self.current_canvas_id].setVisible(True)
#            self.installEventFilter(self._canvases[self.current_canvas_id])
        index = self._canvases.keys().index(name)
        
        self.animation_group = group = QSequentialAnimationGroup()
        
        coverflow_state = self.coverflow_state
        
        if not coverflow_state:
            self.set_coverflow_state()
            self.resizeGL(self.size().width(), self.size().height())
            out = QPropertyAnimation(self, 'perspective_transition')
            out.setDuration(500)
            out.setEasingCurve(QtCore.QEasingCurve.OutQuart)
            out.setStartValue(1.0)
            out.setEndValue(0.0)
            
            self.per_animation_out = out
            group.addAnimation(out)
        
        accross = QPropertyAnimation(self, 'plot_position')
        accross.setDuration(500)
        accross.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        accross.setStartValue(self.plot_position)
        accross.setEndValue(index)
#        accross.finished.connect(self.fin)
        self.per_animation_accross = accross
        group.addAnimation(accross)
        
        if enter_target_canvas or not coverflow_state:
            ain = QPropertyAnimation(self, 'perspective_transition')
            ain.setDuration(500)
            ain.setEasingCurve(QtCore.QEasingCurve.OutQuart)
            ain.setStartValue(0.0)
            ain.setEndValue(1.0)
            ain.finished.connect(self.set_single_canvas_state)
            group.addAnimation(ain)
            self.per_animation_in = ain

        group.start()
        
        self.state_changed()

    @property
    def current_canvas_id(self):
        '''
        return the id of the current canvas.
        '''
        return self._current_canvas_id

    @current_canvas_id.setter
    def current_canvas_id(self, value):
        '''
        return the id of the current canvas.
        '''
#        current_canvas = self.current_canvas
        
#        if current_canvas is not None:
#            print "removeEventFilter"
#            self.removeEventFilter(current_canvas)
            
        self._current_canvas_id = value
        
#        if self.single_canvas_state:
#            print "installEventFilter"
#            self.installEventFilter(self.current_canvas)
        self.state_changed()

    @property
    def current_canvas(self):
        '''
        return the current canvas.
        '''
        return self._canvases.get(self.current_canvas_id)
    
    def add_canvas(self, canvas):
        '''
        Add a canvas. connects listeners
        '''
        self._canvases[canvas.objectName()] = canvas
        canvas.require_redraw.connect(self.update)
        canvas.update_render_target(self.size().width(), self.size().height())
        
        if self.current_canvas_id is None:
            self.current_canvas_id = canvas.objectName()
            
#        print self.objectName(), "installEventFilter:", canvas.objectName()
#        self.installEventFilter(canvas)
    
    def remove_canvas(self, id):
        '''
        Remove the canvas
        '''
        canvas = self._canvases.pop(id)
        canvas.require_redraw.disconnect(self.update)
        
    def resizeGL(self, w, h):
        self.setupViewport(w, h)
        
    def setupViewport(self, w, h):
        '''
        Overload of virtual qt method.  calls delegates to current_canvas if in single canvas mode.
        '''
        self.aspect = aspect = w / h
        
        if self.coverflow_state:
            GL.glViewport(0, 0, w, h)
            
            for canvas in self._canvases.values():
                canvas.update_render_target(w, h)

            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GLU.gluPerspective(45.0, 1.0 * w / h, 0.15, 30.0)
            
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            GLU.gluLookAt(0.0, self.eye, DISTANCE,
                          0.0, self.tgt, 0.0,
                          0.0, 1.0, 0.0)
        else:
            self.current_canvas.resizeGL(w, h)
        
    def setupGL(self):
        
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glEnable(GL.GL_POLYGON_SMOOTH)
        
        GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
        GL.glHint(GL.GL_POLYGON_SMOOTH_HINT, GL.GL_NICEST)
        
        GL.glDisable(GL.GL_DEPTH_TEST)
        
    def initializeGL(self):
        '''
        Initialize the openGL context.
        '''
        
        self.setupGL()
        
        self.drop_pin_tex = self.bindTexture(self.drop_pin.toImage())
        
        for canvas in self.canvases.values():
            canvas.initializeGL()
    
    @contextmanager
    def _make_painter(self):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()

                    
        def cleanup():
            GL.glPopAttrib()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glPopMatrix()
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glPopMatrix()
            painter.end()

        try:
            yield painter
        except:
            cleanup()
            raise
        else:
            cleanup()
            
    @property    
    def in_transition(self):
        return self.perspective_transition != 0.0
    
    def paintEvent(self, event):
        '''
        Main called for screen updates. 
        '''
        self.setupGL()
        self.setupViewport(self.width(), self.height())
        
        with self._make_painter() as painter:
            
            if self.coverflow_state:
                
                painter.save()
                self.draw_coverflow(painter)
                painter.restore()
                
#                if self.in_transition:
#                    for tool in self.current_canvas.tools:
#                        tool.paintGL(painter)
            else:
                self.current_canvas.paintGL(painter)
#                for tool in self.current_canvas.tools:
#                    tool.paintGL(painter)

    
    def set_fog_params(self):
        '''
        set fog for coverflow. 
        
        Note gl_enable(GL.GL_FOG) must be called before this.
        '''
        GL.glFogfv(GL.GL_FOG_COLOR, (.0, .0, .0))
        GL.glFogi(GL.GL_FOG_MODE, GL.GL_LINEAR)
        GL.glFogf(GL.GL_FOG_START, DISTANCE - z_position)
        GL.glFogf(GL.GL_FOG_END, DISTANCE + z_position)

    def interpolate_matricies(self):
        '''
        Linearly Interpolate both the GL_PROJECTION_MATRIX and GL_MODELVIEW_MATRIX.
        from self.perspective_transition==0 (coverflow) to self.perspective_transition==1 (single_canvas) 
        
        '''
        per = self.perspective_transition 
        projection_1 = np.array(GL.glGetDouble(GL.GL_PROJECTION_MATRIX)) 

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        
#        self.current_canvas.projection(self.size().width() / self.size().height(), 0.15, DISTANCE + z_position)
        GL.glOrtho(-1, 1, -1, 1, 0.15, DISTANCE + z_position)

        projection_2 = np.array(GL.glGetDouble(GL.GL_PROJECTION_MATRIX)) 
        GL.glLoadIdentity()
        GL.glLoadMatrixd(((1 - per) * projection_1) + (per * projection_2))
        
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        
        GLU.gluLookAt(0.0, (1.0 - per) * self.eye, DISTANCE,
                      0.0, (1.0 - per) * self.tgt, 0.0,
                      0.0, 1.0, 0.0)

    @contextmanager
    def coverflow_view(self):
        '''
        Set the GL_PROJECTION and GL_MODELVIEW matrices for coverflow state 
        '''
        with matrix(GL.GL_PROJECTION), matrix(GL.GL_MODELVIEW):
            
            per = self.perspective_transition
            if per != 0.0:
                self.interpolate_matricies()
                bg = self.current_canvas.background_color
                GL.glClearColor(per * bg.redF(), per * bg.greenF(), per * bg.blueF(), 0)
            else:
                GL.glClearColor(.0, .0, .0, 0)

            yield
            
        pass
        
    @property
    def screen_aspect(self):
        return self.size().width() / self.size().height()
    
    def draw_coverflow2(self):
        '''
        Draw the coverflow for selection rendering / picking 
        '''
        GL.glInitNames()
        
        GL.glDepthMask(True)
        
        global_pos = self.plot_position
        
        for i, _ in enumerate(self._canvases.keys()):
            pos = i - global_pos
            if abs(pos) < 1:
                current_z = (1 - abs(pos)) * z_position
                current_x = (pos) * one_x 
                current_angle = (pos) * -angle
            else:
                current_z = 0.0 
                direction = (-1 if pos < 0 else 1)
                current_x = direction * (one_x - next_x) + next_x * pos 
                current_angle = -direction * angle

            with matrix(GL.GL_MODELVIEW):
                GL.glTranslatef(current_x, 0.0, current_z)
                GL.glRotate(current_angle, 0, 1, 0)
                
                GL.glPushName(i)
                draw_plot(self.perspective_transition, self.screen_aspect)
                GL.glPopName()
                

    def draw_title_text(self, painter):
        
        with gl_push_all():
            
            GL.glDepthMask(False)
            
            fm = painter.fontMetrics()
            fw = fm.width(self.current_canvas_id)
            fh = fm.height()
            
            pos = QPoint(self.size().width() / 2 - fw / 2, self.size().height() - fh)
            
            painter.drawText(pos, self.current_canvas_id)

    def draw_coverflow(self, painter):
        '''
        Draw the coverflow 
        '''
        canvas_textures = OrderedDict((name, canvas.render_to_texture(painter)) for name, canvas in self._canvases.items())
        
        with gl_push_all():
            with self.coverflow_view():
                
                GL.glEnable(GL.GL_DEPTH_TEST)
                GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
                
                GL.glDepthMask(True)
                global_pos = self.plot_position
                
                with gl_enable(GL.GL_FOG):
                    self.set_fog_params()
                    
                    for i, name in enumerate(self._canvases.keys()):
                        pos = i - global_pos
                        if abs(pos) < 1:
                            current_z = (1 - abs(pos)) * z_position
                            current_x = (pos) * one_x 
                            current_angle = (pos) * -angle
                        else:
                            current_z = 0.0 
                            direction = (-1 if pos < 0 else 1)
                            current_x = direction * (one_x - next_x) + next_x * pos 
                            current_angle = -direction * angle
        
                        with matrix(GL.GL_MODELVIEW):
                            GL.glTranslatef(current_x, 0.0, current_z)
                            GL.glRotate(current_angle, 0, 1, 0)
                            
                            with gl_enable(GL.GL_TEXTURE_2D):
                                GL.glBindTexture(GL.GL_TEXTURE_2D, canvas_textures[name])
                                draw_plot(self.perspective_transition, self.screen_aspect)
        
        
        
        self.draw_title_text(painter)

    @property
    def gl_context(self):
        'return the openGL context'
        return self.context()

    @property
    def cl_context(self):
        'return the openCL context'
        if self._cl_context is None:
            gl_context = self.context()
            gl_context.makeCurrent()
            self._cl_context = cl.Context(properties=get_gl_sharing_context_properties(), devices=[])
            
        return self._cl_context

    def event(self, event):
        '''
        Overload the event method to add a toolTipEvent for the canvas.
        '''
        
        MY_EVENTS = [QEvent.MouseMove, QEvent.KeyPress, QEvent.KeyRelease, QEvent.MouseButtonDblClick, QEvent.MouseButtonPress,
                     QEvent.MouseButtonRelease, QEvent.ContextMenu, QEvent.Enter, QEvent.Leave
                     ]

        if event.type() in MY_EVENTS and self.single_canvas_state and self.current_canvas is not None:
            if self.current_canvas.event(event):
                return True
            
        if event.type() == QtCore.QEvent.ToolTip:
            return self.toolTipEvent(event)
        else:
            return QtOpenGL.QGLWidget.event(self, event)
        
    
    def toolTipEvent(self, event):
        '''
        We want tool tip events for specific non-qt targets within a plot.  
        '''
        if self.coverflow_state:
            return False
        else:
            return self.current_canvas.toolTipEvent(event)

    def mousePressEvent(self, event):
        event.ignore()
        
    def mouseReleaseEvent(self, event):
        index = self.test_over(event.pos())
        
        if index is not None:
            self.goto_canvas(index)
            return
        
        event.ignore()
            
    def mouseDoubleClickEvent(self, event):
        index = self.test_over(event.pos())
        if index is not None:
            self.set_single_canvas_state()
            return
        
        event.ignore()

    def test_over(self, pos):
        '''
        Test what canvas the mouse is over in coverflow mode.
        returns None or the name of a canvas.
        '''
        if not self.coverflow_state:
            return None
        
        with matrix(GL.GL_MODELVIEW), matrix(GL.GL_PROJECTION):
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            GLU.gluPickMatrix(pos.x(), viewport[3] - pos.y(), 4, 4, viewport)
            GLU.gluPerspective(45.0, 1.0 * viewport[2] / viewport[3], 0.15, 30.0)
        
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            
            GLU.gluLookAt(0.0, self.eye, DISTANCE,
                          0.0, self.tgt, 0.0,
                          0.0, 1.0, 0.0)
        
            GL.glRenderMode(GL.GL_RENDER)
            GL.glSelectBuffer(20)
            GL.glRenderMode(GL.GL_SELECT)
            
            self.draw_coverflow2()
            
            GL.glFlush()
            
            hits = GL.glRenderMode(GL.GL_RENDER)
            
            if hits:
                
                top_hit = sorted(hits, key=lambda hit: hit[0])[0]
                index = top_hit[2][0]
                return index
            else:
                return None

    def mouseMoveEvent(self, event):
        
        self.makeCurrent()
        
        if self.test_over(event.pos()) is None:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.PointingHandCursor)

    def contextMenuEvent(self, event):

        menu = QMenu()
        
        for action in self._actions:
            menu.addAction(action)
            
        for sub_menu in self._menus:
            menu.addMenu(sub_menu)
        
        p = event.globalPos()
        menu.exec_(p)
        
        event.accept()
            
        
    def animate_single_canvas_state(self):
        '''
        animate the transition to the single_canvas_state by setting perspective_transition property from current to 0.
        '''
        
        #self.installEventFilter(self.current_canvas)
        
        self.per_animation = QPropertyAnimation(self, 'perspective_transition')
        self.per_animation.setDuration(1000);
        self.per_animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        self.per_animation.setStartValue(self.perspective_transition)
        self.per_animation.setEndValue(1.0)
        self.per_animation.start()
        self.per_animation.finished.connect(self.set_single_canvas_state)

        for tool in self.current_canvas.tools:
            tool.visible = True
            
    def goto_canvas(self, index):
        '''
        Set the canvas at index `index`
        '''
#        print "goto_canvas", index
        names = self._canvases.keys()
        
        self.current_canvas_id = names[index]
        self.animation = QPropertyAnimation(self, 'plot_position')
        self.animation.setDuration(1000)
        self.animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        self.animation.setStartValue(self.plot_position)
        self.animation.setEndValue(float(index))
        
        self.animation.start()
        
        self.state_changed()

    def animate_coverflow_state(self):
        '''
        animate the transition to the single_canvas_state by setting perspective_transition property from current to 1.
        '''

        self.set_coverflow_state()
        self.resizeGL(self.size().width(), self.size().height())
        self.per_animation = QPropertyAnimation(self, 'perspective_transition')
        self.per_animation.setDuration(1000)
        self.per_animation.setEasingCurve(QtCore.QEasingCurve.OutQuart)
        self.per_animation.setStartValue(self.perspective_transition)
        self.per_animation.setEndValue(0.0)
        self.per_animation.start()

        self.state_changed()
        
        for tool in self.current_canvas.tools:
            tool.visible = False

    def keyPressEvent(self, event):
        '''
        TODO: 
        '''
        if self.coverflow_state:
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                self.animate_single_canvas_state()
                return 
            else:
                names = self._canvases.keys()
                index = names.index(self.current_canvas_id)

                if event.key() in [Qt.Key_Left, Qt.Key_Right]:
                    if event.key() == Qt.Key_Left:
                        if index == 0:
                            return
                        pos = -1
                    if event.key() == Qt.Key_Right:
                        if index == len(names) - 1:
                            return 
                        pos = 1
                    
                    self.goto_canvas(index + pos)
                    return
        else:
            if event.key() == Qt.Key_Escape:
                self.animate_coverflow_state()
                return
        
        event.ignore()
