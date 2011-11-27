'''
Created on Nov 23, 2011

@author: sean
'''

from PySide.QtCore import *

class Foo(QObject):
    def eventFilter(self, filter_obj, event):
        print "eventFilter:", self.objectName(), filter_obj.objectName()
        return QCoreApplication.sendEvent(self, event)
        
    def event(self, event):
#        print "event:", self.objectName()
        return QObject.event(self, event)
        
    def _get_value(self):
        print "_get_value"
        return '1'
    def _set_value(self, value):
        print '_set_value', value
    
    value_changed = Signal()
#    def value_changed(self):
#        print "valueChanged"
        
    value = Property(str, _get_value, _set_value, notify=value_changed)
        
class Bar(QObject):
    pass

class Baz(QObject):
    pass

@Slot()
def print_val():
    print "print val" 
    
def main():
    
    foo = Foo()
    
    foo.value_changed.connect(print_val)
    
    foo.value = 'foo'
    print 
    foo.value_changed.emit()
#    app = QCoreApplication([])
#    timer = QTimer()
#    timer.timeout.connect(app.exit)
#    timer.start(2000)
#
#    etimer = QTimer()
#    etimer.setSingleShot(True)
#    
#    f1 = Foo(objectName="F1")
#    print f1.objectName()
#    f2 = Foo(objectName="F2")
#    f1.installEventFilter(f2)
#    
#    def post_me():
#        event = QDynamicPropertyChangeEvent("property")
#        app.postEvent(f1, event)
#        
#    etimer.timeout.connect(post_me)
#    
#    etimer.start(100)
#    
#    
#    
#    print "exec"
#    app.exec_()
#    print "done"
    
if __name__ == '__main__':
    main()
