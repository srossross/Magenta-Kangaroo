'''
Created on Nov 14, 2011

@author: sean
'''
from PySide import QtCore, QtGui
from PySide.QtCore import Qt
from OpenGL import GL
from maka.gl_primitives.rounded_rect import RoundedRect
from maka.util import gl_enable, gl_begin, matrix
import numpy as np

class MWidget(QtCore.QObject):
    pass


class LegendItem(object):
    def __init__(self, text):
        self.text = unicode(text)

class Legend(MWidget):

    def __init__(self, parent=None):
        super(Legend, self).__init__(parent=parent)
        
        self.setObjectName("legend")
        self.legend_items = [LegendItem("Data"),
                             LegendItem("Variance 3 32 3 33 333")]
        
        self.font = QtGui.QFont(u'Helvetica', 18)
        
        self.margin = 10
        
        self._position = QtCore.QPointF(1.0, 1.0) 
        
        self._rounded_rect = None
    
        self.render_target = None
        
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.dim_legend)
        
        self._legend_alpha = 1.0
        
        self._hiding_action = QtGui.QAction("Turn Hiding On", self)
        self._hiding_action.setCheckable(True) 
        self._hiding_action.setChecked(False) 
        self._visible_action = QtGui.QAction("Visible", self)

        self._visible_action.setCheckable(True) 
        self._visible_action.setChecked(True)
         
        self._main_menu = QtGui.QMenu("Main Menu")
        self._legend_menu = QtGui.QMenu("Legend")
        
        self._main_menu.addMenu(self._legend_menu)
        self._legend_menu.addAction(self._hiding_action)
        self._legend_menu.addAction(self._visible_action)
        
#        self.setMouseTracking(True)
        
        self._mouse_offset = None
        
        self._require_update = True
        
    @property
    def hiding_on(self):
        return self._hiding_action.isChecked()

    @property
    def is_visible(self):
        return self._visible_action.isChecked()
    
    def _get_alpha(self):
        return self._legend_alpha
    
    def _set_alpha(self, value):
        self._legend_alpha = value
        self.update()
    
    legend_alpha = QtCore.Property(float, _get_alpha, _set_alpha)
    
    def _get_top(self):
        return self._position.y()
    
    def _set_top(self, value):
        self._position.setY(value)
        self.update()
    
    top = QtCore.Property(float, _get_top, _set_top)

    def _get_right(self):
        return self._position.x()
    
    def _set_right(self, value):
        self._position.setX(value)
        self.update()
    
    right = QtCore.Property(float, _get_right, _set_right)
    
    
    def _get_position(self):
        return self._position
    
    def _set_position(self, value):
        self._position = value
        self.update()
        
    position = QtCore.Property(QtCore.QPointF, _get_position, _set_position)

    @QtCore.Slot(float, float)
    def change_position(self, top, right, animate=True):
        
        if animate:
            new_position = QtCore.QPointF(right, top)
            
            self.pos_animation = anim = QtCore.QPropertyAnimation(self, "position")
            anim.setStartValue(self.position)
            anim.setEndValue(new_position)
            anim.setEasingCurve(QtCore.QEasingCurve.OutQuart)
            anim.setDuration(500)
            anim.start()
        else:
            self.position = QtCore.QPointF(right, top)
        
        self.update()
        
    @property
    def rounded_rect(self):
        if self._rounded_rect is None:
            size = self.box_size
            brect = QtCore.QRect(0, 0, size.width(), size.height())
            self._rounded_rect = RoundedRect(brect, 5)
        return self._rounded_rect
    
    @property
    def box_size(self):
        fm = QtGui.QFontMetrics(self.font)
        max_width = max(fm.width(li.text) for li in self.legend_items)
        width = 2 * self.margin + max_width
        height = (len(self.legend_items) * fm.height()) + (len(self.legend_items) - 1) * 10 + 2 * self.margin
        return QtCore.QSize(width, height)
        
    def initializeGL(self):
        
        print "initializeGL"
        size = self.box_size
        self.update_render_target(size.width() + self.margin * 2, size.height() + self.margin * 2)
        self.paint_legend()
        
    def resizeGL(self, w, h):
        '''
        Overload of virtual qt method.  calls delegates to current_canvas if in single canvas mode.
        '''
        
        size = self.box_size
        self.update_render_target(size.width() + self.margin * 2, size.height() + self.margin * 2)
        self.paint_legend()
        
    @property
    def viewport_rect(self):
        viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        return QtCore.QRect(viewport[0], viewport[1], viewport[2], viewport[3])
    
    def set_viewport(self, rect):
        
        GL.glViewport(rect.x(), rect.y(), rect.width(), rect.height())
        
    def draw_box(self, rect, rrect):
        
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()

        GL.glViewport(rect.left(), rect.top(), rect.width(), rect.height())
        GL.glOrtho(0, rect.width(), 0, rect.height(), -1, 1)

