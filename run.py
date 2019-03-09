from webapp import create_app

app = create_app()

if __name__ == '__main__':
    print("Server starting...")
    # app.run(debug=False)
    app.run(debug=True)
    print("Server started")

# pip install flask
# pip install flask_admin
# pip install flask_simplelogin
# pip install opencv-contrib-python
# pip install face_recognition
# pip --no-cache-dir install face_recognition  # win-en kell hozzá visual studio c++ devtools
# pip intsall scipy
# pip install imutils
# pip install paho-mqtt
# pip install bcrypt
#
#

