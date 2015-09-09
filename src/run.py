import sys

from PyQt5.Qt import QApplication

from gettornado.main import MainWindow


def main():
    app = QApplication(sys.argv)

    ui = MainWindow()
    ui.setupUi()
    ui.show()

    sys.exit(app.exec_())

if __name__=='__main__':
    main()
