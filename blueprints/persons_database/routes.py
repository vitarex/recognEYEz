from flask import Blueprint, render_template, request, redirect
from imutils import paths
from flask import current_app as app
import flask_simplelogin as simplog
import os
import logging
from typing import List

persons_database = Blueprint("persons_database", __name__)


@persons_database.route('/_new_person_from_unk')
@simplog.login_required
def create_new_person_from_unknown():
    """"""
    name = request.args.get('n', 0, type=str)
    folder = request.args.get('f', 0, type=str)
    logging.info("Creating new person:" + folder)
    app.fh.file.create_new_person_from_unk(folder)
    app.fh.db.create_new_from_unknown(name, folder)
    app.fh.reload_from_db()
    return redirect("/person_db")

@persons_database.route('/person_db')
@simplog.login_required
def person_db_view():
    """

    :return:
    """
    unk_persons = app.fh.db.get_unknown_persons()
    unk_names = list((person.name for person in unk_persons))
    unk_folder_names = list((str(n).replace("/", "_").replace(":", "_") for n in unk_names))
    first_unk_pics = list()
    unk_pic_count = list()
    other_pics = list()
    #import pdb; pdb.set_trace()
    for folder in unk_folder_names:
        try:
            img_list = list(paths.list_images(os.path.join("Static", "unknown_pics", folder)))
            unk_pic_count.append(len(img_list))
            first_unk_pics.append(
                img_list[0].split(os.path.sep)[-1]
            )
            other_pics.append(list(
                (pic.split(os.path.sep)[-1] for pic in img_list))
            )
        except IndexError:
           logging.error("There is an empty folder in the unknown_pics folder.")
    unk_data = list()
    # 0 - original name, 1 - folder name, 2 - first pic name, 3 - pic count
    for i, unk_name in enumerate(unk_names):
        if check_length([unk_folder_names, first_unk_pics, unk_pic_count, other_pics], i):
            unk_data.append({
                    "name": unk_name,
                    "folder": unk_folder_names[i],
                    "first pic": first_unk_pics[i],
                    "pic count": unk_pic_count[i],
                    "other pics": other_pics[i][:9]
                })
    if unk_data:
       logging.info(unk_data[0])
    return render_template(
        "person_db.html",
        persons=app.fh.db.get_known_persons(),  # using list instead of dict because of Jinja handles only lists
        unk_data=unk_data,
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
    app.fh.db.remove_name(name)
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
    if app.fh.db.remove_unknown_name(name):
       logging.info(name + " removed successfully from the database")
    app.fh.reload_from_db()
    return redirect("/person_db")


@persons_database.route('/_merge_with')
@simplog.login_required
# TODO: is merge_unknown_with() used??
def merge_unknown_with():
    """"""
    name = request.args.get('n', 0, type=str)
    folder = request.args.get('f', 0, type=str)
    merge_to = request.args.get('m2', 0, type=str)
    logging.info("Mergeing: " + name + " and its folder " + folder + " into " + merge_to)
    app.fh.db.merge_unknown(name, merge_to)
    app.fh.file.merge_unk_file_with(folder, merge_to)
    app.fh.reload_from_db()
    return redirect("/person_db")

