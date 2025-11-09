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

    def start(self, job_id=None, profile_id=None):
        import logging
        def on_connect(client, userdata, flags, rc):
            logging.info(f"[MQTT] Connected with result code {rc}")
            try:
                client.subscribe(f"{self.base_topic}/tele/progress")
                client.message_callback_add(f"{self.base_topic}/tele/progress", handle_progress)
                client.subscribe(f"{self.base_topic}/tele/done")
                client.message_callback_add(f"{self.base_topic}/tele/done", handle_result)
                if job_id and profile_id:
                    import json
                    topic = f"{self.base_topic}/cmd/run_diagnostic"
                    cmd = {
                        "command": "testbox.run_diagnostic",
                        "corr_id": job_id,
                        "device_id": self.base_topic.split("/")[-1],
                        "params": {"profile": profile_id},
                    }
                    logging.info(f"[Orchestrator] 发布命令: {topic} {cmd}")
                    client.publish(topic, json.dumps(cmd))
            except Exception as exc:
                logging.error(f"MQTT on_connect error: {exc}")

        self.mqtt.client.on_connect = on_connect
        self.mqtt.connect()
        self.mqtt.client.loop_forever()

    def run_diagnostic(self, job_id, profile_id):
        cmd = {"job_id": job_id, "profile_id": profile_id}
        import json
        topic = f"{self.base_topic}/cmd/run_diagnostic"
        self.mqtt.publish(topic, json.dumps(cmd))
        self.job_state[job_id] = "pending"
