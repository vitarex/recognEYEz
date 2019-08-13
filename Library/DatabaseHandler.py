from datetime import datetime
import logging
from typing import List
import json
from pathlib import Path
from nacl import pwhash
from peewee import (TextField, DateTimeField, DeferredForeignKey, BooleanField,
                    SqliteDatabase, prefetch, Model, ForeignKeyField, BlobField, Select)

from Library.Handler import Handler


class DBModel(Model):
    """Base model for peewee models"""
    _handler = None

    class Meta:
        database: SqliteDatabase = None

def bulk_update(model: DBModel, item_list: List, field_list: List, value_list: List):
    """Bulk update the given fields with the given values on the list of items

    Arguments:
        model {DBModel} -- The model the items belong to
        item_list {List} -- The list of items to update
        field_list {List} -- The list of fields to update on the items
        value_list {List} -- The list of values to assign to their respective fields

    Raises:
        AssertionError: Incorrect list lengths given
    """
    with model._meta.database.atomic():
        if len(item_list) > 0 and len(field_list) > 0 and len(field_list) == len(value_list):
            for field, value in zip(field_list, value_list):
                for item in item_list:
                    setattr(item, field.name, value)
            model.bulk_update(item_list, field_list)
        else:
            raise AssertionError("Incorrect arguments given")

class Person(DBModel):
    name = TextField(unique=True)
    preference = TextField(null=True)
    first_seen = DateTimeField(null=True)
    last_seen = DateTimeField(null=True)
    thumbnail = DeferredForeignKey(
        'Image', deferrable='INITIALLY DEFERRED', on_delete='SET_NULL', null=True)
    unknown = BooleanField(default=True)

    def change_name(self, new_name: str):
        """Change person's name

        Arguments:
            new_name {str} -- The new name of the person
        """
        self.name = new_name
        with self._meta.database.atomic():
            self.save()
        self._invalidate_handler()

    def change_pref(self, new_pref: str):
        """Change person's preferences

        Arguments:
        new_pref {str} -- The new preferences of the person
        """
        self.preference = new_pref
        with self._meta.database.atomic():
            self.save()
        self._invalidate_handler()

    def merge_with(self, other: 'Person'):
        """Merge with other person

        Arguments:
            other {Person} -- The person to merge this person to
        """
        with self._meta.database.atomic():
            encodings = list(self.encodings)
            images = list(self.images)

            bulk_update(Encoding, encodings, [Encoding.person], [other])
            bulk_update(Image, images, [Image.person], [other])

            self.remove()

    def convert_to_known(self):
        """Convert person to known person
        """
        self.unknown = False
        with self._meta.database.atomic():
            self.save()

    def remove(self):
        """Remove person from database
        """
        with self._meta.database.atomic():
            self.delete_instance()
        self._invalidate_handler()

    def remove_image(self, image_name: str):
        with self._meta.database.atomic():
            next(i for i in self.images if i.name == image_name).delete_instance()
        self._invalidate_handler()

    def add_image(self, image_name: str, set_as_thumbnail: bool = False):
        """Add new image for this person, optionally setting it as the thumbnail

        Arguments:
            image_name {str} -- The name of the image file to add

        Keyword Arguments:
            set_as_thumbnail {bool} -- Whether to set the new image as the thumbnail of the person (default: {False})
        """
        image = Image()
        image.name = image_name
        image.person = self
        with self._meta.database.atomic():
            image.save()

            if set_as_thumbnail:
                self.set_thumbnail(image)

        self._invalidate_handler()

        logging.info("{} image was added for the person {}".format(
            image_name, self.name))

    def add_encoding(self, encodingbytes: bytes):
        """Add a new face encoding for the person

        Arguments:
            encodingbytes {bytes} -- The face encoding to associate with the person
        """
        encoding = Encoding()
        encoding.encoding = encodingbytes
        encoding.person = self
        with self._meta.database.atomic():
            encoding.save()

        self._invalidate_handler()

        logging.info(
            "A new encoding was added for the person {}".format(self.name))

    def set_thumbnail(self, thumbnail: 'Image'):
        """Change the person's thumbnail

        Arguments:
            thumbnail {Image} -- The Image object to set the thumbnail to
        """
        self.thumbnail = thumbnail
        with self._meta.database.atomic():
            self.save()

    def _invalidate_handler(self):
        """Invalidate the DatabaseHandler the model is associated with, causing a cache bust
        """
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
        """Set as the thumbnail for the person of this image
        """
        self.person.set_thumbnail(self)

    def change_person(self, to_person: Person):
        """Change the person of the image

        Arguments:
            to_person {Person} -- The new owner of the image
        """
        self.person = to_person
        with self._meta.database.atomic():
            self.save()


