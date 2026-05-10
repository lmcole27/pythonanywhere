import pytest
import requests
from flask.testing import FlaskClient
from flask_app import app
from routes.umbrella_app import rain_logic
from twilio.base.exceptions import TwilioRestException


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


def test_main_page_renders(client):
    """Test that the main page (/) renders successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

def test_dad_jokes_flask_renders(client, monkeypatch):
    """Test that the DAD JOKES Flask page renders successfully."""
    class FakeDadJokeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"joke": "A test dad joke."}

    monkeypatch.setattr("routes.dad_jokes.requests.get", lambda *args, **kwargs: FakeDadJokeResponse())

    response = client.get('/flask_jokes')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

def test_dad_jokes_js_renders(client):
    """Test that the DAD JOKES JS page renders successfully."""
    response = client.get('/js_jokes')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


def test_rain_page_renders(client):
    """Test that the umbrella app page renders successfully."""
    response = client.get('/rain')
    assert response.status_code == 200
    assert b'City' in response.data
    assert b'Country' in response.data


def test_rain_logic_bring_umbrella():
    """Test rain message when precipitation probability is high."""
    assert rain_logic("Toronto", 75) == "Bring an Umbrella in Toronto!"


def test_rain_logic_no_rain():
    """Test rain message when precipitation probability is low."""
    assert rain_logic("Toronto", 25) == "No rain today in Toronto!"


def test_rain_post_sends_sms(client, monkeypatch):
    """Test that a valid rain form submission sends an SMS."""
    created_messages = []

    class FakeWeatherResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "locations": {
                    "toronto,canada": {
                        "values": [
                            {"pop": 75}
                        ]
                    }
                }
            }

    class FakeMessages:
        def create(self, body, from_, to):
            created_messages.append({
                "body": body,
                "from": from_,
                "to": to,
            })

    class FakeTwilioClient:
        messages = FakeMessages()

    def fake_get(url, params, timeout):
        assert params["locations"] == "toronto,canada"
        assert timeout == 10
        return FakeWeatherResponse()

    monkeypatch.setattr("routes.umbrella_app.requests.get", fake_get)
    monkeypatch.setattr("routes.umbrella_app.get_twilio_client", lambda: FakeTwilioClient())
    monkeypatch.setenv("from_tel", "+15550000000")
    monkeypatch.setenv("WDS_AUTH", "fake-weather-key")

    response = client.post('/rain', data={
        "city": "Toronto",
        "country": "Canada",
        "phone_no": "+15551112222",
    })

    assert response.status_code == 200
    assert b"Sent! Check your messages." in response.data
    assert created_messages == [{
        "body": "Bring an Umbrella in Toronto!",
        "from": "+15550000000",
        "to": "+15551112222",
    }]


def test_rain_post_weather_request_failure_redirects(client, monkeypatch):
    """Test that weather API failures redirect back to the rain page."""
    def fake_get(url, params, timeout):
        raise requests.RequestException("weather unavailable")

    monkeypatch.setattr("routes.umbrella_app.requests.get", fake_get)

    response = client.post('/rain', data={
        "city": "Toronto",
        "country": "Canada",
        "phone_no": "+15551112222",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rain")


def test_rain_post_bad_weather_response_redirects(client, monkeypatch):
    """Test that unexpected weather response data redirects back to the rain page."""
    class FakeWeatherResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"locations": {}}

    monkeypatch.setattr("routes.umbrella_app.requests.get", lambda url, params, timeout: FakeWeatherResponse())

    response = client.post('/rain', data={
        "city": "Toronto",
        "country": "Canada",
        "phone_no": "+15551112222",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rain")


def test_rain_post_twilio_failure_redirects(client, monkeypatch):
    """Test that Twilio failures redirect back to the rain page."""
    class FakeWeatherResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "locations": {
                    "toronto,canada": {
                        "values": [
                            {"pop": 75}
                        ]
                    }
                }
            }

    class FakeMessages:
        def create(self, body, from_, to):
            raise TwilioRestException(400, "/Messages", msg="invalid phone number")

    class FakeTwilioClient:
        messages = FakeMessages()

    monkeypatch.setattr("routes.umbrella_app.requests.get", lambda url, params, timeout: FakeWeatherResponse())
    monkeypatch.setattr("routes.umbrella_app.get_twilio_client", lambda: FakeTwilioClient())
    monkeypatch.setenv("from_tel", "+15550000000")

    response = client.post('/rain', data={
        "city": "Toronto",
        "country": "Canada",
        "phone_no": "bad-phone-number",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rain")
