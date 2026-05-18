"""Data Analysis Agent - core scheduler that routes tasks and aggregates results."""
import json
import logging
from pathlib import Path
from typing import Dict, Any

from backend.config import TASKS_DIR
from backend.modules.automated_eda import AutomatedEDA
from backend.modules.intelligent_visualization import IntelligentVisualization
from backend.modules.automl_modeling import AutoMLModeling
from backend.modules.business_insight import BusinessInsightExtractor
from backend.modules.report_generator import IntelligentReportGenerator
from backend.modules.content_analyzer import ContentAnalyzer
from backend.utils.helpers import SafeEncoder

logger = logging.getLogger(__name__)


class DataAnalysisAgent:
    def __init__(self):
        self.eda = AutomatedEDA()
        self.insight_extractor = BusinessInsightExtractor()
        self.report_generator = IntelligentReportGenerator()
        self.content_analyzer = ContentAnalyzer()

    def _run_content_analysis(self, task_id, df, requirements, update_progress,
                              api_key, task_dir):
        update_progress(phase="content_analysis", progress_pct=15,
                        current_step="文本内容分析", message="正在进行文本预处理...")
        text_col = requirements.get("text_column", "")
        if not text_col:
            # Auto-detect text column (longest text)
            text_cols = df.select_dtypes(include=["object"]).columns
            if len(text_cols) == 0:
                raise ValueError("数据集中没有文本列，无法进行内容分析")
            text_col = max(text_cols, key=lambda c: df[c].dropna().astype(str).str.len().mean())

        results = {"task_type": "content_analysis", "text_column": text_col}

        # Content analysis
        update_progress(phase="content_analysis", progress_pct=30,
                        current_step="关键词提取", message="正在提取高频关键词...")
        content_results = self.content_analyzer.analyze(df, text_col, api_key)
        results["content_analysis"] = content_results
        results["keywords"] = content_results.get("keywords", [])
        results["sentiment"] = content_results.get("sentiment", {})
        results["themes"] = content_results.get("themes", [])
        results["nps"] = content_results.get("nps", {})
        results["pain_points"] = content_results.get("pain_points", [])
        results["competitor_mentions"] = content_results.get("competitor_mentions", {})
        results["user_segments"] = content_results.get("user_segments", [])
        results["jtbd"] = content_results.get("jtbd", [])
        results["customer_journey"] = content_results.get("customer_journey", {})
        results["ai_insights"] = content_results.get("ai_insights", [])
        results["total_texts"] = content_results.get("total_texts", 0)

        # Word cloud
        update_progress(phase="content_analysis", progress_pct=65,
                        current_step="生成词云", message="正在生成关键词云...")
        viz = IntelligentVisualization(task_dir)
        wc_path = viz.plot_wordcloud(content_results.get("keywords", []))
        if wc_path:
            results["visualizations"] = {"wordcloud": Path(wc_path).name}

        # Generate report
        update_progress(phase="report", progress_pct=80, current_step="生成分析报告",
                        message="正在生成内容分析报告...")
        report = self._generate_content_report(content_results, df.shape)
        results["report"] = report

        with open(task_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, cls=SafeEncoder)

        update_progress(phase="completed", progress_pct=100,
                        current_step="分析完成", message="内容分析已完成，可查看结果")
        return results

    def _generate_content_report(self, cr, shape):
        kw_top = [k["word"] for k in cr.get("keywords", [])[:10]]
        sentiment = cr.get("sentiment", {})
        themes = cr.get("themes", [])
        total = cr.get("total_texts", 0)

        summary = f"本次对 {total} 条文本内容进行了分析。"
        if sentiment:
            summary += (f"整体情感倾向：正面 {sentiment.get('positive_ratio', 0)*100:.0f}%、"
                       f"中性 {sentiment.get('neutral_ratio', 0)*100:.0f}%、"
                       f"负面 {sentiment.get('negative_ratio', 0)*100:.0f}%。")
        if kw_top:
            summary += f"高频关键词：{'、'.join(kw_top[:8])}。"

        return {
            "executive_summary": summary,
            "key_insights": [
                f"共分析 {total} 条文本，平均长度 {cr.get('avg_length', 0)} 字",
                f"提取 {len(cr.get('keywords', []))} 个关键词",
                *[f"主题「{t['theme']}」权重 {t['weight']:.2f}" for t in themes[:5]],
            ],
            "recommendations": cr.get("ai_insights", []),
            "metadata": {
                "generated_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "analysis_type": "content_analysis",
                "data_shape": {"rows": shape[0], "cols": shape[1]},
            },
        }

    def process_task(self, task_id: str, task_type: str, df,
                     requirements: Dict[str, Any],
                     update_progress, api_key: str = None) -> Dict[str, Any]:
        task_dir = TASKS_DIR / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        viz = IntelligentVisualization(task_dir)
        results = {}
        df_shape = (len(df), len(df.columns))

        try:
            # Content Analysis branch
            if task_type == "content_analysis":
                return self._run_content_analysis(task_id, df, requirements,
                                                  update_progress, api_key, task_dir)

            # Phase 1: EDA (always runs)
            update_progress(phase="eda", progress_pct=10, current_step="数据探索分析",
                           message="正在进行自动化数据探索...")
            eda_results = self.eda.analyze_dataset(df)
            results["eda"] = eda_results
            results["basic_info"] = eda_results["basic_info"]
            results["quality_analysis"] = eda_results["quality_analysis"]
            results["statistical_analysis"] = eda_results["statistical_analysis"]
            results["correlation_analysis"] = eda_results["correlation_analysis"]
            results["outlier_analysis"] = eda_results["outlier_analysis"]

            update_progress(phase="visualization", progress_pct=30, current_step="生成可视化图表",
                           message="正在自动生成数据图表...")
            target_col = requirements.get("target_column")
            chart_paths = viz.auto_visualize(df, target_col)
            results["visualizations"] = {k: Path(v).name for k, v in chart_paths.items() if v}

            # Phase 2: Modeling (if requested)
            if task_type in ("modeling", "prediction"):
                target = target_col
                if not target:
                    # Auto-select likely target (last numeric column)
                    numeric_cols = list(df.select_dtypes(include=["number"]).columns)
                    if numeric_cols:
                        target = numeric_cols[-1]

                if target and target in df.columns:
                    update_progress(phase="modeling", progress_pct=50, current_step="训练机器学习模型",
                                   message=f"正在针对 '{target}' 训练多个模型...")
                    ml = AutoMLModeling()
                    ml_results = ml.auto_build_model(df, target)
                    results["problem_type"] = ml_results["problem_type"]
                    results["model_results"] = ml_results["model_results"]
                    results["best_model_name"] = ml_results["best_model_name"]
                    results["feature_importance"] = ml_results["feature_importance"]

                    # Feature importance chart
                    if ml_results.get("feature_importance"):
                        fi_path = viz.plot_feature_importance(ml_results["feature_importance"])
                        if fi_path:
                            results["visualizations"]["feature_importance"] = Path(fi_path).name

            # Phase 3: Insights
            update_progress(phase="insight", progress_pct=70, current_step="提取业务洞察",
                           message="正在从数据中提取业务洞察...")
            insights = self.insight_extractor.extract_insights(df, results)
            results["insights"] = insights

            # Phase 4: Report
            update_progress(phase="report", progress_pct=85, current_step="生成分析报告",
                           message="正在生成综合分析报告...")
            report = self.report_generator.generate_comprehensive_report(results, df_shape)
            results["report"] = report

            # Save results to disk
            with open(task_dir / "results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2, cls=SafeEncoder)

            update_progress(phase="completed", progress_pct=100, current_step="分析完成",
                           message="数据分析已完成，可查看结果")

        except Exception as e:
            logger.exception(f"Task {task_id} failed")
            update_progress(phase="failed", current_step="分析失败", message=str(e))
            raise

        return results
