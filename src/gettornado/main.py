import zlib
import gzip
from StringIO import StringIO

from lxml.html import fromstring
from lxml.etree import XMLSyntaxError

from PyQt4 import QtGui
from PyQt4.Qt import QHttp, QUrl, QTableWidgetItem, QFileDialog, QString

from gettornado.base.main import Ui_BaseMainWindow


def parseDoc(doc):
    results = []

    for tr in doc.cssselect("tr[id^=torrent_]"):
        torrentname = tr.cssselect("div.torrentname a.cellMainLink")[0].text_content().strip()
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

def parseHeaders(rawHeaders):
    return dict((str(k), str(v))
                for k, v in rawHeaders.values())


def decodeData(data, headers):
    if 'Content-Encoding' not in headers:
        return data

    encoding = headers['Content-Encoding']
    if encoding == 'deflate':
        return StringIO(zlib.decompress(data)).read()

    elif encoding == 'x-gzip' or encoding == 'gzip':
        return gzip.GzipFile('', 'rb', 9, StringIO(data)).read()

    return data


class Ui_MainWindow(Ui_BaseMainWindow, QtGui.QMainWindow):

    headers = {}
    selectedTorrent = None

    def setupUi(self, BaseMainWindow):
        Ui_BaseMainWindow.setupUi(self, BaseMainWindow)

        self.searchBtn.clicked.connect(self.searchTorrents)

        self.resultList.itemActivated.connect(self.resultSelected)
        self.resultList.setColumnWidth(0, 510)
        self.resultList.setColumnWidth(1, 90)

        self.downloadBtn.clicked.connect(self.download)

    def searchTorrents(self):
        q = self.qText.text()
        url = QUrl('http://kickass.to/usearch/'+q + '/')

        self.http = QHttp(self)

        @self.http.responseHeaderReceived.connect
        def onHeaderReceived(headers):
            self.headers = parseHeaders(headers)

        self.http.requestFinished.connect(self.onRequestFinished)
        self.http.setHost(url.host(), url.port(80))
        self.http.get(url.path())

    def onRequestFinished(self, request_id, has_error):
        if has_error:
            print 'error on finished' % request_id
            return

        rqData = decodeData(str(self.http.readAll()), self.headers)
        rqData = rqData.decode('utf-8')

        self.resultList.clear()
        self.resultList.setRowCount(0)
        self.selectedTorrent = None

        # parse doc
        try:
            doc = fromstring(rqData)
        except XMLSyntaxError:
            self.results = []
            return

        self.results = parseDoc(doc)

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
        self.selectedTorrent = result[1]

    def download(self):
        if self.selectedTorrent is None:
            return

        http = QHttp(self)
        url = QUrl(self.selectedTorrent)
        http.setHost(url.host(), url.port(80))
        http.get(url.path())

        headers = {}

        @http.responseHeaderReceived.connect
        def onHeaderReceived(_headers):
            headers.update(dict((unicode(k), unicode(v))
                                for k, v in _headers.values()))

        @http.requestFinished.connect
        def onRequestFinished(rq_id, error):
            rqData = decodeData(str(http.readAll()), headers)
            if len(rqData) == 0:
                return

            # save
            path = QFileDialog.getSaveFileName(parent=self, caption=QString('Choose location...'))
            path = str(path.toUtf8())
            if path == '':
                return

            with open(path, 'wb') as f:
                f.write(rqData)
