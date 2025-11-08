"""
TestBox 编排层数据结构。
"""
from pydantic import BaseModel

class DiagnosticJob(BaseModel):
    job_id: str
    profile_id: str
