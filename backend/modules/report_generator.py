"""Intelligent Report Generator - produces comprehensive analysis reports."""
from typing import Dict, Any, List
from datetime import datetime


class IntelligentReportGenerator:
    def __init__(self):
        self.insights = []

    def generate_comprehensive_report(self, analysis_results: Dict[str, Any],
                                      df_shape: tuple = None) -> Dict[str, Any]:
        key_insights = self._extract_key_insights(analysis_results)
        executive_summary = self._generate_summary(analysis_results, key_insights)
        recommendations = self._generate_recommendations(analysis_results)

        return {
            "executive_summary": executive_summary,
            "key_insights": key_insights,
            "recommendations": recommendations,
            "metadata": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "analysis_type": analysis_results.get("problem_type", "exploration"),
                "data_shape": {"rows": df_shape[0], "cols": df_shape[1]} if df_shape else {},
            },
        }

    def _extract_key_insights(self, results: Dict) -> List[str]:
        insights = []

        # Data quality insights
        qa = results.get("quality_analysis", {})
        missing_vars = [col for col, info in qa.get("missing_analysis", {}).items()
                        if info.get("missing_percentage", 0) > 20]
        if missing_vars:
            insights.append(f"发现 {len(missing_vars)} 个变量存在超 20% 的缺失值：{', '.join(missing_vars[:5])}，建议关注数据收集质量")

        dup_pct = qa.get("duplicate_percentage", 0)
        if dup_pct > 10:
            insights.append(f"数据集中存在 {dup_pct:.1f}% 的重复记录，建议在分析前进行去重处理")

        # Statistical insights
        stats = results.get("statistical_analysis", {})
        for col, s in stats.items():
            if abs(s.get("skewness", 0)) > 2:
                direction = "右偏" if s["skewness"] > 0 else "左偏"
                insights.append(f"{col} 分布严重{direction}（偏度={s['skewness']:.2f}），建议进行数据变换")

        # Model performance
        model_results = results.get("model_results", {})
        if model_results:
            valid = {k: v for k, v in model_results.items() if "error" not in v}
            if valid:
                key_metric = "r2_score" if "r2_score" in list(valid.values())[0] else "accuracy"
                best = max(valid.items(), key=lambda x: x[1].get(key_metric, 0))
                insights.append(f"最佳模型为 {best[0]}，{key_metric}={best[1][key_metric]:.4f}")

        # Feature importance
        fi = results.get("feature_importance", {})
        if fi:
            top_f = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:3]
            insights.append(f"影响目标变量的前三关键因素：{'、'.join(f[0] for f in top_f)}")

        return insights[:8]

    def _generate_summary(self, results: Dict, key_insights: List[str]) -> str:
        basic = results.get("basic_info", {})
        problem_type = results.get("problem_type", "数据探索")

        summary = f"本次对包含 {basic.get('row_count', 'N')} 行、{basic.get('column_count', 'N')} 列的数据集进行了{problem_type}分析。\n\n"

        if results.get("quality_analysis"):
            qa = results["quality_analysis"]
            summary += f"数据质量方面，整体缺失率为 {qa.get('missing_cells', 0) / max(qa.get('total_cells', 1), 1) * 100:.1f}%，"
            summary += f"重复记录占比 {qa.get('duplicate_percentage', 0):.1f}%。\n\n"

        if results.get("model_results"):
            model_results = results["model_results"]
            valid = {k: v for k, v in model_results.items() if "error" not in v}
            if valid:
                key_metric = "r2_score" if "r2_score" in list(valid.values())[0] else "accuracy"
                best = max(valid.items(), key=lambda x: x[1].get(key_metric, 0))
                summary += f"模型建模完成，共训练 {len(valid)} 个模型。"
                summary += f"最佳模型 {best[0]} 在测试集上 {key_metric} 达到 {best[1][key_metric]:.4f}。\n\n"

        if key_insights:
            summary += "关键发现：\n"
            for i, ins in enumerate(key_insights[:3], 1):
                summary += f"{i}. {ins}\n"

        return summary

    def _generate_recommendations(self, results: Dict) -> List[Dict[str, str]]:
        recommendations = []

        # Quality-based recommendations
        qa = results.get("quality_analysis", {})
        if qa.get("missing_cells", 0) > qa.get("total_cells", 1) * 0.1:
            recommendations.append({
                "title": "数据质量优先",
                "detail": "当前数据缺失率较高，建议在建模前先完善数据采集流程，或使用插补方法处理缺失值。",
                "action": "对缺失率 > 20% 的列进行评估（删除/插补），对关键列使用中位数/众数填充。",
            })

        # Model-based recommendations
        model_results = results.get("model_results", {})
        if model_results:
            recommendations.append({
                "title": "模型选择与部署",
                "detail": "已训练多个模型并进行交叉验证。建议选择 CV 分数稳定且解释性好的模型进行部署。",
                "action": "将最佳模型导出为 pickle 文件，并在新数据上持续监控模型性能衰减。",
            })

        # Feature importance based
        fi = results.get("feature_importance", {})
        if fi:
            top = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:3]
            recommendations.append({
                "title": f"聚焦核心驱动因素：{'、'.join(f[0] for f in top)}",
                "detail": "特征重要性分析显示以上变量对目标影响最大，应优先投入资源优化这些维度。",
                "action": f"围绕 '{top[0][0]}' 设计专项改进方案，并追踪其对目标变量的实际提升效果。",
            })

        # Standard recommendation
        recommendations.append({
            "title": "用数据验证假设",
            "detail": "分析结果提供的是统计相关性而非因果关系。建议将关键发现转化为可执行的实验方案，通过 A/B 测试验证实际效果。",
            "action": "选取 Top 3 洞察，设计对应的实验方案（假设 → 变量 → 样本量 → 预期效果 → 评估周期）。",
        })

        return recommendations
