import paho.mqtt.client as mqtt
import sqlite3 as sql
import time


class MqttHandler:

    def __init__(self, db_address):
        self.init_from_db(db_address)
        self.client = mqtt.Client()
        # self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.connect()
        self.client.loop_start()

    def init_from_db(self, db_address):
        self.data = dict()
        con = sql.connect(db_address)
        c = con.cursor()
        for row in c.execute('SELECT * FROM notification_settings'):
            self.data[row[0]] = row[1]
        # print(self.data)
        con.close()

    def start_loop(self):
        self.client.loop_start()

    def stop_loop(self):
        self.client.loop_stop()

    def connect(self):
        """ connects to the broker defined in the db """
        if self.client.connect(self.data["broker_url"], int(self.data["port"])):
            print("MQTT connected to " + self.data["broker_url"])

    def publish(self, topic, payload=None):
        self.client.publish(topic, payload)

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def on_message(self, client, userdata, message):
        print("[MQTT-REC][" + message.topic + "]: " + str(message.payload.decode("utf-8")))
        pass

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

if __name__ == "__main__":
    mqtt_test = MqttHandler()
    mqtt_test.subscribe("face_handler")
    mqtt_test.publish("face_handler", "Okay")
    time.sleep(10)
    mqtt_test.stop_loop()

