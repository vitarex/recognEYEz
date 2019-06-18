from flask import Blueprint, render_template
from flask import current_app as app
import flask_simplelogin as simplog

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
    logs = app.fh.db.get_all_events()
    names = []
    if app.fh != None:
        names = [n for n in app.fh.visible_persons.keys()]
    return render_template(
        "live_view.html",
        running=app.fh.cam_is_running,
        names=names,
        recpicdate=prev_date,
        log=logs,
        runsince=app.fh.running_since.strftime(app.config["TIME_FORMAT"]))

