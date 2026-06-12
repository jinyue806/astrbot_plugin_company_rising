"""员工管理系统：KPI 考核、月度活动、加薪、公司设施。"""

import random

# ========================================================================
# 5.1 KPI 系统
# ========================================================================

KPI_METRICS = {
    "progress": {"name": "项目进度", "field": "projects", "desc": "项目进度提升 X%"},
    "loyalty": {"name": "忠诚度", "field": "loyalty", "desc": "忠诚度维持 X 以上"},
    "skill_avg": {"name": "技能均值", "field": "skills", "desc": "技能平均等级达 X"},
}

KPI_REWARDS = {
    "raise_": "加薪",
    "bonus_": "奖金",
}

KPI_PENALTIES = {
    "warning": "口头警告",
    "salary_cut_": "降薪",
}


def set_kpi(state: dict, emp_name: str, metric: str, target: float,
            deadline: str = "", reward: str = "raise_0.5",
            penalty: str = "warning") -> dict:
    """给员工设定 KPI。"""
    emp = _find_employee(state, emp_name)
    if not emp:
        return {"ok": False, "msg": f"⚠️ 没找到员工「{emp_name}」。"}
    if metric not in KPI_METRICS:
        return {"ok": False, "msg": f"⚠️ 指标无效。可选: {', '.join(KPI_METRICS.keys())}"}

    if not deadline:
        deadline = _next_quarter_deadline(state)

    emp["kpi"] = {
        "metric": metric,
        "target": target,
        "deadline": deadline,
        "reward": reward,
        "penalty": penalty,
        "set_time": state.get("meta", {}).get("time", ""),
    }
    return {"ok": True, "msg": f"✅ 已给 {emp_name} 设定 KPI: {KPI_METRICS[metric]['name']} ≥ {target}"}


def cancel_kpi(state: dict, emp_name: str) -> dict:
    """取消员工 KPI。"""
    emp = _find_employee(state, emp_name)
    if not emp:
        return {"ok": False, "msg": f"⚠️ 没找到员工「{emp_name}」。"}
    if not emp.get("kpi"):
        return {"ok": False, "msg": f"⚠️ {emp_name} 当前没有 KPI。"}
    emp.pop("kpi", None)
    return {"ok": True, "msg": f"✅ 已取消 {emp_name} 的 KPI。"}


def evaluate_kpis(state: dict) -> list[dict]:
    """月度 KPI 考核，返回考核结果列表。"""
    results = []
    current_time = state.get("meta", {}).get("time", "")

    for emp in state.get("employees", []):
        if emp.get("status") not in ("active", None):
            continue
        kpi = emp.get("kpi")
        if not kpi:
            continue

        metric = kpi["metric"]
        target = kpi["target"]
        achieved = False

        if metric == "progress":
            # 检查项目进度
            for p in state.get("projects", []):
                if p.get("status") == "研发中" and p.get("progress", 0) >= target:
                    achieved = True
                    break
        elif metric == "loyalty":
            achieved = emp.get("loyalty", 70) >= target
        elif metric == "skill_avg":
            skills = emp.get("skills", {})
            avg = sum(skills.values()) / max(len(skills), 1) if skills else 0
            achieved = avg >= target

        # 检查是否过期
        deadline_passed = _is_deadline_passed(current_time, kpi.get("deadline", ""))

        if achieved:
            _apply_kpi_reward(state, emp, kpi)
            results.append({
                "emp": emp.get("name", "?"),
                "metric": metric,
                "status": "达标",
                "reward": kpi.get("reward", ""),
            })
            emp.pop("kpi", None)
        elif deadline_passed:
            _apply_kpi_penalty(state, emp, kpi)
            emp["loyalty"] = max(0, emp.get("loyalty", 70) - 10)
            results.append({
                "emp": emp.get("name", "?"),
                "metric": metric,
                "status": "未达标(已过期)",
                "penalty": kpi.get("penalty", ""),
            })
            emp.pop("kpi", None)

    return results


def _apply_kpi_reward(state: dict, emp: dict, kpi: dict) -> None:
    """应用 KPI 奖励。"""
    reward = kpi.get("reward", "raise_0.5")
    if reward.startswith("raise_"):
        try:
            amount = float(reward.split("_")[1])
        except (ValueError, IndexError):
            amount = 0.5
        emp["salary"] = round(emp.get("salary", 0) + amount, 2)
    elif reward.startswith("bonus_"):
        try:
            amount = float(reward.split("_")[1])
        except (ValueError, IndexError):
            amount = 1.0
        state["finance"]["cash"] -= amount
        # 奖金不加薪资，一次性


