"""
TestBox Orchestrator 主入口，自动下发诊断命令并进入消息循环。
"""
import sys
from ..shared.mqtt_client import MQTTClient
from .workflow import TestBoxWorkflow
import os
import time

if __name__ == "__main__":
    # 读取配置
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    broker_url = config["mqtt"].get("broker_url", "localhost")
    broker_port = config["mqtt"].get("broker_port", 1883)

    # 初始化 MQTT 客户端和编排流程
    mqtt_client = MQTTClient(broker_url, broker_port)
    workflow = TestBoxWorkflow(mqtt_client, config_path=config_path)

    # 启动编排流程（下发命令并进入消息循环）
    job_id = f"job_{int(time.time())}"
    profile_id = "default"
    print(f"[Orchestrator] 下发诊断命令: job_id={job_id}, profile_id={profile_id}")
    workflow.run_diagnostic(job_id, profile_id)
    workflow.start()
