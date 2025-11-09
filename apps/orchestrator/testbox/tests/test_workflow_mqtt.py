import pytest
import json
from unittest.mock import MagicMock
from apps.orchestrator.testbox.workflow import TestBoxWorkflow

def test_publish_command(monkeypatch):
    # 模拟 MQTT 客户端
    published = {}
    class DummyMQTT:
        def __init__(self):
            self.client = self
        def connect(self):
            pass
        def publish(self, topic, payload, qos=0, retain=False):
            published[topic] = json.loads(payload)
        def subscribe(self, topic, callback=None):
            pass
        def message_callback_add(self, topic, callback):
            pass
        def loop_forever(self):
            pass
    # 构造 workflow
    workflow = TestBoxWorkflow(DummyMQTT(), config_path=None)
    workflow.base_topic = "lab/local/line/device_testbox/TB-001"
    job_id = "job_test"
    profile_id = "default"
    workflow.start(job_id=job_id, profile_id=profile_id)
    # 检查命令格式
    topic = f"lab/local/line/device_testbox/TB-001/cmd/run_diagnostic"
    assert topic in published
    cmd = published[topic]
    assert cmd["command"] == "testbox.run_diagnostic"
    assert cmd["corr_id"] == job_id
    assert cmd["device_id"] == "TB-001"
    assert cmd["params"]["profile"] == profile_id

def test_handle_progress_and_result(monkeypatch):
    # 测试消息处理函数
    from apps.orchestrator.testbox.handlers import handle_progress, handle_result
    class DummyMsg:
        def __init__(self, payload):
            self.payload = payload.encode()
    # 进度消息
    progress_payload = json.dumps({
        "corr_id": "job_test",
        "progress": 0.5,
        "stage": "diagnostic_sequence"
    })
    # 结果消息
    result_payload = json.dumps({
        "corr_id": "job_test",
        "result": "PASS",
        "duration_s": 45.0,
        "summary": "OK"
    })
    # 捕获输出
    import io, sys
    out = io.StringIO()
    sys.stdout = out
    handle_progress(None, None, DummyMsg(progress_payload))
    handle_result(None, None, DummyMsg(result_payload))
    sys.stdout = sys.__stdout__
    output = out.getvalue()
    assert "diagnostic_sequence" in output
    assert "PASS" in output