def _apply_kpi_penalty(state: dict, emp: dict, kpi: dict) -> None:
    """应用 KPI 惩罚。"""
    penalty = kpi.get("penalty", "warning")
    if penalty.startswith("salary_cut_"):
        try:
            amount = float(penalty.split("_")[1])
        except (ValueError, IndexError):
            amount = 0.3
        emp["salary"] = round(max(0.5, emp.get("salary", 0) - amount), 2)
    # warning: 只叙事，无数值效果


# ========================================================================
# 5.3 员工月度活动（打工人整活事件表）
# ========================================================================

# 正经工作类 (30%)
SERIOUS_ACTIVITIES = [
    {"id": "act01", "name": "主动加班", "effects": {"progress_delta": +5, "loyalty_delta": -3},
     "desc": "{name} 主动加班赶进度"},
    {"id": "act02", "name": "内部分享", "effects": {"loyalty_delta": +2, "all_loyalty": True},
     "desc": "{name} 做了一场技术分享，全员受益"},
    {"id": "act03", "name": "提案建议", "effects": {},
     "desc": "{name} 提出了一个创新方案"},
    {"id": "act04", "name": "客户好评", "effects": {"reputation_delta": +3, "loyalty_delta": +5},
     "desc": "{name} 获得客户好评"},
]

# 摸鱼整活类 (40%)
FUN_ACTIVITIES = [
    {"id": "act05", "name": "💩 带薪拉屎", "effects": {"progress_delta": -2, "loyalty_delta": +8, "cash_delta": -0.05},
     "desc": "{name} 带薪拉屎，厕所办公效率拉胯但心情大好"},
    {"id": "act06", "name": "🎮 上班打游戏", "effects": {"progress_delta": -3, "loyalty_delta": +5},
     "desc": "{name} 上班偷偷打游戏被发现了"},
    {"id": "act07", "name": "📦 摸鱼网购", "effects": {"loyalty_delta": +3, "cash_delta": -0.02},
     "desc": "{name} 上班摸鱼网购，拿公司快递"},
    {"id": "act08", "name": "🍜 中午吃火锅", "effects": {"loyalty_delta": +6, "progress_delta": -2, "all_loyalty": True},
     "desc": "{name} 请全员中午吃火锅，下午全员犯困"},
    {"id": "act09", "name": "📱 上班刷抖音", "effects": {"progress_delta": -2, "loyalty_delta": +4},
     "desc": "{name} 上班刷抖音停不下来"},
    {"id": "act10", "name": "🧑‍💻 偷学竞对技术", "effects": {"progress_delta": +3, "loyalty_delta": -5},
     "desc": "{name} 偷学竞对技术，有法律风险"},
    {"id": "act11", "name": "🎂 办公室过生日", "effects": {"cash_delta": -0.3, "loyalty_delta": +5, "all_loyalty": True},
     "desc": "{name} 在办公室过生日，全员吃蛋糕"},
    {"id": "act12", "name": "🍺 团建喝醉", "effects": {"cash_delta": -0.5, "loyalty_delta": +8, "progress_delta": -3, "all_loyalty": True},
     "desc": "{name} 组织团建喝酒，第二天全员宿醉"},
    {"id": "act13", "name": "💤 午睡睡过头", "effects": {"progress_delta": -4, "loyalty_delta": +6},
     "desc": "{name} 午睡睡过头，醒来发现项目完成了（做梦）"},
]

# 人际冲突类 (20%)
CONFLICT_ACTIVITIES = [
    {"id": "act14", "name": "同事冲突", "effects": {"loyalty_delta": -5},
     "desc": "{name} 和同事发生激烈争吵"},
    {"id": "act15", "name": "办公室八卦", "effects": {},
     "desc": "{name} 在茶水间被八卦缠住了"},
    {"id": "act16", "name": "抢会议室", "effects": {"progress_delta": -1},
     "desc": "{name} 为了抢会议室和其他部门打起来了"},
    {"id": "act17", "name": "外卖被偷", "effects": {"loyalty_delta": -3},
     "desc": "{name} 的外卖被偷了！谁偷了我的黄焖鸡！"},
]

