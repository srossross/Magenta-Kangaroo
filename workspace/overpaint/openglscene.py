'''
***************************************************************************
**
** Copyright (C) 2008 Nokia Corporation and/or its subsidiary(-ies).
** Contact: Qt Software Information (qt-info@nokia.com)
**
** This file is part of the documentation of Qt. It was originally
** published as part of Qt Quarterly.
**
** Commercial Usage
** Licensees holding valid Qt Commercial licenses may use this file in
** accordance with the Qt Commercial License Agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and Nokia.
**
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License versions 2.0 or 3.0 as published by the Free
** Software Foundation and appearing in the file LICENSE.GPL included in
** the packaging of this file.  Please review the following information
** to ensure GNU General Public Licensing requirements will be met:
** http://www.fsf.org/licensing/licenses/info/GPLv2.html and
** http://www.gnu.org/copyleft/gpl.html.  In addition, as a special
** exception, Nokia gives you certain additional rights. These rights
** are described in the Nokia Qt GPL Exception version 1.3, included in
** the file GPL_EXCEPTION.txt in this package.
**
** Qt for Windows(R) Licensees
** As a special exception, Nokia, as the sole copyright holder for Qt
** Designer, grants users of the Qt/Eclipse Integration plug-in the
** right for the Qt/Eclipse Integration to link to functionality
** provided by Qt Designer and its related libraries.
**
** If you are unsure which license is appropriate for your use, please
** contact the sales department at qt-sales@nokia.com.
**
***************************************************************************
'''

#include "openglscene.h"
#include "model.h"

#include <QtGui>
#include <QtOpenGL>

#ifndef GL_MULTISAMPLE
#define GL_MULTISAMPLE  0x809D
#endif

from PySide.QtCore import *
from PySide.QtGui import *

from OpenGL.GL import *
from OpenGL.GLU import *

from model import Model
class OpenGLScene2(QGraphicsScene):
    
    def createDialog(self, windowTitle):
        
#        dialog = QDialog(None)
        dialog = QWidget()
#        dialog = QDialog(None, Qt.CustomizeWindowHint | Qt.WindowTitleHint)
    
        dialog.setWindowOpacity(0.8)
        dialog.setWindowTitle(windowTitle)
        dialog.setLayout(QVBoxLayout())
    
        return dialog
    
    def __init__(self):
        super(OpenGLScene2, self).__init__()

        controls = self.createDialog("Controls")
        
#        self.m_modelButton = QPushButton("Load model")
#        controls.layout().addWidget(self.m_modelButton)
    
        wireframe = QCheckBox("Render as wireframe")
        controls.layout().addWidget(wireframe)
    
        normals = QCheckBox("Display normals vectors")
        controls.layout().addWidget(normals)

        colorButton = QPushButton("Choose model color")
        controls.layout().addWidget(colorButton)
    
        backgroundButton = QPushButton("Choose background color")
        controls.layout().addWidget(backgroundButton)

        self.addWidget(controls)
    
    def drawBackground(self, painter, rect):
        print "drawBackground"

class OpenGLScene(QGraphicsScene):
#    
#    OpenGLScene()
#
#    void drawBackground(QPainter *painter, const QRectF &rect)
#
#public slots:
#    void enableWireframe(bool enabled)
#    void enableNormals(bool enabled)
#    void setModelColor()
#    void setBackgroundColor()
#    void loadModel()
#    void loadModel(const QString &filePath)
#    void modelLoaded()
#
#protected:
#    void mousePressEvent(QGraphicsSceneMouseEvent *event)
#    void mouseReleaseEvent(QGraphicsSceneMouseEvent *event)
#    void mouseMoveEvent(QGraphicsSceneMouseEvent *event)
#    void wheelEvent(QGraphicsSceneWheelEvent * wheelEvent)
#
#private:
#    QDialog *createDialog(const QString &windowTitle) const
#
#    void setModel(Model *model)
#
#    bool m_wireframeEnabled
#    bool m_normalsEnabled
#
#    QColor m_modelColor
#    QColor m_backgroundColor
#
#    Model *m_model
#
#    QTime m_time
#    int m_lastTime
#    int m_mouseEventTime
#
#    float m_distance
#    Point3d m_rotation
#    Point3d m_angularMomentum
#    Point3d m_accumulatedMomentum
#
#    QLabel *m_labels[4]
#    QWidget *m_modelButton
#
#    QGraphicsRectItem *m_lightItem


    def createDialog(self, windowTitle):
        
        dialog = QDialog(None, Qt.CustomizeWindowHint | Qt.WindowTitleHint)
    
        dialog.setWindowOpacity(0.8)
        dialog.setWindowTitle(windowTitle)
        dialog.setLayout(QVBoxLayout())
    
        return dialog
    
    def __init__(self):
        
        super(OpenGLScene, self).__init__()
        
        self.m_time = QTimer()
        self.m_wireframeEnabled = False
        self.m_normalsEnabled = False
        self.m_modelColor = QColor(153, 255, 0)
        self.m_backgroundColor = QColor(0, 170, 255)
        self.m_model = 0
        self.m_lastTime = 0
        self.m_distance = 1.4
        self.m_angularMomentum = 0, 40, 0

        controls = self.createDialog("Controls")

        self.m_modelButton = QPushButton("Load model")
        self.m_modelButton.clicked.connect(self.loadModel)

        controls.layout().addWidget(self.m_modelButton)
    
        wireframe = QCheckBox("Render as wireframe")
        wireframe.toggled.connect(self.enableWireframe)
        controls.layout().addWidget(wireframe)
    
        normals = QCheckBox("Display normals vectors")
