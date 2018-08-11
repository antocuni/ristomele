import pytest
import requests
from ristomele.gui import util
from ristomele.gui.error import ErrorMessage

class FakeRequests(object):

    def get(self, url, *arg):
        resp = requests.Response()
        resp.status_code = 200
        resp.body = 'fake requests'
        if url == '/error':
            resp.status_code = 404
        return resp

class TestSmartRequests(object):

    @pytest.fixture
    def fakerequests(self, monkeypatch):
        fake = FakeRequests()
        monkeypatch.setattr(util, 'requests', fake)
        return fake

    def test_FakeRequests(self, fakerequests):
        resp = fakerequests.get('/foo')
        assert resp.status_code == 200
        assert resp.body == 'fake requests'
        #
        resp = fakerequests.get('/error')
        assert resp.status_code == 404
        assert resp.body == 'fake requests'
        pytest.raises(requests.RequestException, "resp.raise_for_status()")

    def test_do_smart_request(self, fakerequests):
        smart = util.SmartRequests()
        resp = smart.get('/foo')
        assert resp.status_code == 200
        assert resp.body == 'fake requests'

    def test_do_smart_request_error(self, fakerequests):
        smart = util.SmartRequests()
        with pytest.raises(ErrorMessage) as exc:
            smart.get('/error', error="Cannot fetch the page")
        assert exc.value.message == "Cannot fetch the page"
