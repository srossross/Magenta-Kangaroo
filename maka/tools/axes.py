'''
Created on Nov 25, 2011

@author: sean
'''


from PySide.QtCore import QObject, QRect, QRectF, QPointF, Property, Qt, QPropertyAnimation
from PySide.QtCore import QEasingCurve, QEvent, Slot
from PySide.QtGui import QPolygonF, QPainterPath, QBrush, QPen, QFont, QFontMetricsF, QAction
from PySide.QtGui import QMenu

from maka.util import gl_attributes, gl_push_all

class Axes(QObject):
    
    def __init__(self, parent=None, title="This is the Title"):
        QObject.__init__(self, parent)

        self.title = title
        self.margin = 50 
        self._perc = 0.0 # == Visible;  1 == hidden
        
        self.menu = menu = QMenu("Axes")
        self._visible_action = act = QAction("Visible", self)
        act.setCheckable(True) 
        act.setChecked(True) 
        menu.addAction(act)
        act.triggered.connect(self.toggle_visible)
        
        self._hiding_action = act = QAction("Turn Hiding On", self)
        act.setCheckable(True) 
        act.setChecked(False) 
        menu.addAction(act)
        act.triggered.connect(self.toggle_hiding)

    
    def isVisible(self):
        return self._visible_action.isChecked()
    
    def setVisible(self, value):
        self._visible_action.setChecked(value)
        if self.isVisible():
            print "animateShow"
            self.animateShow()
        else:
            print "animateHide"
            self.animateHide()
    
    visible = Property(bool, isVisible, setVisible)
    
    @property 
    def hiding(self):
        return self._hiding_action.isChecked() and self.visible
    
    @Slot()
    def toggle_visible(self):
        if self.isVisible():
            print "animateShow"
            self.animateShow()
        else:
            print "animateHide"
            self.animateHide()

    @Slot()
    def toggle_hiding(self):
        pass
    
    def initializeGL(self):
        pass
    
    def resizeGL(self, w, h):
        pass
    
    def _get_perc(self):
        return self._perc

    def _set_perc(self, value):
        self._perc = value
        self.parent().require_redraw.emit()
    
    perc = Property(float, _get_perc, _set_perc)

    def draw_top(self, painter):
        
        width = painter.viewport().width()
        margin = self.margin
        
        poly = QPolygonF([QPointF(0, 0), QPointF(margin, 0), QPointF(margin, margin)])
        left_tri = QPainterPath()
        left_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(width, 0), QPointF(width - margin, 0), QPointF(width - margin, margin)])
        right_tri = QPainterPath()
        right_tri.addPolygon(poly)
        
        painter.save()

        painter.translate(QPointF(0, -(margin + 1) * self.perc))

        bg = self.background_color
        
        painter.fillPath(left_tri, QBrush(bg))
        painter.fillPath(right_tri, QBrush(bg))
        
        #Bottom        
        painter.fillRect(QRect(margin, 0, width - margin * 2, margin), bg)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(margin, margin, width - margin, margin) #Horozontal
        
        font = QFont(u'Monaco')
        font.setPixelSize(margin // 2)
        painter.setFont(font)
        
        fm = QFontMetricsF(font)
        font_height = fm.height()
        font_width = fm.width(self.title)
        
        title = self.title
        title_base = self.title
        
        
        while font_width > (width - margin * 2):
            title_base = title_base[:-2]
            title = title_base + '...'
            font_width = fm.width(title + '...')
            
        topLeft = QPointF(margin + ((width - margin * 2) - font_width) / 2.0, (margin + font_height) / 2.0)
        
        painter.drawText(topLeft, title)
        painter.restore()
        
    @property
    def background_color(self):
        widget = self.parent().parent()
        return widget.palette().color(widget.backgroundRole()).lighter(102)
    
    def draw_right_axis(self, painter):
        
        width = painter.viewport().width()
        height = painter.viewport().height()
        
        margin = self.margin
        
        poly = QPolygonF([QPointF(width, height), QPointF(width, height - margin), QPointF(width - margin, height - margin)])
        bottom_tri = QPainterPath()
        bottom_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(width, 0), QPointF(width, margin), QPointF(width - margin, margin)])
        top_tri = QPainterPath()
        top_tri.addPolygon(poly)

        painter.save()
        
        painter.translate(QPointF((margin + 1) * self.perc, 0))
        
        bg = self.background_color
        
        #Left        
        painter.fillRect(QRect(width - margin, margin, margin, height - margin * 2), bg)
        painter.fillPath(top_tri, QBrush(bg))
        painter.fillPath(bottom_tri, QBrush(bg))
        
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(width - margin, margin, width - margin, height - margin) #Vertical
        
        painter.restore()
        
    def draw_left_axis(self, painter):

        margin = self.margin
        height = painter.viewport().height()

        poly = QPolygonF([QPointF(0, height), QPointF(0, height - margin), QPointF(margin, height - margin)])
        bottom_tri = QPainterPath()
        bottom_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(0, 0), QPointF(0, margin), QPointF(margin, margin)])
        top_tri = QPainterPath()
        top_tri.addPolygon(poly)

        painter.save()
        
        painter.translate(QPointF(-(margin + 1) * self.perc, 0))
        
        bg = self.background_color
        
        #Left        
        painter.fillRect(QRect(0, margin, margin, height - margin * 2), bg)
        painter.fillPath(top_tri, QBrush(bg))
        painter.fillPath(bottom_tri, QBrush(bg))
        
        pen = QPen(Qt.black)
        pen.setWidthF(0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(height - margin, margin, -20):
            painter.drawLine(margin, i, margin - 10, i)

        
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(margin, margin, margin, height - margin) #Vertical
#        painter.drawLine(0, height, margin, height - margin) #Diag
        
        painter.restore()
        #=======================================================================
        # 
        #=======================================================================
#        painter.save()
#        
#        grad_left = QLinearGradient(QPointF(0, 0), QPointF(5, 0))
#        grad_left.setColorAt(0, QColor(0, 0, 0, 90))
#        grad_left.setColorAt(1, QColor(0, 0, 0, 0))
#
#        painter.fillRect(QRect(0, margin, margin, height - margin * 2), grad_left)
#        painter.fillPath(bottom_tri, QBrush(grad_left))
#        painter.fillPath(top_tri, QBrush(grad_left))
#
#        painter.restore()
        
    def draw_bottom_axis(self, painter):
        
        width = painter.viewport().width()
        height = painter.viewport().height()
        margin = self.margin
        
        poly = QPolygonF([QPointF(0, height), QPointF(margin, height), QPointF(margin, height - margin)])
        left_tri = QPainterPath()
        left_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(width, height), QPointF(width - margin, height), QPointF(width - margin, height - margin)])
        right_tri = QPainterPath()
        right_tri.addPolygon(poly)
        
        painter.save()

        painter.translate(QPointF(0, (margin + 1) * self.perc))

        bg = self.background_color
        
        painter.fillPath(left_tri, QBrush(bg))
        painter.fillPath(right_tri, QBrush(bg))
        
        #Bottom        
        painter.fillRect(QRect(margin, height - margin, width - margin * 2, margin), bg)

        pen = QPen(Qt.white)
        pen.setWidthF(2.6)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(margin, width - margin, 20):
            painter.drawLine(i, height - margin, i, height - margin + 10)

        pen = QPen(Qt.black)
        pen.setWidthF(0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(margin, width - margin, 20):
            painter.drawLine(i, height - margin, i , height - margin + 10)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(margin, height - margin, width - margin, height - margin) #Horozontal
#        painter.drawLine(0, height, margin, height - margin) #Diag
        
        painter.restore()
        #=======================================================================
        # 
        #=======================================================================
#        painter.save()
#        
#        grad_x = QLinearGradient(QPointF(0, height - 5), QPointF(0, height))
#        grad_x.setColorAt(1, QColor(0, 0, 0, 90))
#        grad_x.setColorAt(0, QColor(0, 0, 0, 0))
#
#        painter.fillRect(QRect(margin, height - margin, width - margin * 2, margin), grad_x)
#        painter.fillPath(left_tri, QBrush(grad_x))
#        painter.fillPath(right_tri, QBrush(grad_x))
#        
#        painter.restore()
        

    def draw_axes(self, painter):
        if self.perc != 1.0:
            self.draw_left_axis(painter)
            self.draw_right_axis(painter)
            self.draw_top(painter)
            self.draw_bottom_axis(painter)
    
    def paintGL(self, painter):
        
        if painter is None:
            return
        
    
        
        painter.save()
        self.draw_axes(painter)
        
        painter.setBrush(Qt.NoBrush)
        painter.setPen(Qt.black)
        
        rect = QRectF(painter.viewport())
        
        rect.adjust(self.perc - 1, self.perc - 1,
                    1 - self.perc, 1 - self.perc)
        
        painter.drawRect(rect)
        
        painter.restore()
        viewport = painter.viewport()
        window = painter.window()
        
#        print "window", window
#        print "viewport", viewport
#        if self.visible:
        p = 1 - self._perc
        margin = self.margin * p
        viewport.adjust(margin , margin, -margin, -margin)              
        window.adjust(0 , 0, -2 * margin, -2 * margin)              
        painter.setViewport(viewport)
        painter.setWindow(window)

    def event(self, event):
        
        if event.type() == QEvent.Leave:
            self.leaveEvent(event)
        elif event.type() == QEvent.Enter:
            self.enterEvent(event)
            
        event.ignore()
        return False

    def animateShow(self):
        self.perc_anim = anim = QPropertyAnimation(self, 'perc', self)
        anim.setEasingCurve(QEasingCurve.OutQuart)
        anim.setDuration(600)
        anim.setStartValue(self.perc)
        anim.setEndValue(0)
        anim.start()
        
    def animateHide(self):
        self.perc_anim = anim = QPropertyAnimation(self, 'perc', self)
        anim.setEasingCurve(QEasingCurve.OutQuart)
        anim.setDuration(600)
        anim.setStartValue(self.perc)
        anim.setEndValue(1)
        anim.start()
        
    def enterEvent(self, event):
        if self._perc != 0 and self.hiding and self.visible:
            self.animateShow()



    def leaveEvent(self, event):
        if self._perc != 1 and self.hiding and self.visible:
            self.animateHide()
