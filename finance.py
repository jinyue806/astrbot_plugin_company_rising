from .achievements import unlock_achievements
from .constants import OFFICE_TYPES
from .utils import get_industry_by_name, get_office_rent, parse_time_to_month_idx
from .ceo import get_talent_effects


def compute_runway(state: dict) -> tuple[float, float, str]:
    cash = state["finance"]["cash"]
    monthly_burn = (
        state["finance"]["fixed_cost"]
        + get_office_rent(state)
        + state["staff"]["total_salary"]
    )
    if cash <= 0:
        return 0.0, round(monthly_burn, 2), "dead"
    if monthly_burn <= 0:
        return float("inf"), 0.0, "safe"
    runway = cash / monthly_burn
    if runway <= 1:
        level = "red"
    elif runway <= 3:
        level = "yellow"
    else:
        level = "safe"
    return round(runway, 1), round(monthly_burn, 2), level


def raise_funding(state: dict) -> dict:
    if state["ceo"]["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足，无法启动融资。"}
    if state["finance"]["reputation"] < 30:
        return {
            "ok": False,
            "msg": f"⚠️ 声誉 {state['finance']['reputation']} 低于 30，找不到领投方。先把产品做出来 / 多扛几次月报。",
        }

    current_idx = parse_time_to_month_idx(state["meta"]["time"])
    last_idx = state.get("meta", {}).get("_last_funding_idx")
    talent_effects = get_talent_effects(state)
    cooldown_months = max(1, 3 - talent_effects.get("cooldown_reduction", 0))
    if last_idx is not None and (current_idx - last_idx) < cooldown_months:
        remain = cooldown_months - (current_idx - last_idx)
        return {
            "ok": False,
            "msg": f"⚠️ 融资冷却期：上次融资距今 {current_idx - last_idx} 月，还需等 {remain} 月。",
        }

    cash = state["finance"]["cash"]
    rep = state["finance"]["reputation"]
    base = max(50.0, cash * 2 + rep * 3)
    ind = get_industry_by_name(state["meta"]["industry"])
    if ind:
        pe = (ind["pe_min"] + ind["pe_max"]) / 2 / 10
    else:
        pe = 1.5

    valuation_bonus = talent_effects.get("valuation_bonus", 0)
    valuation = round(base * pe * (1 + valuation_bonus), 1)
    dilution_reduction = talent_effects.get("dilution_reduction", 0)
    dilution = max(0.05, 0.15 - dilution_reduction)
    raise_amount = round(valuation * dilution, 1)

    state["ceo"]["ap"] -= 1
    state["finance"]["cash"] += raise_amount
    state.setdefault("meta", {})["funding_rounds"] = state["meta"].get("funding_rounds", 0) + 1
    state["meta"]["_last_funding_idx"] = current_idx

    new_achievements = unlock_achievements(state)

    return {
        "ok": True,
        "msg": "",
        "valuation": valuation,
        "raise_amount": raise_amount,
        "dilution": dilution,
        "rounds": state["meta"]["funding_rounds"],
        "achievements": new_achievements,
    }


def list_company(state: dict) -> dict:
    if state["ceo"]["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足，无法启动 IPO 流程。"}
    if state.get("meta", {}).get("ipo_status") == "listed":
        return {"ok": False, "msg": "🏆 公司已上市，不可重复 IPO。"}

    cash = state["finance"]["cash"]
    rep = state["finance"]["reputation"]

    if cash < 1000:
        return {
            "ok": False,
            "msg": f"⚠️ 上市门槛：现金需 ≥ 1000 万，当前 {cash} 万。继续做大业务 / 多融几轮。",
        }
    if rep < 200:
        return {
            "ok": False,
            "msg": f"⚠️ 上市门槛：声誉需 ≥ 200，当前 {rep}。多交付项目 / 扛过几次危机。",
        }

    completed_projects = sum(1 for p in state.get("projects", []) if p.get("status") == "completed")
    if completed_projects < 2:
        return {
            "ok": False,
            "msg": f"⚠️ 上市门槛：需完成 ≥ 2 个项目，当前 {completed_projects} 个。继续研发。",
        }

    total_staff = state["staff"]["tech"] + state["staff"]["design"] + state["staff"]["marketing"] + 1  # +CEO
    if total_staff < 3:
        return {
            "ok": False,
            "msg": f"⚠️ 上市门槛：团队需 ≥ 3 人（含 CEO），当前 {total_staff} 人。请 /招聘。",
        }

    pre_valuation = state["finance"].get("valuation", 5000)
    talent_effects = get_talent_effects(state)
    ipo_multiplier = talent_effects.get("ipo_valuation_multiplier", 1.0)
    ipo_valuation = round(pre_valuation * 10 * ipo_multiplier, 1)
    raise_amount = round(ipo_valuation * 0.25, 1)

    state["ceo"]["ap"] -= 1
    state["finance"]["cash"] += raise_amount
    state["finance"]["valuation"] = ipo_valuation
    state["finance"]["reputation"] = rep * 2
    state.setdefault("meta", {})["ipo_status"] = "listed"
    state["meta"]["ipo_time"] = state["meta"]["time"]
    state["meta"]["ipo_pre_valuation"] = pre_valuation

    new_achievements = unlock_achievements(state)

    return {
        "ok": True,
        "msg": "",
        "ipo_valuation": ipo_valuation,
        "raise_amount": raise_amount,
        "new_reputation": state["finance"]["reputation"],
        "achievements": new_achievements,
    }


def change_office(state: dict, new_key: str) -> dict:
    if new_key not in OFFICE_TYPES:
        return {"ok": False, "msg": f"⚠️ 办公室编号无效。可选: {', '.join(OFFICE_TYPES.keys())}"}
    current_key = state.get("meta", {}).get("office", "A")
    if new_key == current_key:
        cur = OFFICE_TYPES[current_key]
        return {"ok": False, "msg": f"⚠️ 你已经在 {cur['name']} 了。"}

    if state["ceo"]["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足，无法换办公室。"}

    new = OFFICE_TYPES[new_key]
    cur = OFFICE_TYPES[current_key]

    talent_effects = get_talent_effects(state)
    office_discount = talent_effects.get("office_upgrade_discount", 0)
    upgrade_cost = max(0, new["tier"] - cur["tier"]) * 0.4 * (1 - office_discount)
    upgrade_cost = round(upgrade_cost, 2)
    if state["finance"]["cash"] < upgrade_cost:
        return {"ok": False, "msg": f"⚠️ 装修/搬迁需要 {upgrade_cost} 万现金。"}

    state["ceo"]["ap"] -= 1
    state["finance"]["cash"] -= upgrade_cost
    state.setdefault("meta", {})["office"] = new_key
    if new["tier"] > cur["tier"]:
        state["finance"]["reputation"] += new["reputation_bonus"]

    new_achievements = unlock_achievements(state)

    return {
        "ok": True,
        "msg": "",
        "office_name": new["name"],
        "rent": new["rent"],
        "upgrade_cost": upgrade_cost,
        "reputation_bonus": new["reputation_bonus"] if new["tier"] > cur["tier"] else 0,
        "downgrade": new["tier"] < cur["tier"],
        "capacity_bonus": new["capacity_bonus"],
        "hire_bonus": new["hire_bonus"],
        "achievements": new_achievements,
    }
