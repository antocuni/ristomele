import pytest
import textwrap
from datetime import datetime
from ristomele import model
from server.testing.test_server import example_order_data

@pytest.fixture
def example_order(example_order_data):
    return model.Order.from_dict(example_order_data)

def test_Restaurant():
    tables = [
        dict(name='11', waiter='pippo'),
        dict(name='12', waiter='pluto')
    ]
    r = model.Restaurant(2, 3, tables)
    assert len(r.tables) == 6
    names = [t.name for t in r.tables]
    assert names == ['11', '21', '31',
                     '12', '22', '32']
    t11 = r.tables[0]
    t12 = r.tables[3]
    assert t11.waiter == 'pippo'
    assert t12.waiter == 'pluto'

def test_Order_from_dict(example_order, example_order_data):
    o = example_order
    data = example_order_data
    assert o.id is None
    assert o.date is None
    assert o.table.name == data['table']
    assert o.table.waiter == data['waiter']
    assert o.customer == data['customer']
    assert o.notes == data['notes']
    for o_item, d_item in zip(o.menu, data['menu']):
        assert o_item.kind == d_item['kind']
        assert o_item.name == d_item['name']
        assert o_item.count == d_item['count']
        assert o_item.price == d_item['price']

def test_Order_get_total(example_order):
    assert example_order.get_total() == 10 + 2*15

def test_Order_as_dict(example_order):
    d = example_order.as_dict()
    assert d == dict(
        table='11',
        cashier='gian',
        waiter='anto',
        customer='pippo',
        notes='my notes',
        menu=[
            dict(kind='separator', name='First Dishes', count=0, price=0),
            dict(kind='item',      name='Pasta', count=1, price=10),
            dict(kind='separator', name='Desserts', count=0, price=0),
            dict(kind='item',      name='Tiramisu', count=2, price=15),
            ])

def test_Menu_as_textural_recepit(example_order):
    example_order.menu.extend([
        model.MenuItem(name='Gelato', count=0, price=1),
        model.MenuItem(name='Very long item description', count=1, price=1),
        model.MenuItem(name='Even longer and longer item description', count=1, price=1)
    ])
    txt = example_order.as_textual_receipt(width=32)
    assert txt == textwrap.dedent("""
        Numero ordine:  
        Tavolo: 11 [anto]
        Cassiere: gian
        Cliente: pippo

        Pasta                  x1  10.00
        Tiramisu               x2  30.00
        Very long item description 
                               x1   1.00
        Even longer and longer item desc
                               x1   1.00

                           TOTALE: 42.00

        RICEVUTA NON FISCALE
        """).strip()
    lines = txt.splitlines()
    for line in lines:
        assert len(line) <= 32
    #
    example_order.id = 1
    example_order.date = datetime(2015, 8, 15, 20, 0, 0)
    txt = example_order.as_textual_receipt(width=32)
    exp = textwrap.dedent("""
        Numero ordine: 1 [15/08 20:00]
        Tavolo: 11 [anto]
        Cassiere: gian
        Cliente: pippo
        """).strip()
    assert txt.startswith(exp)
