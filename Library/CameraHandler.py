from pathlib import Path
import logging
import threading
import datetime
import cv2
from Library.Handler import Handler


class OpencvCamera:
    resolutions = {"vga": (640, 480), "qvga": (320, 240), "qqvga": (
        160, 120), "hd": (1280, 720), "fhd": (1920, 1080)}

    def __init__(self, cam_id: int, url: str = None):
        if url is not None:
            self.cam = cv2.VideoCapture(url)
        else:
            self.cam = cv2.VideoCapture(cam_id)
        self.cam_is_running = True

    @classmethod
    def from_url(cls, url: str):
        return cls(0, url)

    @classmethod
    def from_id(cls, id: int):
        return cls(id)

    def set_resolution(self, res: str):
        res = self.resolutions[res]
        return self.cam.set(4, res[1]) and self.cam.set(3, res[0])

    def read(self):
        return self.cam.read()

    def release(self) -> bool:
        try:
            self.cam.release()
            return True
        except Exception as e:
            print(e)
            return False


class CameraHandler(Handler):
    cam: OpencvCamera = None
    cam_lock: threading.RLock = threading.RLock()

    def __init__(self, app):
        super().__init__(app)
        # loads video with OpenCV
        self.cam_is_running = False
        self.cam_is_processing = False
        logging.info("Camera opened")

    def camera_start_processing(self):
        with self.cam_lock:
            if not self.cam_is_running:
                self.start_cam()
            logging.info("The camera handler object: {}".format(self))
            if self.app.fh\
                    and self.cam_is_running\
                    and not self.cam_is_processing:
                self.app.fh.running_since = datetime.datetime.now()
                if self.app.camera_thread is None or not self.app.camera_thread.isAlive():
                    self.app.camera_thread = threading.Thread(
                        target=self.camera_process, daemon=True)
                    self.app.camera_thread.start()
                self.cam_is_processing = True
                logging.info("Camera started")
            logging.info("Camera scanning started")

    def camera_stop_processing(self):
        with self.cam_lock:
            if self.app.fh and self.cam_is_running and self.cam_is_processing:
                self.stop_cam()
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
                if ticker > int(self.app.sh.get_face_recognition_settings()["dnn-scan-freq"])\
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

            active_camera_setting = self.app.sh.get_camera_setting_by_name(
                self.app.sh.get_face_recognition_settings()["selected-setting"])

            def create_camera():
                if active_camera_setting["preferred-id"] == -1:
                    self.cam = OpencvCamera.from_url(
                        active_camera_setting["URL"])
                    self.cam_is_running = self.cam.cam_is_running
                    logging.info("IP camera started")
                else:
                    self.cam = OpencvCamera.from_id(
                        active_camera_setting["preferred-id"])
                    self.cam_is_running = self.cam.cam_is_running
                    logging.info("Web camera started")

            create_camera()
            self.cam.set_resolution(active_camera_setting["resolution"])

            if not self.cam.read()[0]:
                logging.error("Could not set resolution. The camera might not support changing the resolution. Retrying...")
                self.cam.release()
                create_camera()

            logging.info("Camera object: {}".format(self.cam))

    def stop_cam(self):
        with self.cam_lock:
            if self.cam_is_running:
                self.cam_is_running = False
                if self.app.camera_thread is not None:
                    self.app.camera_thread.join()
                if not self.cam.release():
                    raise Exception("Couldn't release camera object")

    def available_cameras(self) -> int:
        """Discover the number of currently available cameras
        This includes all hardware cameras, such as webcams and the RPi cam

        Returns:
            int -- Number of available hardware cameras
        """
        i = 0
        cam = cv2.VideoCapture(i)
        try:
            while cam.isOpened():
                if cam.read()[1] is None:
                    break
                cam.release()
                i += 1
                cam = cv2.VideoCapture(i)
            cam.release()
        except Exception as e:
            logging.error(e)
        finally:
            if cam.isOpened():
                cam.release()
        return i
