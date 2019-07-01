from flask import Blueprint, render_template, jsonify
from Library.errors import InvalidUsage
import logging

errors = Blueprint("errors", __name__)

@errors.app_errorhandler(InvalidUsage)
def error_invalid_usage(error: InvalidUsage):
    logging.error(error.message)
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@errors.app_errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404


@errors.app_errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403


@errors.app_errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500
