import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "analysis.db"
UPLOAD_DIR = DATA_DIR / "uploads"
TASKS_DIR = DATA_DIR / "tasks"
SAMPLES_DIR = DATA_DIR / "samples"

DEFAULT_MODEL_PARAMS = {
    "test_size": 0.2,
    "random_state": 42,
    "cv_folds": 5,
    "n_estimators": 100,
}

DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

for d in [DATA_DIR, UPLOAD_DIR, TASKS_DIR, SAMPLES_DIR]:
    d.mkdir(parents=True, exist_ok=True)
