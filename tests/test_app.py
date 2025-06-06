import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import app
except ModuleNotFoundError as e:
    pytest.skip(f"flask not available: {e}", allow_module_level=True)

def test_index_route():
    os.environ["TASK_AZ"] = "test-az"
    with app.app.test_client() as client:
        resp = client.get('/')
        assert resp.status_code == 200
        assert b"Welcome to the Flask Bootstrap App" in resp.data
        assert b"test-az" in resp.data
