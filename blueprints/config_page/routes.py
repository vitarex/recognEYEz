from flask import Blueprint, render_template, request, redirect
from flask import current_app as app
import flask_simplelogin as simplog

from WebApplication.webapp import set_hashed_login_passwd

config_page = Blueprint("config_page", __name__)


@config_page.route('/change_password', methods=['POST'])
# @simplog.login_required TODO ez igy nem maradhat
def change_password():
    set_hashed_login_passwd(request.form["new_password"])
    return redirect("/config")


@config_page.route('/config')
# @simplog.login_required TODO ez igy nem maradhat
def config_view():
    return render_template(
        "config.html",
        frec=app.fh.db.load_face_recognition_settings(),
        notif=app.fh.db.load_notification_settings()
    )


@config_page.route('/face_recognition_settings', methods=['POST'])
@simplog.login_required
def update_face_recognition_settings():
    app.fh.db.update_face_recognition_settings(request.form)
    restart = app.fh.cam_is_running
    app.fh.load_settings_from_db()
    if restart:
        app.fh.stop_cam()
        app.fh.start_cam()
    return render_template(
        "config.html",
        frec=app.fh.db.load_face_recognition_settings(),
        notif=app.fh.db.load_notification_settings()
    )


@config_page.route('/notification_settings', methods=['POST'])
@simplog.login_required
def update_notification_settings():
    app.fh.db.update_notification_settings(request.form)
    return render_template(
        "config.html",
        frec=app.fh.db.load_face_recognition_settings(),
        notif=app.fh.db.load_notification_settings()
    )
