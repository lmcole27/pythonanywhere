import requests
from flask import Blueprint, render_template

dad_jokes_flask_blueprint = Blueprint("dad_jokes_flask", __name__)
dad_jokes_js_blueprint = Blueprint("dad_jokes_js", __name__)


#@app.route('/flask_jokes', methods=['GET', 'POST'])
@dad_jokes_flask_blueprint.get("/flask_jokes", strict_slashes=False)
def flask_jokes():
    response = requests.get('https://icanhazdadjoke.com', headers={"Accept":"application/json"})
    response.raise_for_status()
    data = response.json()
    result = data["joke"]
    print(result)
    return render_template("flask_jokes.html", result=result)

#JS DAD JOKES
#@app.route('/js_jokes', methods=['GET', 'POST'])
@dad_jokes_js_blueprint.get("/js_jokes", strict_slashes=False)
def js_jokes():
    return render_template("js_jokes.html")