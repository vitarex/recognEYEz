from flask import Blueprint, redirect, make_response
from flask import current_app as app
from flask_simplelogin import login_required
import os
import sys
import cv2
import logging

from Library.helpers import OKResponse

actions = Blueprint("actions", __name__)


# background process

@actions.route('/start_camera')
@login_required
def start_cam():
    app.ch.camera_start_processing()
    return OKResponse()


@actions.route('/stop_camera')
@login_required
def stop_cam():
    app.ch.camera_stop_processing()
    return OKResponse()


@actions.route('/force_rescan')
@login_required
def force_a_rescan():
    app.force_rescan = True
    return OKResponse()


@actions.route('/retrain')
@login_required
def retrain_dnn():
    # TODO: fix train_dnn
    # app.fh.train_dnn()
    logging.info("NOT OPERATIONAL Camera algorithm retrained")
    return redirect("/")


@actions.route('/hard_reset')
@login_required
def hard_reset():
    logging.info("Camera performing hard reset")
    try:
        os.execv(__file__, sys.argv)
    except OSError:
        pass
    logging.info([sys.executable, __file__] + sys.argv)
    # os.execv(sys.executable, [sys.executable, __file__.replace("/", "\\")])
    os.execv("'" + sys.executable + "'", [sys.executable, __file__] + sys.argv)
    logging.info("Camera hard reset performed")


@actions.route('/preview')
@login_required
def preview():
    image_binary = app.preview_image
    retval, buffer = cv2.imencode('.png', image_binary)
    response = make_response(buffer.tobytes())
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set('Content-Disposition', 'inline')
    return response
