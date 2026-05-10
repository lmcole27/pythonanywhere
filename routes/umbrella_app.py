
import os
from flask import Blueprint, render_template, request, redirect, flash, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField
from wtforms.validators import DataRequired
#from flask_wtf.csrf import CSRFProtect
from twilio.rest import Client
import requests

umbrella_blueprint = Blueprint("umbrella", __name__)


# CREATE TWILIO CLIENT
def get_twilio_client():
    ACCOUNT_SID = os.environ.get('ACCOUNT_SID')
    AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    return Client(ACCOUNT_SID, AUTH_TOKEN)


# RAIN TRACKER INPUT FORM
class rainForm(FlaskForm):
    city = StringField('City', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    phone_no = TelField('Phone Number', validators=[DataRequired()])
    submit = SubmitField('Submit')


# RAIN TRACKER LOGIC TO CHECK THE WEATHER 
def rain_logic(city, precipitation):
    if precipitation > 50:
        return f"Bring an Umbrella in {city}!"
    return f"No rain today in {city}!"

def send_rain_notification(content, to_tel):
    try:
        #SEND THE NOTIFICATION TO YOUR DEVICE USING TWILIO
        twilioClient = get_twilio_client()
        from_tel = os.environ.get('from_tel')
        message = twilioClient.messages \
                        .create(
                                body=content,
                                from_=from_tel,
                                to=to_tel
                            )

    except Exception:
        flash("Hmmm... we can't reach that telephone number. Please try again.")
        return redirect(url_for('umbrella.rain'))

    return flash("Sent! Check your messages.")


# UMBRELLA APP HOME PAGE
@umbrella_blueprint.route("/rain", methods=["GET", "POST"], strict_slashes=False)
def rain():
    form = rainForm()

    if request.method == "POST" and form.validate_on_submit():
        wds_auth = os.environ.get('WDS_AUTH')
        # CONVERT LOCATION TO LOWERCASE
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
            return redirect(url_for('umbrella.rain'))

        else:
            content = rain_logic(city = request.form['city'], precipitation = precipitation)
            send_rain_notification(content, to_tel)

    return render_template("rain.html", form=form)