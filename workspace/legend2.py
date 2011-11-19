from PySide.QtGui import *
from PySide.QtCore import *


app = QApplication([])

#widget = QWidget()
#widget.setLayout(QVBoxLayout())
#
#box = QGroupBox("Legend", widget)
#box.setLayout(QVBoxLayout())
#l1 = QLabel("This is a label")
#l2 = QLabel("WKAKA WAKA")
#
#box.layout().addWidget(l1)
#box.layout().addWidget(l2)
#widget.layout().addWidget(box)
#
#pal = widget.palette()
#color = pal.color(widget.backgroundRole())
#
#pal.setColor(widget.backgroundRole(), Qt.transparent)
#widget.setPalette(pal)
#
#print color
#
#pal = box.palette()
#pal.setColor(box.backgroundRole(), color)
#box.setPalette(pal)

#widget = QTabWidget()
#widget.setDocumentMode(False)
#
#w2 = QWidget()
#w2.setLayout(QVBoxLayout())
#l1 = QLabel("Label")
#w2.layout().addWidget(l1)
#widget.addTab(w2, "W2")
#
#
#pal = w2.palette()
#color = pal.color(w2.backgroundRole())
#pal.setColor(w2.backgroundRole(), Qt.transparent)
#w2.setPalette(pal)
widget = QWidget()
widget.setStyleSheet('QWidget {margin:0;}')
layout = QVBoxLayout(widget)
widget.setLayout(layout)
layout.addWidget(QLabel('Data 1'))
layout.addWidget(QLabel('More Data'))


widget.show()

size = widget.size()

pixmap = QPixmap(size)
#pixmap.fill(Qt.blue)
pixmap.fill(Qt.transparent)

print pixmap.hasAlpha() 
print pixmap.hasAlphaChannel() 

painter = QPainter(pixmap)
painter.setRenderHint(painter.Antialiasing, True)
painter.setRenderHint(painter.TextAntialiasing, True)

painter.setBrush(Qt.white)
painter.setPen(Qt.NoPen)
painter.drawRoundedRect(1, 1, size.width() - 2, size.height() - 2, 10.0, 10.0)

painter.setBrush(Qt.NoBrush)

alpha = 60
x = 0
y = 0
w = size.width()
h = size.height()

n = 5
da = alpha / n
for i in range(n):
    pen = QPen(QColor(0, 0, 0, alpha))
    pen.setWidthF(2)
    painter.setPen(pen)
    
    painter.drawRoundedRect(x, y, w, h, 10.0, 10.0)

    alpha -= da
    x += 1; w -= 2
    y += 1; h -= 2

widget.render(painter, QPoint(0, 0), QRegion(widget.rect()), QWidget.RenderFlags(QWidget.DrawChildren))


#painter.begin(pixmap)
painter.end()
pixmap.save('pix.png', 'PNG')

#
#
#app.exec_()
