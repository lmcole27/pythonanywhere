import logging
import sys
from flask import Flask, render_template, url_for, request, redirect, flash, send_file, Response, stream_with_context, jsonify, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField
from wtforms.validators import DataRequired
#from flask_wtf.csrf import CSRFProtect
from twilio.rest import Client
import requests
from openai import OpenAI
from flask_cors import CORS
#import json
from assistantFunctions import load_chat, add_message, save_chat #history_cleanup
#from api import guest
import uuid
#import atexit
# from apscheduler.schedulers.background import BackgroundScheduler #This is not allowed in pythonanywhere... need to find another method.
import os
import csv
from dotenv import load_dotenv


#REQUIRED FOR LOGGING IN PYTHONANYWHERE
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

load_dotenv()

#INFO REQUIRED TO LOAD .env in pythonanywhere
project_folder = os.path.expanduser('~/mysite')
load_dotenv(os.path.join(project_folder, '.env'))


#RAIN TRACKER SECRET ENDPOINT INFORMTION - WEATHER & TWILIO
ACCOUNT_SID = os.environ.get('ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
wds_auth = os.environ.get('WDS_AUTH')
from_tel = os.environ.get('from_tel')

#CREATE API CLIENTS
twilioClient = Client(ACCOUNT_SID, AUTH_TOKEN)
openaiClient = OpenAI(api_key=os.environ['OPENAI_API_KEY'], organization=os.environ['ORGANIZATION'], project=os.environ['PROJECT'])

#CREATE WEBAPP
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ['FLASK_SECRET_KEY']
app.config['SESSION_COOKIE_SECURE'] = True  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

#RAIN TRACKER INPUT FORM
class rainForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    phone_no = TelField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Submit')

#OPENAI CLIENT FUNCTION
def generate_response(question: str, chat_history):
    # Send API request to ChatGPT and recieve resonse
    response = openaiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question},
                  {"role": "system", "content": f"consider the conversation context {chat_history}"},
                  {"role": "system", "content":"provide response with HTML tags but no header."
                   }],
        stream=True,
    )

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            ans = chunk.choices[0].delta.content
            yield ans

#WEB HOME PAGE
@app.route('/', methods=['GET', 'POST'])
def welcome():
    return render_template("index.html")

#LOG FILE PROCESSOR HOMEPAGE
@app.route('/log', methods=['GET', 'POST'])
def process_log():
    return render_template("processlog.html")

#LOG FILE PROCESSOR OUTPUT
@app.route('/upload', methods=['POST'])
def upload():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return render_template("processlog.html")
    file = request.files['file']

    # Check if the file has a valid name
    if file.filename == '':
        return render_template("processlog.html")

    #Set variables
    i_list = [] # list of Unique IDs
    count = 0 # Number of Unique IDs
    writeunid = 0 # Indicator of whether this is an error to capture

    # Read file content directly / load to memory
    file_content = file.read().decode('utf-8')  # Assuming the file is a text file
    lines=file_content.splitlines()

    for line in lines:
        if 'severity' in line:
            if 'severity="Critical"' in line:
                writeunid = 1
            else:
                writeunid =0
        if "<unid>" in line and writeunid==1:
            unid= str(line).strip()
            i_list.append(unid)
            writeunid==0

    for item in i_list:
        count += 1

    return render_template("processlog_output.html", DATA=i_list, count=count)

#LOG FILE PROCESSOR HOMEPAGE
@app.route('/compare', methods=['GET', 'POST'])
def comparefiles():
    return render_template("compare.html")

#LOG FILE PROCESSOR OUTPUT
@app.route('/uploadfiles', methods=['POST'])
def uploadfiles():
    # Check if a file was uploaded
    if 'file1' not in request.files:
        return render_template("compare.html")
    elif 'file2' not in request.files:
        return render_template("compare.html")

    primaryfile = request.files['file1']
    secondaryfile = request.files['file2']

    # Check if the file has a valid name
    if primaryfile.filename == '':
        return render_template("compare.html")
    elif secondaryfile.filename == '':
        return render_template("compare.html")

    # Read file content directly
    primaryfile_content = primaryfile.read().decode('utf-8')  # Assuming the file is a text file
    secondaryfile_content = secondaryfile.read().decode('utf-8')
    primelines=primaryfile_content.splitlines()
    secondlines=secondaryfile_content.splitlines()

        # Initialize an empty set to store the rows
    primeset = set()
    secondset = set()
    missingitemset = set()
    extraitemset = set()

    # Initialize count variables
    primecount = 0
    secondcount = 0
    blanks = 0
    missingcount = 0
    blanks2 = 0
    duplicates2 = 0
    extracount = 0

    # Append the row to the list
    for row in primelines:
        if row == "":
            blanks += 1
        else:
            primeset.add(row)

    primecount = len(primelines)
    duplicates = int(primecount) - int(len(primeset)) - int(blanks)

    for row in secondlines:
        if row == "":
            blanks2 += 1
        else:
            secondset.add(row)

    secondcount = len(secondlines)
    duplicates2 = int(secondcount) - int(len(secondset)) - int(blanks2)

    for item in primeset:
        if item not in secondset:
            missingitemset.add(item)
            missingcount+=1

    for item in secondset:
        if item not in primeset:
            extraitemset.add(item)
            extracount += 1

    # Save to a CSV file
    with open("output.csv", mode="w", newline="") as csvoutputfile:
        writer = csv.writer(csvoutputfile)
        writer.writerow(missingitemset)

    with open('output.txt', 'w') as txtoutputfile:
        for row in missingitemset:
            txtoutputfile.write(row + '\n')

    return render_template("compare_output.html", missingitemlist=missingitemset, primecount=primecount, secondcount=secondcount, blanks=blanks, duplicates=duplicates, missingcount=missingcount, blanks2=blanks2, extracount=extracount, extraitemlist=extraitemset, duplicates2=duplicates2)


