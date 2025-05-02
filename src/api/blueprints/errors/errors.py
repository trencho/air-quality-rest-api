from logging import getLogger

from flask import Blueprint, jsonify, Response
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from werkzeug.routing import ValidationError

errors_blueprint = Blueprint("errors", __name__)

logger = getLogger(__name__)


@errors_blueprint.app_errorhandler(ValidationError)
def handle_validation_error(error) -> tuple[Response, int]:
    return (
        jsonify(error_message="Invalid parameter value", details=str(error)),
        HTTP_400_BAD_REQUEST,
    )


@errors_blueprint.app_errorhandler(HTTP_404_NOT_FOUND)
def handle_not_found_error(error) -> tuple[Response, int]:
    return (
        jsonify(
            error_message="Resource not found",
            details=getattr(error, "description", error.__class__.__name__),
        ),
        HTTP_404_NOT_FOUND,
    )


@errors_blueprint.app_errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
def handle_unexpected_error(error) -> tuple[Response, int]:
    logger.exception("Unexpected server error", exc_info=True)
    return (
        jsonify(
            error_message="Internal server error",
            details=getattr(error, "description", error.__class__.__name__),
        ),
        HTTP_500_INTERNAL_SERVER_ERROR,
    )


@errors_blueprint.app_errorhandler(Exception)
def handle_generic_exception(error) -> tuple[Response, int]:
    logger.exception("Unexpected server error", exc_info=True)
    return (
        jsonify(error_message="Unhandled exception", details=str(error)),
        HTTP_500_INTERNAL_SERVER_ERROR,
    )
