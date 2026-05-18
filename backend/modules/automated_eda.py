"""Automated Exploratory Data Analysis module."""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any


class AutomatedEDA:
    def __init__(self):
        self.report_data = {}

    def analyze_dataset(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {
            "basic_info": self._get_basic_info(df),
            "quality_analysis": self._analyze_data_quality(df),
            "statistical_analysis": self._perform_statistical_analysis(df),
            "correlation_analysis": self._analyze_correlations(df),
            "outlier_analysis": self._detect_outliers(df),
        }

    def _get_basic_info(self, df: pd.DataFrame) -> Dict:
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
        }

    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict:
        missing_analysis = {}
        for col in df.columns:
            missing_count = int(df[col].isnull().sum())
            missing_analysis[col] = {
                "missing_count": missing_count,
                "missing_percentage": round(missing_count / len(df) * 100, 2),
            }

        duplicate_count = int(df.duplicated().sum())
        duplicate_percentage = round(duplicate_count / len(df) * 100, 2)

        return {
            "missing_analysis": missing_analysis,
            "duplicate_count": duplicate_count,
            "duplicate_percentage": duplicate_percentage,
            "total_cells": len(df) * len(df.columns),
            "missing_cells": int(df.isnull().sum().sum()),
        }

    def _perform_statistical_analysis(self, df: pd.DataFrame) -> Dict:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        stats_dict = {}
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            stats_dict[col] = {
                "mean": round(float(col_data.mean()), 3),
                "std": round(float(col_data.std()), 3),
                "min": round(float(col_data.min()), 3),
                "q25": round(float(col_data.quantile(0.25)), 3),
                "median": round(float(col_data.median()), 3),
                "q75": round(float(col_data.quantile(0.75)), 3),
                "max": round(float(col_data.max()), 3),
                "skewness": round(float(col_data.skew()), 3),
                "kurtosis": round(float(col_data.kurtosis()), 3),
            }
        return stats_dict

    def _analyze_correlations(self, df: pd.DataFrame) -> Dict:
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return {"pairs": [], "matrix": {}}

        corr_matrix = numeric_df.corr()
        matrix = {}
        for col in corr_matrix.columns:
            matrix[col] = {str(k): round(float(v), 3) for k, v in corr_matrix[col].items()}

        # Top correlation pairs
        pairs = []
        seen = set()
        for i, col1 in enumerate(corr_matrix.columns):
            for col2 in corr_matrix.columns[i+1:]:
                val = float(corr_matrix.loc[col1, col2])
                if abs(val) > 0.3:
                    pairs.append({"var1": str(col1), "var2": str(col2), "correlation": round(val, 3)})
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return {"pairs": pairs[:20], "matrix": matrix}

    def _detect_outliers(self, df: pd.DataFrame) -> Dict:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outlier_results = {}
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) < 10:
                continue
            Q1 = float(col_data.quantile(0.25))
            Q3 = float(col_data.quantile(0.75))
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = int(outlier_mask.sum())
            outlier_results[col] = {
                "outlier_count": outlier_count,
                "outlier_percentage": round(outlier_count / len(df) * 100, 2),
                "lower_bound": round(lower_bound, 3),
                "upper_bound": round(upper_bound, 3),
            }
        return outlier_results
