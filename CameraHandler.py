
import logging
import threading
import datetime
import cv2

def camera_start(app):
    logging.info("The facehandler object: {}".format(app.fh))
    if app.fh and not app.fh.cam_is_running:
        app.fh.cam_is_running = True
        app.fh.running_since = datetime.datetime.now()
        app.camera_thread = threading.Thread(target=camera_check, args=(app,))
        app.camera_thread.start()
        # app.threads.append(camera_thread)
        logging.info("Camera started")
    logging.info("Camera scanning started")

def camera_stop(app):
    if app.fh and app.fh.cam_is_running:
        app.fh.cam_is_running = False
        app.preview_image = cv2.imread("Static/empty_pic.png")

    logging.info("Camera scanning stopped")

def camera_check(app):
    """
    Continously calls the process_next_frame() method to process frames from the camera
    app_cont: used to access the main application instance from blueprints
    """
    ticker = 0
    error_count = 0
    while app.fh.cam_is_running:
        try:
            if ticker > int(app.fh.face_rec_settings["dnn_scan_freq"]) or app.force_rescan:
                names, frame, rects = app.fh.process_next_frame(True, save_new_faces=True)
                ticker = 0
                app.force_rescan = False

                app.preview_image = frame
            else:
                names, frame, rects = app.fh.process_next_frame(save_new_faces=True)
            ticker += 1
            error_count = 0
        except Exception as e:
            error_count += 1
            if app.fh.cam:
                app.fh.cam.release()
            logging.info(e)
            if error_count > 5:
                app.fh.cam_is_running = False