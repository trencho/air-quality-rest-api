from pathlib import Path

from flask import Blueprint, Response, send_from_directory

icon_blueprint = Blueprint("icon", __name__)


@icon_blueprint.get("/favicon.ico/")
def favicon() -> Response:
    return send_from_directory(Path(icon_blueprint.root_path) / "icon", "aqra-logo.svg")
