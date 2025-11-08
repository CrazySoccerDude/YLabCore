"""
TestBox 仪器编排流程示例。
"""
from ..shared.mqtt_client import MQTTClient


from .handlers import handle_progress, handle_result


import yaml
import os

class TestBoxWorkflow:
    def __init__(self, mqtt_client, config_path=None):
        self.mqtt = mqtt_client
        self.job_state = {}
        # 读取 base_topic
        config_file = config_path or os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        self.base_topic = config["mqtt"].get("base_topic", "lab/local/line/device_testbox/TB-001")

    def start(self):
        # 连接并订阅结果主题
        self.mqtt.connect()
        self.mqtt.subscribe("tele/progress", handle_progress)
        self.mqtt.subscribe("tele/result", handle_result)
        self.mqtt.loop_forever()

    def run_diagnostic(self, job_id, profile_id):
        cmd = {"job_id": job_id, "profile_id": profile_id}
        import json
        topic = f"{self.base_topic}/cmd/run_diagnostic"
        self.mqtt.publish(topic, json.dumps(cmd))
        self.job_state[job_id] = "pending"
