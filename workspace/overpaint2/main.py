
from PySide.QtCore import *
from PySide.QtGui import *

from glwidget import GLWidget

def main():
    app = QApplication([]);
    window = GLWidget();
    window.show();
    return app.exec_();

if __name__ == '__main__':
    main()