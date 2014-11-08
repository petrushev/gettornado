import sys

from PyQt4.Qt import QApplication

from gettornado.main import Ui_MainWindow

if __name__=='__main__':

    app = QApplication(sys.argv)
    #app.focusChanged.connect(onFocusChange)

    ui = Ui_MainWindow()
    ui.setupUi(ui)
    ui.show()

    sys.exit(app.exec_())
