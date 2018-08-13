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

@pytest.fixture
def example_order_data():
    return dict(
        table='11',
        cashier='gian',
        waiter='anto',
        customer='pippo',
        notes='my notes',
        menu=[
            dict(kind='separator', name='First Dishes', count=0, price=0, is_drink=False),
            dict(kind='item',      name='Pasta', count=1, price=10, is_drink=False),
            dict(kind='separator', name='Desserts', count=0, price=0, is_drink=False),
            dict(kind='item',      name='Tiramisu', count=2, price=15, is_drink=False),
            dict(kind='item',      name='Birra', count=1, price=3, is_drink=True),
        ])

class TestModel(object):

    def test_Order_from_dict(self, example_order_data):
        myorder = model.Order.from_dict(example_order_data)
        assert myorder.table == '11'
        assert myorder.waiter == 'anto'
        assert myorder.customer == 'pippo'
        assert myorder.notes == 'my notes'
        assert json.loads(myorder.menu) == example_order_data['menu']

    def test_textual_id(self, example_order_data):
        with freeze_time('2018-08-15 20:00'):
            myorder = model.Order.from_dict(example_order_data)
            assert myorder.textual_id() == ' [15/08 20:00]'
            myorder.id = 42
            assert myorder.textual_id() == '42 [15/08 20:00]'

    def test_Order_as_dict(self, example_order_data):
        with freeze_time('2018-08-15 20:00'):
            myorder = model.Order.from_dict(example_order_data)
            mydict = myorder.as_dict()
            id = mydict.pop('id')
            date = mydict.pop('date')
            assert id is None
            assert date == '2018-08-15 20:00:00'
            assert mydict == example_order_data

    def test_Order_as_dict_error(self, example_order_data):
        order = model.Order.from_dict(example_order_data)
        order.menu = 'this is invalid json'
        order_dict = order.as_dict()
        assert order_dict['menu'] is None


class TestServer(object):

    def dir_is_empty(self, d):
        return d.check(exists=False) or d.listdir() == []

    def test_new_order(self, client, example_order_data):
        ex = example_order_data
        with freeze_time('2018-08-15 20:00'):
            resp = client.post('/orders/', json=ex)
            assert resp.json == {
                'result': 'OK',
                'order': {
                    'id': 1,
                    'date': '2018-08-15 20:00:00',
                    'cashier': ex['cashier'],
                    'table': ex['table'],
                    'waiter': ex['waiter'],
                    'customer': ex['customer'],
                    'notes': ex['notes'],
                    'menu': ex['menu'],
                    }
                }
            #
            myorder = model.Order.query.get(1)
            assert myorder.date == datetime(2018, 8, 15, 20, 0, 0)
            assert myorder.customer == ex['customer']

    def test_new_order_spooldir(self, client, spooldir, example_order_data):
        orders_dir = spooldir.join('orders')
        drinks_dir = spooldir.join('drinks')
        html = orders_dir.join('order_000001.html')
        txt = drinks_dir.join('order_000001.txt')
        #
        assert self.dir_is_empty(orders_dir)
        assert self.dir_is_empty(drinks_dir)
        resp = client.post('/orders/', json=example_order_data)
        assert orders_dir.listdir() == [html]
        assert drinks_dir.listdir() == [txt]
        #
        html.remove()
        resp = client.post('/orders/1/print/')
        assert resp.status_code == 200
        assert orders_dir.listdir() == [html]
        #
        txt.remove()
        resp = client.post('/orders/1/print_drinks/')
        assert resp.status_code == 200
        assert drinks_dir.listdir() == [txt]

    def test_print_drinks_only_if_any(self, client, spooldir, example_order_data):
        # remove the only drink the the menu
        beer = example_order_data['menu'].pop()
        assert beer['is_drink']
        #
        # check that we don't print the drink receipt
        drinks_dir = spooldir.join('drinks')
        resp = client.post('/orders/', json=example_order_data)
        assert self.dir_is_empty(drinks_dir)

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

    def test_tables(self, client):
        resp = client.put('/tables/11/', json=dict(waiter='anto'))
        assert resp.status_code == 200
        client.put('/tables/12/', json=dict(waiter='pippo'))
        assert resp.status_code == 200
        #
        resp = client.get('/tables/')
        assert resp.status_code == 200
        assert resp.json == [
            dict(name='11', waiter='anto'),
            dict(name='12', waiter='pippo')
            ]
        #
        # now, try to update one table
        resp = client.put('/tables/11/', json=dict(waiter='pluto'))
        assert resp.status_code == 200
        resp = client.get('/tables/')
        assert resp.status_code == 200
        assert resp.json == [
            dict(name='11', waiter='pluto'),
            dict(name='12', waiter='pippo')
            ]

    def test_update_many_tables(self, client):
        client.put('/tables/11/', json=dict(waiter='anto'))
        new_tables = [
            dict(name='12', waiter='pippo'),
            dict(name='13', waiter='pluto')
            ]
        resp = client.put('/tables/', json=new_tables)
        assert resp.status_code == 200
        all_tables = model.Table.query.all()
        items = [(t.name, t.waiter) for t in all_tables]
        assert items == [
            ('11', 'anto'),
            ('12', 'pippo'),
            ('13', 'pluto'),
            ]
