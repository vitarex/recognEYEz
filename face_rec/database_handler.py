import sqlite3 as sql
from datetime import datetime
import logging


class DatabaseHandler:
    TIME_FORMAT = "%Y.%m.%d. %H:%M:%S"

    def __init__(self, db_location="person.db"):
        self.db_loc = db_location
        self.active_connection = False



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

    def read_log(self):
        active_connection = sql.connect("log.db")
        c = active_connection.cursor()
        retval = list()
        for row in c.execute("SELECT * FROM log ORDER BY time DESC LIMIT 100"):
            retval.append("[" + str(row[0]) + "] " + str(row[1]))
        active_connection.close()
        return retval

    def log(self, text):
        active_connection = sql.connect("log.db")
        c = active_connection.cursor()
        c.execute("INSERT INTO log VALUES (?, ?)", (datetime.now().strftime(self.TIME_FORMAT), text))
        active_connection.commit()
        active_connection.close()

    def remove_name(self, name):
        """Removes the given name from both tables (removes all the encodings)"""
        c = self.open_and_get_cursor()
        c.execute('DELETE FROM persons WHERE name = ?', (name,))
        c.execute('DELETE FROM encodings WHERE name = ?', (name,))
        self.commit_and_close_connection()
        return True

    def remove_unknown_name(self, name):
        """Removes the given name from both tables (removes all the encodings)"""
        c = self.open_and_get_cursor()
        c.execute('DELETE FROM recent_unknowns WHERE name = ?', (name,))
        c.execute('DELETE FROM unknown_encodings WHERE name = ?', (name,))
        self.commit_and_close_connection()
        return True

    def merge_unknown(self, old_name, new_name):
        """"""
        c = self.open_and_get_cursor()
        for row in c.execute('SELECT encoding FROM unknown_encodings WHERE name = ?', (old_name,)):
            c.execute('INSERT INTO encodings VALUES (?, ?)', (new_name, row[0]))
        c.execute('DELETE FROM unknown_encodings WHERE name = ?', (old_name,))
        c.execute('DELETE FROM recent_unknowns WHERE name = ?', (old_name,))
        self.commit_and_close_connection()
        return True

    def create_new_from_unknown(self, name, folder):
        """"""
        c = self.open_and_get_cursor()
        c.execute("INSERT INTO persons (name) VALUES (?)", (folder,) )
        for row in c.execute('SELECT encoding FROM unknown_encodings WHERE name = ?', (name,)):
            c.execute('INSERT INTO encodings VALUES (?, ?)', (folder, row[0]))
        c.execute('DELETE FROM unknown_encodings WHERE name = ?', (name,))
        c.execute('DELETE FROM recent_unknowns WHERE name = ?', (name,))
        self.commit_and_close_connection()
        return True

    def get_persons_data(self, formatting="list"):
        """
        Returns a list containing a list of attributes, which represents persons
            0 - id, 1 - name, 2 - pref, 6 - thumbnail
        Can return a dict:
            key: id, name, pref, thumbnail
        don't use ID in code
        """
        c = self.open_and_get_cursor()
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
        return retval

    def get_unknown_data(self, formatting="list"):
        """
        Returns a list containing a list of attributes, which represents persons
            0 - id, 1 - name
        Can return a dict:
            key: id, name, date
        don't use ID in code
        """
        c = self.open_and_get_cursor()
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
        return retval

    def update_person_data(self, old_name, new_name=None, new_pref=None):
        """
        Updates recors in persons table
        Uses the old name to find the record
        Returns the new person
        """
        if not new_name:
            new_name = old_name
        c = self.open_and_get_cursor()
        if new_pref:
            c.execute("UPDATE persons SET name = ?, preference = ? WHERE name = ?", (new_name, new_pref, old_name))
            c.execute("UPDATE encodings SET name = ? WHERE name = ?", (new_name, old_name))
        else:
            c.execute("UPDATE persons SET name = ? WHERE name = ?", (new_name, old_name))
        retval = c.execute('SELECT * FROM persons WHERE name = ?', (new_name,))
        self.commit_and_close_connection()
        return retval

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

    def change_thumbnail(self, name, pic):
        c = self.open_and_get_cursor()
        c.execute("UPDATE persons SET thumbnail = ? WHERE name = ?", (pic, name))
        self.commit_and_close_connection()

    def get_thumbnail(self, name):
        c = self.open_and_get_cursor()
        c.execute("SELECT thumbnail FROM persons WHERE name=?", (name,))
        pic_name = c.fetchone()
        self.commit_and_close_connection()
        return pic_name

