import sqlite3 as sql
from datetime import datetime
import logging
from peewee import *
from typing import List
import logging
from pathlib import Path
from imutils import paths

db = SqliteDatabase('recogneyez.db')


class DBModel(Model):
    _handler = None
    class Meta:
        database = db


class Person(DBModel):
    name = TextField(unique=True)
    preference = TextField(null=True)
    first_seen = DateTimeField(null=True)
    last_seen = DateTimeField(null=True)
    thumbnail = DeferredForeignKey(
        'Image', deferrable='INITIALLY DEFERRED', on_delete='SET_NULL', null=True)
    unknown = BooleanField(default=True)

    def change_name(self, new_name: str):
        with db.atomic():
            self.update()

    def merge_with(self, other: 'Person') -> bool:
        with db.atomic():
            self.encodings.update(person=other)
            self.images.update(person=other)
        self.remove()

    def convert_to_known(self):
        self.unknown = False
        with db.atomic():
            self.save()

    def remove(self):
        with db.atomic():
            self.delete_instance()
        self._invalidate_handler()

    def add_image(self, image_name: str, set_as_thumbnail: bool = False):
        image = Image()
        image.name = image_name
        image.person = self
        with db.atomic():
            image.save()

        if set_as_thumbnail:
            self.set_thumbnail(image)

        self._invalidate_handler()

        logging.info("{} image was added for the person {}".format(
            image_name, self.name))

    def add_encoding(self, encodingbytes: bytes):
        encoding = Encoding()
        encoding.encoding = encodingbytes
        encoding.person = self
        with db.atomic():
            encoding.save()

        self._invalidate_handler()

        logging.info("A new encoding was added for the person {}".format(self.name))

    def set_thumbnail(self, thumbnail: 'Image'):
        self.thumbnail = thumbnail
        with db.atomic():
            self.save()

    def _invalidate_handler(self):
        if self._handler is not None:
            self._handler.invalidate()


class Encoding(DBModel):
    encoding = BlobField(null=True)
    person = ForeignKeyField(Person, backref='encodings', on_delete='CASCADE')


class UserEvent(DBModel):
    datetime = DateTimeField()
    event = TextField()


class Image(DBModel):
    name = TextField(unique=True)
    person = ForeignKeyField(Person, backref='images', on_delete='CASCADE')

    def set_as_thumbnail(self):
        self.person.set_thumbnail(self)


class DatabaseHandler:
    TIME_FORMAT = "%Y.%m.%d. %H:%M:%S"
    _persons_select: Select = None
    _unknown_persons_select: Select = None
    _known_persons_select: Select = None
    _images_select: Select = None
    _encodings_select: Select = None
    valid = False

    def __init__(self, db_location):
        DBModel._handler = self
        
        self.db_loc = db_location
        self.active_connection = False

        db.connect()
        db.create_tables([UserEvent, Encoding, Person, Image])
        self.refresh()

    def add_person(self, name: str, unknown: bool = True, thumbnail: Image = None) -> Person:
        new_person = Person()
        new_person.name = name
        new_person.first_seen = datetime.now()
        new_person.last_seen = new_person.first_seen
        new_person.unknown = unknown
        new_person.thumbnail = thumbnail
        with db.atomic():
            new_person.save()

        self.refresh()

        logging.info("A new {} person was added with the name {}".format(
            'unkown' if unknown else 'known', name))
        
        return new_person
    
    def get_person_by_name(self, name: str) -> Person:
        return Person.get(Person.name == name)

    def open_and_get_cursor(self):
        """ Opens and stores connection for the db + returns a cursor object"""
        self.active_connection = sql.connect(self.db_loc)
        return self.active_connection.cursor()

    def commit_and_close_connection(self):
        """Commits the current changes and closes the connection"""
        self.active_connection.commit()
        self.active_connection.close()
        self.active_connection = False
        return True

    def get_all_events(self) -> List:
        return UserEvent.select()

    def log_event(self, text: str):
        new_event = UserEvent.create(datetime=datetime.now(), event=text)
        new_event.save()

    def invalidate(self):
        self.valid = False

    def refresh(self):
        self._persons_select = Person.select()
        self._known_persons_select = Person.select().where(Person.unknown==False)
        self._unknown_persons_select = Person.select().where(Person.unknown==True)
        self._images_select = Image.select()
        self._encodings_select = Encoding.select()
        self.valid = True

    def get_persons(self) -> List[Person]:
        """
        Returns all persons, known and unknown both
        """
        logging.info("Getting all persons")
        if not self.valid:
            self.refresh()
        return prefetch(self._persons_select, self._images_select, self._encodings_select)

    def get_known_persons(self) -> List[Person]:
        logging.info("Getting known persons")
        if not self.valid:
            self.refresh()
        return prefetch(self._known_persons_select, self._images_select, self._encodings_select)

    def get_unknown_persons(self) -> List[Person]:
        logging.info("Getting unknown persons")
        if not self.valid:
            self.refresh()
        return prefetch(self._unknown_persons_select, self._images_select, self._encodings_select)

    def update_face_recognition_settings(self, form):
        c = self.open_and_get_cursor()
        for key, value in form.items():
            c.execute(
                "UPDATE face_recognition_settings SET value = ? WHERE key = ?", (value, key))
        # not so elegant, but unchecked HTML checkboxes are hard to handle
        checkbox_names = ["force_dnn_on_new", "flip_cam", "cache_unknown"]
        for box in checkbox_names:
            if box not in list(form.keys()):
                logging.info("setting off for: " + box)
                c.execute(
                    "UPDATE face_recognition_settings SET value = ? WHERE key = ?", ("off", box))
        self.commit_and_close_connection()

    def update_notification_settings(self, form):
        c = self.open_and_get_cursor()
        for key, value in form.items():
            c.execute(
                "UPDATE notification_settings SET value = ? WHERE key = ?", (value, key))
        # not so elegant, but unchecked HTML checkboxes are hard to handle
        checkbox_names = ["m_notif_spec", "m_notif_kno",
                          "m_notif_unk", "e_notif_spec", "e_notif_kno", "e_notif_unk"]
        for box in checkbox_names:
            if box not in list(form.keys()):
                logging.info("setting off for: " + box)
                c.execute(
                    "UPDATE notification_settings SET value = ? WHERE key = ?", ("off", box))
        self.commit_and_close_connection()

    # loads the face_recognition_settings table from the database into a dictionary
    def load_face_recognition_settings(self):
        c = self.open_and_get_cursor()
        d = dict()
        for row in c.execute("SELECT * FROM face_recognition_settings"):
            d[row[0]] = row[1]
        return d

    # loads the notification_settings table from the database into a dictionary
    def load_notification_settings(self):
        c = self.open_and_get_cursor()
        d = dict()
        for row in c.execute("SELECT * FROM notification_settings"):
            d[row[0]] = row[1]
        return d
