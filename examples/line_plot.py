#!/usr/bin/env python

"""PySide port of the opengl/samplebuffers example from Qt v4.x"""

import sys
from PySide import QtCore, QtGui, QtOpenGL
from pyopencl import Program 
import numpy as np
from maka.plot.line import LinePlot
from maka.canvas import MakaCanvasWidget
from maka.cl_pipe import ComputationalPipe
from maka.util import bring_to_front, execute

n_vertices = 100

src = """

__kernel void generate_sin(__global float2* a, float scale)
{
    int id = get_global_id(0);
    int n = get_global_size(0);
    float r = (float)id / (float)n;
    float x = r * 16.0f * 3.1415f;
    
    a[id].x = r * 2.0f - 1.0f;
    a[id].y = native_sin(x) * scale;
}
"""


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    f = QtOpenGL.QGLFormat.defaultFormat()

    f.setSampleBuffers(True)
    QtOpenGL.QGLFormat.setDefaultFormat(f)

    canvas = MakaCanvasWidget()

    gl_context = canvas.gl_context
    cl_context = canvas.cl_context

    plot1 = LinePlot(gl_context, cl_context, n_vertices, color=(1, 0, 0), name="Plot 1")
    plot2 = LinePlot(gl_context, cl_context, n_vertices, color=(0, .8, .2), name="Plot 2")
    
    generate_sin = Program(cl_context, src).build().generate_sin

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin, plot1.vtx_array.cl_buffer, np.float32(1.1))
    plot1.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot1)

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin, plot2.vtx_array.cl_buffer, np.float32(0.6))
    plot2.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot2)

    widget = QtGui.QWidget()
    widget_layout = QtGui.QVBoxLayout(widget)
    widget.setLayout(widget_layout)
    widget_layout.addWidget(canvas)

    slider = QtGui.QSlider(widget)

    def change_a(value):
        pipe_segment.kernel_args[1] = np.float32(float(value) / 100.0)
        pipe_segment.update()

    slider.valueChanged.connect(change_a)

    widget_layout.addWidget(slider)
    slider.setOrientation(QtCore.Qt.Horizontal)
    slider.setMinimum(0)
    slider.setMaximum(100)

    widget.resize(640, 480)

    widget.show()

    bring_to_front()
    
    execute(app, epic_fail=True)
#    sys.exit(app.exec_())

        
