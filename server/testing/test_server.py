import os
import pytest
from server.app import create_app
from server import model

@pytest.fixture
def client(tmpdir):
    dbfile = tmpdir.join('db-test.sqlite')
    app = create_app(dbfile)
    app.config['TESTING'] = True
    client = app.test_client()
    with app.app_context():
        yield client


def test_new_order(client):
    menu = dict(table=dict(),
                items=[])
    resp = client.post('/order/', json=menu)
