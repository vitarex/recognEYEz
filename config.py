logging_config = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s]: %(message)s - in [%(module)s]',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        },
        'filehandler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': 'logs\\log.log',
            'mode': 'a',
            'backupCount': 1,
            'maxBytes': 5242800
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi', 'filehandler']
    }
}

class Config:
    TIME_FORMAT = "%Y.%m.%d. %H:%M:%S"
    PICTURE_FOLDER = "dnn_data"  # relative from the Static folder
    SIMPLELOGIN_USERNAME = 'admin'
    IMAGES_PATH = 'Static'
    SEND_FILE_MAX_AGE_DEFAULT = 0  # to update images with the same filename, but dif content
