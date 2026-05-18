"""Business Insight Extractor - trends, anomalies, correlations, segmentation."""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List


class BusinessInsightExtractor:
    def __init__(self):
        self.insight_rules = []

    def extract_insights(self, df: pd.DataFrame,
                         analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        insights = []

        trend_insights = self._analyze_trends(df)
        insights.extend(trend_insights)

        correlation_insights = self._extract_correlation_insights(analysis_results)
        insights.extend(correlation_insights)

        outlier_insights = self._summarize_outliers(analysis_results)
        insights.extend(outlier_insights)

        segmentation_insights = self._analyze_segmentation(df)
        insights.extend(segmentation_insights)

        insights.sort(key=lambda x: x["importance_score"], reverse=True)
        return insights[:20]

    def _analyze_trends(self, df: pd.DataFrame) -> List[Dict]:
        insights = []
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for date_col in date_cols:
            df_sorted = df.sort_values(date_col)
            for num_col in list(numeric_cols)[:5]:
                series = df_sorted.groupby(date_col)[num_col].mean().dropna()
                if len(series) < 5:
                    continue
                x = np.arange(len(series))
                y = series.values
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                if abs(r_value) > 0.3 and p_value < 0.05:
                    direction = "上升" if slope > 0 else "下降"
                    insights.append({
                        "type": "trend",
                        "title": f"{num_col} 呈现明显{direction}趋势",
                        "description": f"{num_col} 在时间序列上呈{direction}趋势，相关系数 r={r_value:.3f}，p值={p_value:.4f}。"
                                       f"平均变化率 {slope:.3f}/周期。",
                        "importance_score": round(abs(r_value) * 0.8, 3),
                        "confidence": round(1 - p_value, 3),
                    })
        return insights

    def _extract_correlation_insights(self, results: Dict) -> List[Dict]:
        insights = []
        corr_data = results.get("correlation_analysis", {})
        pairs = corr_data.get("pairs", [])
        for pair in pairs[:10]:
            if abs(pair["correlation"]) > 0.5:
                ctype = "正相关" if pair["correlation"] > 0 else "负相关"
                insights.append({
                    "type": "correlation",
                    "title": f"{pair['var1']} 与 {pair['var2']} 存在强{ctype}",
                    "description": f"相关系数 r={pair['correlation']:.3f}，表明两个变量存在显著的线性关联。"
                                   f"建议进一步分析因果方向。",
                    "importance_score": round(abs(pair["correlation"]) * 0.9, 3),
                    "confidence": abs(pair["correlation"]),
                })
        return insights

    def _summarize_outliers(self, results: Dict) -> List[Dict]:
        insights = []
        outlier_data = results.get("outlier_analysis", {})
        for col, info in outlier_data.items():
            if info.get("outlier_percentage", 0) > 5:
                insights.append({
                    "type": "anomaly",
                    "title": f"{col} 存在 {info['outlier_percentage']:.1f}% 的异常值",
                    "description": f"检测到 {info['outlier_count']} 个异常值（基于 IQR 方法），"
                                   f"正常范围 [{info['lower_bound']:.2f}, {info['upper_bound']:.2f}]。"
                                   f"建议检查数据来源或考虑截尾处理。",
                    "importance_score": round(min(info["outlier_percentage"] / 100, 1) * 0.7, 3),
                    "confidence": 0.85,
                })
        return insights

    def _analyze_segmentation(self, df: pd.DataFrame) -> List[Dict]:
        insights = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns

        for cat_col in categorical_cols[:3]:
            if df[cat_col].nunique() > 10:
                continue
            numeric_for_seg = [c for c in numeric_cols if c != cat_col][:3]
            for num_col in numeric_for_seg:
                groups = df.groupby(cat_col)[num_col].mean()
                if len(groups) < 2:
                    continue
                best = groups.idxmax()
                worst = groups.idxmin()
                ratio = groups.max() / (groups.min() + 0.001)
                if ratio > 1.5:
                    insights.append({
                        "type": "segmentation",
                        "title": f"{cat_col}={best} 的 {num_col} 最高",
                        "description": f"在 {cat_col} 维度下，'{best}' 组平均 {num_col}={groups[best]:.2f}，"
                                       f"而 '{worst}' 组仅 {groups[worst]:.2f}，差异 {(ratio-1)*100:.0f}%。"
                                       f"建议聚焦高价值分群。",
                        "importance_score": round(min(ratio / 5, 1), 3),
                        "confidence": 0.75,
                    })
        return insights[:5]
