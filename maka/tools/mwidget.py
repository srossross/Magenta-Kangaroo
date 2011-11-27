'''
Created on Nov 25, 2011

@author: sean
'''

from PySide.QtCore import QObject

class MWidget(QObject):
    
    def event(self, event):
        return QObject.event(self, event)
