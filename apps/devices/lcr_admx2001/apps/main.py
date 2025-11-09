"""Entry point for LCR_ADMX2001 device service."""
import os
import argparse
import logging
import yaml
from .actor import LCRADMX2001Runtime, create_actor
from .hb import HeartbeatConfig, HeartbeatPublisher, configure_last_will

def _load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)

def _default_config_path():
    return os.path.join(os.path.dirname(__file__), "../configs/device_lcr_admx2001.yaml")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="LCR_ADMX2001 service")
    parser.add_argument("--mode", choices=["mqtt", "demo"], default="mqtt")
    parser.add_argument("--config", default=_default_config_path())
    args = parser.parse_args()
    cfg = _load_config(args.config)
    if args.mode == "mqtt":
        # TODO: run_mqtt(cfg)
        print("[LCR_ADMX2001] MQTT mode not yet implemented.")
    else:
        # TODO: run_demo(cfg)
        print("[LCR_ADMX2001] Demo mode not yet implemented.")
