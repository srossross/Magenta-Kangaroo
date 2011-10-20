'''
Created on Oct 19, 2011

@author: sean
'''

import sys
from PySide import QtCore, QtGui, QtOpenGL
from PySide.QtGui import QColor
from pyopencl import Program 
import numpy as np
from maka.plot.line import LinePlot
from maka.cl_pipe import ComputationalPipe
from maka.util import bring_to_front, execute
from maka.plot_widget import PlotWidget

def main(args):
    app = QtGui.QApplication(args)

    f = QtOpenGL.QGLFormat.defaultFormat()

    f.setSampleBuffers(True)
    QtOpenGL.QGLFormat.setDefaultFormat(f)
    
    plot_widget = PlotWidget(name='My Plots') 
#    canvas = MakaCanvasWidget(parent=plot_widget, name)

    plot_widget.resize(640, 480)

    plot_widget.show()

    bring_to_front()
    
    execute(app, epic_fail=True)

    
if __name__ == '__main__':
    main(sys.argv)
    
    
        
