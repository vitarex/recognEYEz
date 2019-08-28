from pathlib import Path
import logging
import threading
import datetime
import cv2
from Library.Handler import Handler
from time import sleep

class Camera:
    resolutions = {"vga": (640, 480), "qvga": (320, 240), "qqvga": (
        160, 120), "hd": (1280, 720), "fhd": (1920, 1080)}

    def set_resolution(self, res: str):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def release(self):
        raise NotImplementedError


try:
    from picamera import PiCamera
    from picamera.array import PiMotionAnalysis, PiRGBAnalysis

    class MotionFrame(PiMotionAnalysis):
        camera = None

        def analyze(self, frame):
            self.camera.current_motion = frame

    class BGRFrame(PiRGBAnalysis):
        camera = None

        def analyze(self, frame):
            self.camera.current_frame = frame

    class RaspberryCamera(Camera):
        current_frame = None
        current_motion = None
        capture_thread: threading.Thread
        _run: bool

        def __del__(self):
            if self.capture_thread is not None\
                    and self.capture_thread.isAlive():
                self.capture_thread.join()

        def set_resolution(self, res: str):
            self.resolution = self.resolutions[res]

        def start_recording(self):
            self.capture_thread = threading.Thread(
                target=self.start, daemon=True
            )
            self._run = True
            self.capture_thread.start()
            self.cam_is_running = True

        def release(self) -> bool:
            self._run = False
            self.capture_thread.join()
            return True

        def start(self):
            sleep(2)
            with PiCamera() as camera:
                with BGRFrame(camera) as regular_output:
                    regular_output.camera = self
                    with MotionFrame(camera) as motion_output:
                        motion_output.camera = self
                        camera.resolution = self.resolution
                        camera.framerate = 30
                        camera.start_recording(
                            "/dev/null",
                            format="h264",
                            motion_output=motion_output
                        )
                        camera.start_recording(
                            regular_output,
                            splitter_port=2,
                            format="bgr",
                        )
                        while self._run:
                            camera.wait_recording(1)
                        camera.stop_recording()
                        camera.stop_recording(splitter_port=2)

        def read(self):
            return (True, self.current_frame)


except ImportError:
    pass


class OpencvCamera(Camera):
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
    cam: Camera = None
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
        try:
            if self.app.sh.get_camera_setting_by_name(
                    self.app.sh.get_face_recognition_settings()["selected-setting"])["preferred-id"] == -2:
                sleep(2)
            while self.cam_is_running:
                try:
                    if (ticker > int(self.app.sh.get_face_recognition_settings()["dnn-scan-freq"])
                        and int(self.app.sh.get_face_recognition_settings()["dnn-scan-freq"]) != -1)\
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
                        if int(self.app.sh.get_face_recognition_settings()["dnn-scan-freq"]) == -1:
                            ticker = 0
                    ticker += 1
                except AssertionError as e:
                    print(e)
        except Exception as e:
            if self.cam:
                self.cam.release()
            logging.info(e)
            raise e

    def start_cam(self):
        with self.cam_lock:
            if self.cam_is_running:
                return

            active_camera_setting = self.app.sh.get_camera_setting_by_name(
                self.app.sh.get_face_recognition_settings()["selected-setting"])

            def create_camera():
                if active_camera_setting["preferred-id"] == -2:
                    self.cam = RaspberryCamera()
                elif active_camera_setting["preferred-id"] == -1:
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

            if active_camera_setting["preferred-id"] > 0:
                if not self.cam.read()[0]:
                    logging.error("Could not set resolution. The camera might not support changing the resolution. Retrying...")
                    self.cam.release()
                    create_camera()
            if active_camera_setting["preferred-id"] == -2:
                self.cam.start_recording()
                self.cam_is_running = self.cam.cam_is_running
                logging.info("PiCamera startd")

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
        return 3
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

    def available_picamera(self) -> bool:
        try:
            from picamera import PiCamera
            from picamera.exc import PiCameraError
            try:
                with PiCamera():
                    return True
            except PiCameraError:
                logging.error("Could not set up picamera. Please check the camera connection.")
                return False
        except ImportError:
            logging.warning("Picamera module not found, this device is either not a Raspberry,"
                            " or the module is not installed correctly.")
            return False
