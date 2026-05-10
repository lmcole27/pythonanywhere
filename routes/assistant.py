import os
import uuid
from openai import OpenAI
from assistantFunctions import load_chat, add_message, save_chat #history_cleanup
from flask import Blueprint, render_template, request, Response, stream_with_context, jsonify, session 


assistant_blueprint = Blueprint("assistant", __name__)


# Get OpenAI client
def get_openai_client():
    return OpenAI(
        api_key=os.environ['OPENAI_API_KEY'], 
        organization=os.environ['ORGANIZATION'], 
        project=os.environ['PROJECT'],
        )


# OPENAI CLIENT FUNCTION
def generate_response(question: str, chat_history):
    # Send API request to ChatGPT and receive resonse
    response = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"consider the conversation context {chat_history}"},
            {"role": "system", "content": "provide response with HTML tags but no header."},
            {"role": "user", "content": question}
            ],
        stream=True,
    )

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            ans = chunk.choices[0].delta.content
            yield ans


@assistant_blueprint.get("/assistant", strict_slashes=False)
def index():
    return render_template('assistant.html')


@assistant_blueprint.get("/assistantAPI/set_session", strict_slashes=False)
def set_session():
    token = uuid.uuid4()  # unique guest ID
    token_str = str(token)
    session['token'] = token_str  # Store the token in session
    return jsonify(success=True, token=token_str)


@assistant_blueprint.get("/assistantAPI/get_session", strict_slashes=False)
def get_session():
    session_token = session.get('token', None)
    #sesh = session.get('session', None)
    #print("session_token = ", session_token, "sesh = ", sesh)
    if session_token is None:
        return jsonify({"error": "No session found"}), 404
    return jsonify(success=True, token=session_token)


@assistant_blueprint.post("/generate", strict_slashes=False)
def generate():
    question = request.form.get("question", "").strip()
    if not question:
        return "Please provide a question", 400

    # Get session token
    session_token = session.get('token')
    if not session_token:
        return "Session token not found", 400

    # Load chat history for the user
    chat_history = load_chat(session_token)

    # Save question to chat_history
    add_message(chat_history, "user", question)
    save_chat(chat_history, session_token)

    def stream_response():
        for chunk in generate_response(question, chat_history):
            yield chunk

    return Response(stream_with_context(stream_response()), mimetype='text/plain')


@assistant_blueprint.post("/assistantAPI/response", strict_slashes=False)
def receive_post():
    # Get JSON data from the request
    data = request.get_json(silent=True) or {}
    response_text = data.get("message", "").strip()


    if not response_text:
        return jsonify({"error": "No message provided"}), 400

    # Get session token
    session_token = session.get('token')
    if not session_token:
        return jsonify({"error": "Session token not found"}), 400

    # Load chat history for the user
    chat_history = load_chat(session_token)

    # Save response to chat_history
    add_message(chat_history, "assistant", response_text)
    save_chat(chat_history, session_token)

    # Respond back to client
    return jsonify({"message": "Data received successfully"}), 200