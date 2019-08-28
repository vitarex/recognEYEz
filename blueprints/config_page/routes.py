from flask import Blueprint, render_template, request, redirect, session
from flask import current_app as app
from flask_simplelogin import login_required
import jinja2
from Library.helpers import parse, parse_list, OKResponse
from nacl.exceptions import InvalidkeyError
import webapp
import logging

config_page = Blueprint("config_page", __name__)


app: webapp.FHApp


@config_page.route('/change_password', methods=['POST'])
@login_required
def change_password():
    try:
        username, old_password, new_password = parse_list(request, ['username', 'old_password', 'new_password'], True)
        app.dh.get_user_by_name(username).change_password(old_password, new_password)
    except InvalidkeyError as e:
        return str(e), 401
    return OKResponse()


@config_page.route('/config')
@login_required
def config_view():
    return render_template(
        "config.html",
        frec=app.sh.load_face_recognition_settings(),
        camera_settings=app.sh.get_face_recognition_settings()["camera-settings"],
        available_cameras=app.ch.available_cameras(),
        available_picamera=app.ch.available_picamera(),
        notif=app.sh.load_notification_settings(),
        username=session['simple_username']
    )

@jinja2.contextfilter
@config_page.app_template_filter()
def get_setting(_, frec, camera_name, setting_name):
    for setting in frec["camera-settings"]:
        if setting["setting-name"] == camera_name:
            try:
                return setting[setting_name]
            except KeyError:
                return None


@config_page.route('/face_recognition_settings', methods=['POST'])
@login_required
def update_face_recognition_settings():
    app.sh.save_face_rec_configuration(app.sh.transform_form_to_dict(request.form))
    with app.ch.cam_lock:
        if app.ch.cam_is_running:
            app.ch.stop_cam()
            app.ch.start_cam()
    return redirect("/config")


@config_page.route('/notification_settings', methods=['POST'])
@login_required
def update_notification_settings():
    app.sh.save_notification_configuration(app.sh.transform_form_to_dict(request.form))
    return redirect("/config")


@config_page.route('/delete_camera_config', methods=['POST'])
@login_required
def remove_camera_settings():
    camera_setting = parse(request, 'setting_name', raise_if_none=True)
    app.sh.remove_camera_settings(camera_setting)
    logging.info("Removed camera setting {}".format(camera_setting))
    return OKResponse()

@config_page.route('/add_new_preset', methods=['GET'])
@login_required
def add_new_preset():
    app.sh.add_camera_setting()
    logging.info("Added new camera setting")
    return redirect("/config")
