'''
Created on Jul 21, 2011

@author: sean
'''

from PySide import QtCore

class ComputationalPipe(QtCore.QObject):

    def __init__(self, gl_context, cl_context, global_size, local_size, kernel, *args):
        super(ComputationalPipe, self).__init__()
        self.gl_context = gl_context
        self.cl_context = cl_context

        self.global_size = global_size
        self.local_size = local_size
        self.kernel = kernel
        self.kernel_args = list(args)

    changed = QtCore.Signal(QtCore.QObject)

    @QtCore.Slot()
    def update(self):
        self.changed.emit(self)

    def compute(self, queue):
        self.kernel(queue, *self.kernel_args, global_work_size=self.global_size, local_work_size=self.local_size)

