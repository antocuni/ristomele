import pytest
import textwrap
from ristomele import model

@pytest.fixture
def example_menu():
    return model.Menu(
        table=model.Table(name='11', waiter='anto'),
        customer='pippo',
        notes='my notes',
        items=[
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

def test_Menu_as_dict(example_menu):
    d = example_menu.as_dict()
    assert d == dict(
        table=dict(
            name='11',
            waiter='anto',
            busy=False),
        customer='pippo',
        notes='my notes',
        items=[
            dict(kind='separator', name='First Dishes', count=0, price=0),
            dict(kind='item',      name='Pasta', count=1, price=10),
            dict(kind='separator', name='Desserts', count=0, price=0),
            dict(kind='item',      name='Tiramisu', count=2, price=15),
            ])

def test_Menu_as_textural_recepit(example_menu):
    example_menu.items.extend([
        model.MenuItem(name='Gelato', count=0, price=1),
        model.MenuItem(name='Very long item description', count=1, price=1),
        model.MenuItem(name='Even longer and longer item description', count=1, price=1)
    ])
    txt = example_menu.as_textual_receipt(width=32)
    assert txt == textwrap.dedent("""
        RICEVUTA NON FISCALE
        Numero ordine: xxx
        Tavolo: 11
        Cliente: pippo

        Pasta                  x1  10.00
        Tiramisu               x2  30.00
        Very long item description 
                               x1   1.00
        Even longer and longer item desc
                               x1   1.00

                           TOTALE: 42.00
        """).strip()
    lines = txt.splitlines()
    for line in lines:
        assert len(line) <= 32
