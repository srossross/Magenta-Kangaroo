'''
Created on Oct 19, 2011

@author: sean
'''


import sys
from PySide import QtCore, QtGui, QtOpenGL
from PySide.QtCore import Qt
from PySide.QtGui import QColor, QMainWindow, QMenu, QMenuBar, QWidget, QSlider, QVBoxLayout

from pyopencl import Program, Buffer, mem_flags, enqueue_copy #@UnresolvedImport
import numpy as np
from maka.plot.line import LinePlot
from maka.cl_pipe import ComputationalPipe
from maka.util import bring_to_front, execute
from maka.plot_widget import PlotWidget
from maka.canvas import Canvas
from maka.image.implot import ImagePlot, Interp
from maka.image.color_map import ColorMap, COLORMAPS
from maka.scene import Scene


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

def get_data():
    import PIL.Image #@UnresolvedImport
    
    im = PIL.Image.open('lena.bmp')
    ix, iy = im.size[0], im.size[1]
    image = im.tostring('raw', 'RGB')
    
    a = np.frombuffer(image, dtype=np.uint8)
    a.resize(512, 512, 3)
    #
    image = np.zeros([512, 512, 4], dtype=np.uint8)
    image[:, :, :3] = a
    image[:, :, 3] = 128
    return np.array(image[:, :, :3].sum(-1), dtype=np.float32)

def create_image_canvas(plot):
    
    canvas = Canvas(parent=plot, aspect=1)

    gl_context = plot.gl_context
    cl_context = plot.cl_context

    data = get_data()
    
    shape = list(data.shape)
    
    print 'shape', shape

    implot = ImagePlot(gl_context, cl_context, shape, name='Lena', share=False, interp=Interp.NEAREST)

    cl_data = Buffer(cl_context, mem_flags.READ_WRITE, data.nbytes)


    pipe_segment = ColorMap(gl_context, cl_context, COLORMAPS['gray'],
                            cl_data, implot.texture.cl_image,
                            shape, clim=(np.float32(data.min()), np.float32(data.max())))
    
    enqueue_copy(implot.queue, cl_data, data)

    implot.queue.finish()

    implot.color_map = pipe_segment

    implot.process()

    canvas.add_plot(implot)

    return canvas

def plot_on_canvas(canvas):

    gl_context = canvas.parent().gl_context
    cl_context = canvas.parent().cl_context

    plot1 = LinePlot(gl_context, cl_context, n_vertices, color=QColor(255, 0, 0), name="Plot1", parent=canvas)
    plot2 = LinePlot(gl_context, cl_context, n_vertices, color=QColor(0, 200, 50), name="Plot2", parent=canvas)
    
    generate_sin = Program(cl_context, src).build().generate_sin

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin, plot1.vtx_array.cl_buffer, np.float32(1.1))
    plot1.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot1)

    pipe_segment = ComputationalPipe(gl_context, cl_context, (n_vertices,), None, generate_sin, plot2.vtx_array.cl_buffer, np.float32(0.6))
    plot2.add_pipe_segment(pipe_segment)
    canvas.add_plot(plot2)


def create_3dScene(plot_widget):
    scene = Scene(plot_widget, '3D', background_color=Qt.darkGray)
    return scene

def main(args):
    app = QtGui.QApplication(args)
    
    

    f = QtOpenGL.QGLFormat.defaultFormat()

    f.setSampleBuffers(True)
    QtOpenGL.QGLFormat.setDefaultFormat(f)
    
    plot_widget = PlotWidget(name='My Plots') 
    
    canvas = Canvas(plot_widget, name='P1')
    
    image_canvas = create_image_canvas(plot_widget)
    
    scene = create_3dScene(plot_widget)
    
    plot_widget.add_canvas(canvas)
    plot_widget.add_canvas(image_canvas)
    plot_widget.add_canvas(scene)
    
    busy_canvas = Canvas(plot_widget, name='Busy Working', start_busy=True)
    plot_widget.add_canvas(busy_canvas)
    
    plot_on_canvas(canvas)
    
    settings = QtCore.QSettings("Enthought", "multi_canvas")
#    settings = QtCore.QSettings("plot.ini", QtCore.QSettings.IniFormat)
    
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
    
    
        
