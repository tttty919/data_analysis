"""DeepSeek API integration for NLU and insight generation."""
import json
import requests
from typing import Optional
from backend.config import DEEPSEEK_API, DEEPSEEK_MODEL


def call_deepseek(prompt: str, api_key: str, temperature: float = 0.3,
                  max_tokens: int = 2000, timeout: int = 90) -> Optional[str]:
    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
        return content
    except Exception:
        return None


def test_api_key(api_key: str) -> dict:
    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": "回复：通"}],
                "max_tokens": 5,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return {"ok": True, "message": f"连接成功: {resp.json()['choices'][0]['message']['content']}"}
        return {"ok": False, "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.exceptions.Timeout:
        return {"ok": False, "message": "连接超时，可能需要开 VPN"}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "message": "网络不通，无法连接 DeepSeek API"}
    except Exception as e:
        return {"ok": False, "message": f"{type(e).__name__}: {e}"}


def parse_user_requirements(user_input: str, df_columns: list,
                            api_key: str) -> dict:
    """Use DeepSeek to parse natural language analysis requirements."""
    if not api_key:
        return _rule_parse(user_input, df_columns)

    prompt = (
        "你是数据分析系统。从用户输入中提取分析需求，返回纯JSON。\n"
        f"数据集列名: {df_columns}\n"
        f"用户输入: {user_input}\n"
        '返回格式: {"task_type":"exploration|modeling","target_column":null|"列名","focus":["关注点1","关注点2"]}'
    )
    result = call_deepseek(prompt, api_key, temperature=0.1, max_tokens=300)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return _rule_parse(user_input, df_columns)


def _rule_parse(user_input: str, df_columns: list) -> dict:
    """Rule-based fallback for requirement parsing."""
    text = user_input.lower()
    task_type = "exploration"
    target_column = None

    # Detect modeling intent
    for word in ["预测", "建模", "回归", "分类", "predict", "model", "regression", "classification"]:
        if word in text:
            task_type = "modeling"
            break

    # Try to find target column
    for col in df_columns:
        if col.lower() in text:
            target_column = col
            break

    return {"task_type": task_type, "target_column": target_column, "focus": []}


def generate_nlu_insights(analysis_results: dict, api_key: str = None) -> list:
    """Generate natural language insights from analysis results using DeepSeek."""
    if not api_key:
        return _rule_insights(analysis_results)

    prompt = (
        "你是资深数据分析顾问。基于以下分析结果，给出3-5条业务洞察建议。"
        "每条包含 title(核心观点), detail(数据支撑), action(可执行动作)。"
        f"分析结果: {json.dumps(analysis_results, ensure_ascii=False, default=str)[:3000]}\n"
        '返回纯JSON数组: [{title, detail, action}]'
    )
    result = call_deepseek(prompt, api_key, temperature=0.5, max_tokens=2000)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return _rule_insights(analysis_results)


def _rule_insights(results: dict) -> list:
    insights = []

    # Correlation insights
    corr_data = results.get("correlation_analysis", {})
    pairs = corr_data.get("pairs", [])
    if pairs:
        top = pairs[0]
        insights.append({
            "title": f"强相关发现: {top['var1']} ↔ {top['var2']}",
            "detail": f"两个变量的相关系数为 {top['correlation']:.3f}，表明存在显著的线性关联。建议进一步分析因果关系，判断是否存在可干预的杠杆变量。",
            "action": f"对 {top['var1']} 和 {top['var2']} 进行 Granger 因果检验，设计对照实验验证因果关系。",
        })

    # Model insights
    model_results = results.get("model_results", {})
    if model_results:
        valid = {k: v for k, v in model_results.items() if "error" not in v}
        if valid:
            key = "r2_score" if "r2_score" in list(valid.values())[0] else "accuracy"
            best = max(valid.items(), key=lambda x: x[1].get(key, 0))
            insights.append({
                "title": f"最佳模型: {best[0]}",
                "detail": f"{best[0]} 在测试集上 {key}={best[1][key]:.4f}，CV 均值为 {best[1].get('cv_mean', 'N/A')}，表现稳健。",
                "action": f"将 {best[0]} 部署为预测服务，同时监控特征漂移，每季度重新训练。",
            })

    # Quality insights
    qa = results.get("quality_analysis", {})
    missing_total = qa.get("missing_cells", 0)
    total_cells = qa.get("total_cells", 1)
    if missing_total / max(total_cells, 1) > 0.05:
        insights.append({
            "title": "数据质量有待提升",
            "detail": f"当前缺失率为 {missing_total/max(total_cells,1)*100:.1f}%，可能影响模型精度。",
            "action": "优先修复关键列的缺失值，或使用 KNN Imputer 进行智能填充。",
        })

    return insights[:5]
