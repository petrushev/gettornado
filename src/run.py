import sys

from PyQt4.Qt import QApplication

from gettornado.main import MainWindow

if __name__=='__main__':

    app = QApplication(sys.argv)

    ui = MainWindow()
    ui.setupUi()
    ui.show()

    sys.exit(app.exec_())
