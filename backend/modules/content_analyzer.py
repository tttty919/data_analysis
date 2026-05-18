"""Content Analysis module - NLP for text/social media content."""
import re
import math
import json
from collections import Counter
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Optional imports
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False


class ContentAnalyzer:
    def __init__(self):
        pass

    def analyze(self, df: pd.DataFrame, text_column: str,
                api_key: str = None) -> Dict[str, Any]:
        """Full content analysis pipeline with all 6 advanced capabilities."""
        texts = df[text_column].dropna().astype(str).tolist()
        if not texts:
            return {"error": "文本列为空"}

        cleaned = [clean_text(t) for t in texts]
        all_text = " ".join(cleaned)

        # 1. Keywords
        keywords = extract_keywords(all_text, top_n=50)

        # 2. Sentiment
        sentiment = analyze_sentiment(cleaned)

        # 3. Theme clustering
        themes = _cluster_themes(keywords, cleaned, api_key)

        # 4. NPS proxy
        nps = _calculate_nps_proxy(sentiment, cleaned)

        # 5. Pain point prioritization
        pain_points = _prioritize_pain_points(cleaned, keywords, sentiment, api_key)

        # 6. Competitor mentions
        competitor_mentions = _detect_competitor_mentions(all_text, cleaned)

        # 7. User segmentation
        user_col = None
        for c in df.columns:
            if c != text_column and "用户" in str(c) or "作者" in str(c) or "user" in str(c).lower():
                user_col = c
                break
        user_names = df[user_col].astype(str).tolist() if user_col else [f"用户{i+1}" for i in range(len(texts))]
        segments = _segment_users(cleaned, user_names, sentiment, api_key)

        # 8. JTBD extraction
        jtbds = _extract_jtbd(cleaned, keywords, api_key)

        # 9. Customer journey emotion curve
        journey = _map_customer_journey(cleaned, sentiment, api_key)

        # 10. AI insights
        ai_insights = []
        if api_key:
            ai_insights = _generate_ai_insights(keywords, sentiment, cleaned, api_key)

        return {
            "total_texts": len(texts),
            "text_column": text_column,
            "avg_length": round(sum(len(t) for t in texts) / max(len(texts), 1), 0),
            "keywords": keywords[:30],
            "sentiment": sentiment,
            "themes": themes,
            "nps": nps,
            "pain_points": pain_points,
            "competitor_mentions": competitor_mentions,
            "user_segments": segments,
            "jtbd": jtbds,
            "customer_journey": journey,
            "ai_insights": ai_insights,
        }


