'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtGui
from maka.cgl_plot_widget import CGLPlotWidget
from maka.color_map import ColorMap
from maka.image_plot import ImagePlot, Interp
from mydemo import bring_to_front
from pyopencl.tools import get_gl_sharing_context_properties
import PIL.Image
import numpy as np
import pyopencl as cl
import sys

im = PIL.Image.open('lena.bmp')

ix, iy = im.size[0], im.size[1]
image = im.tostring('raw', 'RGB')

a = np.frombuffer(image, dtype=np.uint8)
a.resize(512, 512, 3)
#
image = np.zeros([512, 512, 4], dtype=np.uint8)
image[:, :, :3] = a
image[:, :, 3] = 128

def main(argv):

    app = QtGui.QApplication(sys.argv)

    widget = CGLPlotWidget(aspect=1)

    gl_context = widget.context()
    gl_context.makeCurrent()


    data = np.array(image[:, :, :3].sum(-1), dtype=np.float32)
    shape = list(data.shape)
    print shape

    plat, = cl.get_platforms()
    ati, intel = plat.get_devices()
    print intel

    cl_context = cl.Context(devices=[intel])

    implot = ImagePlot(widget.context(), cl_context, shape, share=False, interp=Interp.NEAREST)

    cl_data = cl.Buffer(cl_context, cl.mem_flags.READ_WRITE, data.nbytes)

    import pylab
    cdict = pylab.cm.jet._segmentdata
    pipe_segment = ColorMap(gl_context, cl_context, cdict,
                                     cl_data, implot.texture.cl_image,
                                     shape, clim=(np.float32(data.min()), np.float32(data.max()))
                                     )

    cl.enqueue_copy(implot.queue, cl_data, data)

    implot.queue.finish()

    implot._pipe_segments.append(pipe_segment)

    implot.process()

    widget.add_plot(implot)

    widget.show()
    widget.resize(480, 640,)

    bring_to_front()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main(sys.argv)
