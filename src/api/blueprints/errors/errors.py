from logging import getLogger

from flask import Blueprint, jsonify, Response
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from werkzeug.exceptions import HTTPException
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
    logger.exception(
        "Unexpected server error",
    )
    return (
        jsonify(
            error_message="Internal server error",
            details=getattr(error, "description", error.__class__.__name__),
        ),
        HTTP_500_INTERNAL_SERVER_ERROR,
    )


@errors_blueprint.app_errorhandler(Exception)
def handle_generic_exception(error) -> tuple[Response, int]:
    # Preserve the intended status for HTTP errors (429 rate-limited, 405, ...) instead
    # of masking every HTTPException as a 500. Only genuinely unexpected (non-HTTP)
    # exceptions are 500s.
    if isinstance(error, HTTPException):
        return (
            jsonify(error_message=error.name, details=error.description),
            error.code,
        )

    logger.exception(
        "Unexpected server error",
    )
    return (
        jsonify(error_message="Unhandled exception", details=str(error)),
        HTTP_500_INTERNAL_SERVER_ERROR,
    )
