import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from backend.config import UPLOAD_DIR, SAMPLES_DIR
from backend.services.sample_datasets import get_dataset

ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "latin-1"]


def load_data(source: str) -> Tuple[pd.DataFrame, str]:
    """
    Load data from file path or sample dataset name.
    Returns (DataFrame, display_name).
    """
    # Check if it's a sample dataset name
    sample_names = {"iris", "tips", "titanic", "sales"}
    if source in sample_names:
        df = get_dataset(source)
        return df, source

    # Otherwise treat as file path
    fp = Path(source)
    if not fp.exists():
        # Try looking in uploads directory
        fp = UPLOAD_DIR / source
    if not fp.exists():
        # Try glob matching
        candidates = list(UPLOAD_DIR.glob(f"{source}*"))
        if candidates:
            fp = candidates[0]
    if not fp.exists():
        raise FileNotFoundError(f"数据源不存在: {source}")

    display_name = fp.name

    if fp.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(str(fp))
    elif fp.suffix.lower() == ".csv":
        df = _read_csv_with_fallback(str(fp))
    else:
        raise ValueError(f"不支持的文件格式: {fp.suffix}")

    return df, display_name


def _read_csv_with_fallback(path: str) -> pd.DataFrame:
    for enc in ENCODINGS:
        try:
            return pd.read_csv(path, encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return pd.read_csv(path, encoding="utf-8", errors="replace")


def get_preview(df: pd.DataFrame, rows: int = 5) -> dict:
    """Get column info and preview data for frontend."""
    headers = list(df.columns)
    col_types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_types[col] = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_types[col] = "datetime"
        else:
            col_types[col] = "categorical"

    preview = []
    for _, row in df.head(rows).iterrows():
        preview.append([str(v)[:100] if pd.notna(v) else "" for v in row])

    return {
        "headers": headers,
        "col_types": col_types,
        "preview": preview,
        "total_rows": len(df),
    }
