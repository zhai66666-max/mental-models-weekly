#!/usr/bin/env python3
"""
思维格栅日报 — 每天一个经典思维模型深度拆解
每天 7:00 AM（北京时间）自动生成并邮件推送。
DeepSeek 深度解读 + 温故知新复习模块。
"""

import os
import sys
import re
import json
import smtplib
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, Any, List, Optional, Tuple

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.json")

# ─── 思维模型主库（52个，一年不重样）─────────────────────────────────────────

MENTAL_MODELS: List[Dict[str, str]] = [
    # 认知偏误
    {"name": "幸存者偏差", "category": "认知偏误", "keywords": "survivorship bias, selection bias, 成功学"},
    {"name": "确认偏误", "category": "认知偏误", "keywords": "confirmation bias, 选择性注意"},
    {"name": "沉没成本谬误", "category": "认知偏误", "keywords": "sunk cost, escalation of commitment"},
    {"name": "锚定效应", "category": "认知偏误", "keywords": "anchoring, negotiation, pricing"},
    {"name": "可得性启发", "category": "认知偏误", "keywords": "availability heuristic, recency bias"},
    {"name": "损失厌恶", "category": "认知偏误", "keywords": "loss aversion, prospect theory"},
    {"name": "基本归因错误", "category": "认知偏误", "keywords": "fundamental attribution error, actor-observer"},
    {"name": "过度自信偏误", "category": "认知偏误", "keywords": "overconfidence, Dunning-Kruger, 能力错觉"},
    {"name": "框架效应", "category": "认知偏误", "keywords": "framing effect, 表述方式影响决策"},
    {"name": "后见之明偏误", "category": "认知偏误", "keywords": "hindsight bias, 事后诸葛亮"},
    {"name": "从众效应", "category": "认知偏误", "keywords": "bandwagon effect, herd behavior, 羊群效应"},
    {"name": "现状偏误", "category": "认知偏误", "keywords": "status quo bias, default effect"},

    # 思维模型
    {"name": "第一性原理", "category": "思维模型", "keywords": "first principles, Musk, 本质思考"},
    {"name": "二阶思维", "category": "思维模型", "keywords": "second-order thinking, consequences, 连锁反应"},
    {"name": "逆向思维", "category": "思维模型", "keywords": "inversion, 反过来想, 查理芒格"},
    {"name": "奥卡姆剃刀", "category": "思维模型", "keywords": "Occam's razor, simplicity, 简洁原则"},
    {"name": "地图不等于疆域", "category": "思维模型", "keywords": "map is not territory, 模型与现实的差距"},
    {"name": "能力圈", "category": "思维模型", "keywords": "circle of competence, Buffett, 知道自己不知道"},
    {"name": "复利思维", "category": "思维模型", "keywords": "compounding, exponential growth, 长期主义"},
    {"name": "安全边际", "category": "思维模型", "keywords": "margin of safety, 冗余, 容错"},
    {"name": "反馈循环", "category": "思维模型", "keywords": "feedback loops, systems thinking, 正反馈负反馈"},
    {"name": "杠杆原理", "category": "思维模型", "keywords": "leverage, Archimedes, 以小博大"},
    {"name": "反脆弱", "category": "思维模型", "keywords": "antifragile, Taleb, 从波动中获益"},
    {"name": "帕累托法则", "category": "思维模型", "keywords": "Pareto principle, 80/20, 关键少数"},
    {"name": "汉隆剃刀", "category": "思维模型", "keywords": "Hanlon's razor, 别把愚蠢归为恶意"},
    {"name": "临界质量", "category": "思维模型", "keywords": "critical mass, tipping point, 引爆点"},
    {"name": "委托代理问题", "category": "思维模型", "keywords": "principal-agent problem, incentives, 激励相容"},

    # 系统与策略
    {"name": "囚徒困境", "category": "系统与策略", "keywords": "prisoner's dilemma, game theory, 合作与背叛"},
    {"name": "公地悲剧", "category": "系统与策略", "keywords": "tragedy of the commons, shared resources"},
    {"name": "网络效应", "category": "系统与策略", "keywords": "network effects, Metcalfe's law, 平台经济"},
    {"name": "路径依赖", "category": "系统与策略", "keywords": "path dependence, lock-in, QWERTY"},
    {"name": "黑天鹅事件", "category": "系统与策略", "keywords": "black swan, Taleb, 极端事件"},
    {"name": "蝴蝶效应", "category": "系统与策略", "keywords": "butterfly effect, chaos theory, 非线性"},
    {"name": "耗散结构", "category": "系统与策略", "keywords": "dissipative structure, entropy, 开放系统"},
    {"name": "冗余与韧性", "category": "系统与策略", "keywords": "redundancy, resilience, 备份系统"},
    {"name": "涌现", "category": "系统与策略", "keywords": "emergence, complexity, 整体大于部分"},
    {"name": "林迪效应", "category": "系统与策略", "keywords": "Lindy effect, 越活越久"},

    # 决策与概率
    {"name": "贝叶斯更新", "category": "决策与概率", "keywords": "Bayesian updating, 先验后验, 动态调整信念"},
    {"name": "期望值思维", "category": "决策与概率", "keywords": "expected value, probability, 决策树"},
    {"name": "回归均值", "category": "决策与概率", "keywords": "regression to mean, 均值回归"},
    {"name": "大数定律", "category": "决策与概率", "keywords": "law of large numbers, sample size, 统计思维"},
    {"name": "基尼系数与不平等", "category": "决策与概率", "keywords": "Gini coefficient, inequality, 分配"},
    {"name": "选项价值", "category": "决策与概率", "keywords": "optionality, real options, 保留选择权"},
    {"name": "遍历性与非遍历性", "category": "决策与概率", "keywords": "ergodicity, ensemble vs time, 概率陷阱"},
    {"name": "辛普森悖论", "category": "决策与概率", "keywords": "Simpson's paradox, 数据聚合陷阱"},

    # 经济与商业
    {"name": "比较优势", "category": "经济与商业", "keywords": "comparative advantage, trade, 分工"},
    {"name": "供需定律", "category": "经济与商业", "keywords": "supply and demand, market equilibrium"},
    {"name": "机会成本", "category": "经济与商业", "keywords": "opportunity cost, trade-offs"},
    {"name": "边际效用递减", "category": "经济与商业", "keywords": "diminishing returns, marginal utility"},
    {"name": "创造性破坏", "category": "经济与商业", "keywords": "creative destruction, Schumpeter, 创新"},
    {"name": "护城河", "category": "经济与商业", "keywords": "moat, competitive advantage, Buffett"},
    {"name": "激励相容", "category": "经济与商业", "keywords": "incentive compatibility, mechanism design"},
    {"name": "科斯定理", "category": "经济与商业", "keywords": "Coase theorem, transaction costs, 产权"},
]

