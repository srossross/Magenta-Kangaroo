'''
Created on Dec 8, 2011

@author: sean
'''

from PySide.QtCore import QThread
from PySide.QtGui import QApplication
maka_app = None

#class AppRunner(QThread):
#    def run(self):
#        pass
#    
def start():
    global maka_app
    maka_app = QApplication([])
    pass

def plot_window():
    pass

window.plot(data)

def show(window):
    
    global maka_app
    window.show()
    maka_app.exec_()
#
#
#if __name__ == '__main__':
#    runner = AppRunner()


