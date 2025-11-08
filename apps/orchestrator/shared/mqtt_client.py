"""
统一 MQTT 客户端工具，供各设备编排模块复用。
"""
import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker_url, broker_port):
        self.client = mqtt.Client()
        self.broker_url = broker_url
        self.broker_port = broker_port

    def connect(self):
        self.client.connect(self.broker_url, self.broker_port)

    def publish(self, topic, payload, qos=0, retain=False):
        self.client.publish(topic, payload, qos, retain)

    def subscribe(self, topic, callback):
        self.client.subscribe(topic)
        self.client.message_callback_add(topic, callback)

    def loop_forever(self):
        self.client.loop_forever()
