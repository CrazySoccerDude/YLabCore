"""
TestBox 消息处理模块。
"""

import json

def handle_progress(client, userdata, message):
    payload = json.loads(message.payload.decode())
    job_id = payload.get("job_id")
    percent = payload.get("percent")
    print(f"Progress for job {job_id}: {percent}%")

def handle_result(client, userdata, message):
    payload = json.loads(message.payload.decode())
    job_id = payload.get("job_id")
    result = payload.get("result")
    print(f"Result for job {job_id}: {result}")