@app.route('/downloads')
def download():
    return render_template('downloads.html')

@app.route('/download/<filename>')
def download_file(filename):
    file_path = filename

    try:
        # Serve the file for download
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}", 404


#FLASK DAD JOKES
@app.route('/flask_jokes', methods=['GET', 'POST'])
def flask_jokes():
    response = requests.get('https://icanhazdadjoke.com', headers={"Accept":"application/json"})
    response.raise_for_status()
    data = response.json()
    result = data["joke"]
    print(result)
    return render_template("flask_jokes.html", result=result)

#JS DAD JOKES
@app.route('/js_jokes', methods=['GET', 'POST'])
def js_jokes():
    return render_template("js_jokes.html")

#UMBRELLA APP HOME PAGE
@app.route('/rain', methods=['GET', 'POST'])
def rain():
    form = rainForm()

    if request.method == "POST":

        #CONVERT TO LOWERCASE
        location = (str(request.form["city"]) + "," + str(request.form["country"])).lower()
        to_tel = request.form["phone_no"]

        #BUILD THE ENDPOINT
        WDS_ENDPOINT = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/forecast?locations="+ location + "&aggregateHours=24&forcastDays=1&unitGroup=us&shortColumnNames=true&contentType=json&key=" + wds_auth

        #FIND THE WEATHER
        response = requests.get(url=WDS_ENDPOINT)

        try:
            data = response.json()
            precipitation = data['locations'][location]['values'][0]['pop']

        except:
            flash("Hmmm... we can't find that city. Please try again.")
            return redirect(url_for('rain'))

        else:
            #LOGIC FOR RAIN/UMBRELLA
            if precipitation >50:
                content = "Bring an Umbrella in " + request.form["city"] + "!"
            else:
                content = "No rain today in " + request.form["city"] + "!"

            try:
                #SEND THE NOTIFICATION TO YOUR DEVICE USING TWILIO
                message = twilioClient.messages \
                                .create(
                                        body=content,
                                        from_=from_tel,
                                        to=to_tel
                                    )

            except:
                flash("Hmmm... we can't reach that telephone number. Please try again.")
                return redirect(url_for('rain'))

            else:
                flash("Sent! Check your messages.")

            finally:
                return redirect(url_for('rain'))

        finally:
            return redirect(url_for('rain'))
    else:
        return render_template("rain.html", form=form)

    return render_template("rain.html", form=form)

# ASSISTANT CODE

@app.route('/assistant', methods=['GET', 'POST'])
def index():
    return render_template('assistant.html')

@app.route('/assistantAPI/set_session', methods=['GET','POST'])
def set_session():
    token = uuid.uuid4()  # unique guest ID
    token_str = str(token)
    session['token'] = token_str  # Store the token in session
    return jsonify(success=True, token=token_str)

@app.route('/assistantAPI/get_session', methods=['GET', 'POST'])
def get_session():
    id = session.get('token', None)
    sesh = session.get('session', None)
    print("id = ", id, "sesh = ", sesh)
    if id is None:
        return jsonify({"error": "No session found"}), 404
    return jsonify(success=True, token=id)

@app.route('/generate', methods=['POST'])
def generate():
    question = request.form.get('question')
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

    def generate():
        for chunk in generate_response(question, chat_history):
            yield chunk

    return Response(stream_with_context(generate()), mimetype='text/plain')


@app.route('/assistantAPI/response', methods=['POST'])
def receive_post():
    try:
        # Get JSON data from the request
        data = request.get_json()
        response = data["message"]

        # Get session token
        session_token = session.get('token')
        if not session_token:
            return jsonify({"error": "Session token not found"}), 400

        # Load chat history for the user
        chat_history = load_chat(session_token)

        # Save response to chat_history
        add_message(chat_history, "assistant", response)
        save_chat(chat_history, session_token)

        # Respond back to client
        return jsonify({"message": "Data received successfully", "received": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# # Schedule job
# scheduler = BackgroundScheduler(daemon=True)
# scheduler.add_job(
#     func=history_cleanup,
#     trigger="interval",
#     days=7,
#     id='history_cleanup',
#     replace_existing=True
# )
# scheduler.start()

# # Shut down the scheduler when exiting the app
# atexit.register(lambda: scheduler.shutdown())

#RUN THE WEBAPP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)