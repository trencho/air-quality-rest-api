from os import path

from flask import Blueprint, send_from_directory

from api.config.cache import cache

icon_blueprint = Blueprint('icon', __name__)


@icon_blueprint.route('/favicon.ico/', methods=['GET'])
@cache.cached(timeout=0)
def favicon():
    return send_from_directory(path.join(icon_blueprint.root_path, 'icon'), 'aqra-logo.svg')
