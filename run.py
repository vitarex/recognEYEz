from webapp import create_app
import logging

app = create_app()

if __name__ == '__main__':
    logging.info("Server starting.")
    # app.run(debug=False)

    # Starts flask app on localhost port 5000
    #app.run(host="0.0.0.0", debug=True)
    app.run(host="0.0.0.0")
    logging.info("Server stopped.")
