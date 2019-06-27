import paho.mqtt.client as mqtt
import logging
from Library.Handler import Handler
from socket import gaierror

class MqttHandler(Handler):

    def __init__(self, app):
        super().__init__(app)
        self.data = self.app.sh.get_notification_settings()
        self.client = mqtt.Client()
        # self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        try:
            self.connect()
        except gaierror as error:
            logging.info("Can't set up MQTT since there is probably no internet: {}".format(error))
            return
        self.client.loop_start()

    def start_loop(self):
        self.client.loop_start()

    def stop_loop(self):
        self.client.loop_stop()

    def connect(self):
        """ connects to the broker defined in the db """
        if self.client.connect(self.data["broker_url"], int(self.data["port"])):
            logging.info("MQTT connected to " + self.data["broker_url"])

    def publish(self, topic, payload=None):
        self.client.publish(topic, payload)

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def on_message(self, client, userdata, message):
        logging.info("[MQTT-REC][" + message.topic + "]: " + str(message.payload.decode("utf-8")))
        pass
