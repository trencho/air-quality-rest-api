from flask import Blueprint, jsonify, make_response, Response
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

errors_blueprint = Blueprint('errors', __name__)


@errors_blueprint.app_errorhandler(HTTP_404_NOT_FOUND)
def handle_not_found_error(error) -> Response:
    return make_response(jsonify(error_message=error.__class__.__name__), HTTP_404_NOT_FOUND)


@errors_blueprint.app_errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
def handle_unexpected_error(error) -> Response:
    return make_response(jsonify(error_message=error.__class__.__name__), HTTP_500_INTERNAL_SERVER_ERROR)
