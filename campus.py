"""校园筹备期：隐藏背景、校园事件、回家继承家产、催婚相亲。"""

import copy
import random

from .constants import INDUSTRIES

# ========= 隐藏背景 =========

BACKGROUNDS = {
    "普通": {"weight": 0.70, "desc": "普通家庭"},
    "中产": {"weight": 0.20, "desc": "中产家庭"},
    "富二代": {"weight": 0.10, "desc": "富二代"},
}


def roll_background() -> str:
    r = random.random()
    if r < 0.10:
        return "富二代"
    elif r < 0.30:
        return "中产"
    return "普通"


# ========= 开局选项 =========

MAJOR_OPTIONS = {
    "1": {"name": "计算机", "tech": 5, "marketing": -2, "management": 0},
    "2": {"name": "市场营销", "tech": -2, "marketing": 5, "management": 0},
    "3": {"name": "工商管理", "tech": 0, "marketing": 0, "management": 3},
}

FUNDING_OPTIONS = {
    "1": {"name": "兼职攒的", "cash": 3, "reputation": 5, "equity_loss": 0},
    "2": {"name": "家里给的", "cash": 8, "reputation": 0, "equity_loss": 0},
    "3": {"name": "学长投资", "cash": 12, "reputation": 0, "equity_loss": 0.05},
}

DIRECTION_OPTIONS = {
    "1": {"name": "用宿舍项目", "dev_cost_mult": 0.7},
    "2": {"name": "全新点子", "market_potential": 1.2},
    "3": {"name": "先接外包", "stable_income": True},
}

# ========= 晋升条件 =========

def check_promotion_eligibility(state: dict) -> dict:
    campus = state.get("campus", {})
    savings = campus.get("savings", 0)
    reputation = campus.get("reputation", 0)
    has_partner = campus.get("has_partner", False)
    has_investor = campus.get("has_investor", False)

    cond1 = savings >= 30 and reputation >= 20
    cond2 = savings >= 15 and has_partner
    cond3 = reputation >= 50 and has_investor
    can_promote = cond1 or cond2 or cond3

    missing = []
    if not cond1:
        if savings < 30:
            missing.append(f"积蓄 {savings:.0f}/30万")
        if reputation < 20:
            missing.append(f"声望 {reputation}/20")
    if not cond2:
        if savings < 15:
            missing.append(f"积蓄 {savings:.0f}/15万")
        if not has_partner:
            missing.append("需要合伙人")
    if not cond3:
        if reputation < 50:
            missing.append(f"声望 {reputation}/50")
        if not has_investor:
            missing.append("需要投资人")

    return {"ok": can_promote, "missing": missing}


# ========= 公司转换 =========

