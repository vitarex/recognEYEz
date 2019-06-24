import cv2
import datetime
from pathlib import Path
import time
import numpy as np
import face_recognition
import Library.tracking as tracking
from imutils import paths
import sqlite3 as sql
import errno
import logging
import os
from itertools import *
from typing import *
from collections import Counter

from Library.Mailer import Mailer
from Library.DatabaseHandler import *
from Library.FileHandler import FileHandler
from Library.MqttHandler import MqttHandler
from Library.CameraHandler import CameraHandler
from Library.Handler import Handler
import sys


class FaceHandler(Handler):
    font = cv2.FONT_HERSHEY_DUPLEX
    TIME_FORMAT = "%Y_%m_%d__%H_%M_%S"
    pic_folder_path = Path("Static", "Images")

    def __init__(self,
                 app,
                 db_loc,
                 cascade_xml="haarcascade_frontalface_default.xml",
                 img_root="Images"
                 ):
        logging.info("FaceHandler init started")
        super().__init__(app)
        self.database_location = db_loc

        # ??? creates a variable called ct that contains the CentroidTracker???
        self.ct = tracking.CentroidTracker()
        # sets the path where the haarcascade_frontalface_default.xml file is found (recognEYEz\Library\haarcascade_frontalface_default.xml)
        cascade_path = Path(__file__).resolve(
        ).parent.joinpath(cascade_xml)
        # loads the OpenCV face_detector / CascadeClassifier from the cascade_path
        self.face_detector = cv2.CascadeClassifier(str(cascade_path))
        logging.info("OpenCV facedetector loaded")

        """ # creates empty directories and fills them with info from database
        self.load_encodings_from_database()
        self.load_unknown_encodings_from_database()

        self.load_persons_from_database()
        self.load_unknown_persons_from_database() """

        # creates two empty dictionaries that will be modified by later functions
        self.visible_persons = set()
        self.prev_visible_persons = set()

        self.notification_settings = self.app.dh.load_notification_settings()

        # loads the face_recognition_settings table from the database into self.face_rec_settings
        self.face_rec_settings = self.app.dh.load_face_recognition_settings()
        logging.info("Database tables loaded")

        # MQTT setup
        self.mqtt = MqttHandler(self.database_location)
        self.mqtt.subscribe(self.notification_settings["topic"])
        logging.info("MQTT connected")

        self.file = FileHandler(img_root)
        # TODO: use mailer to send notifications to users
        self.mail = Mailer("email@gmail.com", "emailpass")
        self.mail.send_mail_cooldown_seconds = 120
        self.mail.last_mail_sent_date = None
        logging.info("FaceHandler init finished")

    def get_known_encodings(self) -> List[Encoding]:
        return [encoding for person in self.app.dh.get_known_persons() for encoding in person.encodings]

    def get_unknown_encodings(self) -> List[Encoding]:
        return [encoding for person in self.app.dh.get_unknown_persons() for encoding in person.encodings]

    def process_next_frame(self, use_dnn=False, show_preview=False, save_new_faces=False):
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
        ret, frame = self.app.ch.cam.read()
        if not ret:
            raise Exception("The camera didn't return a frame object. Maybe it failed to start properly.")
        if self.app.sh.get_face_rec_settings()["flip_cam"] == "on":
            frame = cv2.flip(frame, -1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # detect the faces on the frame, creating absolute rectangle point positions
        face_rects = [(y, x + w, y + h, x)
                      for (x, y, w, h) in self.detect_faces(gray)]

        rect_to_person = dict()
        # executing DNN face recognition on found faces
        if use_dnn or ((len(face_rects) != len(self.visible_persons)) and self.app.sh.get_face_rec_settings["force_dnn_on_new"]):
            # the returned object is a dictionary of rectangles to persons
            # only the rectangles that have a person associated with them are returned here
            rect_to_person = self.recognize_faces(
                rgb, face_rects, frame, save_new_faces=save_new_faces)
            # create a set of persons that are currently visible
            # TODO: what if two detected faces resolve to the same person?
            # while this would usually be a false positive, it still has to be accounted for
            # also twins
            self.visible_persons = set(rect_to_person.values())

        centroid_objects = self.ct.update(
            face_rects, [person.id for person in self.visible_persons])

        # drawing dots(?), rectangles and names on the frame
        if self.visible_persons:
            for rect in face_rects:
                (top, right, bottom, left) = rect
                # drawing rectangles
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 255, 0), 2)
                # drawing names if the rect has a person associated with it
                if rect in rect_to_person.keys():
                    # resolve the person object
                    p = rect_to_person[rect]
                    y = top - 15 if top - 15 > 15 else top + 15
                    text = p.name
                    cv2.putText(frame, text, (left, y),
                                self.font, 0.4, (0, 255, 0), 2)

        # check for arriving and leaving persons, based on set differences
        delta_arrived = self.visible_persons.difference(
            self.prev_visible_persons)
        self.on_known_face_enters(delta_arrived)

        delta_left = self.prev_visible_persons.difference(self.visible_persons)
        self.on_known_face_leaves(delta_left)

        # replace the old set with the new one for the next frame
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
            minSize=(int(self.app.ch.minW), int(self.app.ch.minH)))
        return faces  # x, y, w, h

    def recognize_faces(self, rgb, face_rects, frame, save_new_faces=False) -> Dict[Tuple, Person]:
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
        :return: a dictionary of found persons mapped to their respective rectangle coordinates
        """
        # encode all faces found in the frame
        face_encodings = face_recognition.face_encodings(rgb, face_rects)
        rect_to_person = dict()
        # for every encoding, let's try to resolve it to a person, known or unknown
        for rect_count, e in enumerate(face_encodings):
            # get a flat list of known encodings
            # TODO: there might be a more effective way of handling this
            known_encodings = self.get_known_encodings()
            # check our current encoding against these known persons
            matches = face_recognition.compare_faces(
                list(map(lambda encoding: np.frombuffer(encoding.encoding), known_encodings)), e, tolerance=float(self.app.sh.get_face_rec_settings["dnn_tresh"])
            )
            # if there was a match in the known persons
            if True in matches:
                # face_recognition.compare_faces returns a list of boolean values indicating wether an item in the list matched the encoding
                # so we filter out the encodings which didn't have any matches
                found_encodings = list(compress(known_encodings, matches))
                # let's map every encoding to their person, then count them up
                # then take the person with the most hits as the most likely candidate
                most_likely_match = Counter(
                    map(lambda encoding: encoding.person, found_encodings)).most_common(1)[0][0]
                logging.info("Found a person: {}".format(
                    most_likely_match.name))
                # add the rectangle to person mapping to our dictionary
                rect_to_person[face_rects[rect_count]] = most_likely_match
            # if no match found in knowns, check unknowns
            else:
                # same logic as for known persons
                unknown_encodings = self.get_unknown_encodings()
                matches = face_recognition.compare_faces(
                    list(map(lambda encoding: np.frombuffer(encoding.encoding), unknown_encodings)), e, tolerance=float(
                        self.app.sh.get_face_rec_settings["dnn_tresh"])
                )
                if True in matches:
                    found_encodings = list(
                        compress(unknown_encodings, matches))

                    most_likely_match = Counter(
                        map(lambda encoding: encoding.person, found_encodings)).most_common(1)[0][0]
                    logging.info("Found a previously seen unknown: {}".format(
                        most_likely_match.name))
                    if save_new_faces:
                        # save a new image
                        new_image_name = self.take_cropped_pic(
                            frame, face_rects[rect_count], person=most_likely_match)
                        # record the image on the person object as well
                        most_likely_match.add_image(new_image_name)

                    rect_to_person[face_rects[rect_count]] = most_likely_match
                # if not in unknowns
                else:
                    # check closely if it really is a face
                    if self.is_it_a_face(frame, face_rects[rect_count]):
                        # get a new unknown name
                        unk_name = self.next_unknown_name()
                        logging.info(
                            "Found new unknown person and named them {}".format(unk_name))
                        # add unkown person to db, along with the encoding and image
                        new_unk_person = self.app.dh.add_person(unk_name)
                        new_image_name = self.take_cropped_pic(
                            frame, face_rects[rect_count], person=new_unk_person)
                        new_unk_person.add_encoding(e.tobytes())
                        new_unk_person.add_image(new_image_name, True)
                        # TODO: refresh local copies?

                        # TODO: check which, if any, of the following are needed ->
                        # self.unknown_face_data["encodings"].append(e)
                        # self.unknown_face_data["names"].append(unk_name)
                        # self.load_unknown_persons_from_database()

                        rect_to_person[face_rects[rect_count]] = new_unk_person
                    else:
                        logging.info(
                            "HOG method found a false positive or low quality face")
        return rect_to_person

    # if there are faces on the picture, this function'll return true
    def is_it_a_face(self, img, r):
        if face_recognition.face_locations(img[r[0]:r[2], r[3]:r[1]], model='cnn'):
            return True
        return False

    # this function returns name of the next unknown person
    def next_unknown_name(self):
        name = "_Unk_" + datetime.now().strftime("%m_%d_%H_%M_%S")
        while name in [self.app.dh.get_unknown_persons()]:
            name = name + "_"
        return name

    # Known person arrived
    def on_known_face_enters(self, persons):
        for p in persons:
            logging.info("Entered: {}".format(p.name))

    # The known person left the camera
    def on_known_face_leaves(self, persons):
        for p in persons:
            logging.info("Left: {}".format(p.name))

    def on_unknown_face_found(self, name):
        pass

    # Type the id of the new person
    def gather_new_face_data(self, id):
        face_id = input('\n enter user id and press <return> ==>  ')

    def save_unknown_encoding_to_db(self, name, encoding):
        self.app.dh.add_encoding(name, encoding.tobytes())

    def train_dnn(self, dataset=Path("Static").joinpath("dnn")):
        # TODO: Fix this whole method
        if self.app.ch.cam_is_running:
            self.app.ch.stop_cam()
        logging.info("Quantifying faces...")
        self.app.dh.empty_encodings()
        logging.info("Encodings table truncated")

        image_paths = list(paths.list_images(dataset))

        # initialize the list of known encodings and known names
        known_encodings = []
        known_names = []
        for (i, image_path) in enumerate(image_paths):
            # extract the person name from the image path
            name = image_path.split(Path("/"))[-2]
            logging.info(
                "processing image {}/{} - {}".format(i + 1, len(image_paths), name))
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

        person_names = (person.name for person in self.app.dh.get_persons())
        # logging.info(persons)
        for n in known_names:
            if n not in person_names:
                logging.info("Inserting new name to DB: " + n)
                self.app.dh.add_person(n, False)
                person_names.append(n)

        for n, e in zip(known_names, known_encodings):
            self.app.dh.add_encoding(n, e.tobytes())
        # self.reload_from_db() !!!

    def take_cropped_pic(self, img, r, folder_path="Static/Images/", person=None):
        if person is None:
            # TODO: What happens if there's no person here?
            raise Exception("Not implemented")
            db.add_person()
        # every image of the person gets a unique index
        image_name = '{}_{}.png'.format(
            person.name, len(person.images)+1)
        path = Path(folder_path).joinpath(image_name)
        try:
            os.makedirs(folder_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        cv2.imwrite(str(path), img[r[0]:r[2], r[3]:r[1]])
        logging.info("Picture taken: {}".format(image_name))
        return image_name
