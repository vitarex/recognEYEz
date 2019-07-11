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

    def get_camera_setting_by_name(self, setting_name: str) -> Dict:
        """Get a specific camera setting by its name

        Arguments:
            setting_name {str} -- The camera setting's unique name

        Returns:
            Dict -- The camera setting
        """
        self.get_face_recognition_settings()
        return self.__face_recognition_settings["camera-settings"][self.get_current_settings_index(
            self.__face_recognition_settings,
            setting_name)]

    def get_face_recognition_settings(self) -> Dict:
        """Get the dictionary containing settings related to the face recognition process

        Returns:
            Dict -- Face recognition setting dictionary
        """
        if not self.__face_recognition_settings:
            self.__face_recognition_settings = self.load_face_recognition_settings()
        return self.__face_recognition_settings

    def load_face_recognition_settings(self) -> Dict:
        """Load the face recognition setting JSON as a dictionary from the file system

        Returns:
            Dict -- The face recognition setting dictionary
        """
        with open("Data/FaceRecSettings.json") as ffp:
            return json.load(ffp)

    def transform_form_to_dict(self, form) -> Dict:
        """Transform the form data coming from the API into a friendlier format
        Parses string values into numbers and bools

        Arguments:
            form {MultiDict} -- Form data

        Returns:
            Dict -- Transformed data
        """
        tr_form = {}
        for key, value in form.items():
            if value == "on":
                tr_form[key] = True
            elif value == "off":
                tr_form[key] = False
            elif "-float" in key:
                if not value == "":
                    tr_form[key.replace("-float", "")] = float(value)
            elif "-int" in key:
                if not value == "":
                    tr_form[key.replace("-int", "")] = int(value)
            else:
                tr_form[key] = value
        return tr_form

    def save_face_rec_configuration(self, transformed_form_data):
        """Overwrite the face recognition JSON setting file on the file system

        Arguments:
            transformed_form_data {Dict} -- Dictionary containing the new setting values
        """
        current_settings_dict = self.get_face_recognition_settings()
        settings_index = self.get_current_settings_index(current_settings_dict, transformed_form_data["selected-setting-static"])
        transformed_form_data["selected-setting-static"] = transformed_form_data["setting-name"]
        for key, value in transformed_form_data.items():
            if key.endswith("-static"):
                current_settings_dict[key.replace("-static", "")] = value
            else:
                current_settings_dict["camera-settings"][settings_index][key] = value

        with open(Path("Data/FaceRecSettings.json"), 'w') as ffp:
            json.dump(current_settings_dict, ffp, indent=3)
        self.__face_recognition_settings = current_settings_dict

    def get_current_settings_index(self, current_settings_dict, setting_name) -> int:
        """Get the index of a camera setting based on a setting name
        If a setting with the given cannot be found, it is added to the end of the list

        Arguments:
            current_settings_dict {Dict} -- The settings dictionary to parse
            setting_name {str} -- Setting name to look for

        Returns:
            int -- Zero based index of the camera setting
        """
        for i, settings in enumerate(current_settings_dict["camera-settings"]):
            if settings["setting-name"] == setting_name:
                return i
        current_settings_dict["camera-settings"].append({})
        return len(current_settings_dict["camera-settings"])-1

    def remove_camera_settings(self, camera_settings):
        new_dict = self.load_face_recognition_settings()
        for key, value, in new_dict:
            if key == camera_settings :
                del dict[key]
        with open(Path("Data/FaceRecSettings.json"), 'w') as ffp:
            json.dump(new_dict, ffp, indent=3)
        self.__face_recognition_settings = new_dict

