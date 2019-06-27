from typing import Dict
from pathlib import Path
import json
from Library.Handler import Handler

class SettingsHandler(Handler):
    __face_recognition_settings = dict()
    __notification_settings = dict()

    def __init__(self, app):
        super().__init__(app)

    def get_notification_settings(self) -> Dict:
        if not self.__notification_settings:
            self.__notification_settings = self.load_notification_settings()
        return self.__notification_settings

    def load_notification_settings(self) -> Dict:
        with open("Data/NotificationSettings.json") as nfp:
            return json.load(nfp)

    def update_notification_settings(self, form):
        sett = {}
        for key, value in form.items():
            sett[key] = value
        checkbox_names = ["m_notif_spec", "m_notif_kno",
                          "m_notif_unk", "e_notif_spec", "e_notif_kno", "e_notif_unk"]
        for box in checkbox_names:
            if box not in list(form.keys()):
                sett[box] = "off"
        with open(Path("Data/NotificationSettings.json"), 'w') as nfp:
            json.dump(sett, nfp, indent=3)
        self.__notification_settings = sett

    def get_face_recognition_settings(self) -> Dict:
        if not self.__face_recognition_settings:
            self.__face_recognition_settings = self.load_face_recognition_settings()
        return self.__face_recognition_settings

    def load_face_recognition_settings(self) -> Dict:
        with open("Data/FaceRecSettings.json") as ffp:
            return json.load(ffp)

    def update_face_recognition_settings(self, form_dict):
        sett = self.load_face_recognition_settings()
        for key, value in form_dict.items():
            sett[key] = value
        with open(Path("Data/FaceRecSettings.json"), 'w') as ffp:
            json.dump(sett, ffp, indent=3)
        self.__face_recognition_settings = sett

    def transform_form_to_dict(self, form) -> Dict:
        tr_form = {}
        for key, value in form.items():
            if value == "on":
                tr_form[key] = True
            elif value == "off":
                tr_form[key] = False
            elif key.endswith("-float"):
                tr_form[key] = float(value)
            elif key.endswith("-int"):
                tr_form[key] = int(value)
            else:
                tr_form[key] = value
        return tr_form