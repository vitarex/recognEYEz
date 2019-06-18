from flask import Blueprint, render_template
from flask import current_app as app
import flask_simplelogin as simplog

live_view = Blueprint("live_view", __name__)


@live_view.route('/live_view')
@live_view.route('/')
@simplog.login_required
def home():
    names = []
    if app.fh != None:
        names = [n for n in app.fh.visible_persons.keys()]
    return render_template(
        "live_view.html",
        running=app.fh.cam_is_running,
        names=names,
        log=[],
        runsince=app.fh.running_since.strftime(app.config["TIME_FORMAT"])
    )

