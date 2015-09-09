import zlib
from urllib import urlencode
from StringIO import StringIO
from gzip import GzipFile

from PyQt5.QtCore import pyqtSignal, QObject, QUrl, pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest


def decodeData(data, headers):
    encoding = headers.get('Content-Encoding', None)

    if encoding=='deflate':
        f = StringIO(zlib.decompress(data))

    elif encoding=='x-gzip' or encoding=='gzip':
        f = GzipFile('', 'rb', 9, StringIO(data))

    else:
        return data

    # data in object file handler
    data = f.read()
    f.close()

    return data


class QRequest(QObject):

    manager = QNetworkAccessManager()
    finished = pyqtSignal()

    def __init__(self, url, params=None, parent=None):
        QObject.__init__(self, parent=parent)

        self.data = ''
        self.headers = {}
        self.statusCode = None

        self.params = params

        if params is not None:
            url = url + "?" + urlencode(params)
        self.qUrl = QUrl(url)

        self.request = QNetworkRequest(self.qUrl)

    def get(self):
        self.response = self.manager.get(self.request)
        self.response.readyRead.connect(self._onDataReady)
        self.response.finished.connect(self._onFinished)

    @pyqtSlot()
    def _onDataReady(self):
        self.data = self.data + self.response.readAll().data()

    @pyqtSlot()
    def _onFinished(self):
        self.finished.emit()
