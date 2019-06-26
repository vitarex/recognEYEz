from flask import Blueprint, render_template, request, redirect
from flask import current_app as app
import flask_simplelogin as simplog
import webapp

from webapp import set_hashed_login_passwd

config_page = Blueprint("config_page", __name__)


app: webapp.FHApp


@config_page.route('/change_password', methods=['POST'])
@simplog.login_required
def change_password():
    set_hashed_login_passwd(request.form["new_password"])
    return redirect("/config")

camera_dict = {
        "pi_camera": True,
        "webcams":[
            {
                "id": 0,
                "name": "webcam0"
            },
            {
                "id": 1,
                "name": "webcam1"
            }
        ]
    }


@config_page.route('/config')
@simplog.login_required
def config_view():
    return render_template(
        "config.html",
        frec=app.sh.get_face_recognition_settings(),
        notif=app.sh.get_notification_settings(),
        cam_dict=camera_dict
    )


@config_page.route('/face_recognition_settings', methods=['POST'])
@simplog.login_required
def update_face_recognition_settings():
    app.sh.update_face_recognition_settings(request.form)
    with app.ch.cam_lock:
        if app.ch.cam_is_running:
            app.ch.stop_cam()
            app.ch.start_cam()
    return redirect("/config")


@config_page.route('/notification_settings', methods=['POST'])
@simplog.login_required
def update_notification_settings():
    app.sh.update_notification_settings(request.form)
    return redirect("/config")