def campus_to_company(state: dict, company_name: str, industry: str) -> dict:
    campus = state.get("campus", {})
    campus_snapshot = copy.deepcopy(campus)
    major = campus.get("major", "1")
    industry_name = _normalize_industry(industry)

    tech_bonus = MAJOR_OPTIONS.get(major, {}).get("tech", 0)
    marketing_bonus = MAJOR_OPTIONS.get(major, {}).get("marketing", 0)
    mgmt_bonus = MAJOR_OPTIONS.get(major, {}).get("management", 0)

    campus_savings = campus.get("savings", 0)
    campus_rep = campus.get("reputation", 0)
    usable_savings = max(0, campus_savings)
    investor_cash = 10.0 if campus.get("has_investor") else 0.0
    equity_loss = campus.get("equity_loss", 0) + (0.10 if campus.get("has_investor") else 0)
    total_cash = usable_savings + investor_cash
    cash_sources = []
    if usable_savings > 0:
        cash_sources.append(f"积蓄 {usable_savings:.1f}万")
    if investor_cash > 0:
        cash_sources.append(f"投资人 {investor_cash:.1f}万")
    if not cash_sources:
        cash_sources.append("无额外资金")

    talent_points = 0
    if max(tech_bonus, marketing_bonus, mgmt_bonus) >= 5:
        talent_points = 1
    if campus.get("hackathon_win"):
        talent_points += 1

    if tech_bonus >= marketing_bonus and tech_bonus >= mgmt_bonus:
        trait = "技术领袖"
    elif marketing_bonus >= mgmt_bonus:
        trait = "商业奇才"
    else:
        trait = "管理铁腕"

    company_state = {
        "meta": {
            "company": company_name,
            "industry": industry_name,
            "time": "1年1月",
            "office": "A",
            "campus_origin": True,
            "background": campus.get("background", "普通"),
        },
        "finance": {
            "cash": round(total_cash, 1),
            "fixed_cost": 0.5,
            "valuation": round(total_cash, 1),
            "reputation": campus_rep,
        },
        "ceo": {
            "ap": 3,
            "max_ap": 3,
            "trait": trait,
            "xp": 0,
            "level": 1,
            "talent_points": talent_points,
            "unlocked_talents": [],
        },
        "staff": {"tech": 0, "design": 0, "marketing": 0, "total_salary": 0.0},
        "projects": [],
        "customers": {
            "count": 0, "arr_per_customer": 0.5,
            "churn_rate": 0.10, "growth_rate": 0.0, "history": [],
        },
        "log": [],
        "employees": [],
        "phase": "company",
        "campus": campus_snapshot,
    }

    state.clear()
    state.update(copy.deepcopy(company_state))
    state["company_state"] = copy.deepcopy(company_state)

    return {
        "ok": True,
        "cash": round(total_cash, 1),
        "cash_sources": " + ".join(cash_sources),
        "trait": trait,
        "talent_points": talent_points,
        "equity_loss": equity_loss,
    }


# ========= 校园操作 =========

def do_part_time(state: dict, job_type: str) -> dict:
    campus = state.get("campus", {})
    earnings = {"tutor": 0.3, "freelance": 0.8, "intern": 1.5}
    rep_gain = {"tutor": 0, "freelance": 3, "intern": 5}
    earn = earnings.get(job_type, 0.5)
    rep = rep_gain.get(job_type, 0)
    campus["savings"] = campus.get("savings", 0) + earn
    campus["reputation"] = campus.get("reputation", 0) + rep
    return {"ok": True, "earnings": earn, "reputation": rep}


def do_product(state: dict, product_name: str) -> dict:
    campus = state.get("campus", {})
    tech = campus.get("tech_skill", 30)
    success_rate = min(0.9, 0.3 + tech / 100)
    if random.random() < success_rate:
        campus["reputation"] = campus.get("reputation", 0) + 10
        campus["products"] = campus.get("products", []) + [product_name]
        return {"ok": True, "success": True, "reputation": 10}
    else:
        campus["savings"] = campus.get("savings", 0) - 1
        return {"ok": True, "success": False, "loss": 1}


def do_competition(state: dict) -> dict:
    campus = state.get("campus", {})
    tech = campus.get("tech_skill", 30)
    win_rate = min(0.8, 0.2 + tech / 150)
    if random.random() < win_rate:
        campus["savings"] = campus.get("savings", 0) + 5
        campus["reputation"] = campus.get("reputation", 0) + 15
        campus["hackathon_win"] = True
        return {"ok": True, "won": True, "prize": 5, "reputation": 15}
    else:
        campus["reputation"] = campus.get("reputation", 0) + 3
        return {"ok": True, "won": False, "reputation": 3}


def do_network(state: dict) -> dict:
    campus = state.get("campus", {})
    gain = random.randint(2, 6)
    campus["network"] = campus.get("network", 0) + gain
    if random.random() < 0.15 and not campus.get("has_partner"):
        campus["has_partner"] = True
        return {"ok": True, "gain": gain, "found_partner": True}
    return {"ok": True, "gain": gain, "found_partner": False}


def find_partner(state: dict) -> dict:
    campus = state.get("campus", {})
    network = campus.get("network", 0)
    if campus.get("has_partner"):
        return {"ok": False, "msg": "已有合伙人"}
    if network < 30:
        return {"ok": False, "msg": f"人脉不足 ({network}/30)"}
    campus["has_partner"] = True
    return {"ok": True, "msg": "找到合伙人!"}


