import requests
from flask import Blueprint, render_template

dad_jokes_blueprint = Blueprint("dad_jokes", __name__)


@dad_jokes_blueprint.get("/flask_jokes", strict_slashes=False)
def flask_jokes():
    response = requests.get('https://icanhazdadjoke.com', headers={"Accept":"application/json"})
    response.raise_for_status()
    data = response.json()
    result = data["joke"]
    print(result)
    return render_template("flask_jokes.html", result=result)

#JS DAD JOKES
@dad_jokes_blueprint.get("/js_jokes", strict_slashes=False)
def js_jokes():
    return render_template("js_jokes.html")