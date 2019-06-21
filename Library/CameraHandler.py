import os
import logging
import threading
import datetime
import cv2

class CameraHandler:

    def camera_start_processing(app):
        logging.info("The facehandler object: {}".format(app.fh))
        if app.fh and app.fh.cam_is_running and not app.fh.cam_is_processing:
            app.fh.cam_is_processing = True
            app.fh.running_since = datetime.datetime.now()
            if app.camera_thread == None:
                app.camera_thread = threading.Thread(target=camera_process, daemon=True, args=(app,))
                app.camera_thread.start()
            logging.info("Camera started")
        logging.info("Camera scanning started")

    def camera_stop_processing(app):
        if app.fh and app.fh.cam_is_running and app.fh.cam_is_processing:
            app.fh.cam_is_processing = False
            app.preview_image = cv2.imread(os.path.join("Static","empty_pic.png"))

        logging.info("Camera scanning stopped")

    def camera_process(app):
        """
        Continously calls the process_next_frame() method to process frames from the camera
        app_cont: used to access the main application instance from blueprints
        """
        ticker = 0
        error_count = 0
        while app.fh.cam_is_running:
            try:
                if ticker > int(app.fh.face_rec_settings["dnn_scan_freq"]) or app.force_rescan:
                    names, frame, rects = app.fh.process_next_frame(True, save_new_faces=True, app=app)
                    ticker = 0
                    app.force_rescan = False

                    app.preview_image = frame
                else:
                    names, frame, rects = app.fh.process_next_frame(save_new_faces=True, app=app)
                ticker += 1
                error_count = 0
            except Exception as e:
                error_count += 1
                if app.fh.cam:
                    app.fh.cam.release()
                logging.info(e)
                if error_count > 5:
                    app.fh.cam_is_running = False
                raise e