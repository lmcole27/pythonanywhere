
import os
from flask import Blueprint, render_template, redirect, flash, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TelField
from wtforms.validators import DataRequired
#from flask_wtf.csrf import CSRFProtect
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import requests

umbrella_blueprint = Blueprint("umbrella", __name__)


# CREATE TWILIO CLIENT
def get_twilio_client():
    ACCOUNT_SID = os.environ.get('ACCOUNT_SID')
    AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    return Client(ACCOUNT_SID, AUTH_TOKEN)


# RAIN TRACKER INPUT FORM
class RainForm(FlaskForm):
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
        twilio_client = get_twilio_client()
        from_tel = os.environ.get('from_tel')
        twilio_client.messages.create(
            body=content,
            from_=from_tel,
            to=to_tel
        )

    except TwilioRestException:
        flash("Hmmm... we can't reach that telephone number. Please try again.")
        return False

    flash("Sent! Check your messages.")
    return True

# UMBRELLA APP HOME PAGE
@umbrella_blueprint.route("/rain", methods=["GET", "POST"], strict_slashes=False)
def rain():
    form = RainForm()

    if form.validate_on_submit():
        wds_auth = os.environ.get('WDS_AUTH')
        # CONVERT LOCATION TO LOWERCASE
        location = f"{form.city.data},{form.country.data}".lower()
        to_tel = form.phone_no.data
        WDS_ENDPOINT = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/weatherdata/forecast"

        params = {
            "locations": location,
            "aggregateHours": 24,
            "forecastDays": 1,
            "unitGroup": "us",
            "shortColumnNames": "true",
            "contentType": "json",
            "key": wds_auth,
        }

        try:
            response = requests.get(WDS_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            precipitation = data['locations'][location]['values'][0]['pop']

        except (requests.RequestException, KeyError, IndexError, ValueError):
            flash("Hmmm... we can't find that city. Please try again.")
            return redirect(url_for('umbrella.rain'))

        else:
            content = rain_logic(city=form.city.data, precipitation=precipitation)
            if not send_rain_notification(content, to_tel):
                return redirect(url_for('umbrella.rain'))

    return render_template("rain.html", form=form)