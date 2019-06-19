import sqlite3 as sql
from datetime import datetime
import logging
from peewee import *
from typing import List
import logging

db = SqliteDatabase('recogneyez.db')

class DBModel(Model):
    class Meta:
        database = db

class Person(DBModel):
    name = TextField(unique = True)
    preference = TextField(null = True)
    group = IntegerField(null = True)
    first_seen = DateTimeField(null = True)
    last_seen = DateTimeField(null = True)
    thumbnail = CharField(null = True)
    unknown = BooleanField(default = True)

class Encoding(DBModel):
    encoding = BlobField(null = True)
    person = ForeignKeyField(Person, backref = 'encodings')

class UserEvent(DBModel):
    datetime = DateTimeField()
    event = TextField()

class DatabaseHandler:
    TIME_FORMAT = "%Y.%m.%d. %H:%M:%S"

    def __init__(self, db_location):
        self.db_loc = db_location
        self.active_connection = False
        db.connect()
        db.create_tables([UserEvent, Encoding, Person])

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

    def log_event(self, text:str):
        new_event = UserEvent.create(datetime=datetime.now(), event=text)
        new_event.save()

    def remove_name(self, name:str) -> bool:
        """Removes the given name from both tables (removes all the encodings)"""
        return Person.delete().where(Person.name == name).execute() > 0

    def remove_unknown_name(self, name:str) -> bool:
        """Removes the given name from both tables (removes all the encodings)"""
        return self.remove_name(name)

    def merge_unknown(self, old_name:str , new_name:str) -> bool:
        """"""
        logging.info("DatabaseHandler merge_unknown")
        """ c = self.open_and_get_cursor()
        for row in c.execute('SELECT encoding FROM unknown_encodings WHERE name = ?', (old_name,)):
            c.execute('INSERT INTO encodings VALUES (?, ?)', (new_name, row[0]))
        c.execute('DELETE FROM unknown_encodings WHERE name = ?', (old_name,))
        c.execute('DELETE FROM recent_unknowns WHERE name = ?', (old_name,))
        self.commit_and_close_connection()
        return True """
        merge_to = Person.select().where(Person.name == new_name)
        merge_from = Person.select().where(Person.name == old_name)
        merge_from.encodings.update(person = merge_to).execute()
        return merge_from.delete().execute() > 0

    def create_new_from_unknown(self, name:str , folder:str) -> bool:
        """"""
        logging.info("DatabaseHandler create_new_from_unknown")
        """ c = self.open_and_get_cursor()
        c.execute("INSERT INTO persons (name) VALUES (?)", (folder,) )
        for row in c.execute('SELECT encoding FROM unknown_encodings WHERE name = ?', (name,)):
            c.execute('INSERT INTO encodings VALUES (?, ?)', (folder, row[0]))
        c.execute('DELETE FROM unknown_encodings WHERE name = ?', (name,))
        c.execute('DELETE FROM recent_unknowns WHERE name = ?', (name,))
        self.commit_and_close_connection() """
        Person.update(unknown = False).where(Person.name == name).execute()

    def get_persons(self) -> List[Person]:
        """
        Returns a list containing a list of attributes, which represents persons
            0 - id, 1 - name, 2 - pref, 6 - thumbnail
        Can return a dict:
            key: id, name, pref, thumbnail
        don't use ID in code
        """
        logging.info("DatabaseHandler get_persons")
        """ c = self.open_and_get_cursor()
        if formatting == "list":
            retval = list()
            for row in c.execute('SELECT * FROM persons ORDER BY id'):
                retval.append(row)
        if formatting == "dict":
            retval = list()
            for row in c.execute('SELECT * FROM persons ORDER BY id'):
                id = row[0]
                name = row[1]
                pref = row[2]
                thumbnail = row[6]
                retval.append({"id":id, "name": name, "pref": pref, "thumbnail": thumbnail})
        self.commit_and_close_connection()
        return retval """
        return Person.select()

    def get_known_persons(self) -> List[Person]:
        logging.info("DatabaseHandler get_known_persons")
        return Person.select().where(Person.unknown == False)

    def get_unknown_persons(self) -> List[Person]:
        """
        Returns a list containing a list of attributes, which represents persons
            0 - id, 1 - name
        Can return a dict:
            key: id, name, date
        don't use ID in code
        """
        logging.info("DatabaseHandler get_unknown_persons")
        """ c = self.open_and_get_cursor()
        if formatting == "list":
            retval = list()
            for row in c.execute('SELECT * FROM recent_unknowns ORDER BY id'):
                retval.append(row)
        if formatting == "dict":
            retval = list()
            for row in c.execute('SELECT * FROM persons ORDER BY id'):
                id = row[0]
                name = row[1]
                date = row[2]
                retval.append({"id":id, "name": name, "date": date})
        self.commit_and_close_connection()
        return retval """
        return Person.select().where(Person.unknown == True)

    def update_person_data(self, old_name: str, new_name: str=None, new_pref:str=None) -> Person:
        """
        Updates recors in persons table
        Uses the old name to find the record
        Returns the new person
        """
        logging.info("DatabaseHandler update_person_data")
        """ if not new_name:
            new_name = old_name
        c = self.open_and_get_cursor()
        if new_pref:
            c.execute("UPDATE persons SET name = ?, preference = ? WHERE name = ?", (new_name, new_pref, old_name))
            c.execute("UPDATE encodings SET name = ? WHERE name = ?", (new_name, old_name))
        else:
            c.execute("UPDATE persons SET name = ? WHERE name = ?", (new_name, old_name))
        retval = c.execute('SELECT * FROM persons WHERE name = ?', (new_name,))
        self.commit_and_close_connection()
        return retval """
        if not new_name:
            new_name = old_name
        if new_pref:
            Person.update(name = new_name, preference = new_pref).where(Person.name == old_name).execute()
        else:
            Person.update(name = new_name).where(Person.name == old_name).execute()
        return Person.get(Person.name == new_name)

    def update_face_recognition_settings(self, form):
        c = self.open_and_get_cursor()
        for key, value in form.items():
                c.execute("UPDATE face_recognition_settings SET value = ? WHERE key = ?", (value, key))
        # not so elegant, but unchecked HTML checkboxes are hard to handle
        checkbox_names = ["force_dnn_on_new", "flip_cam", "cache_unknown"]
        for box in checkbox_names:
            if box not in list(form.keys()):
                logging.info("setting off for: " + box)
                c.execute("UPDATE face_recognition_settings SET value = ? WHERE key = ?", ("off", box))
        self.commit_and_close_connection()

    def update_notification_settings(self, form):
        c = self.open_and_get_cursor()
        for key, value in form.items():
                c.execute("UPDATE notification_settings SET value = ? WHERE key = ?", (value, key))
        # not so elegant, but unchecked HTML checkboxes are hard to handle
        checkbox_names = ["m_notif_spec", "m_notif_kno", "m_notif_unk", "e_notif_spec", "e_notif_kno", "e_notif_unk"]
        for box in checkbox_names:
            if box not in list(form.keys()):
                logging.info("setting off for: " + box)
                c.execute("UPDATE notification_settings SET value = ? WHERE key = ?", ("off", box))
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

    def change_thumbnail(self, name: str, pic:str):
        logging.info("DatabaseHandler change_thumbnail")
        """ c = self.open_and_get_cursor()
        c.execute("UPDATE persons SET thumbnail = ? WHERE name = ?", (pic, name))
        self.commit_and_close_connection() """
        Person.update(thumbnail = pic).where(Person.name == name).execute()

    def get_thumbnail(self, name: str) -> Person:
        logging.info("DatabaseHandler get_thumbnail")
        """ c = self.open_and_get_cursor()
        c.execute("SELECT thumbnail FROM persons WHERE name=?", (name,))
        pic_name = c.fetchone()
        self.commit_and_close_connection() """
        return Person.select(Person.thumbnail).where(Person.name == name).get()

    def empty_encodings(self):
        logging.info("DatabaseHandler empty_encodings")
        Encoding.delete().execute()

    def add_person(self, name:str, unknown:bool = True) -> Person:
        logging.info("DatabaseHandler add_person")
        new_person = Person()
        new_person.name = name
        new_person.first_seen = datetime.now()
        new_person.last_seen = datetime.now()
        new_person.unknown = unknown
        new_person.save()
        return new_person

    def add_encoding(self, name: str, encodingbytes: bytes):
        logging.info("DatabaseHandler add_encoding")
        encoding = Encoding()
        encoding.encoding = encodingbytes
        person_by_name = Person.get_or_none(name = name)
        encoding.person = person_by_name[0] if person_by_name is not None else self.add_person(name)
        encoding.save()
