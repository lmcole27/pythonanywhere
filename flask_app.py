import logging
import sys
import os

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from routes.dad_jokes import dad_jokes_blueprint
from routes.umbrella_app import umbrella_blueprint
from routes.assistant import assistant_blueprint
from routes.index import index_blueprint


#REQUIRED FOR LOGGING IN PYTHONANYWHERE
logging.basicConfig(stream=sys.stderr, level=logging.INFO)


#INFO REQUIRED TO LOAD .env in pythonanywhere
load_dotenv()
project_folder = os.path.expanduser('~/mysite')
load_dotenv(os.path.join(project_folder, '.env'))


#CREATE WEBAPP
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ['FLASK_SECRET_KEY']
app.config['SESSION_COOKIE_SECURE'] = True  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# app register via Blueprint
app.register_blueprint(index_blueprint)
app.register_blueprint(dad_jokes_blueprint)
app.register_blueprint(umbrella_blueprint)
app.register_blueprint(assistant_blueprint)

#RUN THE WEBAPP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
