from webapp import create_app
from config import logging_config
import logging
import logging.config
import logging.handlers

app = create_app()

if __name__ == '__main__':
    logging.config.dictConfig(logging_config)

    for handler in logging.getLogger().handlers:
        if issubclass(handler.__class__, logging.handlers.BaseRotatingHandler):
            handler.namer = lambda fn: fn.replace("log.1", "1.log")

    logging.info("Server starting.")
    # app.run(debug=False)

    # Starts flask app on localhost port 5000
    app.run(host="0.0.0.0", debug=False)
    # app.run(host="0.0.0.0")
    logging.info("Server stopped.")
