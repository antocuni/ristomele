import pytest
from cStringIO import StringIO
import requests
from ristomele.gui import util
from ristomele.gui.error import ErrorMessage

class FakeApp(object):
    timeout = 3

    def get_timeout(self):
        return self.timeout

class FakeRequests(object):

    def _build_response(self, status, content):
        resp = requests.Response()
        resp.status_code = status
        resp.raw = StringIO(content)
        return resp

    def get(self, url, timeout=None, *args):
        resp = requests.Response()
        if url == '/error':
            return self._build_response(404, '')
        elif url == '/timeout':
            return self._build_response(200, 'timeout: %d' % timeout)
        else:
            return self._build_response(200, 'fake requests')


class TestSmartRequests(object):

    @pytest.fixture
    def fakerequests(self, monkeypatch):
        fake = FakeRequests()
        monkeypatch.setattr(util, 'requests', fake)
        return fake

    def test_FakeRequests(self, fakerequests):
        resp = fakerequests.get('/foo')
        assert resp.status_code == 200
        assert resp.text == 'fake requests'
        #
        resp = fakerequests.get('/error')
        assert resp.status_code == 404
        pytest.raises(requests.RequestException, "resp.raise_for_status()")

    def test_do_smart_request(self, fakerequests):
        smart = util.SmartRequests(FakeApp())
        resp = smart.get('/foo')
        assert resp.status_code == 200
        assert resp.text == 'fake requests'

    def test_do_smart_request_error(self, fakerequests):
        smart = util.SmartRequests(FakeApp())
        with pytest.raises(ErrorMessage) as exc:
            smart.get('/error', error="Cannot fetch the page")
        assert exc.value.message == "Cannot fetch the page"

    def test_timeout(self, fakerequests):
        app = FakeApp()
        smart = util.SmartRequests(app)
        resp = smart.get('/timeout')
        assert resp.status_code == 200
        assert resp.text == 'timeout: 3'
        #
        app.timeout = 5
        resp = smart.get('/timeout')
        assert resp.status_code == 200
        assert resp.text == 'timeout: 5'
        #
        resp = smart.get('/timeout', timeout=42)
        assert resp.status_code == 200
        assert resp.text == 'timeout: 42'