# 特殊整活类 (10%)
SPECIAL_ACTIVITIES = [
    {"id": "act18", "name": "🏆 员工获行业大奖", "effects": {"reputation_delta": +10, "loyalty_delta": +15, "salary_delta": +0.3},
     "desc": "{name} 获得行业大奖，公司知名度提升"},
    {"id": "act19", "name": "🎤 员工参加脱口秀", "effects": {"reputation_delta": +5, "loyalty_delta": +10},
     "desc": "{name} 去参加脱口秀节目吐槽公司"},
    {"id": "act20", "name": "💻 员工黑了竞品网站", "effects": {"progress_delta": +5},
     "desc": "{name} 黑了竞品网站，律师函在路上了"},
    {"id": "act21", "name": "🐱 员工带宠物上班", "effects": {"loyalty_delta": +8, "progress_delta": -5, "all_loyalty": True},
     "desc": "{name} 带猫上班，猫坐在键盘上"},
    {"id": "act22", "name": "👔 穿拖鞋上班", "effects": {"loyalty_delta": +5},
     "desc": "{name} 穿拖鞋上班，引发办公室文化讨论"},
]

ACTIVITY_POOLS = [
    (SERIOUS_ACTIVITIES, 0.30),
    (FUN_ACTIVITIES, 0.40),
    (CONFLICT_ACTIVITIES, 0.20),
    (SPECIAL_ACTIVITIES, 0.10),
]


def roll_employee_activities(state: dict) -> list[dict]:
    """员工月度活动掷骰，返回触发事件列表（最多 2 个）。"""
    kpi_enabled = state.get("meta", {}).get("_kpi_enabled", True)
    active_emps = [e for e in state.get("employees", []) if e.get("status") in ("active", None)]
    if not active_emps:
        return []

    results = []
    max_activities = 2

    for emp in active_emps:
        if len(results) >= max_activities:
            break
        if random.random() > 0.4:  # 40% 概率触发
            continue

        # 按权重选类别
        pool = _weighted_choice(ACTIVITY_POOLS)
        activity = random.choice(pool)
        _apply_activity(state, emp, activity)
        results.append({
            "emp": emp.get("name", "?"),
            "activity": activity["name"],
            "desc": activity["desc"].format(name=emp.get("name", "?")),
        })

    return results


def _apply_activity(state: dict, emp: dict, activity: dict) -> None:
    """应用员工活动效果。"""
    effects = activity.get("effects", {})
    all_loyalty = effects.get("all_loyalty", False)

    if "progress_delta" in effects:
        delta = effects["progress_delta"]
        for p in state.get("projects", []):
            if p.get("status") == "研发中":
                p["progress"] = max(0, min(100, p["progress"] + delta))
                break

    if "loyalty_delta" in effects:
        delta = effects["loyalty_delta"]
        if all_loyalty:
            for e in state.get("employees", []):
                if e.get("status") in ("active", None):
                    e["loyalty"] = max(0, min(100, e.get("loyalty", 70) + delta))
        else:
            emp["loyalty"] = max(0, min(100, emp.get("loyalty", 70) + delta))

    if "cash_delta" in effects:
        state.setdefault("finance", {})["cash"] = (
            state["finance"].get("cash", 0) + effects["cash_delta"]
        )

    if "reputation_delta" in effects:
        state.setdefault("finance", {})["reputation"] = max(
            0, state["finance"].get("reputation", 0) + effects["reputation_delta"]
        )

    if "salary_delta" in effects:
        emp["salary"] = round(emp.get("salary", 0) + effects["salary_delta"], 2)


# ========================================================================
# 5.5 加薪系统
# ========================================================================

def check_salary_demands(state: dict) -> list[dict]:
    """检查是否有员工主动要求加薪（忠诚度 < 40 时 20% 概率）。"""
    demands = []
    for emp in state.get("employees", []):
        if emp.get("status") not in ("active", None):
            continue
        loyalty = emp.get("loyalty", 70)
        if loyalty < 40 and random.random() < 0.2:
            demands.append({
                "emp": emp,
                "name": emp.get("name", "?"),
                "current_salary": emp.get("salary", 0),
                "demand": round(emp.get("salary", 0) * 0.3, 2),
            })
    return demands


