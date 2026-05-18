import json
import shutil
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import BASE_DIR, DATA_DIR, UPLOAD_DIR, TASKS_DIR, SAMPLES_DIR
from backend.database import init_db
from backend.models import CreateTaskRequest, ApiKeyRequest
from backend.task_store import (
    create_task, get_task, update_task, list_tasks, delete_task as delete_task_record
)
from backend.services.data_loader import load_data, get_preview
from backend.services.sample_datasets import list_datasets
from backend.services.llm_service import test_api_key, parse_user_requirements, generate_nlu_insights
from backend.services.report_exporter import generate_html_report, generate_excel_report
from backend.agent.data_analysis_agent import DataAnalysisAgent
from backend.utils.helpers import generate_task_id

app = FastAPI(title="智能数据分析系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

stop_flags: dict = {}
agent = DataAnalysisAgent()


def on_progress(task_id: str, **kwargs):
    """Callback for agent to report progress back to task_store."""
    update_task(task_id, **kwargs)


def run_analysis_task(task_id: str, task_type: str, data_source: str,
                      requirements: dict, api_key: str = None):
    """Background thread entry point for running analysis."""
    try:
        update_task(task_id, status="running", phase="data_loading",
                    current_step="加载数据", message="正在读取数据...")

        df, display_name = load_data(data_source)
        preview = get_preview(df)

        # Check stop flag before each major phase
        def update_progress(**kwargs):
            if stop_flags.get(task_id):
                raise StopIteration("用户停止任务")
            update_task(task_id, **kwargs)

        results = agent.process_task(
            task_id=task_id,
            task_type=task_type,
            df=df,
            requirements=requirements,
            update_progress=update_progress,
            api_key=api_key,
        )

        # Generate downloadable reports
        if results.get("report"):
            generate_html_report(task_id, results["report"])
            generate_excel_report(task_id, results["report"], results.get("eda"))

        # Save results JSON
        update_task(
            task_id,
            status="completed",
            progress_pct=100,
            phase="completed",
            current_step="完成",
            message="分析完成",
            results=json.dumps(results, ensure_ascii=False, default=str),
            report=json.dumps(results.get("report", {}), ensure_ascii=False, default=str),
        )

        # Clean up uploaded file if it was an upload
        source_path = UPLOAD_DIR / data_source
        if not source_path.exists():
            candidates = list(UPLOAD_DIR.glob(f"{data_source}*"))
            if candidates:
                source_path = candidates[0]

    except StopIteration:
        update_task(task_id, status="stopped", phase="stopped",
                    current_step="已停止", message="用户手动停止")
    except Exception as e:
        update_task(task_id, status="failed", phase="failed",
                    current_step="失败", message=str(e), error=str(e))


# ==================== API Routes ====================

@app.on_event("startup")
def startup():
    init_db()


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload CSV or Excel file, return preview."""
    if not file.filename:
        raise HTTPException(400, "未选择文件")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        raise HTTPException(400, "仅支持 CSV / Excel 文件")

    task_id = generate_task_id()
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"
    content = await file.read()
    file_path.write_bytes(content)

    try:
        df, _ = load_data(str(file_path))
        preview = get_preview(df)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(400, f"文件读取失败: {e}")

    # Store reference in task table
    create_task(task_id, "exploration", str(file_path), {})

    return {
        "task_id": task_id,
        "filename": file.filename,
        **preview,
    }


@app.get("/api/datasets")
async def get_datasets():
    """Get list of sample datasets."""
    return list_datasets()


@app.post("/api/tasks")
async def create_analysis_task(req: CreateTaskRequest, background_tasks: BackgroundTasks):
    """Create and start an analysis task."""
    task_id = generate_task_id()

    # If using sample dataset, data_source is the dataset name
    data_source = req.data_source

    # If using uploaded file, find the file path
    if req.data_source not in ("iris", "tips", "titanic", "sales"):
        # Try to find the uploaded file
        candidates = list(UPLOAD_DIR.glob(f"{req.data_source}_*"))
        if candidates:
            data_source = str(candidates[0])
        elif not Path(req.data_source).exists():
            raise HTTPException(400, f"数据源不存在: {req.data_source}。请先上传文件或选择示例数据集。")

    # Parse natural language requirements if present
    requirements = req.requirements
    user_input = requirements.get("user_input", "")
    if user_input and req.api_key:
        try:
            df, _ = load_data(data_source)
            parsed = parse_user_requirements(user_input, list(df.columns), req.api_key)
            requirements.update(parsed)
        except Exception:
            pass

    create_task(task_id, req.task_type.value, data_source, requirements, req.api_key)
    update_task(task_id, status="pending", phase="idle")

    background_tasks.add_task(
        run_analysis_task, task_id, req.task_type.value,
        data_source, requirements, req.api_key
    )

    return {"task_id": task_id, "status": "pending"}


@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks."""
    return list_tasks()


@app.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """Get full task detail with results."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    # Build progress object
    progress = {
        "task_id": task_id,
        "phase": task.get("phase", "idle"),
        "progress_pct": task.get("progress_pct", 0),
        "current_step": task.get("current_step", ""),
        "message": task.get("message", ""),
    }

    return {
        **task,
        "progress": progress,
    }


@app.get("/api/tasks/{task_id}/progress")
async def get_task_progress(task_id: str):
    """Get task progress (for polling)."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")

    return {
        "task_id": task_id,
        "phase": task.get("phase", "idle"),
        "progress_pct": task.get("progress_pct", 0),
        "current_step": task.get("current_step", ""),
        "message": task.get("message", ""),
        "status": task.get("status", "unknown"),
    }


