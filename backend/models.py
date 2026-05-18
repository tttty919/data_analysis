from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class TaskType(str, Enum):
    EXPLORATION = "exploration"
    MODELING = "modeling"
    CONTENT_ANALYSIS = "content_analysis"
    PREDICTION = "prediction"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class CreateTaskRequest(BaseModel):
    task_type: TaskType = TaskType.EXPLORATION
    data_source: str = Field(..., description="上传文件路径或示例数据集名称")
    requirements: Dict[str, Any] = Field(default_factory=dict)
    api_key: Optional[str] = None


class ApiKeyRequest(BaseModel):
    api_key: str


class TaskProgress(BaseModel):
    task_id: str
    phase: str = "idle"
    progress_pct: float = 0.0
    current_step: str = ""
    message: str = ""


class TaskDetail(BaseModel):
    task_id: str
    task_type: str
    status: str
    data_source: str
    progress: Optional[TaskProgress] = None
    results: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    created_at: str = ""
    updated_at: str = ""
    error: Optional[str] = None
