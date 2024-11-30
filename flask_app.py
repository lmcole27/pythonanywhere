import logging
import sys
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField
from wtforms.validators import DataRequired
#from flask_wtf.csrf import CSRFProtect
from twilio.rest import Client
import requests
import os
from dotenv import load_dotenv


#REQUIRED FOR LOGGING IN PYTHON ANYWHERE
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

load_dotenv()

#INFO REQUIRED TO LOAD .env in pythonanywhere
project_folder = os.path.expanduser('~/mysite')
load_dotenv(os.path.join(project_folder, '.env'))

#RAIN TRACKER SECRET KEY FOR FLASK WTF
secret_key = os.environ.get('SECRET_KEY')
#csrf_secret_key = os.environ.get('CSFR_KEY')

#RAIN TRACKER SECRET ENDPOINT INFORMTION - WEATHER & TWILIO
ACCOUNT_SID = os.environ.get('ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
wds_auth = os.environ.get('WDS_AUTH')
from_tel = os.environ.get('from_tel')

#CREATE TWILIO CLIENT
client = Client(ACCOUNT_SID, AUTH_TOKEN)

#CREATE WEBAPP
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
#app.config['WTF_CSRF_SECRET_KEY']= csrf_secret_key
#csrf = CSRFProtect(app)

#RAIN TRACKER INPUT FORM
class rainForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    phone_no = TelField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Submit')


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
                message = client.messages \
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


#RUN THE WEBAPP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)