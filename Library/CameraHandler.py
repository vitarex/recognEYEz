from pathlib import Path
import logging
import threading
import datetime
import cv2
import numpy as np
from typing import Dict
import platform
from Library.Handler import Handler


class Camera:
    """Base camera class"""

    def read(self):
        return np.empty((0, 0))

    def release(self) -> bool:
        return True


class WebcamCamera(Camera):
    resolutions = {"vga": [640, 480], "qvga": [320, 240], "qqvga": [
        160, 120], "hd": [1280, 720], "fhd": [1920, 1080]}

    def __init__(self, cam_id: int, res: str):
        res = self.resolutions[res]
        self.cam = cv2.VideoCapture(cam_id)
        self.cam.set(3, res[0])  # set video width
        self.cam.set(4, res[1])  # set video height
        self.cam_is_running = True

    def read(self):
        return self.cam.read()

    def release(self) -> bool:
        try:
            self.cam.release()
            return True
        except Exception as e:
            print(e)
            return False


class IPWebcam(Camera):
    resolutions = {"vga": [640, 480], "qvga": [320, 240], "qqvga": [
        160, 120], "hd": [1280, 720], "fhd": [1920, 1080]}

    def __init__(self, url: str, res: str):
        res = self.resolutions[res]
        self.cam = cv2.VideoCapture(url)
        self.cam.set(3, res[0])  # set video width
        self.cam.set(4, res[1])  # set video height
        self.cam_is_running = True

    def read(self):
        return self.cam.read()


class PiCamera(Camera):
    #resolutions = {"vga": [640, 480], "qvga": [320, 240], "qqvga": [
        #160, 120], "hd": [1280, 720], "fhd": [1920, 1080]}

    def __init__(self):
        #res = self.resolutions[res]
        self.cam = cv2.VideoCapture()
        self.cam.set(3, 320)  # set video width
        self.cam.set(4, 240)  # set video height
        self.cam_is_running = True


class CameraHandler(Handler):
    cam: Camera = None
    cam_lock: threading.RLock = threading.RLock()

    def __init__(self, app):
        super().__init__(app)
        # loads video with OpenCV
        self.cam_is_running = False
        self.cam_is_processing = False
        self.start_cam()
        logging.info("Camera opened")

    def camera_start_processing(self):
        with self.cam_lock:
            logging.info("The camera handler object: {}".format(self))
            if self.app.fh\
                    and self.cam_is_running\
                    and not self.cam_is_processing:
                self.app.fh.running_since = datetime.datetime.now()
                if self.app.camera_thread is None:
                    self.app.camera_thread = threading.Thread(
                        target=self.camera_process, daemon=True)
                    self.app.camera_thread.start()
                self.cam_is_processing = True
                logging.info("Camera started")
            logging.info("Camera scanning started")

    def camera_stop_processing(self):
        with self.cam_lock:
            if self.app.fh and self.cam_is_running and self.cam_is_processing:
                self.cam_is_processing = False
                self.app.preview_image = cv2.imread(
                    str(Path("Static", "empty_pic.png")))

            logging.info("Camera scanning stopped")

    def camera_process(self):
        """
        Continously calls the process_next_frame() method
        to process frames from the camera
        """
        ticker = 0
        error_count = 0
        try:
            while self.cam_is_running:
                if ticker > int(self.app.sh.get_face_recognition_settings()["dnn-scan-freq-int-static"])\
                        or self.app.force_rescan:
                    _, frame, _ = self.app.fh.process_next_frame(
                        True, save_new_faces=True)
                    ticker = 0
                    self.app.force_rescan = False

                    self.app.preview_image = frame
                else:
                    _, frame, _ = self.app.fh.process_next_frame(
                        save_new_faces=True)
                    self.app.preview_image = frame
                ticker += 1
                error_count = 0
        except AssertionError as e:
            print(e)
        except Exception as e:
            error_count += 1
            if self.cam:
                self.cam.release()
            logging.info(e)
            if error_count > 5:
                self.cam_is_running = False
            raise e

    def start_cam(self):
        with self.cam_lock:
            if self.cam_is_running:
                return

            face_rec_dict = self.app.sh.get_face_recognition_settings()
            if face_rec_dict["selected_camera"].startswith("Webcam"):
                if int(face_rec_dict["selected_camera"][-1]) == 0:
                    self.cam = WebcamCamera(
                        int(self.app.sh.get_face_recognition_settings()["selected_camera"][-1]),
                        self.app.sh.get_face_recognition_settings(face_rec_dict["selected_camera"])["resolution"])
                    self.cam_is_running = self.cam.cam_is_running
            if face_rec_dict["selected_camera"] == "ipcamera":
                self.cam = IPWebcam(
                    self.app.sh.get_face_recognition_settings(face_rec_dict["selected_camera"])["URL"],
                    self.app.sh.get_face_recognition_settings(face_rec_dict["selected_camera"])["resolution"])
                self.cam_is_running = self.cam.cam_is_running
            if face_rec_dict["selected_camera"] == "picamera":
                self.cam = PiCamera()
                    #self.app.sh.get_face_recognition_settings(face_rec_dict["selected_camera"])["resolution"])
                self.cam_is_running = self.cam.cam_is_running

    def stop_cam(self):
        with self.cam_lock:
            if self.cam_is_running:
                if not self.cam.release():
                    raise Exception("Couldn't release camera object")
                self.cam_is_running = False

    def available_cameras(self) -> Dict:
        cameras = dict()
        cameras['webcams'] = list()
        i = 0

        cam = cv2.VideoCapture(i)
        while cam.isOpened():
            if cam.read()[1] is not None:
                cameras['webcams'].append({'id': i})
            cam.release()
            i += 1
            cam = cv2.VideoCapture(i)
        cam.release()

        if platform.system() == 'Linux' and platform.machine().startswith('arm'):
            import subprocess
            c = subprocess.check_output(["vcgencmd", "get_camera"])
            if int(c.strip()[-1]):
                cameras['pi_camera'] = True
            else:
                cameras['pi_camera'] = False
        else:
            cameras['pi_camera'] = False
        return cameras
