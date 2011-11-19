
from PySide.QtGui import *
from PySide.QtCore import *
from PySide.QtOpenGL import *
from OpenGL.GL import *
import contextlib
from PySide import QtGui
from maka.util import execute, bring_to_front

class Widget(QGLWidget):
    
    def __init__(self, parent=None, title="This is the Title"):
        QGLWidget.__init__(self, QGLFormat(QGL.SampleBuffers), parent)
        
        self.title = title
        self._perc = 0 #Visible
        
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
#        self.progress.set
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)
        self.progress.setValue(0)
        
        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.update)
#        self.timer.start(1000 // 30)
        
        self.margin = 50
        
        
    def _get_perc(self):
        return self._perc

    def _set_perc(self, value):
        self._perc = value
        self.update()
    
    perc = Property(float, _get_perc, _set_perc)
    
    def initializeGL(self):
        pass
        
    def resizeGL(self, w, h):
        self.setupViewport(w, h)
    
    def paintGL(self):
        
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        
    def setupViewport(self, w, h):
        
        glViewport(0, 0, w, h)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
    
    
    def draw_top(self, painter):
        
        size = self.margin
        
        poly = QPolygonF([QPointF(0, 0), QPointF(size, 0), QPointF(size, size)])
        left_tri = QPainterPath()
        left_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(self.width(), 0), QPointF(self.width() - size, 0), QPointF(self.width() - size, size)])
        right_tri = QPainterPath()
        right_tri.addPolygon(poly)
        
        painter.save()

        painter.translate(QPointF(0, -(size + 1) * self.perc))

        bg = self.background_color
        
        painter.fillPath(left_tri, QBrush(bg))
        painter.fillPath(right_tri, QBrush(bg))
        
        #Bottom        
        painter.fillRect(QRect(size, 0, self.width() - size * 2, size), bg)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(size, size, self.width() - size, size) #Horozontal
        
        font = QFont(u'Monaco')
        font.setPixelSize(size // 2)
        painter.setFont(font)
        
        fm = QFontMetricsF(font)
        font_height = fm.height()
        font_width = fm.width(self.title)
        
        title = self.title
        title_base = self.title
        
        
        while font_width > (self.width() - size * 2):
            title_base = title_base[:-2]
            title = title_base + '...'
            font_width = fm.width(title + '...')
            
        topLeft = QPointF(size + ((self.width() - size * 2) - font_width) / 2.0, (size + font_height) / 2.0)
        
        painter.drawText(topLeft, title)
        painter.restore()
        
    @property
    def background_color(self):
#        return self.palette().color(self.backgroundRole())
        return self.palette().color(self.backgroundRole()).lighter(102)
    
    def draw_right_axis(self, painter):

        size = self.margin
        
        poly = QPolygonF([QPointF(self.width(), self.height()), QPointF(self.width(), self.height() - size), QPointF(self.width() - size, self.height() - size)])
        bottom_tri = QPainterPath()
        bottom_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(self.width(), 0), QPointF(self.width(), size), QPointF(self.width() - size, size)])
        top_tri = QPainterPath()
        top_tri.addPolygon(poly)

        painter.save()
        
        painter.translate(QPointF((size + 1) * self.perc, 0))
        
        bg = self.background_color
        
        #Left        
        painter.fillRect(QRect(self.width() - size, size, size, self.height() - size * 2), bg)
        painter.fillPath(top_tri, QBrush(bg))
        painter.fillPath(bottom_tri, QBrush(bg))
        
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(self.width() - size, size, self.width() - size, self.height() - size) #Vertical
        
        painter.restore()
        
    def draw_left_axis(self, painter):

        size = self.margin
        
        poly = QPolygonF([QPointF(0, self.height()), QPointF(0, self.height() - size), QPointF(size, self.height() - size)])
        bottom_tri = QPainterPath()
        bottom_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(0, 0), QPointF(0, size), QPointF(size, size)])
        top_tri = QPainterPath()
        top_tri.addPolygon(poly)

        painter.save()
        
        painter.translate(QPointF(-(size + 1) * self.perc, 0))
        
        bg = self.background_color
        
        #Left        
        painter.fillRect(QRect(0, size, size, self.height() - size * 2), bg)
        painter.fillPath(top_tri, QBrush(bg))
        painter.fillPath(bottom_tri, QBrush(bg))
        
        pen = QPen(Qt.black)
        pen.setWidthF(0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(self.height() - size, size, -20):
            painter.drawLine(size, i, size - 10, i)

        
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(size, size, size, self.height() - size) #Vertical
#        painter.drawLine(0, self.height(), size, self.height() - size) #Diag
        
        painter.restore()
        #=======================================================================
        # 
        #=======================================================================
#        painter.save()
#        
#        grad_left = QLinearGradient(QPointF(0, 0), QPointF(5, 0))
#        grad_left.setColorAt(0, QColor(0, 0, 0, 90))
#        grad_left.setColorAt(1, QColor(0, 0, 0, 0))
#
#        painter.fillRect(QRect(0, size, size, self.height() - size * 2), grad_left)
#        painter.fillPath(bottom_tri, QBrush(grad_left))
#        painter.fillPath(top_tri, QBrush(grad_left))
#
#        painter.restore()
        
    def draw_bottom_axis(self, painter):
        
        size = self.margin
        
        poly = QPolygonF([QPointF(0, self.height()), QPointF(size, self.height()), QPointF(size, self.height() - size)])
        left_tri = QPainterPath()
        left_tri.addPolygon(poly)
        
        poly = QPolygonF([QPointF(self.width(), self.height()), QPointF(self.width() - size, self.height()), QPointF(self.width() - size, self.height() - size)])
        right_tri = QPainterPath()
        right_tri.addPolygon(poly)
        
        painter.save()

        painter.translate(QPointF(0, (size + 1) * self.perc))

        bg = self.background_color
        
        painter.fillPath(left_tri, QBrush(bg))
        painter.fillPath(right_tri, QBrush(bg))
        
        #Bottom        
        painter.fillRect(QRect(size, self.height() - size, self.width() - size * 2, size), bg)

        pen = QPen(Qt.white)
        pen.setWidthF(2.6)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(size, self.width() - size, 20):
            painter.drawLine(i, self.height() - size, i, self.height() - size + 10)

        pen = QPen(Qt.black)
        pen.setWidthF(0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        for i in range(size, self.width() - size, 20):
            painter.drawLine(i, self.height() - size, i , self.height() - size + 10)

        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        
        painter.drawLine(size, self.height() - size, self.width() - size, self.height() - size) #Horozontal
#        painter.drawLine(0, self.height(), size, self.height() - size) #Diag
        
        painter.restore()
        #=======================================================================
        # 
        #=======================================================================
#        painter.save()
#        
#        grad_x = QLinearGradient(QPointF(0, self.height() - 5), QPointF(0, self.height()))
#        grad_x.setColorAt(1, QColor(0, 0, 0, 90))
#        grad_x.setColorAt(0, QColor(0, 0, 0, 0))
#
#        painter.fillRect(QRect(size, self.height() - size, self.width() - size * 2, size), grad_x)
#        painter.fillPath(left_tri, QBrush(grad_x))
#        painter.fillPath(right_tri, QBrush(grad_x))
#        
#        painter.restore()
        

    def draw_axes(self, painter):
        self.draw_left_axis(painter)
        self.draw_right_axis(painter)
        self.draw_top(painter)
        self.draw_bottom_axis(painter)

    def paint_qt(self, painter):
        
        self.draw_axes(painter)
                
        painter.save()
        
        
        rf = QWidget.RenderFlags(QWidget.DrawChildren)
        
        x = (self.width() - self.progress.width()) / 2
        y = (self.height() - self.progress.height()) / 2
        
        self.progress.render(painter, QPoint(x, y), QRegion(self.progress.rect()), rf)
        
        rect = QRectF(self.rect())
        rect.adjust(self.perc - 1, self.perc - 1,
                    1 - self.perc, 1 - self.perc)
        painter.drawRect(rect)
        
        painter.restore()
    
    @contextlib.contextmanager
    def _painter(self):
         
        painter = QPainter()
        painter.begin(self)
        
        try:
            yield painter
        finally:
            painter.end()
        
    def paintEvent(self, event):
        
        self.makeCurrent()
        
        with self._painter() as painter:
            painter.setRenderHint(QPainter.Antialiasing)
            
            glPushAttrib(GL_ALL_ATTRIB_BITS)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
    
            self.setupViewport(self.width(), self.height())
            
            self.paintGL()
            
            glPopAttrib()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
    
            glDisable(GL_CULL_FACE) ### not required if begin() also does it
            
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
    
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            
            self.paint_qt(painter)
            
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            
    def enterEvent(self, event):
        if self._perc != 0:
            self.perc_anim = anim = QPropertyAnimation(self, 'perc', self)
            anim.setEasingCurve(QEasingCurve.OutQuart)
            anim.setDuration(600)
            anim.setStartValue(self.perc)
            anim.setEndValue(0)
            anim.start()

    def leaveEvent(self, event):
        if self._perc != 1:
            self.perc_anim = anim = QPropertyAnimation(self, 'perc', self)
            anim.setEasingCurve(QEasingCurve.OutQuart)
            anim.setDuration(600)
            anim.setStartValue(self.perc)
            anim.setEndValue(1)
            anim.start()
            
app = QApplication([])

widget = QWidget()
widget.setLayout(QVBoxLayout())
slider = QSlider(Qt.Horizontal, widget)
glw = Widget()

widget.layout().addWidget(glw)
widget.layout().addWidget(slider)

widget.setWindowTitle("Paint")
widget.setMinimumSize(QSize(250, 250))
widget.show()

bring_to_front()
execute(app, epic_fail=True)
#app.exec_()
