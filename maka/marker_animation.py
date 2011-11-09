'''
Created on Nov 8, 2011

@author: sean
'''
from __future__ import division

from PySide.QtCore import QPointF, QObject, Property, QPointF, Property, QPropertyAnimation, QEasingCurve


class MarkerAnimation(QObject):
    '''
    Class to animate placement of the marker.
    '''
    def __init__(self, name, drop_point, canvas):
        super(MarkerAnimation, self).__init__(parent=canvas)
        self.name = name
        end_point = canvas.mapToGL(drop_point)
        start_point = canvas.mapToGL(QPointF(drop_point.x(), drop_point.y() - 100))
        canvas.markers[name] = start_point
        
        self.animation = anim = QPropertyAnimation(self, 'pos')
        anim.setDuration(500)
        anim.setEasingCurve(QEasingCurve.Linear)
        
        anim.setStartValue(start_point)
        anim.setEndValue(end_point)

    def _get_pos(self):
        return self.parent().markers[self.name]
    
    def _set_pos(self, value):
        self._pos = value
        self.parent().markers[self.name] = value
        self.parent().require_redraw.emit()

    pos = Property(QPointF, _get_pos, _set_pos)
    
    def start(self):
        self.animation.start()
    
    def accept(self, name):
        '''
        The marker will be permanent 
        '''
        if self.name != name:
            old_name = self.name
            self.parent().markers[name] = QPointF(self.parent().markers[old_name])
            self.name = name
            del self.parent().markers[old_name]
            self.parent().require_redraw.emit()
    
    def reject(self):
        self.animation.stop()
        del self.parent().markers[self.name]
