
import subprocess
import time
import requests
import pytest

# Start the FastAPI server
@pytest.fixture(scope="session", autouse=True)
def start_server():
    process = subprocess.Popen(["uvicorn", "dashboard.app:app", "--host", "0.0.0.0", "--port", "8000"])
    time.sleep(2)  # Wait for the server to start
    yield
    process.terminate()

def test_get_patterns_endpoint_succeeds():
    response = requests.get("http://0.0.0.0:8000/api/patterns")
    assert response.status_code == 200
