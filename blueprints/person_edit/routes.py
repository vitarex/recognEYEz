from flask import Blueprint, render_template, request, redirect
from flask import current_app as app
from flask_simplelogin import login_required
from pathlib import Path
import logging

from Library.helpers import parse, parse_list, OKResponse

if False:
    import webapp
    app: webapp.FHApp

stat_folder = Path('../../Static')
person_edit = Blueprint("person_edit", __name__, static_folder=stat_folder, static_url_path='/Static')


@person_edit.route('/change_pic_owner', methods=['POST'])
@login_required
def change_pic_owner():
    """Places the selected pic to the selected persons folder"""
    old_name, new_name, pic = parse_list(request, ['oname', 'nname', 'image'], raise_if_none=True)
    logging.info("Moving picture {} from {} to {}".format(pic, old_name, new_name))
    app.dh.get_image_by_name(pic).change_person(app.dh.get_person_by_name(new_name))
    return OKResponse()


@person_edit.route('/edit_known_person/', methods=['GET', 'POST'])
@login_required
def edit_known_person():
    """ Webpage for editing a specific person (name, pref, pictures) """
    name = parse(request, "name")
    if name is None:
        logging.error("No name was passed in")
        return redirect('/person_db')
    person = app.dh.get_person_by_name(name)
    logging.info("The name is: {0} ".format(person.name))
    logging.info("Thumbnail {0} ".format(person.thumbnail.name))
    return render_template(
        "person_edit.html",
        person=person,
        # check if thmb is set (eg in case of manual folder addition
        thumbnail=person.thumbnail or "not set",
        known_persons=app.dh.get_known_persons()
    )


@person_edit.route('/change_thumbnail_for_person', methods=['POST'])
@login_required
def change_thumbnail_for_person():
    """ Changes the thumbnail file name for the person int the database """
    name, pic = parse_list(request, ['name', 'image'], raise_if_none=True)
    logging.info("Setting the thumbnail on the person {} to the image {}".format(name, pic))
    app.dh.get_person_by_name(name).set_thumbnail(app.dh.get_image_by_name(pic))
    return OKResponse()


@person_edit.route('/modify_person', methods=['POST'])
@login_required
def modify_person():
    """ Modifies the given persons parameters in the background"""
    old_name, new_name, extra = parse_list(request, ["old_name", "new_name", "extra"])
    logging.info("Modifying person {}".format(old_name))
    if old_name is None:
        return redirect('/person_db')
    if extra is not None:
        app.dh.get_person_by_name(old_name).change_pref(extra)
    if new_name is not None:
        app.dh.get_person_by_name(old_name).change_name(new_name)
        return redirect("/person_db")

    return OKResponse()


@person_edit.route('/delete_image_of_person', methods=['POST'])
@login_required
def remove_pic_for_person():
    """ Removes the selected picture in the background """
    name, image = parse_list(request, ['name', 'image'], raise_if_none=True)
    app.dh.get_person_by_name(name).remove_picture(image)
    logging.info("Removed the image {} from the person {}".format(image, name))
    return OKResponse()