@app.get("/api/tasks/{task_id}/report")
async def get_task_report(task_id: str):
    """Get task analysis report."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    if not task.get("results"):
        raise HTTPException(400, "任务尚未完成分析")

    results = task["results"]
    if isinstance(results, str):
        results = json.loads(results)

    return results


@app.post("/api/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    """Stop a running task."""
    stop_flags[task_id] = True
    return {"ok": True, "message": "已发送停止信号"}


@app.delete("/api/tasks/{task_id}")
async def remove_task(task_id: str):
    """Delete a task and its data."""
    stop_flags.pop(task_id, None)

    # Remove uploaded files
    for f in UPLOAD_DIR.glob(f"{task_id}_*"):
        f.unlink(missing_ok=True)

    # Remove task data
    task_dir = TASKS_DIR / task_id
    if task_dir.exists():
        shutil.rmtree(str(task_dir), ignore_errors=True)

    delete_task_record(task_id)
    return {"ok": True}


@app.get("/api/tasks/{task_id}/download/html")
async def download_html(task_id: str):
    """Download HTML report."""
    path = TASKS_DIR / task_id / "report.html"
    if not path.exists():
        raise HTTPException(404, "报告尚未生成")
    return FileResponse(path, filename=f"分析报告_{task_id}.html")


@app.get("/api/tasks/{task_id}/download/excel")
async def download_excel(task_id: str):
    """Download Excel report."""
    path = TASKS_DIR / task_id / "report.xlsx"
    if not path.exists():
        raise HTTPException(404, "Excel报告尚未生成")
    return FileResponse(
        path, filename=f"分析数据_{task_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/api/test-api-key")
async def test_api(req: ApiKeyRequest):
    """Test DeepSeek API key connectivity."""
    return test_api_key(req.api_key)


# ==================== Static files & root ====================

@app.get("/api/charts/{task_id}/{name}")
async def get_chart(task_id: str, name: str):
    """Serve generated chart images."""
    path = TASKS_DIR / task_id / name
    if not path.exists():
        raise HTTPException(404, "图表不存在")
    return FileResponse(path)


@app.get("/")
async def root():
    """Health check + basic info."""
    return {
        "app": "智能数据分析系统",
        "version": "1.0.0",
        "docs": "/docs",
    }
