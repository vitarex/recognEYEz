import cv2
import datetime
import os
import time
import numpy as np
import face_recognition
import Library.tracking as tracking
from imutils import paths
import sqlite3 as sql
import errno
import logging

from Library.Mailer import Mailer
from Library.DatabaseHandler import DatabaseHandler
from Library.FileHandler import FileHandler
from Library.MqttHandler import MqttHandler

class FaceHandler:
    resolutions = {"vga": [640, 480], "qvga": [320, 240], "qqvga": [160, 120], "hd": [1280, 720], "fhd": [1920, 1080]}
    font = cv2.FONT_HERSHEY_DUPLEX
    TIME_FORMAT = "%Y_%m_%d__%H_%M_%S"
    unknown_pic_folder_path = os.path.join("Static","unknown_pics")

    def __init__(self,
                 cascade_xml="haarcascade_frontalface_default.xml",
                 db_loc="facerecognition.db",
                 img_root="Images"
                 ):
        logging.info("FaceHandler init started")
        self.database_location = db_loc
        self.db = DatabaseHandler(self.database_location)
        self.settings = dict()
        self.load_settings_from_db()

        # loads video with OpenCV
        self.cam = cv2.VideoCapture(0)
        self.minW = 0.1 * self.cam.get(3)
        self.minH = 0.1 * self.cam.get(4)
        logging.info("Video loaded")

        # ??? creates a variable called ct that contains the CentroidTracker???
        self.ct = tracking.CentroidTracker()
        # sets the path where the haarcascade_frontalface_default.xml file is found (recognEYEz\Library\haarcascade_frontalface_default.xml)
        cascade_path = os.path.dirname(os.path.realpath(__file__)) + "/Library/" + cascade_xml
        # loads the OpenCV face_detector / CascadeClassifier from the cascade_path
        self.face_detector = cv2.CascadeClassifier(cascade_path)
        logging.info("OpenCV facedetector loaded")


        self.database_location = db_loc

        # creates empty directories and fills them with info from database
        self.settings = dict()
        self.load_settings_from_db()
        self.face_data = dict()
        self.unknown_face_data = dict()
        self.load_encodings_from_database()
        self.load_unknown_encodings_from_database()

        self.persons = dict()
        self.unknown_persons = dict()
        self.load_persons_from_database()
        self.load_unknown_persons_from_database()

        # creates two empty dictionaries that will be modified by later functions
        self.visible_persons = dict()
        self.prev_visible_persons = dict()
        #TODO: is self.id2name_dict used anywhere?
        self.id2name_dict = dict()
        self.cam_is_running = False

        self.notification_settings = self.db.load_notification_settings()
        # loads the face_recognition_settings table from the database into self.face_rec_settings
        self.face_rec_settings = self.db.load_face_recognition_settings()
        logging.info("Database tables loaded")

        self.mqtt = MqttHandler(self.database_location)
        self.mqtt.subscribe(self.notification_settings["topic"])
        logging.info("MQTT connected")

        self.file = FileHandler(img_root)
        # TODO: what is self.mail used for????
        self.mail = Mailer("email@gmail.com", "emailpass")
        self.mail.send_mail_cooldown_seconds = 120
        self.mail.last_mail_sent_date = None
        logging.info("FaceHandler init finished")

    def load_settings_from_db(self):
        con = sql.connect(self.database_location)
        c = con.cursor()
        d = dict()
        for row in c.execute("SELECT * FROM face_recognition_settings"):
            d[row[0]] = row[1]
        self.settings = d

    def load_encodings_from_database(self):
        names = list()
        encodings = list()
        for person in self.db.get_known_persons():
                names.append(person.name)
                for encoding in person.encodings:
                    encodings.append(np.frombuffer(encoding.encoding))
        self.face_data = {"names": names, "encodings": encodings}

    def load_unknown_encodings_from_database(self):
        names = list()
        encodings = list()
        for person in self.db.get_unknown_persons():
                names.append(person.name)
                for encoding in person.encodings:
                    encodings.append(np.frombuffer(encoding.encoding))
        self.unknown_face_data = {"names": names, "encodings": encodings}

    def load_persons_from_database(self):
        for person in self.db.get_known_persons():
            encodings = list()
            for i, n in enumerate(self.face_data["names"]):
                if n == person.name:
                    encodings.append(self.face_data["encodings"][i])
            self.persons[person.name] = person

    def load_unknown_persons_from_database(self):
        for person in self.db.get_unknown_persons():
            encodings = list()
            for i, n in enumerate(self.unknown_face_data["names"]):
                if n == person.name:
                    encodings.append(self.unknown_face_data["encodings"][i])
            self.unknown_persons[person.name] = person

    def add_visible_person(self, name):
        if name[0:5] != "_Unk_":
            self.visible_persons[name] = self.persons[name]
            self.persons[name].is_visible = True
        else:
            try:
                self.visible_persons[name] = self.unknown_persons[name]
            except KeyError:
               logging.error("KeyError in add_visible_person for key: " + name + "in dict: " +
                      str(self.unknown_persons.keys()))

    def remove_visible_person(self, name):
        del self.visible_persons[name]
        self.persons[name].is_visible = False

    def start_cam(self):
        if self.cam_is_running:
            return
        # try:
        self.cam = cv2.VideoCapture(int(self.settings["cam_id"]))
        # except NameError:
        #     self.cam = cv2.VideoCapture(int(self.settings["cam_id"]))
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

    def process_next_frame(self, use_dnn=False, show_preview=False, save_new_faces=False, app=None):
        """
        If use_dnn is set, checks faces with a Neural Network, if not, then only detects the faces and tries to guess
        the owner by the positions on the previous frame. If the number of faces differs from the previous frame, or
        this is the first frame, than a NN scan always runs.

        It also:
            - keeps record of all the visible faces in the self.visible_faces
            - calls events when a person arrives, leaves

        :param save_new_faces: save a picture of the new face if parameter is true
        :param use_dnn: use more precise, more time consuming CNN method?
        :param show_preview: show pop-up preview?
        :return: the visible persons, the frame itself and the rectangles corresponding to the found faces
        """

        start_t = time.time()
        ret, frame = self.cam.read()
        if self.settings["flip_cam"] == "on":
            frame = cv2.flip(frame, -1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face_rects = [(y, x + w, y + h, x) for (x, y, w, h) in self.detect_faces(gray)]  # points from height and width

        # executing DNN face recognition on found faces
        if use_dnn or ((len(face_rects) != len(self.visible_persons)) and self.settings["force_dnn_on_new"]):
            self.visible_persons = dict()
            found_names = self.recognize_faces(rgb, face_rects, frame, save_new_faces=save_new_faces)
            for name in found_names:
                if name != "not a face" :  # and name[0:5] != "_Unk_"
                    self.add_visible_person(name)

        centroid_objects = self.ct.update(face_rects, [pers.id for pers in self.visible_persons.values()])

        # drawing dots, rectangles and names on the frame
        if self.visible_persons:
            # drawing names
            for ((top, right, bottom, left), p) in zip(face_rects, self.visible_persons.values()):
                y = top - 15 if top - 15 > 15 else top + 15
                text = p.name
                if not text:
                    text = self.persons[0].name
                cv2.putText(frame, text, (left, y), self.font, 0.4, (0, 255, 0), 2)
            # drawing rectangles
            for (top, right, bottom, left) in face_rects:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        """
        Checking for persons arrived, left by comparing the the visible persons list with the previous one
        The corresponding events are getting called here
        """
        delta_arrived = {p.name: p for p in self.visible_persons.values() if p.name not in self.prev_visible_persons.keys()}
        if delta_arrived:
            self.on_known_face_enters(delta_arrived)

        delta_left = {p.name: p for p in self.prev_visible_persons.values() if p.name not in self.visible_persons.keys()}
        if delta_left:
            self.on_known_face_leaves(delta_left)

        self.prev_visible_persons = self.visible_persons

        # show preview, display FPS
        if show_preview:
            cv2.imshow('camera', frame)
            cv2.waitKey(25) & 0xff
        if use_dnn:
           logging.info("DNN FPS: {:.4f}".format(1/(time.time() - start_t)))
        return self.visible_persons, frame, face_rects  # unknown_rects

    def detect_faces(self, gray):
        """
        Detect faces with HOG from a gray image

        :param gray: gray image (numpy)
        :return: face rectangle (x, y, w, h)
        """
        faces = self.face_detector.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(self.minW), int(self.minH)), )
        return faces  # x, y, w, h

    def recognize_faces(self, rgb, face_rects, frame, save_new_faces=False):
        """
        Make encodings from the found faces than check them against the stored encodings of known faces.
        1st they are checked against known faces.
        2nd if no match found check against recent unknowns
        3rd if no match found check more precisely if it is a face or not
            If it is, add it to the recent unknowns

        Method: creates a 128D vector for every face and compares it to known vectors corresponding to known faces
        There's a name connected to every vector, if a match is found, the name gets +1pt
        Last, the name with the most points wins.

        :param rgb: numpy array corresponding to an RGB pic
        :param face_rects: rectangle coordinates for found faces
        :param frame: numpy array corresponding to the original BGR pic
        :return: a list for the found names
        """
        face_encodings = face_recognition.face_encodings(rgb, face_rects)
        names = []
        # check every face
        for rect_count, e in enumerate(face_encodings):
            matches = face_recognition.compare_faces(
                self.face_data["encodings"], e, tolerance=float(self.settings["dnn_tresh"])
            )
            # if there was a match in knowns
            if True in matches:
                matched_indices = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                for i in matched_indices:
                    name = self.face_data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                else:
                    name = max(counts, key=counts.get)
                names.append(name)
            # if no match found in knowns, check recent unknowns
            else:
                matches = face_recognition.compare_faces(
                    self.unknown_face_data["encodings"], e, tolerance=float(self.settings["dnn_tresh"])
                )
                # if recent unknown
                if True in matches:

                    matched_indices = [i for (i, b) in enumerate(matches) if b]
                    counts = {}

                    for i in matched_indices:
                        try:
                            name = self.unknown_face_data["names"][i]
                            counts[name] = counts.get(name, 0) + 1
                        except IndexError:
                           logging.info("IndexError while recognizing previously seen unknown: " +
                                  str(self.unknown_face_data["names"]) + " and index: " + str(i))
                    if counts:
                        name = max(counts, key=counts.get)
                        names.append(name)
                        logging.info("Found a previously seen unknown: " + name)
                        self.on_unknown_face_found(name)
                        name = name.replace("/", "_").replace(":", "_")
                        if save_new_faces:
                            path = self.unknown_pic_folder_path + "/" + name
                            self.take_cropped_pic(frame, face_rects[rect_count], path)
                # if nor in recent unknowns
                else:
                    # overview HOG with CNN, is it really a face?
                    if self.is_it_a_face(frame, face_rects[rect_count]):
                        unk_name = self.next_unknown_name()
                        self.save_unknown_encoding_to_db(unk_name, e)
                        self.unknown_face_data["encodings"].append(e)
                        self.unknown_face_data["names"].append(unk_name)
                        self.load_unknown_persons_from_database()
                        logging.info(unk_name + " added to unknown database")

                        names.append(unk_name)
                        self.on_unknown_face_found(unk_name)
                        unk_name = unk_name.replace("/", "_").replace(":", "_")
                        path = self.unknown_pic_folder_path + "/" + unk_name
                        self.take_cropped_pic(frame, face_rects[rect_count], path)
                    else:
                        names.append("not a face")  # to make correct indices
                        logging.info("HOG method found a false positive or low quality face")
        return names

    # if there are faces on the picture, this function'll return true
    def is_it_a_face(self, img, r):
        if face_recognition.face_locations(img[r[0]:r[2], r[3]:r[1]], model='cnn'):
            return True
        return False

    # this function returns name of the next unknown person
    def next_unknown_name(self):
        name = "_Unk_" + datetime.datetime.now().strftime("%m/%d_%H:%M:%S")
        while name in self.unknown_face_data["names"]:
            name = name + "_"
        return name

    # Known person arrived
    def on_known_face_enters(self, persons):
        logging.info("Entered: " + str(persons.keys()))

    # The known person left the camera
    def on_known_face_leaves(self, persons):
        logging.info("Left: " + str(persons.keys()))

    def on_unknown_face_found(self, name):
        pass

    #Type the id of the new person
    def gather_new_face_data(self, id):
        face_id = input('\n enter user id and press <return> ==>  ')

    def save_unknown_encoding_to_db(self, name, encoding):
        self.db.add_encoding(name, encoding.tobytes())

    def train_dnn(self, dataset=os.path.join("Static", "dnn")):
        if self.cam_is_running:
            self.stop_cam()
        logging.info("quantifying faces...")
        self.db.empty_encodings()
        logging.info("Encodings table truncated")

        image_paths = list(paths.list_images(dataset))

        # initialize the list of known encodings and known names
        known_encodings = []
        known_names = []
        for (i, image_path) in enumerate(image_paths):
            # extract the person name from the image path
            name = image_path.split(os.path.sep)[-2]
            logging.info("processing image {}/{} - {}".format(i + 1, len(image_paths), name))
            image = cv2.imread(image_path)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb, model="hog")

            encodings = face_recognition.face_encodings(rgb, boxes)

            # loop over the encodings
            for encoding in encodings:
                # add each encoding + name to our set of known names and
                # encodings
                known_encodings.append(encoding)
                known_names.append(name)

                # dump the facial encodings + names to disk
        logging.info("Loading data into the DB...")

        person_names = (person.name for person in self.db.get_persons())
        #logging.info(persons)
        for n in known_names:
            if n not in person_names:
                logging.info("Inserting new name to DB: " + n)
                self.db.add_person(n, False)
                person_names.append(n)

        for n, e in zip(known_names, known_encodings):
            self.db.add_encoding(n, e.tobytes())
        self.reload_from_db()

    def reload_from_db(self):
        self.load_persons_from_database()
        self.load_unknown_persons_from_database()
        self.load_encodings_from_database()
        self.load_unknown_encodings_from_database()

    def take_cropped_pic(self, img, r, folder_path="Static/unknowns/", name=None):
        if name is None:
            name = datetime.datetime.now().strftime(self.TIME_FORMAT)
        path = folder_path + "/" + name + '.png'
        try:
            os.makedirs(folder_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        cv2.imwrite(path, img[r[0]:r[2], r[3]:r[1]])
        logging.info("Picture taken: " + path)


class Face:
    def __init__(self, rect):
        self.rect = rect
        self.person = Person(0, "Unknown", None)


class Person:
    def __init__(self, id, name, encodings, preference, thumbnail=None):
        self.id = id
        self.name = name
        self.encodings = encodings
        self.pref = preference
        self.is_visible = False
        self.thumbnail = thumbnail
