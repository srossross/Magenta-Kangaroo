'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtGui
from maka.canvas import MakaCanvasWidget
from maka.image.color_map import ColorMap
from maka.image.implot import ImagePlot, Interp
from maka.util import bring_to_front, execute
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

    widget = MakaCanvasWidget(aspect=1)

    gl_context = widget.gl_context
    cl_context = widget.cl_context

    data = np.array(image[:, :, :3].sum(-1), dtype=np.float32)
    shape = list(data.shape)
    print shape

    plat, = cl.get_platforms()
    ati, intel = plat.get_devices()
    print intel

    implot = ImagePlot(widget.context(), cl_context, shape, name='Lena', share=False, interp=Interp.NEAREST)

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

#    sys.exit(app.exec_())
    execute(app, epic_fail=True)


if __name__ == '__main__':
    main(sys.argv)