# ========= 胜利/失败 =========

def check_win_lose(state: dict) -> dict | None:
    meta = state.get("meta", {})
    finance = state.get("finance", {})
    campus = state.get("campus", {})

    if meta.get("ipo_status") == "listed":
        return {"type": "win", "ending": "ipo"}
    if meta.get("funding_rounds", 0) >= 1:
        return {"type": "win", "ending": "funding"}
    if finance.get("cash", 0) < -10:
        return {"type": "lose", "ending": "bankruptcy"}

    if state.get("phase") == "campus":
        total_months = campus.get("months_played", 0)
        if total_months < 48:
            return None
        rep = campus.get("reputation", 0)
        if rep >= 50:
            return {"type": "win", "ending": "wall_street"}
        if rep >= 30:
            return {"type": "win", "ending": "vlog_star"}
        background = campus.get("background", meta.get("background", "普通"))
        endings = {
            "富二代": "inherit_fortune",
            "中产": "exam_grind",
            "普通": "real_unemployment",
        }
        return {"type": "lose", "ending": endings.get(background, "real_unemployment")}

    time_str = meta.get("time", "1年1月")
    try:
        year = int(time_str.split("年")[0])
        month = int(time_str.split("年")[1].split("月")[0])
        total_months = (year - 1) * 12 + month
    except (ValueError, IndexError):
        total_months = 0

    if total_months >= 48:
        rep = finance.get("reputation", 0)
        if rep >= 50:
            return {"type": "win", "ending": "wall_street"}
        if rep >= 30:
            return {"type": "win", "ending": "vlog_star"}
        background = meta.get("background", campus.get("background", "普通"))
        endings = {
            "富二代": "inherit_fortune",
            "中产": "exam_grind",
            "普通": "real_unemployment",
        }
        return {"type": "lose", "ending": endings.get(background, "real_unemployment")}

    return None


def _normalize_industry(industry: str) -> str:
    if industry in INDUSTRIES:
        return INDUSTRIES[industry]["name"]
    for v in INDUSTRIES.values():
        name = v.get("name", "")
        if industry == name or industry in name:
            return name
    return industry


# ========= 格式化 =========

def format_campus_status(state: dict) -> str:
    campus = state.get("campus", {})

    major_name = MAJOR_OPTIONS.get(campus.get("major", "1"), {}).get("name", "?")
    savings = campus.get("savings", 0)
    reputation = campus.get("reputation", 0)
    network = campus.get("network", 0)
    total_months = campus.get("months_played", 0)
    year = total_months // 12 + 1
    month = total_months % 12 + 1
    time_str = f"{year}年{month}月"
    months_left = max(0, 48 - total_months)

    lines = [
        "🎓 【校园筹备期】还没注册公司",
        f"⏰ {time_str} | 🎓 毕业倒计时: {months_left} 个月",
        f"💰 积蓄: {savings:.1f}万 | ⭐ 声望: {reputation} | 🤝 人脉: {network}",
        (
            f"📚 专业: {major_name} | 技术 {campus.get('tech_skill', 0)}"
            f" | 市场 {campus.get('marketing_skill', 0)}"
            f" | 管理 {campus.get('management_skill', 0)}"
        ),
    ]

    if campus.get("has_partner"):
        lines.append("👥 合伙人: 有")
    if campus.get("has_investor"):
        lines.append("💼 投资人: 有")
    if not campus.get("background_revealed"):
        lines.append("❓ 家庭背景: ???（失败时揭晓）")

    products = campus.get("products", [])
    if products:
        lines.append(f"📦 产品: {', '.join(products[-3:])}")

    return "\n".join(lines)


def format_promotion_check(state: dict) -> str:
    result = check_promotion_eligibility(state)
    if result["ok"]:
        return "✅ 条件成熟！使用 /创业 <公司名> <行业> 注册公司，进入公司期"
    lines = ["❌ 晋升条件不足："]
    for m in result["missing"]:
        lines.append(f"  · {m}")
    lines.append("\n💡 继续 /打工 /做产品 /比赛 /社交 积累资源")
    return "\n".join(lines)
