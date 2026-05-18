"""Intelligent visualization - auto-generates charts based on data types."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional

# Chinese font setup
for fname in ["SimHei", "Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei", "Noto Sans CJK SC"]:
    try:
        fm.findfont(fname, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [fname, "DejaVu Sans"]
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False


class IntelligentVisualization:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sns.set_palette("husl")

    def auto_visualize(self, df: pd.DataFrame, target_column: Optional[str] = None) -> Dict[str, str]:
        paths = {}
        numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
        categorical_cols = list(df.select_dtypes(include=["object", "category"]).columns)

        if target_column and target_column in numeric_cols:
            numeric_cols.remove(target_column)

        if len(numeric_cols) > 0:
            paths["distributions"] = self._plot_distributions(df, numeric_cols)
        if len(numeric_cols) > 1:
            paths["correlation"] = self._plot_correlation_heatmap(df, numeric_cols)
        if len(categorical_cols) > 0:
            paths["categorical"] = self._plot_categorical(df, categorical_cols)
        if target_column and target_column in df.columns:
            paths["target_analysis"] = self._plot_target_analysis(df, target_column)

        return paths

    def _plot_distributions(self, df: pd.DataFrame, numeric_cols: List[str]) -> str:
        n = len(numeric_cols)
        n_cols = min(3, n)
        n_rows = max(1, (n + n_cols - 1) // n_cols)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = list(axes)
        else:
            axes = list(axes.flatten())

        for i, col in enumerate(numeric_cols[: len(axes)]):
            data = df[col].dropna()
            axes[i].hist(data, bins=30, alpha=0.7, density=True, color="#6366f1", edgecolor="white")
            if len(data) > 1:
                data.plot.density(ax=axes[i], color="#ef4444", linewidth=2)
            axes[i].set_title(f"{col} 分布", fontsize=12)
            axes[i].set_ylabel("密度")
            axes[i].grid(True, alpha=0.3)

        for i in range(len(numeric_cols), len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        path = str(self.output_dir / "distributions.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def _plot_correlation_heatmap(self, df: pd.DataFrame, numeric_cols: List[str]) -> str:
        corr = df[numeric_cols].corr()
        fig_size = max(8, len(numeric_cols) * 1.2)
        plt.figure(figsize=(fig_size, fig_size * 0.8))
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, cmap="RdYlBu_r", center=0,
                    square=True, linewidths=0.5, fmt=".2f",
                    cbar_kws={"shrink": 0.8})
        plt.title("特征相关性热力图", fontsize=14)
        plt.tight_layout()
        path = str(self.output_dir / "correlation_heatmap.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def _plot_categorical(self, df: pd.DataFrame, categorical_cols: List[str]) -> str:
        cols = categorical_cols[:6]  # Max 6 categorical charts
        n = len(cols)
        n_cols = min(2, n)
        n_rows = max(1, (n + n_cols - 1) // n_cols)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 4 * n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = list(axes)
        else:
            axes = list(axes.flatten())

        for i, col in enumerate(cols):
            counts = df[col].value_counts().head(15)
            axes[i].barh(counts.index[::-1], counts.values[::-1], color="#6366f1", alpha=0.8)
            axes[i].set_title(f"{col} 分布", fontsize=12)
            axes[i].set_xlabel("计数")

        for i in range(n, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        path = str(self.output_dir / "categorical.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def _plot_target_analysis(self, df: pd.DataFrame, target: str) -> str:
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target]
        if not numeric_cols:
            return ""
        n = len(numeric_cols)
        n_cols = min(3, n)
        n_rows = max(1, (n + n_cols - 1) // n_cols)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = list(axes)
        else:
            axes = list(axes.flatten())

        for i, col in enumerate(numeric_cols[: len(axes)]):
            valid = df[[col, target]].dropna()
            axes[i].scatter(valid[col], valid[target], alpha=0.5, s=10, color="#6366f1")
            axes[i].set_xlabel(col, fontsize=10)
            axes[i].set_ylabel(target, fontsize=10)
            axes[i].grid(True, alpha=0.3)

        for i in range(n, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        path = str(self.output_dir / "target_analysis.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def plot_feature_importance(self, features: Dict[str, float], title: str = "特征重要性") -> str:
        items = sorted(features.items(), key=lambda x: x[1])
        if not items:
            return ""
        names, values = zip(*items)
        plt.figure(figsize=(10, max(5, len(items) * 0.4)))
        plt.barh(names, values, color="#6366f1", alpha=0.8)
        plt.title(title, fontsize=14)
        plt.xlabel("重要性")
        plt.tight_layout()
        path = str(self.output_dir / "feature_importance.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def plot_wordcloud(self, keywords: list, title: str = "关键词云") -> str:
        """Generate a word cloud from keyword list [{word, score, frequency}]."""
        try:
            from wordcloud import WordCloud
        except ImportError:
            return self._plot_word_freq_chart(keywords, title)

        # Build frequency dict
        freq_dict = {k["word"]: k.get("score", k.get("frequency", 1)) * 100 for k in keywords[:80]}
        if not freq_dict:
            return ""

        # Try to find a Chinese font
        font_path = None
        for fp in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
                    "C:/Windows/Fonts/msyhbd.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
            if Path(fp).exists():
                font_path = fp
                break

        wc = WordCloud(
            width=800, height=500,
            background_color="white",
            font_path=font_path,
            max_words=60,
            colormap="viridis",
            random_state=42,
        )
        wc.generate_from_frequencies(freq_dict)

        plt.figure(figsize=(12, 7.5))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.title(title, fontsize=16, fontweight="bold", pad=20)
        plt.tight_layout(pad=0)
        path = str(self.output_dir / "wordcloud.png")
        plt.savefig(path, dpi=200, bbox_inches="tight")
        plt.close()
        return path

    def _plot_word_freq_chart(self, keywords: list, title: str) -> str:
        """Fallback: horizontal bar chart for keywords."""
        items = sorted(keywords[:25], key=lambda x: x.get("score", x.get("frequency", 0)))
        if not items:
            return ""
        words = [k["word"] for k in items]
        values = [k.get("score", k.get("frequency", 1)) for k in items]
        plt.figure(figsize=(10, max(5, len(items) * 0.35)))
        plt.barh(words, values, color="#6366f1", alpha=0.8)
        plt.title(title, fontsize=14)
        plt.xlabel("重要度")
        plt.tight_layout()
        path = str(self.output_dir / "wordcloud.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path
