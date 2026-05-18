"""Built-in sample datasets for demonstration."""
import pandas as pd
import numpy as np
from pathlib import Path
from backend.config import SAMPLES_DIR

SAMPLE_META = [
    {"name": "iris", "description": "鸢尾花数据集 — 150条，4个特征，3种分类（setosa/versicolor/virginica），经典分类问题", "row_count": 150},
    {"name": "tips", "description": "餐厅小费数据集 — 244条，含消费金额、小费、性别、吸烟等字段，适合回归分析", "row_count": 244},
    {"name": "titanic", "description": "泰坦尼克号乘客数据 — 891条，含年龄、舱位、票价等，经典二分类（生存预测）", "row_count": 891},
    {"name": "sales", "description": "模拟电商销售数据 — 1000条，含日期、产品、销售额、利润等，适合趋势分析和预测", "row_count": 1000},
]


def list_datasets() -> list:
    return SAMPLE_META


def get_dataset(name: str) -> pd.DataFrame:
    # Check disk cache first
    fp = SAMPLES_DIR / f"{name}.csv"
    if fp.exists():
        return pd.read_csv(str(fp))

    # Generate and cache
    df = _generate_dataset(name)
    fp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(fp), index=False)
    return df


def _generate_dataset(name: str) -> pd.DataFrame:
    if name == "iris":
        from sklearn.datasets import load_iris
        data = load_iris()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df["species"] = pd.Series(data.target).map({0: "setosa", 1: "versicolor", 2: "virginica"})
        return df
    elif name == "tips":
        import seaborn as sns
        return sns.load_dataset("tips")
    elif name == "titanic":
        import seaborn as sns
        df = sns.load_dataset("titanic")
        return df
    elif name == "sales":
        return _generate_sales_data()
    else:
        raise ValueError(f"未知数据集: {name}")


def _generate_sales_data() -> pd.DataFrame:
    np.random.seed(42)
    n = 1000
    dates = pd.date_range("2023-01-01", periods=365, freq="D")
    products = ["手机", "笔记本", "平板", "耳机", "手表"]
    regions = ["华北", "华东", "华南", "西部"]

    data = {
        "日期": np.random.choice(dates, n),
        "产品": np.random.choice(products, n),
        "地区": np.random.choice(regions, n),
        "销量": np.random.randint(1, 200, n),
        "单价": np.round(np.random.uniform(50, 8000, n), 2),
        "利润": np.round(np.random.uniform(-50, 2000, n), 2),
    }
    df = pd.DataFrame(data)
    df["销售额"] = df["销量"] * df["单价"]
    df = df.sort_values("日期").reset_index(drop=True)
    return df
