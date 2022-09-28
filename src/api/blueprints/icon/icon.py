from os import path

from flask import Blueprint, Response, send_from_directory

icon_blueprint = Blueprint("icon", __name__)


@icon_blueprint.route("/favicon.ico/", methods=["GET"])
def favicon() -> Response:
    return send_from_directory(path.join(icon_blueprint.root_path, "icon"), "aqra-logo.svg")
