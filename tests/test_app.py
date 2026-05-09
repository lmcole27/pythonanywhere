import pytest
from flask.testing import FlaskClient
from flask_app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_main_page_renders(client):
    """Test that the main page (/) renders successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

def test_dad_jokes_flask_renders(client):
    """Test that the DAD JOKES Flask page renders successfully."""
    response = client.get('/flask_jokes')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

def test_dad_jokes_js_renders(client):
    """Test that the DAD JOKES JS page renders successfully."""
    response = client.get('/js_jokes')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data