from flask import Blueprint, render_template, request, redirect
from imutils import paths
from flask import current_app as app
import flask_simplelogin as simplog
from pathlib import Path
import logging
from typing import List

persons_database = Blueprint("persons_database", __name__)


@persons_database.route('/_new_person_from_unk')
@simplog.login_required
def create_new_person_from_unknown():
    """"""
    name = request.args.get('n', 0, type=str)
    person_to_change = app.dh.get_person_by_name(name)
    if person_to_change.unknown:
        logging.info("Creating new person: {}".format(name))
        person_to_change.convert_to_known()
        app.dh.invalidate()
        #app.fh.file.create_new_person_from_unk(name)
    return redirect("/person_db")

@persons_database.route('/person_db')
@simplog.login_required
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

def check_length(list_of_lists: List[List], i: int) -> bool:
    for list_to_check in list_of_lists:
        if len(list_to_check) - 1 < i:
            return False
    return True

@persons_database.route('/_remove_person')
@simplog.login_required
def remove_person():
    """When remove is clicked on person db page"""
    name = request.args.get('p', "missing argument", type=str)
    logging.info("Removing: " + name)
    app.dh.remove_name(name)
    if app.fh.file.remove_known_files(name):
       logging.info("Removed: " + name)
    app.fh.reload_from_db()
    return redirect("/person_db")


@persons_database.route('/_remove_unknown_person')
@simplog.login_required
def remove_unknown_person():
    """When remove is clicked on person db page"""
    name = request.args.get('p', "missing argument", type=str)
    folder = request.args.get('f', "missing argument", type=str)
    logging.info("Removing: " + name)
    if app.fh.file.remove_unknown_files(folder):
       logging.info(name + "'s folder removed successfully")
    if app.dh.remove_unknown_name(name):
       logging.info(name + " removed successfully from the database")
    app.fh.reload_from_db()
    return redirect("/person_db")


@persons_database.route('/_merge_with')
@simplog.login_required
def merge_unknown_with():
    """"""
    name = request.args.get('n', 0, type=str)
    folder = request.args.get('f', 0, type=str)
    merge_to = request.args.get('m2', 0, type=str)
    logging.info("Mergeing: " + name + " and its folder " + folder + " into " + merge_to)
    app.dh.merge_unknown(name, merge_to)
    app.fh.file.merge_unk_file_with(folder, merge_to)
    app.fh.reload_from_db()
    return redirect("/person_db")

