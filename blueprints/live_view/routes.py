from flask import Blueprint, render_template
from flask import current_app as app
from flask_simplelogin import login_required

live_view = Blueprint("live_view", __name__)


@live_view.route('/live_view')
@live_view.route('/')
@login_required
def home():
    names = []
    if app.fh is not None:
        logs = app.dh.get_all_events()
        names = [p.person.name for p in app.fh.tracking_data]
    return render_template(
        "live_view.html",
        running=app.ch.cam_is_processing,
        names=names,
        log=logs,
        runsince=app.fh.running_since.strftime(app.config["TIME_FORMAT"]))
