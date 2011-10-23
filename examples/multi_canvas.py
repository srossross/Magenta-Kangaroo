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
from maka.canvas import Canvas

n_vertices = 100

src = """

__kernel void generate_sin(__global float2* a, float scale)
{
    int id = get_global_id(0);
    int n = get_global_size(0);
    float r = (float)id / (float)n;
    float x = r * 16.0f * 3.1415f;
    
    a[id].x = r * 2.0f - 1.0f;
    a[id].y = (r * 2.0f - 1.0f) + native_sin(x) * scale;
}
"""

def plot_on_canvas(canvas):

    gl_context = canvas.parent().gl_context
    cl_context = canvas.parent().cl_context

    plot1 = LinePlot(gl_context, cl_context, n_vertices, color=QColor(255, 0, 0), name="Plot 1")
    plot2 = LinePlot(gl_context, cl_context, n_vertices, color=QColor(0, 200, 50), name="Plot 2")
    
    generate_sin = Program(cl_context, src).build().generate_sin

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin, plot1.vtx_array.cl_buffer, np.float32(1.1))
    plot1.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot1)

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin, plot2.vtx_array.cl_buffer, np.float32(0.6))
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
    
#    plot.add_canvas(Canvas(plot, name='Yellow', background_color=QColor(255, 255, 0)))
#    plot.add_canvas(Canvas(plot, name='Magenta', background_color=QColor(255, 0, 255)))
#    plot.add_canvas(Canvas(plot, name='Green', background_color=QColor(0, 255, 0)))
#    plot.add_canvas(Canvas(plot, name='Blue', background_color=QColor(0, 0, 255)))

    plot_widget.resize(640, 480)

    plot_widget.show()

    bring_to_front()
    
    execute(app, epic_fail=True)

    
if __name__ == '__main__':
    main(sys.argv)
    
    
        