#        self.qglColor(self.palette().color(QtGui.QPalette.Window))
#        self.qglColor(self.palette().color(QtGui.QPalette.Window))
#        color = QtGui.QColor(Qt.white)
#        GL.glColor(color.redF(), color.greenF(), color.blueF(), color.alphaF())
#        rrect.fill()
#
#        color = QtGui.QColor(Qt.darkGray)
#        GL.glColor(color.redF(), color.greenF(), color.blueF(), color.alphaF())
#
#        GL.glLineWidth(1)
#        rrect.draw_outline()

        font = self.font
        fm = QtGui.QFontMetrics(font)
        
        GL.glColor(0, 0, 0, 1)

        offset = 10.0
        qgl = self.parent().parent()
        for li in self.legend_items[::-1]:
            qgl.renderText(10., offset, 0.0, li.text, font)
            offset += 10.0 + fm.height()

        GL.glPopMatrix()
        
        
    def update_render_target(self, w, h):
        '''
        Create a texture that maps to the pixels of the screen
        '''
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
        '''
        Render the current state to a texture.
        '''
        GL.glFlush()
        
        w, h = self.render_target_size
        with gl_enable(GL.GL_TEXTURE_2D):
        
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glCopyTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 0, 0, w, h, 0)
            
        return self.render_target



    def _animate_hide(self):
        self.alpha_animation = anim = QtCore.QPropertyAnimation(self, 'legend_alpha')
        anim.setDuration(1000)
        anim.setStartValue(self.legend_alpha)
        anim.setEndValue(0.0)
        anim.start()
        
    def _animate_show(self):
        self.alpha_animation = anim = QtCore.QPropertyAnimation(self, 'legend_alpha')
        anim.setDuration(400)
        anim.setStartValue(self.legend_alpha)
        anim.setEndValue(1.0)
        anim.start()

    def enterEvent(self, event):
        self.timer.stop()
        if not self.is_visible:
            event.ignore()
            return

        
        if self.legend_alpha != 1:
            self._animate_show()
    
    def leaveEvent(self, event):
        if not self.is_visible or not self.hiding_on:
            event.ignore()
            return
        
        if self.legend_alpha != 0:
            self.timer.start(1000)
    
    def is_over(self, pos):
        self.xrect.contains(pos.x(), pos.y())
        return self.xrect.contains(pos.x(), self.height() - pos.y())
    
    def mousePressEvent(self, event):
        self.timer.stop()
        if not self.is_visible:
            event.ignore()
            return 
        
        over = self.is_over(event.pos())
        
        if over and event.buttons() & Qt.LeftButton:
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self._mouse_offset = event.pos() 
            
    def mouseReleaseEvent(self, event):
        self._mouse_offset = None
        if self.top != 0 or self.top != 1 or self.right != 0 or self.right != 1:
            self.change_position(1.0 if self.top > .5 else 0.0, 1.0 if self.right > .5 else 0.0, animate=True)
    
        over = self.is_over(event.pos())
        if over:
            self.setCursor(QtCore.Qt.OpenHandCursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)
        
    
    def mouseMoveEvent(self, event):
        self.timer.stop()
        if not self.is_visible:
            event.ignore()
            return
        
        vp = self.viewport_rect
        
        over = self.is_over(event.pos())
        
        if event.buttons() & Qt.LeftButton and self._mouse_offset:
            
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            delta = event.pos() - self._mouse_offset
            self._mouse_offset = event.pos()
            
            edges = self.xrect
            dpx = (delta.x()) / (vp.width() - edges.width() - self.margin)
            dpy = -(delta.y()) / (vp.height() - edges.height() - self.margin)
            
            self.position += QtCore.QPointF(dpx, dpy) 
            self.update()
            return
        elif over:
            self.setCursor(QtCore.Qt.OpenHandCursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)
            
        if self.hiding_on:
            if self.legend_alpha != 0:
                self.timer.start(2000)
            elif self.legend_alpha != 1:
                self._animate_show()
        
    @QtCore.Slot()
    def dim_legend(self):
        if self.legend_alpha != 0:
            self._animate_hide()
    
    def paint_legend(self):
        
        GL.glDisable(GL.GL_DEPTH_TEST)
        
        GL.glClearColor(1, 1, 1, 0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        
        GL.glColor(0, 0, 0, 1)
        
        size = self.box_size
        rrect = self.rounded_rect
        
        rr = QtCore.QRect(self.margin, self.margin, size.width(), size.height())
        
        viewport = self.viewport_rect
        
        self.draw_box(rr, rrect)
        
        GL.glFlush()
        self.render_to_texture()
        
        self.set_viewport(viewport)
        
    
    @property
    def xrect(self):
        vp = self.viewport_rect
        w, h = self.render_target_size
        x = (vp.width() - w) * self.right
        y = (vp.height() - h) * self.top
        
        return QtCore.QRect(x, y, w, h)

    def draw_legend(self, w, h):
        GL.glColor(1, 1, 1, self.legend_alpha if self.hiding_on else 1)
        
        rect = self.xrect
        with gl_enable(GL.GL_TEXTURE_2D):
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.render_target)
            GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
            with gl_begin(GL.GL_QUADS):
                GL.glTexCoord2f(0, 0)
                GL.glVertex2f(rect.left(), rect.top())
                GL.glTexCoord2f(1, 0)
                GL.glVertex2f(rect.right(), rect.top())
                GL.glTexCoord2f(1, 1)
                GL.glVertex2f(rect.right(), rect.bottom())
                GL.glTexCoord2f(0, 1)
                GL.glVertex2f(rect.left(), rect.bottom())
            
    def paintGL(self):
        
        
        with matrix(GL.GL_PROJECTION):
            GL.glLoadIdentity()
            vp = self.viewport_rect
            GL.glOrtho(vp.left(), vp.right(), vp.top(), vp.bottom(), -1, 1)

            qgl = self.parent().parent()
            
            GL.glColor(0, 0, 0, 1)
            offset = 30
            for li in self.legend_items[::-1]:
                qgl.renderText(10., offset, 0.0, li.text)
                offset += 10.0 + 20

            w, h = self.render_target_size
            
#            if self.is_visible:
#                self.draw_legend(w, h)
        
        
    def contextMenuEvent(self, event):
        self._main_menu.exec_(event.globalPos())
        
        
