'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtGui
from maka.canvas import Canvas
from maka.image.color_map import ColorMap
from maka.image.implot import ImagePlot, Interp
from maka.util import bring_to_front, execute
import PIL.Image #@UnresolvedImport
import numpy as np
import pyopencl as cl #@UnresolvedImport
import sys
from maka.plot_widget import PlotWidget

def get_data():
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

    implot = ImagePlot(gl_context, cl_context, shape, name='Lena', share=False, interp=Interp.NEAREST)

    cl_data = cl.Buffer(cl_context, cl.mem_flags.READ_WRITE, data.nbytes)

    import pylab
#    cdict = pylab.cm.jet._segmentdata #@UndefinedVariable
    cdict = pylab.cm.gray._segmentdata #@UndefinedVariable
    pipe_segment = ColorMap(gl_context, cl_context, cdict,
                                     cl_data, implot.texture.cl_image,
                                     shape, clim=(np.float32(data.min()), np.float32(data.max())))
    
    cl.enqueue_copy(implot.queue, cl_data, data)

    implot.queue.finish()

    implot._pipe_segments.append(pipe_segment)

    implot.process()

    canvas.add_plot(implot)

    return canvas
    
def main(argv):

    app = QtGui.QApplication(sys.argv)
    
    widget = PlotWidget(name='Widget')
    
    canvas = create_image_canvas(widget)
    widget.add_canvas(canvas)


    widget.show()
    widget.resize(480, 640)

    bring_to_front()

#    sys.exit(app.exec_())
    execute(app, epic_fail=True)


if __name__ == '__main__':
    main(sys.argv)
