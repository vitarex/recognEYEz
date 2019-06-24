from pathlib import Path
import logging
import threading
import datetime
import cv2


class CameraHandler:

    def __init__(self):
        # loads video with OpenCV
        self.cam_is_running = False
        self.cam_is_processing = False
        self.start_cam()
        logging.info("Camera opened")

    def camera_start_processing(self, app):
        logging.info("The facehandler object: {}".format(app.fh))
        if app.fh and self.cam_is_running and not self.cam_is_processing:
            self.cam_is_processing = True
            app.fh.running_since = datetime.datetime.now()
            if app.camera_thread == None:
                app.camera_thread = threading.Thread(
                    target=self.camera_process, daemon=True, args=(app,))
                app.camera_thread.start()
            logging.info("Camera started")
        logging.info("Camera scanning started")

    def camera_stop_processing(self, app):
        if app.fh and self.cam_is_running and self.cam_is_processing:
            self.cam_is_processing = False
            app.preview_image = cv2.imread(
                os.path.join("Static", "empty_pic.png"))

        logging.info("Camera scanning stopped")

    def camera_process(self, app):
        """
        Continously calls the process_next_frame() method to process frames from the camera
        app_cont: used to access the main application instance from blueprints
        """
        ticker = 0
        error_count = 0
        while app.fh.cam_is_running:
            try:
                if ticker > int(app.fh.face_rec_settings["dnn_scan_freq"]) or app.force_rescan:
                    names, frame, rects = app.fh.process_next_frame(
                        True, save_new_faces=True, app=app)
                    ticker = 0
                    app.force_rescan = False

                    app.preview_image = frame
                else:
                    names, frame, rects = app.fh.process_next_frame(
                        save_new_faces=True, app=app)
                ticker += 1
                error_count = 0
            except Exception as e:
                error_count += 1
                if app.fh.cam:
                    app.fh.cam.release()
                logging.info(e)
                if error_count > 5:
                    self.cam_is_running = False
                raise e

    def start_cam(self):
        if self.cam_is_running:
            return

        self.cam = cv2.VideoCapture(int(self.settings["cam_id"]))
        res = self.resolutions[self.settings["resolution"]]
        self.cam.set(3, res[0])  # set video width
        self.cam.set(4, res[1])  # set video height
        self.minW = 0.1 * self.cam.get(3)
        self.minH = 0.1 * self.cam.get(4)
        self.cam_is_running = True

    def stop_cam(self):
        if self.cam_is_running:
            self.cam.release()
            self.cam_is_running = False
