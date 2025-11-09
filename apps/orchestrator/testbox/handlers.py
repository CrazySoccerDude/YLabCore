"""
TestBox 消息处理模块。
"""

import json

import logging

def handle_progress(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        corr_id = payload.get("corr_id")
        progress = payload.get("progress")
        stage = payload.get("stage")
        logging.info(f"Progress for corr_id {corr_id}: {progress*100:.1f}% (stage: {stage})")
    except Exception as exc:
        logging.error(f"handle_progress error: {exc}")

def handle_result(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        corr_id = payload.get("corr_id")
        result = payload.get("result")
        duration = payload.get("duration_s")
        summary = payload.get("summary")
        logging.info(f"Result for corr_id {corr_id}: {result}, duration={duration}s, summary={summary}")
    except Exception as exc:
        logging.error(f"handle_result error: {exc}")
