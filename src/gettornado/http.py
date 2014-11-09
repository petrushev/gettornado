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


class QRequest(QObject):

    finished = QtCore.pyqtSignal(QObject)

    data = None
    headers = {}
    history = []
    statusCode = None

    def __init__(self, url, data=None):
        QObject.__init__(self)

        self.data = data

        if data is not None:
            url = url + "?" + urlencode(data)
        self.url = url
        self.qUrl = QUrl(url)

        self.rq = QHttp()
        self.rq.setHost(self.qUrl.host(), self.qUrl.port(80))

        self.rq.responseHeaderReceived.connect(self._onHeaderReceived)
        self.rq.done.connect(self._onDone)

    def _onHeaderReceived(self, headers):
        self.statusCode = headers.statusCode()
        self.headers = dict((str(k), str(v))
                            for k, v in headers.values())

    def get(self):
        self.rq.get(self.qUrl.path())

    def _onDone(self, has_error):
        if self.statusCode == 301 or self.statusCode == 302:
            return self._redirected()

        rqData = self.rq.readAll()
        rqData = decodeData(str(rqData), self.headers)
        self.data = rqData.decode('utf-8')

        self.finished.emit(self)

    def _redirected(self):
        self.history.append(self.url)
        self.url = self.headers['Location']

        qNewUrl = QUrl(self.url)
        if qNewUrl.host() == '':
            qNewUrl.setHost(self.qUrl.host())
            qNewUrl.setScheme(self.qUrl.scheme())

        self.rq.setHost(qNewUrl.host(), qNewUrl.port(80))
        self.qUrl = qNewUrl
        self.get()
