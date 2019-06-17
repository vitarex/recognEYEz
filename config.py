from logging.config import dictConfig

logger_config = dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] [%(levelname)s]: %(message)s - in [%(module)s]',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

class Config:
    SECRET_KEY = 'something-secret'
    TIME_FORMAT = "%Y.%m.%d. %H:%M:%S"
    PICTURE_FOLDER = "dnn_data"  # relative from the Static folder
    FACE_DATABASE = "facerecognition.db"
    PAGE_DATABASE = "webpage.db"
    SIMPLELOGIN_USERNAME = 'admin'
    IMAGES_PATH = 'Static'
    SEND_FILE_MAX_AGE_DEFAULT = 0  # to update images with the same filename, but dif content

