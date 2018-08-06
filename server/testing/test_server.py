import os
import pytest
import json
from server.app import create_app
from server import model

@pytest.fixture
def spooldir(tmpdir):
    return tmpdir.join('spooldir').ensure(dir=True)

@pytest.fixture
def client(tmpdir, spooldir):
    dbfile = tmpdir.join('db-test.sqlite')
    app = create_app(dbfile)
    app.config['TESTING'] = True
    app.config['SPOOLDIR'] = spooldir
    client = app.test_client()
    with app.app_context():
        yield client


class TestModel(object):

    def test_Order_as_dict(self):
        menu = json.dumps(dict(a=1, b=2))
        order = model.Order(menu=menu)
        order_dict = order.as_dict()
        assert order_dict == {
            'id': None,
            'menu': {
                'a': 1,
                'b': 2,
                }
            }

    def test_Order_as_dict_error(self):
        menu = 'this is invalid json'
        order = model.Order(menu=menu)
        order_dict = order.as_dict()
        assert order_dict == {
            'id': None,
            'menu': None,
            }


class TestServer(object):

    def test_new_order(self, client):
        menu = dict(table=dict(),
                    items=[])
        resp = client.post('/order/', json=menu)
        assert resp.json == {
            'result': 'OK',
            'order': {
                'id': 1,
                'menu': menu
                }
            }

    def test_new_order_spooldir(self, client, spooldir):
        menu = dict(table=dict(),
                    items=[])
        assert spooldir.listdir() == []
        resp = client.post('/order/', json=menu)
        assert spooldir.listdir() == [
            spooldir.join('order_000001.pdf')
            ]
