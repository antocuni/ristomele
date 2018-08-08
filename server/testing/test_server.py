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

    EXAMPLE_DATA = dict(
        table='11',
        waiter='anto',
        customer='pippo',
        notes='my notes',
        menu=['one', 'two', 'three'],
    )

    def test_Order_from_dict(self):
        myorder = model.Order.from_dict(self.EXAMPLE_DATA)
        assert myorder.table == '11'
        assert myorder.waiter == 'anto'
        assert myorder.customer == 'pippo'
        assert myorder.notes == 'my notes'
        assert json.loads(myorder.menu) == ['one', 'two', 'three']

    def test_Order_as_dict(self):
        with freeze_time('2018-08-15 20:00'):
            myorder = model.Order.from_dict(self.EXAMPLE_DATA)
            mydict = myorder.as_dict()
            id = mydict.pop('id')
            date = mydict.pop('date')
            assert id is None
            assert date == '2018-08-15T20:00:00'
            assert mydict == self.EXAMPLE_DATA

    def test_Order_as_dict_error(self):
        order = model.Order.from_dict(self.EXAMPLE_DATA)
        order.menu = 'this is invalid json'
        order_dict = order.as_dict()
        assert order_dict['menu'] is None


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
                    'date': '2018-08-15T20:00:00',
                    'table': None,
                    'waiter': None,
                    'customer': None,
                    'notes': None,
                    'menu': menu,
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
        items = [(item['id'], item['menu']) for item in resp.json]
        assert items == [
            (3, 103),
            (2, 102),
            (1, 101)
            ]
