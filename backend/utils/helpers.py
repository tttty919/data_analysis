import uuid
import json
import numpy as np


def generate_task_id() -> str:
    return str(uuid.uuid4())[:8]


def is_numeric_dtype(dtype) -> bool:
    return np.issubdtype(dtype, np.number)


def detect_column_types(df) -> dict:
    result = {}
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.number):
            result[col] = "numeric"
        elif np.issubdtype(df[col].dtype, np.datetime64):
            result[col] = "datetime"
        else:
            result[col] = "categorical"
    return result


class SafeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.bool_,)):
            return bool(o)
        return str(o)