def handle_salary_demand(state: dict, emp: dict, action: str) -> dict:
    """处理加薪要求。action: 'accept'/'refuse'/'negotiate'"""
    demand = round(emp.get("salary", 0) * 0.3, 2)

    if action == "accept":
        if state["finance"]["cash"] < demand:
            return {"ok": False, "msg": f"⚠️ 现金不足 {demand} 万。"}
        state["finance"]["cash"] -= demand
        emp["salary"] = round(emp.get("salary", 0) + demand, 2)
        emp["loyalty"] = min(100, emp.get("loyalty", 70) + 15)
        return {"ok": True, "msg": f"✅ 同意加薪 {demand} 万/月，{emp.get('name', '?')} 忠诚度 +15"}

    elif action == "refuse":
        emp["loyalty"] = max(0, emp.get("loyalty", 70) - 15)
        return {"ok": True, "msg": f"❌ 拒绝加薪，{emp.get('name', '?')} 忠诚度 -15"}

    elif action == "negotiate":
        half = round(demand / 2, 2)
        if random.random() < 0.5:
            if state["finance"]["cash"] < half:
                return {"ok": False, "msg": f"⚠️ 现金不足 {half} 万。"}
            state["finance"]["cash"] -= half
            emp["salary"] = round(emp.get("salary", 0) + half, 2)
            emp["loyalty"] = min(100, emp.get("loyalty", 70) + 5)
            return {"ok": True, "msg": f"✅ 谈判成功，折中加薪 {half} 万/月"}
        else:
            emp["loyalty"] = max(0, emp.get("loyalty", 70) - 10)
            return {"ok": True, "msg": f"❌ 谈判破裂，{emp.get('name', '?')} 不满，忠诚度 -10"}

    return {"ok": False, "msg": "⚠️ 未知操作。"}


def give_raise(state: dict, emp_name: str, amount: float) -> dict:
    """主动给员工加薪。"""
    emp = _find_employee(state, emp_name)
    if not emp:
        return {"ok": False, "msg": f"⚠️ 没找到员工「{emp_name}」。"}
    if amount <= 0:
        return {"ok": False, "msg": "⚠️ 加薪金额必须大于 0。"}
    if state["finance"]["cash"] < amount:
        return {"ok": False, "msg": f"⚠️ 现金不足 {amount} 万。"}

    state["finance"]["cash"] -= amount
    emp["salary"] = round(emp.get("salary", 0) + amount, 2)
    emp["loyalty"] = min(100, emp.get("loyalty", 70) + 10)
    return {"ok": True, "msg": f"✅ 已给 {emp_name} 加薪 {amount} 万/月，忠诚度 +10"}


# ========================================================================
# 5.8 公司设施系统
# ========================================================================

FACILITIES = {
    "食堂": {
        "cost": 5, "maintenance": 0.5, "office_tier": 1,
        "effect": {"loyalty_per_month": 3},
        "desc": "全员 loyalty +3/月，外卖被偷事件消失",
    },
    "健身房": {
        "cost": 3, "maintenance": 0.3, "office_tier": 1,
        "effect": {"loyalty_per_month": 2, "overwork_reduction": 0.5},
        "desc": "全员 loyalty +2/月，过劳事件概率 -50%",
    },
    "HR人事部": {
        "cost": 8, "maintenance": 1.0, "office_tier": 2,
        "effect": {"hire_cost_reduction": 0.5, "negotiation_bonus": 0.2},
        "desc": "招聘费用 -50%，离职谈判成功率 +20%",
    },
    "法务部": {
        "cost": 10, "maintenance": 1.5, "office_tier": 2,
        "effect": {"lawsuit_reduction": 0.7, "copy_counterattack": True},
        "desc": "知识产权诉讼伤害 -70%，对手抄袭反击伤害",
    },
    "秘书": {
        "cost": 4, "maintenance": 0.8, "office_tier": 1,
        "effect": {"monthly_reminders": True},
        "desc": "每月主动提醒: KPI 过期、低忠诚度、融资冷却、项目即将完成",
    },
    "茶水间": {
        "cost": 2, "maintenance": 0.2, "office_tier": 0,
        "effect": {"loyalty_per_month": 1},
        "desc": "全员 loyalty +1/月，八卦事件变正面",
    },
    "游戏室": {
        "cost": 3, "maintenance": 0.1, "office_tier": 1,
        "effect": {"game_room": True},
        "desc": "上班打游戏不再扣进度，整活转正面",
    },
}


def buy_facility(state: dict, facility_name: str) -> dict:
    """购买设施。"""
    if facility_name not in FACILITIES:
        return {"ok": False, "msg": f"⚠️ 设施不存在。可选: {', '.join(FACILITIES.keys())}"}

    if state.get("ceo", {}).get("ap", 0) < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足。"}

    facilities = state.setdefault("facilities", [])
    if facility_name in facilities:
        return {"ok": False, "msg": f"⚠️ 已建设 {facility_name}，不可重复购买。"}

    fac = FACILITIES[facility_name]
    cost = fac["cost"]
    required_tier = fac["office_tier"]

    # 检查办公室等级
    from ..utils.utils import get_office
    office = get_office(state)
    office_tier = office.get("tier", 0) if isinstance(office, dict) else 0
    # 用 OFFICE_TYPES 获取 tier
    from ..utils.constants import OFFICE_TYPES
    current_office_key = state.get("meta", {}).get("office", "A")
    current_tier = OFFICE_TYPES.get(current_office_key, {}).get("tier", 0)

    if current_tier < required_tier:
        tier_names = {0: "A 档", 1: "B 档", 2: "C 档", 3: "D 档"}
        need = tier_names.get(required_tier, f"Tier {required_tier}")
        return {"ok": False, "msg": f"⚠️ 需要 {need} 以上办公室才能建设 {facility_name}。"}

    if state.get("finance", {}).get("cash", 0) < cost:
        return {"ok": False, "msg": f"⚠️ 现金不足 {cost} 万。"}

    state["ceo"]["ap"] -= 1
    state["finance"]["cash"] -= cost
    facilities.append(facility_name)
    return {"ok": True, "msg": f"✅ 已建设 {facility_name}！{fac['desc']}"}


