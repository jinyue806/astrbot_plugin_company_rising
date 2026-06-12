import re


def should_make_headline(state: dict) -> bool:
    meta = state.get("meta", {})
    if meta.get("last_milestones"):
        return True
    if meta.get("ipo_status") == "listed":
        return True
    return False


def format_headline(state: dict, raw_text: str, milestone: str = "") -> str:
    company = state.get("meta", {}).get("company", "公司")
    known_names = set()
    for p in state.get("projects", []):
        known_names.add(p.get("name", ""))
    for e in state.get("employees", []):
        known_names.add(e.get("name", ""))

    candidates = set(re.findall(r"[\u4e00-\u9fff]{2,4}", raw_text))
    exclude = {"公司", "发布", "产品", "创业", "团队", "今天", "正式", "完成", "获得", "客户", "用户", "行业", "市场", "上线", "融资", "估值", "投资", "媒体", "新闻", "采访", "报道"}
    hallucinated = candidates - known_names - exclude
    hallucinated = {h for h in hallucinated if h != company and h != milestone}

    text = raw_text.strip()
    if not text.startswith("📰"):
        text = "📰 " + text
    if len(text) > 200:
        text = text[:197] + "..."

    if hallucinated:
        text += f"\n  ⚠️ 校对: {','.join(list(hallucinated)[:3])} 似乎在档案里没找到, 可能是 LLM 幻觉"
    return text


EASTER_EGGS = [
    {
        "id": "media_interview",
        "check": lambda s: s["finance"]["reputation"] >= 200
                          and len(s.get("employees", [])) >= 3,
        "theme": "媒体关注",
        "seed": "36Kr 记者约深度访谈, 标题党『XX 创始人: 我们要重新定义行业』",
        "title": "📰 媒体头条",
        "desc": "声誉 200+ + 3+ 员工: 36Kr/虎嗅主动来约稿, 涨粉 +500",
    },
    {
        "id": "industry_award",
        "check": lambda s: sum(1 for p in s.get("projects", [])
                              if p.get("status") == "completed") >= 3,
        "theme": "行业趋势",
        "seed": "公司被提名『年度新锐』, 颁奖典礼在月底, 需要预支 0.5 万置装费",
        "title": "🏆 行业大奖",
        "desc": "完成 3+ 项目: 行业协会颁奖提名, 声誉 +30, 但要花 0.5 万请客",
    },
    {
        "id": "first_ipo_rumor",
        "check": lambda s: s["finance"]["cash"] >= 500
                          and s["finance"]["reputation"] >= 150
                          and not s.get("meta", {}).get("ipo_status"),
        "theme": "融资环境",
        "seed": "路透社小道消息: 公司在 IPO 辅导期, 估值传闻 5 亿",
        "title": "📈 IPO 传闻",
        "desc": "500+ 现金 + 150+ 声誉: 路透社曝 IPO 辅导, 估值谣言扩散",
    },
    {
        "id": "big_co_poach",
        "check": lambda s: s.get("meta", {}).get("office", "A") == "A"
                          and s["finance"]["cash"] >= 100
                          and s["finance"]["reputation"] >= 80,
        "theme": "人才流动",
        "seed": "鹅厂 P9 慕名而来, 想用 2x 薪资挖走你的核心员工",
        "title": "🏢 大厂挖角",
        "desc": "A 办公室 + 100+ 现金 + 80+ 声誉: 大厂来高薪挖人, 留人成本 +5% 月薪",
    },
    {
        "id": "investor_rescue",
        "check": lambda s: s["finance"]["cash"] < 0 and s["finance"]["reputation"] >= 50,
        "theme": "融资环境",
        "seed": "原股东紧急注资, 带着对赌协议重新救场",
        "title": "🎯 投资人救场",
        "desc": "现金流断裂 + 声誉 50+: 老股东主动上门, 愿意 bridging loan",
    },
]


def detect_easter_egg(state: dict) -> dict | None:
    for egg in EASTER_EGGS:
        try:
            if egg["check"](state):
                return egg
        except Exception:
            continue
    return None
