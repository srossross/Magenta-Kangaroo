'''
Created on Oct 19, 2011

@author: sean
'''

from ctypes import c_float
import sys
from PySide import QtCore, QtGui, QtOpenGL
from PySide.QtGui import QMainWindow, QMenu, QMenuBar, QWidget, QSlider, QVBoxLayout

#from pyopencl import Program, Buffer, mem_flags, enqueue_copy #@UnresolvedImport
import opencl as cl
import numpy as np
from maka.plot.line import LinePlot
from maka.cl_pipe import ComputationalPipe
from maka.util import bring_to_front, execute
from maka.plot_widget import PlotWidget
from maka.canvas import Canvas
import clyther as cly
import clyther.runtime as clrt

n_vertices = 100

@cly.global_work_size(lambda a, scale: [a.size])
@cly.kernel
def generate_sin(a, scale=1):
    
    gid = clrt.get_global_id(0)
    n = clrt.get_global_size(0)
    r = gid / c_float(n)
    
    a[gid].x = gid
    a[gid].y = clrt.native_sin(r) * scale;

def plot_on_canvas(canvas):

    gl_context = canvas.parent().gl_context
    cl_context = canvas.parent().cl_context

    data1 = cl.gl.empty_gl(cl_context, [n_vertices], cly.types.float2)
    data2 = cl.gl.empty_gl(cl_context, [n_vertices], cly.types.float2)
    
    plot1 = LinePlot(data1, color='red', name="Plot 1", parent=canvas)
    plot2 = LinePlot(data2, color='green', name="Plot 2", parent=canvas)
    
    generate_sin_kernel = generate_sin.compile(cl_context, a=cl.global_memory('(2)f'), scale=c_float)

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin_kernel, plot1.vtx_array, 1.1)
    plot1.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot1)

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin_kernel, plot2.vtx_array, 0.6)
    plot2.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot2)


def main(args):
    app = QtGui.QApplication(args)
    
    f = QtOpenGL.QGLFormat.defaultFormat()

    f.setSampleBuffers(True)
    QtOpenGL.QGLFormat.setDefaultFormat(f)
    
    plot_widget = PlotWidget(name='My Plots') 
    
    canvas = Canvas(plot_widget, name='P1')
    
    plot_widget.add_canvas(canvas)
    
    plot_on_canvas(canvas)
    
    settings = QtCore.QSettings("Enthought", "line_plot")
    
    main = QMainWindow()
    
    main.resize(640, 480)
    
    w = QWidget()
    layout = QVBoxLayout()
    w.setLayout(layout)
    slider = QSlider(w)
    layout.addWidget(slider)
    slider.setOrientation(QtCore.Qt.Horizontal)
    slider.setMinimum(0)
    slider.setMaximum(100)

    layout.addWidget(plot_widget)
    
    main.setCentralWidget(w)
    
    menu_bar = QMenuBar()
    
    view_menu = QMenu("View")
    view_menu.addAction(plot_widget.full_screen_action)
    menu_bar.addMenu(view_menu)
    main.setMenuBar(menu_bar)
    
    
    app.setStyleSheet("""
    PlotWidget {
        font : Helvetica;
        font-size : 24px;
        color : white;
    }
    Canvas {
        background : white;
    }
    
    LinePlot#Plot1 {
        color : white;
    } 
    """)

    main.restoreState(settings.value('window_state'))
    main.restoreGeometry(settings.value('window_geom'))
    plot_widget.restoreState(settings)
    
    main.show()
    
    bring_to_front()
    execute(app, epic_fail=True)

    settings.setValue('window_state', main.saveState())
    settings.setValue('window_geom', main.saveGeometry())
    
    plot_widget.saveState(settings)
    
    print 'settings.fileName', settings.fileName()
if __name__ == '__main__':
    main(sys.argv)
    
    
        
