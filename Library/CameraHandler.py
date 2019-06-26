from pathlib import Path
import logging
import threading
import datetime
import cv2
import numpy as np
import urllib.request
from typing import Dict
import platform
import imutils
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
    def __init__(self, cam_id: int, url: str, width: int = 400):
        self.stream = urllib.request.urlopen("url")
        self.bytes = b''
        self.width = width
        self.cam_is_running = True

    def read(self):
        while True:
            self.bytes += self.stream.read(1024)
            start = self.bytes.find(b'\xff\xd8')
            end = self.bytes.find(b'\xff\xd9')
            if start != -1 and end != -1:
                jpg = self.bytes[start:end + 2]
                self.bytes = self.bytes[end + 2:]
                frame = cv2.imdecode(np.fromstring(
                    jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                frame = imutils.resize(frame, width=self.width)
                break
        return frame


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
                if ticker > int(self.app.sh.get_face_recognition_settings()["dnn_scan_freq"])\
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

            if int(self.app.sh.get_face_recognition_settings()["cam_id"]) == 0:
                self.cam = WebcamCamera(
                    int(self.app.sh.get_face_recognition_settings()["cam_id"]),
                    self.app.sh.get_face_recognition_settings()["resolution"])
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
            cam.release()
            cameras['webcams'].append({'id': i})
            i += 1
            cam = cv2.VideoCapture(i)

        cam.release()

        if platform.system == 'Linux' and platform.machine.startswith('arm'):
            import subprocess
            c = subprocess.check_output(["vcgencmd", "get_camera"])
            if int(c.strip()[-1]):
                cameras['pi_camera'] = True
            else:
                cameras['pi_camera'] = False
        else:
            cameras['pi_camera'] = False
        return cameras
