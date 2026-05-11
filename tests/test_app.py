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


def test_main_page_renders(client, monkeypatch):
    """Test that the main page (/) renders successfully."""
    class FakeTelegramResponse:
        def raise_for_status(self):
            pass

    monkeypatch.setattr("routes.index.requests.get", lambda *args, **kwargs: FakeTelegramResponse())

    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


def test_main_page_sends_telegram_alert(client, monkeypatch):
    """Test that the main page sends a Telegram alert on first visit."""
    telegram_requests = []

    class FakeTelegramResponse:
        def raise_for_status(self):
            pass

    def fake_get(url, params, proxies, timeout):
        telegram_requests.append({
            "url": url,
            "params": params,
            "proxies": proxies,
            "timeout": timeout,
        })
        return FakeTelegramResponse()

    monkeypatch.setattr("routes.index.requests.get", fake_get)

    response = client.get('/')

    assert response.status_code == 200
    assert len(telegram_requests) == 1
    assert telegram_requests[0]["url"] == "https://api.telegram.org/bottest-token/sendMessage"
    assert telegram_requests[0]["params"]["chat_id"] == "test-chat-id"
    assert "New visitor on pythonanywhere Homepage!" in telegram_requests[0]["params"]["text"]
    assert telegram_requests[0]["timeout"] == 5
    assert telegram_requests[0]["proxies"] == {
        "http": "http://proxy.server:3128",
        "https": "http://proxy.server:3128",
    }


def test_main_page_does_not_send_telegram_alert_twice(client, monkeypatch):
    """Test that Telegram alert is only sent once per browser session."""
    call_count = 0

    class FakeTelegramResponse:
        def raise_for_status(self):
            pass

    def fake_get(url, params, proxies, timeout):
        nonlocal call_count
        call_count += 1
        return FakeTelegramResponse()

    monkeypatch.setattr("routes.index.requests.get", fake_get)

    first_response = client.get('/')
    second_response = client.get('/')

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert call_count == 1


def test_main_page_telegram_request_failure_does_not_break_homepage(client, monkeypatch):
    """Test that Telegram connection failures do not break the homepage."""
    def fake_get(url, params, proxies, timeout):
        raise requests.RequestException("telegram unavailable")

    monkeypatch.setattr("routes.index.requests.get", fake_get)

    response = client.get('/')

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "alerted" not in session


def test_main_page_telegram_http_error_does_not_break_homepage(client, monkeypatch):
    """Test that Telegram HTTP failures do not break the homepage."""
    class FakeTelegramResponse:
        def raise_for_status(self):
            raise requests.HTTPError("telegram rejected request")

    monkeypatch.setattr("routes.index.requests.get", lambda *args, **kwargs: FakeTelegramResponse())

    response = client.get('/')

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert "alerted" not in session

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
    monkeypatch.setenv("WDS_AUTH", "fake-weather-key")

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
    monkeypatch.setenv("WDS_AUTH", "fake-weather-key")

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
    monkeypatch.setenv("WDS_AUTH", "fake-weather-key")

    response = client.post('/rain', data={
        "city": "Toronto",
        "country": "Canada",
        "phone_no": "bad-phone-number",
    })

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/rain")


def test_rain_post_missing_weather_key_redirects(client, monkeypatch):
    """Test that missing weather API configuration shows a clear setup error."""
    monkeypatch.delenv("WDS_AUTH", raising=False)

    response = client.post('/rain', data={
        "city": "Toronto",
        "country": "Canada",
        "phone_no": "+15551112222",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Weather service is not configured" in response.data


def test_assistant_page_renders(client):
    """Test that the assistant page renders successfully."""
    response = client.get('/assistant')

    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data
    assert b'id="chat-messages"' in response.data
    assert b'id="question-form"' in response.data
    assert b'id="question"' in response.data


def test_assistant_set_session_creates_token(client):
    """Test that set_session creates a guest token in the session."""
    response = client.get('/assistantAPI/set_session')
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["token"]

    with client.session_transaction() as session:
        assert session["token"] == data["token"]


def test_assistant_get_session_without_token_returns_404(client):
    """Test that get_session returns 404 when no guest token exists."""
    response = client.get('/assistantAPI/get_session')

    assert response.status_code == 404
    assert response.get_json() == {"error": "No session found"}


def test_assistant_get_session_with_token_returns_success(client):
    """Test that get_session returns the existing guest token."""
    with client.session_transaction() as session:
        session["token"] = "test-session-token"

    response = client.get('/assistantAPI/get_session')
    data = response.get_json()

    assert response.status_code == 200
    assert data == {"success": True, "token": "test-session-token"}


def test_assistant_generate_requires_question(client):
    """Test that generate requires a question."""
    with client.session_transaction() as session:
        session["token"] = "test-session-token"

    response = client.post('/generate', data={"question": ""})

    assert response.status_code == 400
    assert response.data == b"Please provide a question"


def test_assistant_generate_requires_session_token(client):
    """Test that generate requires an assistant session token."""
    response = client.post('/generate', data={"question": "Hello"})

    assert response.status_code == 400
    assert response.data == b"Session token not found"


def test_assistant_generate_streams_response_and_saves_question(client, monkeypatch):
    """Test that generate saves the user question and streams the assistant response."""
    chat_history = []
    saved_tokens = []

    def fake_generate_response(question, history):
        assert question == "Hello"
        assert history == [{"role": "user", "content": "Hello"}]
        yield "Hi"
        yield " there"

    def fake_save_chat(history, session_token):
        saved_tokens.append(session_token)
        assert history == [{"role": "user", "content": "Hello"}]

    monkeypatch.setattr("routes.assistant.load_chat", lambda session_token: chat_history)
    monkeypatch.setattr("routes.assistant.save_chat", fake_save_chat)
    monkeypatch.setattr("routes.assistant.generate_response", fake_generate_response)

    with client.session_transaction() as session:
        session["token"] = "test-session-token"

    response = client.post('/generate', data={"question": "Hello"})

    assert response.status_code == 200
    assert response.data == b"Hi there"
    assert response.mimetype == "text/plain"
    assert saved_tokens == ["test-session-token"]


def test_assistant_response_requires_session_token(client):
    """Test that assistantAPI response requires a session token."""
    response = client.post('/assistantAPI/response', json={"message": "Hello"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Session token not found"}


def test_assistant_response_requires_message(client):
    """Test that assistantAPI response requires a non-empty message."""
    with client.session_transaction() as session:
        session["token"] = "test-session-token"

    response = client.post('/assistantAPI/response', json={"message": ""})

    assert response.status_code == 400
    assert response.get_json() == {"error": "No message provided"}


def test_assistant_response_saves_message(client, monkeypatch):
    """Test that assistantAPI response saves the assistant message."""
    chat_history = []
    saved_tokens = []

    def fake_save_chat(history, session_token):
        saved_tokens.append(session_token)
        assert history == [{"role": "assistant", "content": "Assistant answer"}]

    monkeypatch.setattr("routes.assistant.load_chat", lambda session_token: chat_history)
    monkeypatch.setattr("routes.assistant.save_chat", fake_save_chat)

    with client.session_transaction() as session:
        session["token"] = "test-session-token"

    response = client.post('/assistantAPI/response', json={"message": "Assistant answer"})
    data = response.get_json()

    assert response.status_code == 200
    assert data == {"message": "Data received successfully"}
    assert saved_tokens == ["test-session-token"]
