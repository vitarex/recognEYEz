from flask import Blueprint, render_template
from flask import current_app as app
import flask_simplelogin as simplog

import pdb

live_view = Blueprint("live_view", __name__)


@live_view.route('/live_view')
@live_view.route('/')
@simplog.login_required
def home():
    global most_recent_scan_date
    # names = []
    # camrun = False
    try:
        prev_date = most_recent_scan_date.strftime(app.TIME_FORMAT)
    except:
        prev_date = "NOT FOUND"
    names = []
    if app.fh != None:
        logs = app.dh.get_all_events()
        names = [p.name for p in app.fh.visible_persons]
    return render_template(
        "live_view.html",
        running=app.fh.cam_is_processing,
        names=names,
        recpicdate=prev_date,
        log=logs,
        runsince=app.fh.running_since.strftime(app.config["TIME_FORMAT"]))

