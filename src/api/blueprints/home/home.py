from flask import Blueprint, redirect, Response

home_blueprint = Blueprint('home', __name__)


@home_blueprint.route('/', methods=['GET'])
def home() -> Response:
    return redirect('https://aqra.feit.ukim.edu.mk/ui')
