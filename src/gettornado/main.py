import os

from lxml.html import fromstring
from lxml.etree import XMLSyntaxError

from PyQt5 import QtCore
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QFileDialog,\
    QApplication, QMessageBox

from gettornado.http import QRequest
from gettornado.base.main import Ui_MainWindow
from gettornado.utils import secure_filename

WaitCursor = QtCore.Qt.WaitCursor
QStandardPaths = QtCore.QStandardPaths
pyqtSlot = QtCore.pyqtSlot


def parseDoc(doc):
    """Retrieve torrent data from html document"""
    results = []

    for tr in doc.cssselect("tr[id^=torrent_]"):
        torrentname = tr.cssselect("div.torrentname a.cellMainLink")
        if len(torrentname) == 0:
            continue

        torrentname = torrentname[0].text_content().strip()
        for a in tr.cssselect("a[href]"):
            href = a.attrib['href'].strip()
            if href.endswith('.torrent'):
                break

        item = (torrentname, href,
                tr.cssselect("td.nobr")[0].text_content(),
                tr.cssselect("td.green")[0].text_content(),
                tr.cssselect("td.red")[0].text_content())

        results.append(item)

    return results


class MainWindow(Ui_MainWindow, QMainWindow):

    selectedTorrent = None

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        self.resultList.setColumnWidth(1, 90)

        self.searchBtn.clicked.connect(self.searchTorrents)
        self.qText.returnPressed.connect(self.searchTorrents)
        self.downloadBtn.clicked.connect(self.download)
        self.resultList.itemActivated.connect(self.resultSelected)

    def resizeEvent(self, event):
        result = QMainWindow.resizeEvent(self, event)
        # set title column to resise dynamically
        self.resultList.setColumnWidth(0, self.size().width() - 127)
        return result

    def searchTorrents(self):
        q = self.qText.text().strip()
        if len(q) < 2:
            return

        # begin search
        request = QRequest('http://kat.cr/usearch/%s/' % q,
                           params={'field': 'seeders', 'sorter': 'desc'},
                           parent=self)
        request.finished.connect(self.onSearchDone(request))
        request.get()

        QApplication.setOverrideCursor(QCursor(WaitCursor))

    def onSearchDone(self, request):

        @pyqtSlot()
        def _onSearchDone():
            QApplication.restoreOverrideCursor()

            self.resultList.clear()
            self.resultList.setRowCount(0)
            self.selectedTorrent = None

            # parse doc
            try:
                doc = fromstring(request.data.decode('utf-8'))
            except XMLSyntaxError:
                self.results = []
                return

            self.results = parseDoc(doc)

            # setup result list
            if self.results == []:
                self.resultList.insertRow(0)
                self.resultList.setItem(0, 0, QTableWidgetItem('No results found'))
                return

            self.resultList.setRowCount(len(self.results))
            for id_, result in enumerate(self.results):
                self.resultList.setItem(id_, 0, QTableWidgetItem(result[0]))
                self.resultList.setItem(id_, 1, QTableWidgetItem(result[2]))

        return _onSearchDone

    def resultSelected(self, item):
        item_id = self.resultList.indexFromItem(item).row()
        result = self.results[item_id]
        self.selectedTorrent = result[:2]

    def download(self):
        if self.selectedTorrent is None:
            return

        rq = QRequest(self.selectedTorrent[1], parent=self)
        rq.finished.connect(self.onDownloaded(rq))
        rq.get()

        QApplication.setOverrideCursor(QCursor(WaitCursor))

    def onDownloaded(self, request):

        @pyqtSlot()
        def _onDownloaded():
            QApplication.restoreOverrideCursor()

            defaultDir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
            path = QFileDialog.getExistingDirectory(parent=self,
                                                    caption='Choose location...',
                                                    directory=defaultDir)
            if path == '':
                return

            path = os.path.join(path,
                                secure_filename(self.selectedTorrent[0]) + '.torrent')
            with open(path, 'wb') as f:
                f.write(request.data)

            msg = QMessageBox()
            msg.setWindowTitle(self.windowTitle() + ':')
            msg.setText('The torrent has been saved successfuly.')
            msg.exec_()

        return _onDownloaded
