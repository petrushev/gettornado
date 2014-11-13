import os

from lxml.html import fromstring
from lxml.etree import XMLSyntaxError

from PyQt4 import QtCore
from PyQt4.QtGui import QMainWindow
from PyQt4.Qt import QTableWidgetItem, QFileDialog, QString, QApplication, QCursor,\
    QMessageBox, QDesktopServices

from gettornado.http import QRequest
from gettornado.base.main import Ui_MainWindow
from gettornado.utils import secure_filename

WaitCursor = QtCore.Qt.WaitCursor


def parseDoc(doc):
    results = []

    for tr in doc.cssselect("tr[id^=torrent_]"):
        torrentname = tr.cssselect("div.torrentname a.cellMainLink")
        torrentname = torrentname[0].text_content().strip()
        for a in tr.cssselect("a[href][class]"):
            if 'idownload' in a.attrib['class']:
                href = a.attrib['href'].strip()
                if href!='#':
                    if not href.startswith('http'):
                        href = 'http://'+href.lstrip('/ ')
                    break
        item = (torrentname, href,
                tr.cssselect("td.nobr")[0].text_content(),
                tr.cssselect("td.green")[0].text_content(),
                tr.cssselect("td.red")[0].text_content())

        results.append(item)

    return results


class MainWindow(Ui_MainWindow, QMainWindow):

    headers = {}
    selectedTorrent = None

    def setupUi(self):
        Ui_MainWindow.setupUi(self, self)
        self.resultList.setColumnWidth(0, 510)
        self.resultList.setColumnWidth(1, 90)

        self.searchBtn.clicked.connect(self.searchTorrents)
        self.qText.returnPressed.connect(self.searchTorrents)
        self.downloadBtn.clicked.connect(self.download)
        self.resultList.itemActivated.connect(self.resultSelected)

    def searchTorrents(self):
        q = str(self.qText.text().toUtf8()).decode('utf-8').strip()
        if len(q) < 2:
            return

        request = QRequest('http://kickass.to/usearch/%s/' % q,
                      params={'field': 'seeders', 'sorter': 'desc'},
                      parent=self)
        request.finished.connect(self.onSearchDone)
        request.get()

        QApplication.setOverrideCursor(QCursor(WaitCursor))

    def onSearchDone(self, request):
        QApplication.restoreOverrideCursor()

        self.resultList.clear()
        self.resultList.setRowCount(0)
        self.selectedTorrent = None

        # parse doc
        try:
            doc = fromstring(request.data)
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


    def resultSelected(self, item):
        item_id = self.resultList.indexFromItem(item).row()
        result = self.results[item_id]
        self.selectedTorrent = result[:2]

    def download(self):
        if self.selectedTorrent is None:
            return

        rq = QRequest(self.selectedTorrent[1], parent=self)
        rq.finished.connect(self.onDownloaded)
        rq.get()

        QApplication.setOverrideCursor(QCursor(WaitCursor))

    def onDownloaded(self, request):
        QApplication.restoreOverrideCursor()

        defaultDir = QDesktopServices.storageLocation(QDesktopServices.DesktopLocation)
        path = QFileDialog.getExistingDirectory(parent=self,
                                                caption=QString('Choose location...'),
                                                directory=defaultDir)

        if path == '':
            return
        path = os.path.join(str(path.toUtf8()),
                            secure_filename(self.selectedTorrent[0])+'.torrent')
        with open(path, 'wb') as f:
            f.write(request.data)

        msg = QMessageBox()
        msg.setWindowTitle(self.windowTitle()+':')
        msg.setText('The torrent has been saved successfuly.')
        msg.exec_()
