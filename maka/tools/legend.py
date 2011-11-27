'''
Created on Nov 14, 2011

@author: sean
'''
from PySide import QtCore, QtGui
from PySide.QtCore import Qt, Slot, Property, QPoint, QRect
from PySide.QtGui import QMenu, QPixmap, QColor, QPen, QFont
from OpenGL import GL
from maka.gl_primitives.rounded_rect import RoundedRect
from maka.util import gl_enable, gl_begin, matrix
import numpy as np

class MWidget(QtCore.QObject):
    
    def event(self, event):
        return QtCore.QObject.event(self, event)


class LegendItem(object):
    def __init__(self, text):
        self.text = unicode(text)

class Legend(MWidget):
    

    def __init__(self, parent=None, pad=10):

        super(Legend, self).__init__(parent=parent)
        
        self.pad = pad
        
        self.menu = QMenu("legend")
        
        self._pixmap = None
        self._visible = True
        
    @Slot()
    def invalidate(self):
        self._pixmap = None
        self.parent().reqest_redraw()
        
    def getPixmap(self):
        return self._pixmap
    
    def isVisible(self):
        return self._visible
    
    def setVisible(self, value):
        self._visible = value
    
    visible = Property(bool, isVisible, setVisible)
    
    pixmap = Property(QPixmap, getPixmap)
    
    def initializeGL(self):
        return

    def resizeGL(self, w, h):
        '''
        Overload of virtual qt method.  calls delegates to current_canvas if in single canvas mode.
        '''
        return

    def paintGL(self, painter):
        
        if not self.visible:
            return
        
        pad = self.pad
        
        painter.save()
        
        bg_color = self.parent().background_color
        
        if bg_color.lightnessF() > .5:
            bg_color = bg_color.darker(110)
        elif bg_color == QColor(Qt.black):
            bg_color = QColor(Qt.darkGray)
        else:
            bg_color = bg_color.lighter(110)
            
        font = QFont("Times")
        font.setPixelSize(20)
        
        brush = QColor(bg_color)
        
        brush.setAlphaF(.8)
        
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.setFont(font)
        
        titles = {plot.objectName(): plot.sample() for plot in self.parent().plots if plot.sample()}
        
        if not titles:
            painter.restore()
            return
#        samples = [plot.sample() for plot in self.parent().plots]
        
        text_height = painter.fontMetrics().height()
        text_width = max(painter.fontMetrics().width(title) for title in titles.keys())
        
        rect = QRect(pad, pad, text_height + text_width + 3 * pad, (text_height + pad) * (len(titles)) + pad)
        painter.drawRoundedRect(rect, 10, 10)
        
        painter.save()
        
        pen = QPen(Qt.white)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        rect.adjust(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 10, 10)

        painter.restore()
        
        painter.translate(QPoint(pad, pad))
        
        painter.setBrush(Qt.white)
        
        for title, sample in titles.items():
            rect = QRect(pad, pad, text_height, text_height)
            painter.drawRect(rect)
            rect.adjust(2, 2, -2, -2)
            painter.drawPixmap(rect, sample)
            
            painter.translate(QPoint(0, text_height + pad))
            painter.drawText(2 * pad + text_height , 0, title)
            
        painter.restore()

