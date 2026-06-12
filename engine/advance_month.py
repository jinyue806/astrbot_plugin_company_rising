import random

from ..company.achievements import unlock_achievements
from ..company.customers import update_customers
from ..utils.endings import GAME_OVER_ENDINGS
from .projects import calc_capacity
from ..utils.utils import get_office_rent, increment_month
from ..company.ceo import gain_xp, get_talent_effects
from ..company.employee import decay_loyalty, grow_skills, check_auto_resignations


def advance_month(state: dict) -> dict:
    meta = state.setdefault("meta", {})
    # 应用天赋效果 (成本减免等)
    talent_effects = get_talent_effects(state)
    fixed_cost_reduction = talent_effects.get("fixed_cost_reduction", 0)
    rent_reduction = talent_effects.get("rent_reduction", 0)
    salary_pressure_reduction = talent_effects.get("salary_pressure_reduction", 0)

    state["meta"]["time"] = increment_month(state)
    state["finance"]["cash"] -= state["finance"]["fixed_cost"] * (1 - fixed_cost_reduction)
    state["finance"]["cash"] -= get_office_rent(state) * (1 - rent_reduction)
    state["finance"]["cash"] -= state["staff"]["total_salary"] * (1 - salary_pressure_reduction)

    # === Task 2: 规模管理成本 ===
    total_emp = len([e for e in state.get("employees", []) if e.get("status") in ("active", None)])
    overhead = 0.0
    if total_emp > 3:
        overhead = (total_emp - 3) * 0.5  # 超3人每人+0.5万/月
        state["finance"]["cash"] -= overhead

    cap = calc_capacity(state)
    total_cap = cap["tech"] + cap["design"] + cap["marketing"]
    project_revenue = 0
    completed_names = []
    # Task 1 天赋: 研发速度、完成 rep、突破
    dev_speed_bonus = talent_effects.get("dev_speed_bonus", 0)
    completion_rep_bonus = talent_effects.get("completion_rep_bonus", 0)
    breakthrough_chance = talent_effects.get("breakthrough_chance", 0)
    # Task 2: 完成项目数用于收入递减
    completed_total = sum(1 for p in state["projects"] if p.get("status") == "completed")

    for p in state["projects"]:
        if p.get("status") in ("completed",):
            continue
        base_gain = min(25, max(8, total_cap // 2))
        progress_gain = int(base_gain * (1 + dev_speed_bonus))
        # Task 1: 突破概率——30% 直接跳完成
        if breakthrough_chance > 0 and random.random() < breakthrough_chance:
            progress_gain = 100 - p["progress"]
        p["progress"] = min(100, p["progress"] + progress_gain)
        if p["progress"] >= 100:
            p["status"] = "completed"
            # Task 2: 收入边际递减
            income = p.get("revenue", 30)
            completed_total += 1
            diminish = max(0.3, 1.0 - completed_total * 0.08)
            income = round(income * diminish, 1)
            project_revenue += income
            # Task 1: 完成额外 rep + Task 2: rep 基础值
            rep_gain = 20 + completion_rep_bonus
            state["finance"]["reputation"] += rep_gain
            completed_names.append(p.get("name", "项目"))
    if project_revenue > 0:
        state["finance"]["cash"] += project_revenue

    # === Task 2: 声誉软上限 + 自然衰减 ===
    rep = state["finance"]["reputation"]
    if rep > 50:
        decay = int((rep - 50) * 0.05)  # 超50的部分每月衰减5%
        state["finance"]["reputation"] -= decay

    # 项目完成 XP
    if completed_names:
        for _ in completed_names:
            gain_xp(state, "project_complete")

    state.setdefault("meta", {})["last_milestones"] = completed_names

    # Task 1: 天赋 ap_bonus (组织进化 AP+1)
    ap_bonus = talent_effects.get("ap_bonus", 0)
    state["ceo"]["ap"] = state["ceo"]["max_ap"] + ap_bonus

    customer_update = update_customers(state)

    # 员工深度系统: 忠诚度衰减 + 技能成长 + 自动离职
    loyalty_events = decay_loyalty(state)
    if meta.get("_employee_skills_enabled", True):
        grown = grow_skills(state)
    else:
        grown = []
    auto_resigns = check_auto_resignations(state)

    new_achievements = unlock_achievements(state)

    # 成就解锁 XP
    if new_achievements:
        for _ in new_achievements:
            gain_xp(state, "achievement_unlock")

    # 月度存活 XP
    gain_xp(state, "monthly_survival")

    # 天赋: 危机公关自动化解
    auto_resolve = talent_effects.get("auto_resolve", 0)
    crisis_reduction = talent_effects.get("crisis_reduction", 0)
    rep_floor = talent_effects.get("rep_floor")

    # === 预留集成点: 随机事件 / 竞争对手 / 员工活动 / KPI ===
    random_events_result = []
    competitor_events = []
    employee_activities = []
    kpi_results = []
    # 随机事件系统 (Task 3)
    if meta.get("_event_frequency", "标准") != "关闭":
        try:
            from .random_events import roll_monthly_event
            random_events_result = roll_monthly_event(state)
        except ImportError:
            pass
    # 竞争对手系统 (Task 4)
    if meta.get("_competitor_enabled", True):
        try:
            from .competitors import advance_competitors
            competitor_events = advance_competitors(state)
        except ImportError:
            pass
    # 员工管理系统 (Task 5)
    try:
        from ..company.employee_management import roll_employee_activities, evaluate_kpis, apply_facilities
        employee_activities = roll_employee_activities(state)
        if meta.get("_kpi_enabled", True):
            kpi_results = evaluate_kpis(state)
        apply_facilities(state)
    except ImportError:
        pass

    state.setdefault("log", []).append({
        "time": state["meta"]["time"],
        "event": state.get("_last_event", "")[:100],
        "milestones": completed_names,
        "revenue": project_revenue,
        "achievements": new_achievements,
        "customer_count": customer_update.get("count", 0),
        "loyalty_events": len(loyalty_events),
        "auto_resigns": len(auto_resigns),
        "skills_grown": len(grown),
        "random_events": random_events_result,
        "competitor_events": competitor_events,
        "employee_activities": employee_activities,
        "kpi_results": kpi_results,
    })
    if len(state["log"]) > 24:
        state["log"] = state["log"][-24:]

    # 声誉下限保护
    if rep_floor is not None and state["finance"]["reputation"] < rep_floor:
        state["finance"]["reputation"] = rep_floor

    if state["finance"]["cash"] < 0:
        # 危机公关: 有概率自动化解破产
        if auto_resolve > 0:
            if random.random() < 0.5:  # 50% 几率触发自动化解
                state["finance"]["cash"] = 0
                return {
                    "ok": True,
                    "msg": "🛡️ 【危机公关】CEO 紧急斡旋，债权人同意延期还款，公司苟活下来了！",
                    "game_over": False,
                    "revenue": project_revenue,
                    "achievements": new_achievements,
                    "loyalty_events": loyalty_events,
                    "auto_resigns": auto_resigns,
                    "skills_grown": grown,
                    "random_events": random_events_result,
                    "competitor_events": competitor_events,
                    "employee_activities": employee_activities,
                    "kpi_results": kpi_results,
                }
        for trigger, msg in GAME_OVER_ENDINGS:
            if trigger(state):
                end_msg = msg
                break
        return {
            "ok": False,
            "msg": end_msg,
            "game_over": True,
            "revenue": project_revenue,
            "achievements": new_achievements,
            "loyalty_events": loyalty_events,
            "auto_resigns": auto_resigns,
            "skills_grown": grown,
            "random_events": random_events_result,
            "competitor_events": competitor_events,
            "employee_activities": employee_activities,
            "kpi_results": kpi_results,
        }
    return {
        "ok": True,
        "msg": "",
        "game_over": False,
        "revenue": project_revenue,
        "achievements": new_achievements,
        "loyalty_events": loyalty_events,
        "auto_resigns": auto_resigns,
        "skills_grown": grown,
        "random_events": random_events_result,
        "competitor_events": competitor_events,
        "employee_activities": employee_activities,
        "kpi_results": kpi_results,
    }
