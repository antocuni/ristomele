import os
from datetime import datetime
import pytest
import json
from freezegun import freeze_time
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
        with freeze_time('2018-08-15 20:00'):
            menu = dict(table=dict(),
                        items=[])
            resp = client.post('/orders/', json=menu)
            assert resp.json == {
                'result': 'OK',
                'order': {
                    'id': 1,
                    'menu': menu
                    }
                }
            #
            myorder = model.Order.query.get(1)
            assert myorder.menu == json.dumps(menu)
            assert myorder.date == datetime(2018, 8, 15, 20, 0, 0)
            assert myorder.textual_id() == '1 [15/08 20:00]'

    def test_new_order_spooldir(self, client, spooldir):
        menu = dict(table=dict(),
                    items=[])
        assert spooldir.listdir() == []
        resp = client.post('/orders/', json=menu)
        assert spooldir.listdir() == [
            spooldir.join('order_000001.pdf')
            ]

    def test_all_orders(self, client):
        o1 = model.Order(menu='101')
        o2 = model.Order(menu='102')
        o3 = model.Order(menu='103')
        model.db.session.add_all([o1, o2, o3])
        model.db.session.commit()
        resp = client.get('/orders/')
        assert resp.json == [
            {'id': 3, 'menu': 103},
            {'id': 2, 'menu': 102},
            {'id': 1, 'menu': 101},
            ]
