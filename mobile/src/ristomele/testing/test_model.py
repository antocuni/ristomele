from ristomele import model

def test_Restaurant():
    r = model.Restaurant(2, 3)
    assert len(r.tables) == 6
    names = [t.name for t in r.tables]
    assert names == ['11', '21', '31',
                     '12', '22', '32']
