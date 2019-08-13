import datetime
from flask import Flask, render_template
from flask_admin import Admin
from flask_simplelogin import SimpleLogin
import logging
import cv2
from pathlib import Path
from nacl.pwhash import InvalidkeyError

from Library.FaceHandler import FaceHandler
from Library.CameraHandler import CameraHandler
from Library.SettingsHandler import SettingsHandler
from Library.DatabaseHandler import DatabaseHandler
from Library.MqttHandler import MqttHandler
from config import Config


class FHApp(Flask):
    fh: FaceHandler = None
    ch: CameraHandler = None
    sh: SettingsHandler = None
    dh: DatabaseHandler = None
    mh: MqttHandler = None


app: FHApp


def validate_login(login_form):
    """ Override simple_login's loginchecker, thus allowing the use of encrypted passwords """
    try:
        app.dh.get_user_by_name(login_form['username']).verify(login_form['password'])
        return True
    except InvalidkeyError:
        logging.error("Invalid password given for the user {}".format(login_form['username']))
        return False


def on_known_enters(persons):
    """ Custom behaviour for the facehandler's callback method of the same name """
    for person in persons:
        logging.info("Entered: {}".format(person.name))
        app.mh.publish(
            app.fh.notification_settings["topic"],
            "[recognEYEz][ARRIVED][date: {}]: {}".format(datetime.datetime.now().strftime(app.config["TIME_FORMAT"]), person.name)
        )
        app.dh.log_event("[ARRIVED]: {}".format(person.name))
        logging.info("[ARRIVED]: {}".format(person.name))


def on_known_leaves(persons):
    """ Custom behaviour for the facehandler's callback method of the same name """
    for person in persons:
        app.mh.publish(
            app.fh.notification_settings["topic"],
            "[recognEYEz][LEFT][date: {}]: {}".format(datetime.datetime.now().strftime(app.config["TIME_FORMAT"]), person.name)
        )
        app.dh.log_event("[LEFT]: {}".format(person.name))
        logging.info("[LEFT]: {}".format(person.name))


def init_app(app: FHApp, db_loc="recogneyez.db"):
    """ Initializes handlers instance """
    if not app.dh:
        app.dh = DatabaseHandler(app, db_loc)
    if not app.sh:
        app.sh = SettingsHandler(app)
    if not app.mh:
        app.mh = MqttHandler(app)
        app.mh.subscribe(app.sh.get_notification_settings()["topic"])
        logging.info("MQTT connected")
    if not app.ch:
        app.ch = CameraHandler(app)
    if not app.fh:
        app.fh = FaceHandler(app,
                             db_loc,
                             cascade_xml="haarcascade_frontalface_default.xml",
                             img_root=Path("Static").joinpath("dnn")
                             )
        app.fh.running_since = datetime.datetime.now()
        # override the callback methods
        app.fh.on_known_face_enters = on_known_enters
        app.fh.on_known_face_leaves = on_known_leaves

# parameter is the config Class from config.py
def create_app(config_class=Config):
    global app
    app = FHApp(__name__, static_url_path='', static_folder='./Static', template_folder='./Templates')
    app.config.from_object(config_class)
    # t = threading.Thread(target=init_fh, args=(app,))
    # t.start()
    init_app(app)

    # import the blueprints
    from blueprints.live_view.routes import live_view
    app.register_blueprint(live_view)

    from blueprints.config_page.routes import config_page
    app.register_blueprint(config_page)

    from blueprints.persons_database.routes import persons_database
    app.register_blueprint(persons_database)

    from blueprints.person_edit.routes import person_edit
    app.register_blueprint(person_edit)

    from blueprints.actions.routes import actions
    app.register_blueprint(actions)

    from blueprints.errors.handlers import errors
    app.register_blueprint(errors)

    app.dnn_iter = 0
    app.present = []
    app.admin = Admin(app, name='recogneyez', template_mode='bootstrap3')
    app.ticker = 0

    SimpleLogin(app, login_checker=validate_login)
    # cache_buster.register_cache_buster(app)
    app.force_rescan = False

    app.preview_image = cv2.imread("Static/empty_pic.png")

    app.camera_thread = None

    # app.ch.camera_start_processing()
    return app
