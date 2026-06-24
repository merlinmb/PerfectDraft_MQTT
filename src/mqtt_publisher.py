import json

import paho.mqtt.client as mqtt


class MqttPublisher:
    def __init__(self, host, port, username, password, base_topic):
        self.base_topic = base_topic.rstrip("/")
        self.client = mqtt.Client()
        if username:
            self.client.username_pw_set(username, password)
        self.client.connect(host, port, keepalive=60)
        self.client.loop_start()

    def publish_machine_state(self, machine_id, data):
        topic = f"{self.base_topic}/{machine_id}/state"
        self.client.publish(topic, json.dumps(data), retain=True)

    def close(self):
        self.client.loop_stop()
        self.client.disconnect()
