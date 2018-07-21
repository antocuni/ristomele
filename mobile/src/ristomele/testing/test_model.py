from ristomele import model

def test_Restaurant():
    r = model.Restaurant(2, 3)
    assert len(r.tables) == 6
    names = [t.name for t in r.tables]
    assert names == ['11', '21', '31',
                     '12', '22', '32']

def test_Menu_as_dict():
    table = model.Table(name='11', waiter='anto')
    menu = model.Menu(
        table=table,
        customer='pippo',
        notes='my notes',
        items=[
            model.MenuItem(name='item1', count=1, price=10),
            model.MenuItem(kind='separator', name='---'),
            model.MenuItem(name='item2', count=2, price=20),
            ])
    d = menu.as_dict()
    assert d == dict(
        table=dict(
            name='11',
            waiter='anto',
            busy=False),
        customer='pippo',
        notes='my notes',
        menuitems=[
            dict(kind='item', name='item1', count=1, price=10),
            dict(kind='separator', name='---', count=0, price=0),
            dict(kind='item', name='item2', count=2, price=20),
            ])
