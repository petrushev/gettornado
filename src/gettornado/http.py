import zlib
from urllib import urlencode
from StringIO import StringIO
from gzip import GzipFile

from PyQt4.Qt import QObject, QUrl, QHttp
from PyQt4 import QtCore

def decodeData(data, headers):
    encoding = headers.get('Content-Encoding', None)

    if encoding=='deflate':
        return StringIO(zlib.decompress(data)).read()

    elif encoding=='x-gzip' or encoding=='gzip':
        return GzipFile('', 'rb', 9, StringIO(data)).read()

    return data


class QRequest(QHttp):

    finished = QtCore.pyqtSignal(QObject)

    def __init__(self, url, params=None, parent=None):
        QHttp.__init__(self, parent=parent)

        self.data = None
        self.headers = {}
        self.history = []
        self.statusCode = None

        self.params = params

        if params is not None:
            url = url + "?" + urlencode(params)
        self.url = url
        self.qUrl = QUrl(url)

        self.setHost(self.qUrl.host(), self.qUrl.port(80))

        self.responseHeaderReceived.connect(self._onHeaderReceived)
        self.done.connect(self._onDone)

    def _onHeaderReceived(self, headers):
        self.statusCode = headers.statusCode()
        self.headers = dict((str(k), str(v))
                            for k, v in headers.values())

    def get(self):
        QHttp.get(self, self.qUrl.path())

    def _onDone(self, has_error):
        if self.statusCode == 301 or self.statusCode == 302:
            return self._redirected()

        rqData = self.readAll()
        self.data = decodeData(str(rqData), self.headers)

        self.finished.emit(self)

    def _redirected(self):
        self.history.append(self.url)
        self.url = self.headers['Location']

        qNewUrl = QUrl(self.url)
        if qNewUrl.host() == '':
            qNewUrl.setHost(self.qUrl.host())
            qNewUrl.setScheme(self.qUrl.scheme())

        self.setHost(qNewUrl.host(), qNewUrl.port(80))
        self.qUrl = qNewUrl
        self.get()
