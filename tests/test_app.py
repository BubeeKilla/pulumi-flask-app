import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

def test_index_route():
    client = app.app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"Welcome to the Flask Bootstrap App" in resp.data
