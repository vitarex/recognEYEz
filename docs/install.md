# Installation

Check the installation instructions below. Probably works on other systems as well (e.g. OSX or other linux distros), but installation instructions may vary.

In all cases, you need to have python 3.6 on your system.

## Raspberry Pi 3

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
# Install OpenCV
##
# First try:
#   pip install opencv-contrib
# If fails, try the following.

# Requirements
sudo apt-get install build-essential cmake pkg-config
sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install libxvidcore-dev libx264-dev
sudo apt-get install libgtk2.0-dev libgtk-3-dev
sudo apt-get install libatlas-base-dev gfortran
sudo apt-get install python2.7-dev python3-dev

# Download, unzip
cd ~/Download
wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.4.0.zip
unzip opencv.zip
wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/3.4.0.zip
unzip opencv_contrib.zip
pip3 install numpy

# Make and install
cd ~/Downloads/opencv-3.4.0/
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D OPENCV_EXTRA_MODULES_PATH=~/Downloads/opencv_contrib-3.4.0/modules \
    -D PYTHON_EXECUTABLE:FILEPATH=/usr/local/bin/python3 \
    -D BUILD_EXAMPLES=ON ..

# Is it there? Check if it works.
ls -l /usr/local/lib/python3.6/site-packages/
python3
>>> import cv2
>>> cv2.__version__
# You should see: '3.4.0'

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

# Face recognition
sudo pip3 --no-cache-dir install face_recognition

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
