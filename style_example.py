'''
Created on Oct 25, 2011

@author: sean
'''

from PySide.QtCore import *
from PySide.QtGui import *


qapp = QApplication([])


class M(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)
        self._x = 0.0
        self._h = 'false'
        
    def _get_x(self):
        return self._x
    
    def _set_x(self, value):
        self._x = value
    
    x = Property(float, _get_x, _set_x)

    def _get_hover(self):
        return self._h
    
    def _set_hover(self, value):
        self._h = bool(value)
    
    hover = Property(str, _get_hover, _set_hover)

    def paintEvent(self, event):
        
        print 'paintEvent x =', self.x
        
        self.hover = 'true'
        
        QWidget.paintEvent(self, event)
        
class MyWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        print "initialized"
        self.setObjectName('widi')
        self._m = M(self)
        
    
    def _get_m(self):
        return self._m
    
    def _set_m(self, value):
        self._m = value
        
    m = Property(QWidget, _get_m, _set_m)
    @property
    def bg_color(self):
        return self.palette().color(QPalette.Window)
    
    def paintEvent(self):
        pass
    
qapp.setStyleSheet("""

MyWidget {
    color: white;
}
M {
    color: red;
    qproperty-line_style: dot;
}

""")

widget = MyWidget()

print "showing"
#print 'widget.bg_color', widget.bg_color
widget.show()
print 'QPalette.WindowText', widget.palette().color(QPalette.WindowText)
print 'QPalette.WindowText M', widget.m.palette().color(QPalette.WindowText)
print widget.children()
print widget.m.x
print "qapp.exec_"
qapp.exec_()

