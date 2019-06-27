from flask import Blueprint, render_template, request, redirect
from flask import current_app as app
from flask_simplelogin import login_required
import logging

persons_database = Blueprint("persons_database", __name__)


@persons_database.route('/_new_person_from_unk')
@login_required
def create_new_person_from_unknown():
    """"""
    name = request.args.get('n', 0, type=str)
    person_to_change = app.dh.get_person_by_name(name)
    if person_to_change.unknown:
        logging.info("Creating new person: {}".format(name))
        person_to_change.convert_to_known()
        app.dh.invalidate()
        # app.fh.file.create_new_person_from_unk(name)
    return redirect("/person_db")

@persons_database.route('/person_db')
@login_required
def person_db_view():
    """

    :return:
    """
    return render_template(
        "person_db.html",
        persons=app.dh.get_known_persons(),
        unk_persons=app.dh.get_unknown_persons(),
        folder_location=app.config["PICTURE_FOLDER"]
    )

@persons_database.route('/_remove_person')
@login_required
def remove_person():
    """When remove is clicked on person db page"""
    name = request.args.get('p', "missing argument", type=str)
    logging.info("Removing: " + name)
    app.dh.get_person_by_name(name).remove()
    logging.info("Removed: " + name)
    app.dh.invalidate()
    return redirect("/person_db")


@persons_database.route('/_remove_unknown_person')
@login_required
def remove_unknown_person():
    """When remove is clicked on person db page"""
    name = request.args.get('p', "missing argument", type=str)
    logging.info("Removing: " + name)
    app.dh.get_person_by_name(name).remove()
    logging.info("{} removed successfully from the database".format(name))
    app.dh.invalidate()
    return redirect("/person_db")


@persons_database.route('/_merge_with')
@login_required
def merge_unknown_with():
    """"""
    name = request.args.get('n', 0, type=str)
    merge_to = request.args.get('m2', 0, type=str)
    logging.info("Merging {} into {}".format(name, merge_to))
    app.dh.get_person_by_name(name).merge_with(app.dh.get_person_by_name(merge_to))
    app.dh.invalidate()
    return redirect("/person_db")