#        connect(normals, SIGNAL(toggled(bool)), this, SLOT(enableNormals(bool)))
        controls.layout().addWidget(normals)

        colorButton = QPushButton("Choose model color")
#        connect(colorButton, SIGNAL(clicked()), this, SLOT(setModelColor()))
        controls.layout().addWidget(colorButton)
    
        backgroundButton = QPushButton("Choose background color")
#        connect(backgroundButton, SIGNAL(clicked()), this, SLOT(setBackgroundColor()))
        controls.layout().addWidget(backgroundButton)
    
        statistics = self.createDialog("Model info")
#        statistics.layout().setMargin(20)

        self.m_labels = []
        for i in range(4):
            label = QLabel()
            self.m_labels.append(label)
            statistics.layout().addWidget(label)

        instructions = self.createDialog("Instructions")
        instructions.layout().addWidget(QLabel("Use mouse wheel to zoom model, and click and drag to rotate model"))
        instructions.layout().addWidget(QLabel("Move the sun around to change the light position"))
    
        self.addWidget(instructions)
        self.addWidget(controls)
        self.addWidget(statistics)
    
        pos = QPointF(10, 10)
        for item in self.items():
            item.setFlag(QGraphicsItem.ItemIsMovable)
            item.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
    
            rect = item.boundingRect()
            item.setPos(pos.x() - rect.x(), pos.y() - rect.y())
            pos += QPointF(0, 10 + rect.height())
    
        gradient = QRadialGradient(40, 40, 40, 40, 40)
        gradient.setColorAt(0.2, Qt.yellow)
        gradient.setColorAt(1, Qt.transparent)
    
        self.m_lightItem = m_lightItem = QGraphicsRectItem(0, 0, 80, 80)
        m_lightItem.setPen(Qt.NoPen)
        m_lightItem.setBrush(gradient)
        m_lightItem.setFlag(QGraphicsItem.ItemIsMovable)
        m_lightItem.setPos(800, 200)
        self.addItem(m_lightItem)
    
        self.loadModel("qt.obj")
        self.m_time.start()

    def drawBackground_(self, painter, rect):

        if (painter.paintEngine().type() not in [QPaintEngine.OpenGL, QPaintEngine.OpenGL2]):
            qWarning("OpenGLScene: drawBackground needs a QGLWidget to be set as viewport on the graphics view")
            return
        
        glClearColor(self.m_backgroundColor.redF(), self.m_backgroundColor.greenF(), self.m_backgroundColor.blueF(), 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
        if (not self.m_model):
            return

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(70, self.width() / self.height(), 0.01, 1000)
    
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
    
        pos = (self.m_lightItem.x() - self.width() / 2, self.height() / 2 - self.m_lightItem.y(), 512, 0)
        glLightfv(GL_LIGHT0, GL_POSITION, pos)
        glColor4f(self.m_modelColor.redF(), self.m_modelColor.greenF(), self.m_modelColor.blueF(), 1.0)
    
        delta = self.m_time.elapsed() - self.m_lastTime
        self.m_rotation += self.m_angularMomentum * (delta / 1000.0)
        self.m_lastTime += delta
    
        glTranslatef(0, 0, -self.m_distance)
        glRotatef(self.m_rotation.x, 1, 0, 0)
        glRotatef(self.m_rotation.y, 0, 1, 0)
        glRotatef(self.m_rotation.z, 0, 0, 1)
    
        glEnable(GL_MULTISAMPLE)
        self.m_model.render(self.m_wireframeEnabled, self.m_normalsEnabled)
        glDisable(GL_MULTISAMPLE)
    
        glPopMatrix()
    
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
    
#        QTimer::singleShot(20, this, SLOT(update()))
#
    @Slot(str)
    def loadModel(self, filePath=None):
        return Model(filePath)

#
#void OpenGLScene::loadModel()
#{
#    loadModel(QFileDialog::getOpenFileName(0, tr("Choose model"), QString(), QLatin1String("*.obj")))
#}
#
#void OpenGLScene::loadModel(const QString &filePath)
#{
#    if (filePath.isEmpty())
#        return
#
#    m_modelButton.setEnabled(false)
#    QApplication::setOverrideCursor(Qt::BusyCursor)
##ifndef QT_NO_CONCURRENT
#    m_modelLoader.setFuture(QtConcurrent::run(::loadModel, filePath))
##else
#    setModel(::loadModel(filePath))
#    modelLoaded()
##endif
#}
#
#void OpenGLScene::modelLoaded()
#{
##ifndef QT_NO_CONCURRENT
#    setModel(m_modelLoader.result())
##endif
#    m_modelButton.setEnabled(true)
#    QApplication::restoreOverrideCursor()
#}
#
#void OpenGLScene::setModel(Model *model)
#{
#    delete m_model
#    m_model = model
#
#    m_labels[0].setText(tr("File: %0").arg(m_model.fileName()))
#    m_labels[1].setText(tr("Points: %0").arg(m_model.points()))
#    m_labels[2].setText(tr("Edges: %0").arg(m_model.edges()))
#    m_labels[3].setText(tr("Faces: %0").arg(m_model.faces()))
#
#    update()
#}

    @Slot(bool)
    def enableWireframe(self, enabled):
        self.m_wireframeEnabled = enabled
        self.update()

#void OpenGLScene::enableNormals(bool enabled)
#{
#    m_normalsEnabled = enabled
#    update()
#}
#
#void OpenGLScene::setModelColor()
#{
#    const QColor color = QColorDialog::getColor(m_modelColor)
#    if (color.isValid()) {
#        m_modelColor = color
#        update()
#    }
#}
#
#void OpenGLScene::setBackgroundColor()
#{
#    const QColor color = QColorDialog::getColor(m_backgroundColor)
#    if (color.isValid()) {
#        m_backgroundColor = color
#        update()
#    }
#}
#
#void OpenGLScene::mouseMoveEvent(QGraphicsSceneMouseEvent *event)
#{
#    QGraphicsScene::mouseMoveEvent(event)
#    if (event.isAccepted())
#        return
#    if (event.buttons() & Qt::LeftButton) {
#        const QPointF delta = event.scenePos() - event.lastScenePos()
#        const Point3d angularImpulse = Point3d(delta.y(), delta.x(), 0) * 0.1
#
#        m_rotation += angularImpulse
#        m_accumulatedMomentum += angularImpulse
#
#        event.accept()
#        update()
#    }
#}
#
#void OpenGLScene::mousePressEvent(QGraphicsSceneMouseEvent *event)
#{
#    QGraphicsScene::mousePressEvent(event)
#    if (event.isAccepted())
#        return
#
#    m_mouseEventTime = m_time.elapsed()
#    m_angularMomentum = m_accumulatedMomentum = Point3d()
#    event.accept()
#}
#
#void OpenGLScene::mouseReleaseEvent(QGraphicsSceneMouseEvent *event)
#{
#    QGraphicsScene::mouseReleaseEvent(event)
#    if (event.isAccepted())
#        return
#
#    const int delta = m_time.elapsed() - m_mouseEventTime
#    m_angularMomentum = m_accumulatedMomentum * (1000.0 / qMax(1, delta))
#    event.accept()
#    update()
#}
#
#void OpenGLScene::wheelEvent(QGraphicsSceneWheelEvent *event)
#{
#    QGraphicsScene::wheelEvent(event)
#    if (event.isAccepted())
#        return
#
#    m_distance *= qPow(1.2, -event.delta() / 120)
#    event.accept()
#    update()
#}
