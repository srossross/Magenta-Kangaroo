#!/usr/bin/env python

"""PySide port of the opengl/samplebuffers example from Qt v4.x"""

import sys
from PySide import QtCore, QtGui, QtOpenGL
import pyopencl as cl #@UnresolvedImport
import numpy as np
from pyopencl.tools import get_gl_sharing_context_properties #@UnresolvedImport
from maka.line_plot import LinePlot
from maka.cgl_plot_widget import CGLPlotWidget
from maka.cl_pipe import ComputationalPipe

n_vertices = 10000

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


def bring_to_front():
    try:
        from appscript import Application
        Application('Python').activate()

    except ImportError:
        from subprocess import Popen
        import sys, os
        if sys.platform == 'darwin' and os.path.exists('/usr/bin/osascript'):
            Popen('/usr/bin/osascript -e \'tell application "Python"\nactivate\nend tell\'', shell=True)
    return


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    f = QtOpenGL.QGLFormat.defaultFormat()

    f.setSampleBuffers(True)
    QtOpenGL.QGLFormat.setDefaultFormat(f)

    canvas = CGLPlotWidget()

    gl_context = canvas.context()
    gl_context.makeCurrent()
    cl_context = cl.Context(properties=get_gl_sharing_context_properties(), devices=[])

    plot1 = LinePlot(gl_context, cl_context,
                     n_vertices, scale=0.5, color=(1, 0, 0))

    plot2 = LinePlot(gl_context, cl_context,
                     n_vertices, scale=1.1, color=(0, .8, .2))


    generate_sin = cl.Program(cl_context, src).build().generate_sin

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None,
                                     generate_sin,
                                     plot1.vtx_array.cl_buffer, np.float32(1.1))

    plot1.add_pipe_segment(pipe_segment)

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None,
                                     generate_sin,
                                     plot2.vtx_array.cl_buffer, np.float32(0.6))

    plot2.add_pipe_segment(pipe_segment)

    plot1.process()
    plot2.process()
    
    canvas.add_plot(plot1)
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
    sys.exit(app.exec_())