def clean_text(text: str) -> str:
    """Clean text: remove HTML, URLs, normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    # Keep CJK, letters, digits, basic punctuation
    text = re.sub(r"[^一-鿿　-〿＀-￯a-zA-Z0-9\s.,!?，。！？、；：""''【】《》（）…—\-\+]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(text: str, top_n: int = 30) -> List[Dict]:
    """Extract keywords using TF-IDF (with jieba) or word frequency."""
    if HAS_JIEBA:
        words = list(jieba.cut(text))
        words = [w.strip() for w in words if len(w.strip()) >= 2 and not w.isspace()]
        return _compute_tfidf(words, top_n)
    else:
        return _simple_word_freq(text, top_n)


def _compute_tfidf(words: List[str], top_n: int) -> List[Dict]:
    total = len(words)
    freq = Counter(words)
    sentences = [s.strip() for s in " ".join(words).split("。")]
    if len(sentences) < 2:
        sentences = [" ".join(words)]

    results = []
    for word, count in freq.most_common(top_n * 3):
        tf = count / max(total, 1)
        doc_count = sum(1 for s in sentences if word in s)
        idf = math.log(max(len(sentences), 1) / max(doc_count, 1)) + 1
        score = tf * idf * count / max(total, 1) * 1000
        results.append({"word": word, "score": round(score, 3), "frequency": count})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def _simple_word_freq(text: str, top_n: int) -> List[Dict]:
    tokens = re.findall(r"[a-zA-Z一-鿿]{2,}", text)
    freq = Counter(tokens)
    total = len(tokens)
    return [
        {"word": w, "score": round(c / max(total, 1) * 100, 3), "frequency": c}
        for w, c in freq.most_common(top_n)
    ]


def analyze_sentiment(texts: List[str]) -> Dict[str, Any]:
    """Sentiment analysis for text items."""
    if HAS_SNOWNLP:
        scores = []
        for t in texts[:500]:
            try:
                scores.append(SnowNLP(t).sentiments)
            except Exception:
                scores.append(0.5)

        if scores:
            pos = sum(1 for s in scores if s > 0.6)
            neg = sum(1 for s in scores if s < 0.4)
            neu = len(scores) - pos - neg
            return {
                "total": len(scores),
                "positive_ratio": round(pos / len(scores), 3),
                "neutral_ratio": round(neu / len(scores), 3),
                "negative_ratio": round(neg / len(scores), 3),
                "avg_score": round(np.mean(scores), 3),
            }

    # Rule-based fallback
    return _rule_sentiment(texts)


def _rule_sentiment(texts: List[str]) -> Dict:
    pos_words = ["好", "棒", "赞", "喜欢", "推荐", "满意", "优秀", "不错", "好用", "方便",
                 "great", "good", "love", "best", "excellent", "amazing"]
    neg_words = ["差", "烂", "失望", "后悔", "难用", "垃圾", "坑", "骗", "投诉", "垃圾",
                 "bad", "terrible", "worst", "awful", "hate", "poor"]

    pos_count = 0
    neg_count = 0
    neut_count = 0
    for t in texts:
        t_lower = t.lower()
        p = sum(1 for w in pos_words if w in t_lower)
        n = sum(1 for w in neg_words if w in t_lower)
        if p > n:
            pos_count += 1
        elif n > p:
            neg_count += 1
        else:
            neut_count += 1

    total = len(texts)
    return {
        "total": total,
        "positive_ratio": round(pos_count / max(total, 1), 3),
        "neutral_ratio": round(neut_count / max(total, 1), 3),
        "negative_ratio": round(neg_count / max(total, 1), 3),
        "avg_score": 0.5,
    }


def _cluster_themes(keywords: List[Dict], texts: List[str],
                    api_key: str = None) -> List[Dict]:
    """Cluster keywords into themes."""
    if api_key:
        llm_result = _llm_cluster(keywords, texts, api_key)
        if llm_result:
            return llm_result
    return _rule_cluster(keywords, texts)


def _rule_cluster(keywords: List[Dict], texts: List[str]) -> List[Dict]:
    groups = {
        "功能体验": ["功能", "体验", "好用", "方便", "实用", "feature", "use", "experience"],
        "价格价值": ["价格", "便宜", "贵", "值得", "性价比", "price", "cost", "worth", "cheap"],
        "设计界面": ["设计", "好看", "颜值", "外观", "UI", "design", "look", "beautiful", "界面"],
        "使用效果": ["效果", "有用", "有效", "改善", "result", "effective", "效果"],
        "用户服务": ["客服", "售后", "服务", "态度", "support", "service", "回复"],
        "推荐意愿": ["推荐", "回购", "种草", "安利", "踩雷", "拔草", "recommend"],
    }

    themes = []
    matched = set()
    total_score = sum(k["score"] for k in keywords) or 1

    for name, triggers in groups.items():
        matched_kw = [k for k in keywords if any(t in k["word"].lower() for t in triggers)]
        if matched_kw:
            weight = sum(k["score"] for k in matched_kw) / total_score
            quotes = []
            for t in texts[:100]:
                if any(trig in t.lower() for trig in triggers):
                    quotes.append(t[:200].strip())
                    if len(quotes) >= 3:
                        break
            themes.append({
                "theme": name,
                "weight": round(min(weight * 3, 1), 3),
                "keywords": [k["word"] for k in matched_kw[:5]],
                "representative_quotes": quotes[:3],
            })
            matched.update(k["word"] for k in matched_kw)

    other = [k for k in keywords if k["word"] not in matched]
    if other:
        themes.append({
            "theme": "其他关注点",
            "weight": round(sum(k["score"] for k in other) / total_score, 3),
            "keywords": [k["word"] for k in other[:8]],
            "representative_quotes": [],
        })

    themes.sort(key=lambda t: t["weight"], reverse=True)
    return themes


def _llm_cluster(keywords: List[Dict], texts: List[str], api_key: str) -> Optional[List[Dict]]:
    from backend.services.llm_service import call_deepseek
    kw_list = [k["word"] for k in keywords[:30]]
    samples = [t[:200].strip() for t in texts[:15] if t.strip()]

    prompt = (
        "你是资深用户研究员。将用户讨论聚合为3-6个需求主题，返回JSON数组："
        "[{theme, weight(0-1), keywords:[], representative_quotes:[]}]"
        f"\n关键词：{kw_list}\n内容摘要：\n" + "\n---\n".join(samples)
    )
    result = call_deepseek(prompt, api_key, temperature=0.3, max_tokens=2000)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


def _generate_ai_insights(keywords: List[Dict], sentiment: Dict,
                          texts: List[str], api_key: str) -> List[Dict]:
    from backend.services.llm_service import call_deepseek

    kw_top = [k["word"] for k in keywords[:20]]
    pos_r = int((sentiment.get("positive_ratio", 0.5)) * 100)
    neg_r = int((sentiment.get("negative_ratio", 0.5)) * 100)
    samples = [t[:200].strip() for t in texts[:15] if t.strip()]

    prompt = (
        "你是产品战略顾问。基于用户讨论数据，给出3-5条产品方向建议。"
        "每条包含：title(核心观点), detail(数据支撑分析), action(可执行动作)。"
        f"好评率{pos_r}%，差评率{neg_r}%，高频关键词：{kw_top}\n"
        f"用户讨论内容：\n" + "\n---\n".join(samples) + "\n"
        "返回纯JSON数组：[{title, detail, action}]"
    )
    result = call_deepseek(prompt, api_key, temperature=0.5, max_tokens=2500)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return []


# ====== NPS Proxy ======

def _calculate_nps_proxy(sentiment: Dict, texts: List[str]) -> Dict:
    """Estimate NPS from sentiment distribution."""
    pos_r = sentiment.get("positive_ratio", 0)
    neg_r = sentiment.get("negative_ratio", 0)
    neu_r = sentiment.get("neutral_ratio", 0)

    promoters = pos_r * 0.65
    detractors = neg_r * 0.80
    passives = 1 - promoters - detractors
    nps_score = round((promoters - detractors) * 100)

    if nps_score >= 50:
        level = "优秀"
    elif nps_score >= 30:
        level = "良好"
    elif nps_score >= 0:
        level = "一般"
    elif nps_score >= -30:
        level = "需要改善"
    else:
        level = "严重问题"

    return {
        "nps_score": nps_score,
        "level": level,
        "promoters_pct": round(promoters * 100, 1),
        "passives_pct": round(passives * 100, 1),
        "detractors_pct": round(detractors * 100, 1),
        "total_respondents": sentiment.get("total", len(texts)),
        "benchmark": "行业平均值约 30-40（供参考）",
    }


# ====== Pain Point Prioritization ======

def _prioritize_pain_points(texts: List[str], keywords: List[Dict],
                            sentiment: Dict, api_key: str = None) -> List[Dict]:
    """Prioritize pain points by frequency × severity."""
    if api_key:
        result = _llm_pain_points(texts, keywords, sentiment, api_key)
        if result:
            return result
    return _rule_pain_points(texts, keywords, sentiment)


def _rule_pain_points(texts: List[str], keywords: List[Dict],
                      sentiment: Dict) -> List[Dict]:
    neg_signals = ["差", "烂", "失望", "后悔", "难用", "垃圾", "坑", "骗", "投诉",
                   "慢", "卡", "贵", "烫", "问题", "坏", "故障", "bug", "崩溃",
                   "不行", "不好", "太", "严重", "没人", "不回", "不"]
    pain_kws = []
    for kw in keywords:
        txt = kw["word"]
        freq = kw["frequency"]
        severity = sum(1 for s in neg_signals if s in txt) * 0.5 + 0.3
        mentions = sum(1 for t in texts if txt in t)
        if mentions >= 1:
            pain_kws.append({
                "pain_point": txt,
                "frequency": freq,
                "mention_count": mentions,
                "severity_score": round(min(severity + freq / max(len(texts), 1) * 3, 1), 3),
                "impact_score": round(min(freq * severity / max(len(texts), 1) * 10, 1), 3),
            })

    pain_kws.sort(key=lambda x: x["impact_score"], reverse=True)
    for i, p in enumerate(pain_kws[:10]):
        if p["impact_score"] > 0.5:
            p["priority"] = "P0 - 紧急"
        elif p["impact_score"] > 0.3:
            p["priority"] = "P1 - 高"
        elif p["impact_score"] > 0.15:
            p["priority"] = "P2 - 中"
        else:
            p["priority"] = "P3 - 低"

    return pain_kws[:15]


def _llm_pain_points(texts: List[str], keywords: List[Dict],
                     sentiment: Dict, api_key: str) -> Optional[List[Dict]]:
    from backend.services.llm_service import call_deepseek
    kw_list = [k["word"] for k in keywords[:25]]
    samples = [t[:150].strip() for t in texts[:15] if t.strip()]
    prompt = (
        "你是用户研究员。从以下用户反馈中识别痛点，按严重度×频率排序。"
        "返回JSON数组：[{pain_point, frequency(1-10), severity_score(0-1), impact_score(0-1), priority(P0/P1/P2/P3)}]"
        f"关键词：{kw_list}\n反馈：\n" + "\n".join(samples)
    )
    result = call_deepseek(prompt, api_key, temperature=0.3, max_tokens=1500)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


# ====== Competitor Mention Detection ======

COMPETITOR_DB = {
    "手机": ["华为", "小米", "OPPO", "vivo", "三星", "iPhone", "苹果", "一加", "荣耀", "realme"],
    "电商": ["淘宝", "京东", "拼多多", "抖音电商", "快手", "小红书"],
    "社交": ["微信", "微博", "抖音", "快手", "小红书", "B站", "知乎"],
    "通用": ["友商", "竞品", "别家", "其他品牌", "别"],
}

def _detect_competitor_mentions(all_text: str, texts: List[str]) -> Dict:
    """Detect competitor brand mentions in user feedback."""
    all_comps = set()
    for brands in COMPETITOR_DB.values():
        all_comps.update(brands)

    mentions = {}
    for comp in all_comps:
        count = sum(1 for t in texts if comp.lower() in t.lower())
        if count > 0:
            # Extract sample quotes
            quotes = [t[:200] for t in texts if comp.lower() in t.lower()][:3]
            # Determine sentiment context
            comp_texts = [t for t in texts if comp.lower() in t.lower()]
            comp_sent = analyze_sentiment(comp_texts) if comp_texts else {}

            mentions[comp] = {
                "brand": comp,
                "mention_count": count,
                "mention_rate": round(count / max(len(texts), 1) * 100, 1),
                "sentiment": comp_sent,
                "sample_quotes": quotes,
            }

    sorted_mentions = sorted(mentions.values(), key=lambda x: x["mention_count"], reverse=True)
    return {
        "total_mentions": sum(m["mention_count"] for m in sorted_mentions),
        "competitors_found": len(sorted_mentions),
        "details": sorted_mentions[:10],
    }


# ====== User Segmentation ======

def _segment_users(texts: List[str], user_names: List[str],
                   sentiment: Dict, api_key: str = None) -> List[Dict]:
    """Segment users based on feedback patterns."""
    if api_key and len(texts) >= 10:
        result = _llm_segment(texts, user_names, api_key)
        if result:
            return result
    return _rule_segment(texts, user_names)


def _rule_segment(texts: List[str], user_names: List[str]) -> List[Dict]:
    # Classify each user by their feedback content
    promoters = []
    detractors = []
    neutrals = []

    for i, (name, text) in enumerate(zip(user_names, texts)):
        pos = sum(1 for w in ["好", "棒", "赞", "喜欢", "推荐", "满意", "优秀", "不错", "好用", "方便", "值得"] if w in text)
        neg = sum(1 for w in ["差", "烂", "失望", "后悔", "难用", "垃圾", "坑", "骗", "投诉", "不行", "问题", "严重"] if w in text)
        entry = {"name": name, "text": text[:100], "index": i}
        if pos > neg:
            promoters.append(entry)
        elif neg > pos:
            detractors.append(entry)
        else:
            neutrals.append(entry)

    segments = []
    if promoters:
        segments.append({
            "segment_name": "推荐者 (Promoters)",
            "count": len(promoters),
            "percentage": round(len(promoters) / max(len(texts), 1) * 100, 1),
            "profile": "对产品满意，愿意推荐给他人",
            "needs": "更多高级功能、个性化体验、社交分享",
            "risk": "可能因一次负面体验转为贬损者",
            "sample_users": [u["name"] for u in promoters[:5]],
        })
    if detractors:
        segments.append({
            "segment_name": "贬损者 (Detractors)",
            "count": len(detractors),
            "percentage": round(len(detractors) / max(len(texts), 1) * 100, 1),
            "profile": "对产品不满，有流失或负面口碑风险",
            "needs": "问题修复、客服响应、补偿机制",
            "risk": "会在社交媒体传播负面评价",
            "sample_users": [u["name"] for u in detractors[:5]],
        })
    if neutrals:
        segments.append({
            "segment_name": "被动者 (Passives)",
            "count": len(neutrals),
            "percentage": round(len(neutrals) / max(len(texts), 1) * 100, 1),
            "profile": "态度中性，使用产品但情感绑定不深",
            "needs": "差异化价值感知、使用习惯培养",
            "risk": "容易被竞品转化",
            "sample_users": [u["name"] for u in neutrals[:5]],
        })

    return segments


def _llm_segment(texts: List[str], user_names: List[str], api_key: str) -> Optional[List[Dict]]:
    from backend.services.llm_service import call_deepseek
    samples = []
    for i, (n, t) in enumerate(zip(user_names[:10], texts[:10])):
        samples.append(f"{n}: {t[:100]}")
    prompt = (
        "你是用户研究员。将用户分为2-4个群体（如推荐者/贬损者/被动者，或按使用场景分群）。"
        "返回JSON：[{segment_name, count, percentage, profile, needs, risk, sample_users:[]}]"
        f"\n用户反馈：\n" + "\n".join(samples)
    )
    result = call_deepseek(prompt, api_key, temperature=0.4, max_tokens=1500)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


# ====== JTBD Extraction ======

def _extract_jtbd(texts: List[str], keywords: List[Dict],
                  api_key: str = None) -> List[Dict]:
    """Extract Jobs-to-be-Done from user feedback."""
    if api_key and len(texts) >= 5:
        result = _llm_jtbd(texts, keywords, api_key)
        if result:
            return result
    return _rule_jtbd(texts, keywords)


def _rule_jtbd(texts: List[str], keywords: List[Dict]) -> List[Dict]:
    jtbd_patterns = {
        "社交表达": ["分享", "晒", "朋友圈", "推荐", "安利", "种草", "show", "朋友"],
        "效率工具": ["快", "方便", "省时", "效率", "一键", "自动", "简单", "轻松"],
        "娱乐消遣": ["玩", "看", "刷", "打发时间", "娱乐", "放松", "kill time", "无聊"],
        "学习成长": ["学", "教程", "课程", "知识", "技能", "提升", "成长", "进步"],
        "性价比追求": ["便宜", "划算", "性价比", "省钱", "值得", "价格", "折扣"],
        "品质生活": ["品质", "质感", "高端", "精致", "设计", "好看", "颜值", "美"],
        "社交连接": ["联系", "沟通", "聊天", "互动", "评论", "私信", "connect"],
        "解决问题": ["解决", "问题", "帮助", "支持", "答疑", "帮", "求助"],
    }

    jtbds = []
    for job_name, triggers in jtbd_patterns.items():
        matched = [t for t in texts[:50] if any(trig in t for trig in triggers)]
        if matched:
            functional = f"用户需要{'、'.join(triggers[:3])}的体验"
            emotional = "感到满足和认可" if "好" in " ".join(matched) else "减少焦虑和不便"
            jtbds.append({
                "job_name": job_name,
                "functional_job": functional,
                "emotional_job": emotional,
                "mention_count": len(matched),
                "mention_rate": round(len(matched) / max(len(texts), 1) * 100, 1),
                "keywords_matched": triggers[:5],
            })

    jtbds.sort(key=lambda x: x["mention_count"], reverse=True)
    return jtbds


def _llm_jtbd(texts: List[str], keywords: List[Dict], api_key: str) -> Optional[List[Dict]]:
    from backend.services.llm_service import call_deepseek
    samples = [t[:150].strip() for t in texts[:12] if t.strip()]
    kw_list = [k["word"] for k in keywords[:15]]
    prompt = (
        "你是JTBD分析师。从用户反馈中识别Jobs-to-be-Done。"
        "返回JSON：[{job_name, functional_job(用户想要完成什么任务), emotional_job(用户想要什么感受), mention_count, keywords_matched:[]}]"
        f"关键词：{kw_list}\n反馈：\n" + "\n---\n".join(samples)
    )
    result = call_deepseek(prompt, api_key, temperature=0.4, max_tokens=1500)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None


# ====== Customer Journey Emotion Curve ======

def _map_customer_journey(texts: List[str], sentiment: Dict,
                          api_key: str = None) -> Dict:
    """Map sentiment across customer journey stages."""
    if api_key and len(texts) >= 5:
        result = _llm_journey(texts, api_key)
        if result:
            return result
    return _rule_journey(texts, sentiment)


def _rule_journey(texts: List[str], sentiment: Dict) -> Dict:
    stages = {
        "认知发现": ["看到", "广告", "推荐", "种草", "听说", "刷到", "朋友介绍", "了解"],
        "决策购买": ["买", "下单", "价格", "便宜", "贵", "性价比", "对比", "选"],
        "开箱使用": ["收到", "开箱", "包装", "物流", "快递", "第", "安装", "设置"],
        "日常体验": ["用", "日常", "每天", "续航", "流畅", "方便", "拍照", "效果"],
        "问题解决": ["问题", "客服", "售后", "维修", "换", "退", "投诉", "解决"],
        "推荐复购": ["推荐", "回购", "再买", "安利", "下次", "还会", "值得"],
    }

    stage_scores = []
    for stage_name, triggers in stages.items():
        matched = [t for t in texts if any(trig in t for trig in triggers)]
        if matched:
            pos = sum(1 for t in matched if any(w in t for w in ["好", "棒", "满意", "推荐", "不错", "喜欢"]))
            neg = sum(1 for t in matched if any(w in t for w in ["差", "烂", "失望", "后悔", "问题", "坑"]))
            score = round((pos - neg) / max(len(matched), 1), 2)
            stage_scores.append({
                "stage": stage_name,
                "mention_count": len(matched),
                "sentiment_score": score,
                "sentiment_label": "正面" if score > 0.2 else ("负面" if score < -0.2 else "中性"),
                "sample_quote": matched[0][:150] if matched else "",
            })

    scores = [s["sentiment_score"] for s in stage_scores if s["mention_count"] >= 2]
    avg_score = round(sum(scores) / max(len(scores), 1), 2) if scores else 0

    pain_stages = [s for s in stage_scores if s["sentiment_score"] < 0]
    joy_stages = [s for s in stage_scores if s["sentiment_score"] > 0.3]

    return {
        "stages": stage_scores,
        "overall_curve_score": avg_score,
        "pain_stages": [s["stage"] for s in pain_stages],
        "joy_stages": [s["stage"] for s in joy_stages],
        "insight": f"用户情感低谷在{'、'.join(s['stage'] for s in pain_stages) if pain_stages else '无明显低谷'}，"
                   f"高峰在{'、'.join(s['stage'] for s in joy_stages) if joy_stages else '无明显高峰'}",
    }


def _llm_journey(texts: List[str], api_key: str) -> Optional[Dict]:
    from backend.services.llm_service import call_deepseek
    samples = [t[:150].strip() for t in texts[:15] if t.strip()]
    prompt = (
        "你是用户体验研究员。分析用户反馈中的旅程阶段和情感变化。"
        "识别3-6个旅程阶段，每个阶段给出情感分数(-1到1)和代表性引语。"
        "返回JSON：{stages:[{stage, mention_count, sentiment_score, sample_quote}],"
        "pain_stages:[], joy_stages:[], insight}"
        f"\n反馈：\n" + "\n---\n".join(samples)
    )
    result = call_deepseek(prompt, api_key, temperature=0.3, max_tokens=1500)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            pass
    return None
