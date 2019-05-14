# Installation

Check the installation instructions below. Probably works on other systems as well (e.g. OSX or other linux distros), but installation instructions may vary.

In all cases, you need to have python 3.5 on your system.

## Raspberry Pi 3

The following installation should work on the latest Raspbian image. At the time of writing the latest release is from April 2019, this includes python 3.5 by default.

```
##
# Install dlib
##
# dlib install preparation
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev libatlas-base-dev
sudo apt-get install libx11-dev libgtk-3-dev
pip3 install numpy

# Increase swap space
sudo mcedit /etc/dphys-swapfile # CONF_SWAPSIZE=100 -> 1024
sudo /etc/init.d/dphys-swapfile stop
sudo /etc/init.d/dphys-swapfile start

pip3 install dlib

##
# OpenCV
##
pip3 install opencv-contrib-python

# Install dependencies
sudo apt-get install libhdf5-dev
sudo apt-get install libhdf5-serial-dev
sudo apt-get install libqtgui4
sudo apt-get install libqt4-test

# Test it if it works
python3
>>> import cv2
>>> cv2.__version__
# You should see something like '3.4.4'

# Face recognition
sudo pip3 --no-cache-dir install face_recognition

# Decrease swap space
sudo mcedit /etc/dphys-swapfile # CONF_SWAPSIZE=1024 -> 100
sudo /etc/init.d/dphys-swapfile stop
sudo /etc/init.d/dphys-swapfile start



##
# Installing additional modules
##
# Installing Flask and related extensions
sudo pip3 install flask
sudo pip3 install flask_admin
sudo pip3 install flask_simplelogin
sudo pip3 install scipy
sudo pip3 install imutils
sudo pip3 install paho-mqtt
sudo pip3 install bcrypt

##
# Installing recognEYEz
##
git clone https://github.com/vitarex/recognEYEz

```

Then you are ready to run with `run.py`.

## Windows

```
pip install flask
pip install flask_admin
pip install flask_simplelogin
pip install opencv-contrib-python
pip --no-cache-dir install face_recognition # On windows: you need visual studio c++ devtools
pip install scipy
pip install imutils
pip install paho-mqtt
pip install bcrypt
```

Then you are ready to clone the git repository and run with `run.py`.
