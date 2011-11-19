

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtOpenGL import *
from OpenGL.GL import *

class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(QGLFormat(QGL.SampleBuffers), parent)
        
        midnight = QTime(0, 0, 0);
        qsrand(midnight.secsTo(QTime.currentTime()));
    
        self.logo = 0
        self.xRot = 0
        self.yRot = 0
        self.zRot = 0
    
        self.qtGreen = QColor.fromCmykF(0.40, 0.0, 1.0, 0.0)
        self.qtPurple = QColor.fromCmykF(0.39, 0.39, 0.0, 0.0)
    
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.animationTimer.timeout.connect(self.animate)
        self.animationTimer.start(25)
    
        self.setAutoFillBackground(False);
        self.setMinimumSize(200, 200);
        self.setWindowTitle("Overpainting a Scene")

#static void qNormalizeAngle(int &angle)
#{
#    while (angle < 0)
#        angle += 360 * 16;
#    while (angle > 360 * 16)
#        angle -= 360 * 16;
#}
#
#void GLWidget::setXRotation(int angle)
#{
#    qNormalizeAngle(angle);
#    if (angle != xRot)
#        xRot = angle;
#}
#
#void GLWidget::setYRotation(int angle)
#{
#    qNormalizeAngle(angle);
#    if (angle != yRot)
#        yRot = angle;
#}
#
#void GLWidget::setZRotation(int angle)
#{
#    qNormalizeAngle(angle);
#    if (angle != zRot)
#        zRot = angle;
#}
#
#//! [2]
#void GLWidget::initializeGL()
#{
#    glEnable(GL_MULTISAMPLE);
#
#    logo = new QtLogo(this);
#    logo->setColor(qtGreen.dark());
#}
#//! [2]
#
#void GLWidget::mousePressEvent(QMouseEvent *event)
#{
#    lastPos = event->pos();
#}
#
#void GLWidget::mouseMoveEvent(QMouseEvent *event)
#{
#    int dx = event->x() - lastPos.x();
#    int dy = event->y() - lastPos.y();
#
#    if (event->buttons() & Qt::LeftButton) {
#        setXRotation(xRot + 8 * dy);
#        setYRotation(yRot + 8 * dx);
#    } else if (event->buttons() & Qt::RightButton) {
#        setXRotation(xRot + 8 * dy);
#        setZRotation(zRot + 8 * dx);
#    }
#    lastPos = event->pos();
#}
#
    def paintEvent(self, event):
        self.makeCurrent()
        glMatrixMode(GL_MODELVIEW);
        glPushMatrix();
        self.qglClearColor(self.qtPurple.dark());
        glShadeModel(GL_SMOOTH);
        glEnable(GL_DEPTH_TEST);
        glEnable(GL_CULL_FACE);
        glEnable(GL_LIGHTING);
        glEnable(GL_LIGHT0);
        glEnable(GL_MULTISAMPLE);
        
        lightPosition = [ 0.5, 5.0, 7.0, 1.0 ]
        glLightfv(GL_LIGHT0, GL_POSITION, lightPosition);
    
        self.setupViewport(self.width(), self.height());

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        glLoadIdentity();
        glTranslatef(0.0, 0.0, -10.0);
        glRotatef(self.xRot / 16.0, 1.0, 0.0, 0.0);
        glRotatef(self.yRot / 16.0, 0.0, 1.0, 0.0);
        glRotatef(self.zRot / 16.0, 0.0, 0.0, 1.0);
    
#        self.logo.draw();

        glShadeModel(GL_FLAT);
        glDisable(GL_CULL_FACE);
        glDisable(GL_DEPTH_TEST);
        glDisable(GL_LIGHTING);
    
        glMatrixMode(GL_MODELVIEW);
        glPopMatrix();

        painter = QPainter(self);
        painter.setRenderHint(QPainter.Antialiasing)
        
        for bubble in self.bubbles:
            if bubble.rect().intersects(event.rect()):
                bubble.drawBubble(painter)
                
        self.drawInstructions(painter)
        painter.end();

    def resizeGL(self, width, height):
        self.setupViewport(width, height);
            
    def showEvent(self, event):
        self.createBubbles(20 - len(self.bubbles));

    def sizeHint(self):
        return QSize(400, 400)

    def createBubbles(self, number):
        for i in range(number):
            position = QPointF(0, 0)
            radius = 1
            velocity = QPointF(0, 1)
    
            self.bubbles.append(Bubble(position, radius, velocity))

    def animate(self):
        for bubble in self.bubbles:
            bubble.move(self.rect())
        self.update()

    def setupViewport(self, width, height):
        
        side = min(width, height)
        glViewport((width - side) / 2, (height - side) / 2, side, side)
    
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-0.5, +0.5, -0.5, 0.5, 4.0, 15.0)
        glMatrixMode(GL_MODELVIEW)
        
    def drawInstructions(self, painter):
        
        text = "Click and drag with the left mouse button to rotate the Qt logo."
        metrics = QFontMetrics(self.font());
        border = max(4, metrics.leading())
    
        rect = metrics.boundingRect(0, 0, self.width() - 2 * border, int(self.height() * 0.125), Qt.AlignCenter | Qt.TextWordWrap, text)
        
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        painter.fillRect(QRect(0, 0, self.width(), rect.height() + 2 * border),
                         QColor(0, 0, 0, 127))
        
        painter.setPen(Qt.white)
        painter.fillRect(QRect(0, 0, self.width(), rect.height() + 2 * border), QColor(0, 0, 0, 127))
        painter.drawText((self.width() - rect.width()) / 2, border, rect.width(), rect.height(),
                          Qt.AlignCenter | Qt.TextWordWrap, text)