# ─── 历史记录管理 ─────────────────────────────────────────────────────────────


def load_history() -> Dict[str, Any]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {"covered": [], "week": 0}


def save_history(h: Dict[str, Any]) -> None:
    with open(HISTORY_FILE, "w") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)


def pick_next_model(history: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """选择下一个未覆盖的模型。"""
    covered_names = {c["name"] for c in history["covered"]}
    for m in MENTAL_MODELS:
        if m["name"] not in covered_names:
            return m
    # 全学完了，重新开始
    history["covered"] = []
    history["week"] = 0
    return MENTAL_MODELS[0]


# ─── DeepSeek 深度拆解 ───────────────────────────────────────────────────────


def generate_deep_dive(model: Dict[str, str], recent: List[Dict[str, Any]], api_key: str) -> Optional[str]:
    """让 DeepSeek 写一篇关于该思维模型的深度文章。"""

    review_text = ""
    if recent:
        review_items = "\n".join(
            f"{i+1}. {r['name']}（{r.get('date', '')}）：{r.get('summary', '')[:100]}"
            for i, r in enumerate(recent[-3:])
        )
        review_text = f"""

温故知新（最近学过的模型）：
{review_items}

请在正文最后加一个【温故知新】小节，用 2-3 句话串联上述近期模型与本周模型之间的关联，帮助读者建立思维格栅。"""

    prompt = f"""你是查理·芒格式的思维导师。请为学习者深度拆解下面这个思维模型或认知偏误，帮助他们真正掌握并应用于生活和商业。

## 本周模型：{model['name']}
类别：{model['category']}
关键词：{model['keywords']}
{review_text}

请按以下格式输出（教学风格，每部分 4-6 句，纯文本，不用 Markdown）：

【是什么】
用一句话定义这个模型。然后解释它的核心含义。举一个直观的例子说明。

【为什么重要】
这个模型/偏误为什么是人类认知中的关键问题？忽略它会带来什么后果？在什么场景下最容易犯错？

【经典案例】
举 2-3 个现实中的经典案例（商业、历史、投资、科技都可以）。每个案例简要说明发生了什么，以及这个模型如何解释了现象。

【如何应用】
给出 3 条具体的实践建议。下次遇到什么情况时应该想起这个模型？有什么检查清单可以帮助应用？

【关联模型】
这个模型与另外哪 2 个思维模型有联系？（从以下列表选：{', '.join(m['name'] for m in MENTAL_MODELS[:60])} 等）。简单说明它们之间的联系。

{ '【温故知新】\n用 2-3 句话把本周模型与最近学过的模型串联起来，说明它们如何共同构建你的思维格栅。' if review_text else '' }

注意：通俗但不失深度，用故事和类比让读者过目不忘。每部分之间空一行。"""

    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "你是查理·芒格式的思维导师。请用中文深入浅出地拆解思维模型，用案例和故事让学习者真正掌握。不要用Markdown，纯文本段落输出。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 1800,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("DeepSeek 失败: %s", exc)
        return None


# ─── HTML ────────────────────────────────────────────────────────────────────

def build_html(model: Dict[str, str], content: str, history: Dict[str, Any], date_str: str) -> str:
    cat_emoji = {"认知偏误": "⚠️", "思维模型": "🧠", "系统与策略": "🔗", "决策与概率": "🎲", "经济与商业": "📊"}
    cat_color = {"认知偏误": "#dc2626", "思维模型": "#7c3aed", "系统与策略": "#0891b2", "决策与概率": "#f59e0b", "经济与商业": "#16a34a"}
    emoji = cat_emoji.get(model["category"], "💡")
    color = cat_color.get(model["category"], "#6b7280")

    week = history.get("week", 1)

    # 解析内容段
    sections: Dict[str, str] = {}
    section_keys = ["是什么", "为什么重要", "经典案例", "如何应用", "关联模型", "温故知新"]
    for key in section_keys:
        marker = f"【{key}】"
        if marker in content:
            parts = content.split(marker, 1)
            if len(parts) > 1:
                sections[key] = parts[1].split("【")[0].strip()

    sec_config = [
        ("是什么", "#dc2626", "1"),
        ("为什么重要", "#f59e0b", "2"),
        ("经典案例", "#2563eb", "3"),
        ("如何应用", "#16a34a", "4"),
        ("关联模型", "#7c3aed", "5"),
        ("温故知新", "#ec4899", "6"),
    ]
    body = ""
    for key, sc, num in sec_config:
        text = sections.get(key, "")
        if text:
            body += f"""
    <div style="margin-top:16px;background-color:#f8fafc;border-left:3px solid {sc};border-radius:0 8px 8px 0;padding:14px 18px;">
    <span style="font-size:16px;font-weight:800;color:{sc};">{num}. {key}</span>
    <div style="font-size:16px;color:#374151;line-height:1.9;margin-top:8px;">{text}</div>
    </div>"""

    # 进度条
    total_models = len(MENTAL_MODELS)
    covered_count = len(history.get("covered", []))
    progress_pct = round(covered_count / total_models * 100)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>思维格栅日报</title>
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei','Helvetica Neue',sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:20px 0;">
<tr><td align="center">
<table width="920" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;max-width:920px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">

<tr>
<td style="background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);padding:40px 36px;text-align:center;">
<div style="font-size:14px;letter-spacing:3px;color:rgba(255,255,255,0.7);margin-bottom:8px;">第 {week} 期 · {date_str}</div>
<h1 style="margin:0;font-size:30px;font-weight:800;color:#ffffff;">🧠 思维格栅日报</h1>
<div style="margin-top:10px;font-size:15px;color:rgba(255,255,255,0.65);">每天拆解一个经典思维模型 · 构建你的多元思维框架</div>
</td>
</tr>

<tr>
<td style="padding:28px 32px 8px;">
<div style="background-color:#fef3c7;border:1px solid #fcd34d;border-radius:10px;padding:16px 20px;">
<span style="font-size:13px;font-weight:700;color:{color};background-color:{color}15;padding:3px 10px;border-radius:6px;">{emoji} {model['category']}</span>
<span style="font-size:24px;font-weight:800;color:#111827;display:block;margin-top:10px;">{model['name']}</span>
<div style="font-size:14px;color:#6b7280;margin-top:6px;">{model['keywords']}</div>
<div style="margin-top:10px;background-color:#e5e7eb;border-radius:4px;height:6px;width:100%;">
<div style="background-color:{color};border-radius:4px;height:6px;width:{progress_pct}%;"></div>
</div>
<div style="font-size:11px;color:#9ca3af;margin-top:4px;">学习进度：{covered_count}/{total_models} 个模型（{progress_pct}%）</div>
</div>
</td>
</tr>

<tr><td style="padding:12px 32px 24px;">{body}</td></tr>

<tr>
<td style="background-color:#f8fafc;padding:24px 32px;text-align:center;border-top:1px solid #e5e7eb;">
<div style="font-size:13px;color:#9ca3af;line-height:1.8;">
思维格栅日报 &bull; 第 {week} 期 &bull; {date_str}<br>
每天 7:00 AM 自动推送 &bull; 内容由 DeepSeek 生成<br>
<span style="color:#d1d5db;">持续积累思维模型，构建认知护城河。</span>
</div>
</td>
</tr>

</table>
</td></tr>
</table>
</body>
</html>"""


# ─── 邮件 ────────────────────────────────────────────────────────────────────

def send_email(html: str, model_name: str, date_str: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"🧠 思维格栅日报：{model_name} — {date_str}", "utf-8")
    msg["From"] = f"Mental Models Weekly <{os.environ['SENDER_EMAIL']}>"
    msg["To"] = os.environ["RECIPIENT_EMAIL"]
    msg.attach(MIMEText(html, "html", "utf-8"))
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(os.environ["SENDER_EMAIL"], os.environ["SENDER_PASSWORD"])
        server.send_message(msg)
    logger.info("邮件发送成功！")


# ─── 入口 ─────────────────────────────────────────────────────────────────────

def main():
    try:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info("=== 思维格栅周报 %s ===", date_str)

        history = load_history()

        # 1. 选择本周模型
        model = pick_next_model(history)
        logger.info("本周模型: %s (%s)", model["name"], model["category"])

        # 2. 取最近学过的 3 个做复习
        recent = history.get("covered", [])[-3:]

        # 3. DeepSeek 生成深度文章
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            logger.error("未设置 DEEPSEEK_API_KEY")
            sys.exit(1)

        logger.info("DeepSeek: 生成深度拆解 …")
        content = generate_deep_dive(model, recent, api_key)
        if not content:
            logger.error("DeepSeek 生成失败")
            sys.exit(1)
        logger.info("DeepSeek: 完成 (%d 字符)", len(content))

        # 4. 保存历史
        summary = content.split("【为什么重要】")[0] if "【为什么重要】" in content else content[:150]
        summary = summary.replace("【是什么】", "").strip()[:200]
        history["covered"].append({
            "name": model["name"],
            "category": model["category"],
            "date": date_str,
            "summary": summary,
        })
        history["week"] = history.get("week", 0) + 1
        save_history(history)
        logger.info("历史已更新: %d/%d 个模型已覆盖", len(history["covered"]), len(MENTAL_MODELS))

        # 5. 生成 HTML
        html = build_html(model, content, history, date_str)
        logger.info("HTML: %.1f KB", len(html) / 1024)

        # 6. 发送邮件
        send_email(html, model["name"], date_str)
        logger.info("完成！")
    except Exception as exc:
        logger.error("致命: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
