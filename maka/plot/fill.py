'''
Created on Nov 5, 2011

@author: sean
'''

from PySide import QtCore
from PySide.QtGui import QAction, QMenu, QColor, QColorDialog
from PySide.QtGui import QWidget, QPalette, QWhatsThis, QApplication, QCursor
from OpenGL import GL
from OpenGL.raw.GL.VERSION.GL_1_5 import glBufferData as rawGlBufferData
import pyopencl as cl #@UnresolvedImport
from contextlib import contextmanager
from maka.util import acquire_gl_objects, client_state, SAction, gl_enable, \
    gl_disable


class FillPlot(QWidget):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