def list_facilities(state: dict) -> str:
    """列出已建设施。"""
    facilities = state.get("facilities", [])
    if not facilities:
        return "🏗️ 【公司设施】\n暂无设施。用 /设施 购买 <名称> 建设。"

    lines = ["🏗️ 【公司设施】\n"]
    total_maintenance = 0
    for name in facilities:
        fac = FACILITIES.get(name, {})
        maint = fac.get("maintenance", 0)
        total_maintenance += maint
        lines.append(f"  ✅ {name} | 月维护 {maint} 万 | {fac.get('desc', '')}")
    lines.append(f"\n  💰 月维护总计: {total_maintenance} 万")

    # 显示可购买设施
    available = [n for n in FACILITIES if n not in facilities]
    if available:
        lines.append(f"\n  🛒 可建设: {', '.join(available)}")
    return "\n".join(lines)


def apply_facilities(state: dict) -> None:
    """月度设施效果应用（在 advance_month 中调用）。"""
    facilities = state.get("facilities", [])
    if not facilities:
        return

    total_maintenance = 0
    total_loyalty_bonus = 0

    for name in facilities:
        fac = FACILITIES.get(name, {})
        total_maintenance += fac.get("maintenance", 0)
        effect = fac.get("effect", {})
        total_loyalty_bonus += effect.get("loyalty_per_month", 0)

    # 扣除维护费
    if total_maintenance > 0:
        state.setdefault("finance", {})["cash"] = (
            state["finance"].get("cash", 0) - total_maintenance
        )

    # 加忠诚
    if total_loyalty_bonus > 0:
        for emp in state.get("employees", []):
            if emp.get("status") in ("active", None):
                emp["loyalty"] = max(0, min(100, emp.get("loyalty", 70) + total_loyalty_bonus))


def get_facility_effects(state: dict) -> dict:
    """汇总所有已建设施的效果。"""
    effects = {}
    for name in state.get("facilities", []):
        fac = FACILITIES.get(name, {})
        for k, v in fac.get("effect", {}).items():
            effects[k] = effects.get(k, 0) + v if isinstance(v, (int, float)) else v
    return effects


# ========================================================================
# 工具函数
# ========================================================================

def _find_employee(state: dict, name: str) -> dict | None:
    """按名字查找在职员工。"""
    for emp in state.get("employees", []):
        if emp.get("name") == name and emp.get("status") in ("active", None):
            return emp
    return None


def _next_quarter_deadline(state: dict) -> str:
    """计算下一个季度截止日期。"""
    time_str = state.get("meta", {}).get("time", "1年1月")
    try:
        parts = time_str.replace("年", " ").replace("月", "").split()
        year = int(parts[0])
        month = int(parts[1])
        # 下个季度
        target_month = ((month - 1) // 3 + 1) * 3 + 3
        target_year = year
        if target_month > 12:
            target_month -= 12
            target_year += 1
        return f"{target_year}年{target_month}月"
    except (ValueError, IndexError):
        return "1年3月"


def _is_deadline_passed(current_time: str, deadline: str) -> bool:
    """判断当前时间是否超过截止日期。"""
    try:
        cur = _parse_time(current_time)
        dl = _parse_time(deadline)
        return cur > dl
    except (ValueError, IndexError):
        return False


def _parse_time(time_str: str) -> tuple[int, int]:
    """解析 'X年Y月' 为 (年, 月) 元组。"""
    parts = time_str.replace("年", " ").replace("月", "").split()
    return (int(parts[0]), int(parts[1]))


def _weighted_choice(pools: list[tuple[list, float]]) -> list:
    """按权重随机选一个池子。"""
    r = random.random()
    cum = 0.0
    for pool, weight in pools:
        cum += weight
        if r <= cum:
            return pool
    return pools[-1][0]
