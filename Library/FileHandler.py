import os
import sys
from shutil import copyfile, rmtree, move
import glob
from imutils import paths
import logging
from pathlib import Path



class FileHandler:

    def __init__(self, stat="Images"):
        # TODO: should we really use sys.argv[0] instead of __file__?
        self.main_image_folder_path = Path(sys.argv[0]).resolve().parent.joinpath(stat)

    def get_all_dnn_pic_name_for_person_name(self, name):
        """
        returns a list containing all the image file names corresponding to the given name
        can be used in Flask templates like:
            <img src='Name/{{list_from_this[0]'>
        """
        return os.listdir(
            Path(self.main_image_folder_path).joinpath(name)
        )

    def rename_person_files(self, old_name, new_name):
        """Upon db change, rename the nessesery files to stay consistent"""
        self.rename_dnn_data_folder(old_name, new_name)

    def rename_dnn_data_folder(self, old_name, new_name):
        src = Path(self.main_image_folder_path).joinpath(old_name)
        dst = Path(self.main_image_folder_path).joinpath(new_name)
        os.rename(src, dst)

    def change_pic_between_persons(self, from_name, to_name, pic_name):
        """ Copies the given image from the given persons folder in the dnn data folder, into the new person's folder"""
        src = Path(self.main_image_folder_path).joinpath(from_name,pic_name)
        dst = Path(self.main_image_folder_path).joinpath(to_name,pic_name)
        os.rename(src, dst)

    def remove_picture(self, name, pic_name):
        """ Removes the selected picture from the given person's dnn_data folder"""
        file = Path(self.main_image_folder_path).joinpath(name,pic_name)
        os.remove(file)

    def remove_known_files(self, folder_name):
        return rmtree(Path(self.main_image_folder_path).joinpath(str(folder_name)))

    def remove_unknown_files(self, folder_name):
        try:
            rmtree(Path("Static").joinpath("unknown_pics",str(folder_name)))  # TODO: beautify
        except FileNotFoundError:
            logging.error("FileNotFound at remove_unknown_files(), folder: " + str(folder_name))

    def merge_unk_file_with(self, from_folder_name, to_folder_name):
        logging.info("Merging {} with {}".format(from_folder_name, to_folder_name))
        from_folder_path = Path("Static").joinpath("unknown_pics",from_folder_name)
        to_folder_path = Path(self.main_image_folder_path).joinpath(from_folder_name)

        pics = paths.list_images(from_folder_path)
        logging.info("pics: " + str(pics))
        for pic in pics:
            move(pic, to_folder_path)
        self.remove_unknown_files(to_folder_name)

    def create_new_person_from_unk(self, from_folder_name):
        from_folder_path = Path("Static").joinpath("unknown_pics",from_folder_name)
        to_folder_path = Path(self.main_image_folder_path).joinpath(from_folder_name)

        move(from_folder_path, to_folder_path)

