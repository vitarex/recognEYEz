from flask import Blueprint, render_template, request, redirect, json
from flask import current_app as app
from flask_simplelogin import login_required
from pathlib import Path
import logging

stat_folder = Path('../../Static')
person_edit = Blueprint("person_edit", __name__, static_folder=stat_folder, static_url_path='/Static')


@person_edit.route('/change_pic_owner')
@login_required
def change_pic_owner():
    """Places the selected pic to the selected persons folder"""
    # FIXME
    old_name = request.args.get('oname', 0, type=str)
    new_name = request.args.get('nname', 0, type=str)
    pic = request.args.get('pic', 0, type=str)
    logging.info("moving " + pic + " from " + old_name + " to " + new_name)
    app.fh.file.change_pic_between_persons(old_name, new_name, pic)
    return render_template(
        "person_edit.html",
        name=old_name,
        img_names=app.fh.file.get_all_dnn_pic_name_for_person_name(old_name),
        extra=app.fh.persons[old_name].pref,
        names=app.fh.persons.keys()
    )


@person_edit.route('/edit_known_person/', methods=['GET', 'POST'])
@login_required
def edit_known_person():
    """ Webpage for editing a specific person (name, pref, pictures) """
    name = request.args.get("name")
    if name is None:
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
    name = request.form['n']
    pic = request.form['p']
    logging.info("Setting the thumbnail on the person {} to the image {}".format(name, pic))
    app.dh.get_person_by_name(name).set_thumbnail(app.dh.get_image_by_name(pic))
    return json.dumps({'status': 'OK', 'n': name, 'p': pic})


@person_edit.route('/modify_person', methods=['GET', 'POST'])
@login_required
def modify_person():
    """ Modifies the given persons parameters in the background"""
    # FIXME
    old_name = request.form['old_name']
    new_name = request.form['new_name']
    extra = request.form['extra']
    logging.info(old_name, new_name, extra)
    app.dh.update_person_data(old_name, new_name, extra)
    app.fh.load_persons_from_database()
    app.fh.load_encodings_from_database()
    if old_name != new_name:
        app.fh.file.rename_person_files(old_name, new_name)
    return redirect("/person_db")


@person_edit.route('/delete_pic_of_person', methods=['POST'])
@login_required
def remove_pic_for_person():
    """ Removes the selected picture in the background """
    name = request.form['n']
    pic = request.form['p']
    app.dh.get_person_by_name(name).remove_picture(pic)
    logging.info("Removed the image {} from the person {}".format(pic, name))
    return json.dumps({'status': 'OK', 'n': name, 'p': pic})
