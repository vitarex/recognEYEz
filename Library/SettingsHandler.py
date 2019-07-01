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

    def get_face_recognition_settings(self, camera_name: str = None) -> Dict:
        if not self.__face_recognition_settings:
            self.__face_recognition_settings = self.load_face_recognition_settings()
        if camera_name is None:
            return self.__face_recognition_settings
        else:
            return self.__face_recognition_settings["camera_settings"][self.get_current_settings_index(self.__face_recognition_settings, camera_name)]

    def load_face_recognition_settings(self) -> Dict:
        with open("Data/FaceRecSettings.json") as ffp:
            return json.load(ffp)

    def transform_form_to_dict(self, form) -> Dict:
        tr_form = {}
        for key, value in form.items():
            if value == "on":
                tr_form[key] = True
            elif value == "off":
                tr_form[key] = False
            elif "-float-" in key:
                if not value == "":
                    tr_form[key] = float(value)
            elif "-int-" in key:
                if not value == "":
                    tr_form[key] = int(value)
            else:
                tr_form[key] = value
        return tr_form

    def save_face_rec_configuration(self, transformed_form_data) ->Dict:
        current_settings_dict=self.get_face_recognition_settings()
        settings_index = self.get_current_settings_index(current_settings_dict, transformed_form_data["camera"])
        current_settings_dict["selected_camera"] = transformed_form_data["camera"]
        for key, value in transformed_form_data.items():
            if key.endswith("-static"):
                current_settings_dict[key] = value
            else:
                current_settings_dict["camera_settings"][settings_index][key] = value

        with open(Path("Data/FaceRecSettings.json"), 'w') as ffp:
            json.dump(current_settings_dict, ffp, indent=3)
        self.__face_recognition_settings = current_settings_dict

    def get_current_settings_index(self, current_settings_dict, camera_name) -> int:
        for i, settings in enumerate(current_settings_dict["camera_settings"]):
            if settings["camera"] == camera_name:
                return i
        current_settings_dict["camera_settings"].append({})
        return len(current_settings_dict["camera_settings"])-1

