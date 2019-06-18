from flask import Blueprint, render_template, request, redirect
from flask import current_app as app
import flask_simplelogin as simplog
import os
import sys
import datetime
import threading
import cv2
import logging

actions = Blueprint("actions", __name__)

def continous_check(app):
    """
    Continously calls the process_next_frame() method to process frames from the camera
    app_cont: used to access the main application instance from blueprints
    """
    global most_recent_scan_date
    ticker = 0
    error_count = 0
    while app.fh.cam_is_running:
        try:
            if ticker > int(app.fh.face_rec_settings["dnn_scan_freq"]) or app.force_rescan:
                names, frame, rects = app.fh.process_next_frame(True, save_new_faces=True)
                ticker = 0
                cv2.imwrite("Static/live_view.png", frame)  # TODO: do we need this?
                most_recent_scan_date = datetime.datetime.now()
                app.force_rescan = False
            else:
                names, frame, rects = app.fh.process_next_frame(save_new_faces=True)
            ticker += 1
            print(ticker)
            error_count = 0
        except Exception as e:
            error_count += 1
            if app.fh.cam:
                app.fh.cam.release()
            logging.info(e)
            if error_count > 5:
                app.fh.cam_is_running = False
    # try:
    #     app_cont.camera_thread
        # app_cont.threads.remove(app_cont.camera_thread)
    # except NameError:
    #    logging.info("Camera thread not found during the end of continous check")


# background process'
@actions.route('/stop_camera')
@simplog.login_required
def stop_cam():
    if app.fh and app.fh.cam_is_running:
        app.fh.cam_is_running = False
    logging.info("Camera scanning stopped")
    return redirect("/")


@actions.route('/start_camera')
@simplog.login_required
def start_cam():
    logging.info("The facehandler object: {}".format(app.fh))
    if app.fh and not app.fh.cam_is_running:
        app.fh.cam_is_running = True
        app.fh.running_since = datetime.datetime.now()
        app.camera_thread = threading.Thread(target=continous_check, args=(app._get_current_object(),))
        app.camera_thread.start()
        # app.threads.append(camera_thread)
        logging.info("Camera started")
    logging.info("Camera scanning started")
    return redirect("/")


@actions.route('/force_rescan')
@simplog.login_required
def force_a_rescan():
    app.force_rescan = True
    while app.force_rescan and app.fh.cam_is_running:
        pass
    return redirect("/")


@actions.route('/retrain')
@simplog.login_required
def retrain_dnn():
    app.fh.train_dnn()
    logging.info("Camera algorithm retrained")
    return redirect("/")


@actions.route('/hard_reset')
@simplog.login_required
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
