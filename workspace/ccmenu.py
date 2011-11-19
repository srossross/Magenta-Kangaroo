
from PySide.QtCore import * 
from PySide.QtGui import *

class QColorMapAction(QWidgetAction):
    
    def __init__(self, parent, pixmap, text):
        QWidgetAction.__init__(self, parent)

        self.pixmap = QPixmap(pixmap)
        self.container = container = QWidget()
        self.img_label = img = QLabel(container)
        self.text_label = ltext = QLabel(text)
        
        img.setMargin(5)
        img.setPixmap(self.pixmap)
        
        layout = QHBoxLayout(container)
        container.setLayout(layout)
        layout.addWidget(img)
        layout.addWidget(ltext)
        self.setDefaultWidget(img)
        
        img.setStyleSheet('QWidget { background: white; }\nQWidget:hover { background: lightblue; color: white; }\n')

class MyWidget(QWidget):
    
    def __init__(self):
        QWidget.__init__(self)
        
        self.jet_action = QColorMapAction(self, 'jet.png', 'jet')
        self.hsv_action = QColorMapAction(self, 'hsv.png', 'hsv')
        custom = QAction('Custom ...', self)

        self.main_menu = main_menu = QMenu("Main")
        self.menu = menu = QMenu("color map")
        main_menu.addMenu(menu)
        
        
        menu.addAction(self.jet_action)
        menu.addAction(self.hsv_action)
        menu.addSeparator()
        menu.addAction(custom)
        
    def contextMenuEvent(self, event):
        
        p = event.globalPos()
        self.main_menu.exec_(p)
        
        event.accept()


    
def main():
    app = QApplication([])
    
    widget = MyWidget()
    widget.show()
    app.exec_()

if __name__ == '__main__':
    main() 
