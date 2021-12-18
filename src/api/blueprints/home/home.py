from flask import Blueprint, redirect

home_blueprint = Blueprint('home', __name__)


@home_blueprint.route('/', methods=['GET'])
def home():
    return redirect('https://aqra.feit.ukim.edu.mk/ui')
