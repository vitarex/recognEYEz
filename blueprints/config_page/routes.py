from flask import Blueprint, render_template, request, redirect
from flask import current_app as app
from flask_simplelogin import login_required
import jinja2
from Library.helpers import parse, parse_list, OKResponse
import webapp

config_page = Blueprint("config_page", __name__)


app: webapp.FHApp


@config_page.route('/change_password', methods=['POST'])
@login_required
def change_password():
    app.dh.get_user_by_name(request.form['username']).change_password(request.form["old_password"], request.form["new_password"])
    return redirect("/config")


@config_page.route('/config')
@login_required
def config_view():
    return render_template(
        "config.html",
        frec=app.sh.get_face_recognition_settings(),
        notif=app.sh.get_notification_settings(),
        cam_dict=app.ch.available_cameras()
    )

@jinja2.contextfilter
@config_page.app_template_filter()
def get_setting(_, frec, camera_name, setting_name):
    for setting in frec["camera_settings"]:
        if setting["camera"] == camera_name:
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
    email, broker_url, port, topic, m_notif_spec, m_notif_kno, m_notif_unk, e_notif_spec, e_notif_kno, e_notif_unk = parse_list(request, ["email", "broker_url", "port", "topic", "m_notif_spec", "m_notif_kno", "m_notif_unk", "e_notif_spec", "e_notif_kno", "e_notif_unk"])
    app.sh.update_notification_settings(app.sh.transform_form_to_dict(request.form))
    return redirect("/config")