class User(DBModel):
    name = TextField(unique=True)
    password_hash = BlobField()

    def verify(self, password: str) -> bool:
        """Verify the login attempt from this user

        Arguments:
            password {str} -- The password of the login attempt

        Returns:
            bool -- Whether the login was accepted
        """
        return pwhash.verify(self.password_hash, password.encode())

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change the user's password

        Arguments:
            old_password {str} -- The old password of the user
            new_password {str} -- The new password of the user

        Returns:
            bool -- Whether the password change was succesful
        """
        if self.verify(old_password):
            self.password_hash = pwhash.str(new_password.encode())
            return True
        return False


class DatabaseHandler(Handler):
    TIME_FORMAT = "%Y.%m.%d. %H:%M:%S"
    _persons_select: Select = None
    _unknown_persons_select: Select = None
    _known_persons_select: Select = None
    _images_select: Select = None
    _encodings_select: Select = None
    valid = False
    database: SqliteDatabase = None

    def __init__(self, app, db_location):
        super().__init__(app)

        DBModel._handler = self
        self.database = SqliteDatabase(db_location, pragmas=(('foreign_keys', 'on'),))
        self.database.connect()
        self.init_tables([UserEvent, Encoding, Person, Image, User])
        # db.close()
        self.refresh()

    def init_tables(self, tables: List[DBModel]):
        # for some reason, changing the meta database on the DBModel doesn't inherit to the model implementations
        # so we have to set it on each table manually
        for table in tables:
            table._meta.database = self.database
        self.database.create_tables(tables)

    def add_person(self, name: str, unknown: bool = True, thumbnail: Image = None) -> Person:
        new_person = Person()
        new_person.name = name
        new_person.first_seen = datetime.now()
        new_person.last_seen = new_person.first_seen
        new_person.unknown = unknown
        new_person.thumbnail = thumbnail
        with self.database.atomic():
            new_person.save()

        self.refresh()

        logging.info("A new {} person was added with the name {}".format(
            'unkown' if unknown else 'known', name))

        return new_person

    def get_person_by_name(self, name: str) -> Person:
        return Person.get(Person.name == name)

    def get_user_by_name(self, name: str) -> User:
        return User.get(User.name == name)

    def get_image_by_name(self, name: str) -> Image:
        return Image.get(Image.name == name)

    def get_all_events(self) -> List:
        return UserEvent.select()

    def log_event(self, text: str):
        new_event = UserEvent.create(datetime=datetime.now(), event=text)
        new_event.save()

    def invalidate(self):
        self.valid = False

    def refresh(self):
        self._persons_select = Person.select()
        # peewee doesn't work with an equality check in the format of Person.unknown is False
        # instead we should use Person.unknown == False
        self._known_persons_select = Person.select().where(Person.unknown == False)  # NOQA
        self._unknown_persons_select = Person.select().where(Person.unknown == True)  # NOQA
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

    # loads the face_recognition_settings table from the database into a dictionary

    def load_face_recognition_settings(self):
        with open(Path("Data/FaceRecSettings.json")) as json_file:
            sett = json.load(json_file)
        return sett

    # loads the notification_settings table from the database into a dictionary
    def load_notification_settings(self):
        with open(Path("Data/NotificationSettings.json")) as json_file:
            sett = json.load(json_file)
        return sett
