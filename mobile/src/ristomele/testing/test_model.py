import pytest
import textwrap
from datetime import datetime
from ristomele import model

@pytest.fixture
def example_order():
    return model.Order(
        table=model.Table(name='11', waiter='anto'),
        customer='pippo',
        notes='my notes',
        menu=[
            model.MenuItem(kind='separator', name='First Dishes'),
            model.MenuItem(name='Pasta', count=1, price=10),
            model.MenuItem(kind='separator', name='Desserts'),
            model.MenuItem(name='Tiramisu', count=2, price=15),
            ])

def test_Restaurant():
    r = model.Restaurant(2, 3)
    assert len(r.tables) == 6
    names = [t.name for t in r.tables]
    assert names == ['11', '21', '31',
                     '12', '22', '32']

def test_Order_as_dict(example_order):
    d = example_order.as_dict()
    assert d == dict(
        table='11',
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
        Tavolo: 11
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
        Tavolo: 11
        Cliente: pippo
        """).strip()
    assert txt.startswith(exp)
