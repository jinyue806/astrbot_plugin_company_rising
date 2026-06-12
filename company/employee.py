"""员工深度系统：忠诚度、技能、离职谈判、竞业协议。"""

import random
from .ceo import get_talent_effects

# ========= 忠诚度 =========

LOYALTY_BASE_DECAY = -3  # 月基础衰减
LOYALTY_RESIGN_THRESHOLD = 20  # 低于此值有离职风险
LOYALTY_AUTO_RESIGN = 10  # 低于此值有自动离职概率
LOYALTY_SKILL_GAIN_BONUS = 0.05  # 技能成长加忠诚

def decay_loyalty(state: dict) -> list[dict]:
    """月度忠诚度衰减，返回可能离职的员工列表。"""
    events = []
    talent_effects = get_talent_effects(state)
    retention_bonus = talent_effects.get("retention_bonus", 0)
    loyalty_floor = talent_effects.get("loyalty_floor", 0)
    for emp in state.get("employees", []):
        if emp.get("status") not in ("active", None):
            continue
        old_loyalty = emp.get("loyalty", 70)
        decay = LOYALTY_BASE_DECAY
        # 低薪惩罚
        if emp.get("salary", 0) < emp.get("market_salary", emp.get("salary", 0)) * 0.8:
            decay -= 5
        # 公司危机惩罚
        if state["finance"]["cash"] < 0:
            decay -= 10
        # 公司成功加成
        if state["finance"]["reputation"] > 100:
            decay += 2
        # 天赋: 人心所向 → 流失减半
        if retention_bonus > 0:
            decay = int(decay * (1 - retention_bonus))
        new_loyalty = max(loyalty_floor, min(100, old_loyalty + decay))
        emp["loyalty"] = new_loyalty
        if new_loyalty <= LOYALTY_AUTO_RESIGN and random.random() < 0.3:
            events.append({"emp": emp, "type": "auto_resign", "reason": "loyalty_too_low"})
        elif new_loyalty <= LOYALTY_RESIGN_THRESHOLD and random.random() < 0.1:
            events.append({"emp": emp, "type": "resign_warning", "reason": "low_loyalty"})
    return events


def adjust_loyalty(emp: dict, delta: int, reason: str = "") -> None:
    """调整员工忠诚度。"""
    old = emp.get("loyalty", 70)
    emp["loyalty"] = max(0, min(100, old + delta))


# ========= 技能系统 =========

SKILLS_BY_ROLE = {
    "tech": ["coding", "architecture", "testing", "devops", "security"],
    "design": ["ui", "ux", "research", "prototyping", "accessibility"],
    "marketing": ["sales", "seo", "brand", "content", "analytics"],
}

SKILL_NAMES_CN = {
    "coding": "编程", "architecture": "架构", "testing": "测试", "devops": "运维", "security": "安全",
    "ui": "界面", "ux": "体验", "research": "调研", "prototyping": "原型", "accessibility": "无障碍",
    "sales": "销售", "seo": "SEO", "brand": "品牌", "content": "内容", "analytics": "分析",
}

SKILL_GROWTH_RATE = 0.1  # 月基础技能成长


def init_skills(emp: dict) -> None:
    """为新员工初始化技能。"""
    role = emp.get("role", "tech")
    skills = {}
    for skill in SKILLS_BY_ROLE.get(role, []):
        base = random.randint(1, 3)
        skills[skill] = base
    emp["skills"] = skills


def grow_skills(state: dict) -> list[str]:
    """月度技能成长，返回成长了技能的员工名列表。"""
    grown = []
    for emp in state.get("employees", []):
        if emp.get("status") not in ("active", None):
            continue
        skills = emp.get("skills", {})
        for skill_name, level in skills.items():
            if level < 5:
                growth = SKILL_GROWTH_RATE + random.random() * 0.05
                skills[skill_name] = min(5, level + growth)
        if any(v > 3 for v in skills.values()):
            grown.append(emp.get("name", "???"))
    return grown


def get_total_skill(emp: dict) -> float:
    """员工总技能等级。"""
    return sum(emp.get("skills", {}).values())


def get_role_skill_avg(emp: dict) -> float:
    """员工主职技能平均等级。"""
    skills = emp.get("skills", {})
    return sum(skills.values()) / max(len(skills), 1)


# ========= 离职谈判 =========

def resignation_negotiate(state: dict, emp: dict, action: str) -> dict:
    """离职谈判。
    action: "raise" (加薪挽留) / "threat" (威胁) / "accept" (放行)
    """
    ceo = state["ceo"]
    if ceo["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足。"}

    if action == "raise":
        cost = round(emp.get("salary", 0) * 0.3, 2)
        if state["finance"]["cash"] < cost:
            return {"ok": False, "msg": f"⚠️ 现金不足 {cost} 万无法加薪。"}
        ceo["ap"] -= 1
        state["finance"]["cash"] -= cost
        emp["salary"] = round(emp.get("salary", 0) + cost, 2)
        adjust_loyalty(emp, 15, "加薪挽留")
        return {"ok": True, "msg": f"✅ 加薪 {cost} 万/月，忠诚度 +15"}

    elif action == "threat":
        ceo["ap"] -= 1
        if random.random() < 0.6:
            adjust_loyalty(emp, 20, "威胁生效")
            return {"ok": True, "msg": "✅ 威胁生效，忠诚度 +20，但其他员工可能不满。"}
        else:
            adjust_loyalty(emp, -30, "威胁失败")
            return {"ok": False, "msg": "❌ 威胁失败！忠诚度 -30，员工愤怒离场。", "resigned": True}

    elif action == "accept":
        return fire_employee(state, emp, "voluntary", f"同意 {emp['name']} 离职。")

    return {"ok": False, "msg": "⚠️ 未知操作。"}


# ========= 辞退 =========

def fire_employee(state: dict, emp: dict, reason: str = "fired",
                  detail: str = "", consume_ap: bool = True) -> dict:
    """辞退员工。
    返回：离职赔偿成本、忠诚度影响等。
    """
    ceo = state["ceo"]
    if consume_ap and ceo["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足。"}

    if consume_ap:
        ceo["ap"] -= 1
    salary = emp.get("salary", 0)
    severance = round(salary * 3, 2)  # N+1=3 个月赔偿
    if state["finance"]["cash"] < severance:
        severance = round(state["finance"]["cash"], 2)
        state["finance"]["cash"] = 0
    else:
        state["finance"]["cash"] -= severance

    if emp.get("status") in ("active", None):
        role = emp.get("role")
        if role in state.get("staff", {}):
            state["staff"][role] = max(0, state["staff"].get(role, 0) - 1)
        state["staff"]["total_salary"] = round(
            max(0, state["staff"].get("total_salary", 0) - salary), 2
        )

    emp["status"] = reason  # "fired" / "voluntary" / "auto_resign"
    emp["fire_time"] = state["meta"]["time"]
    emp["severance"] = severance

    # 团队士气影响
    morale_hit = -10 if reason == "fired" else -5
    for e in state.get("employees", []):
        if e.get("name") != emp["name"] and e.get("status") == "active":
            adjust_loyalty(e, morale_hit, "同事离职")

    return {
        "ok": True,
        "msg": f"✅ {emp['name']} 已离职。赔偿 {severance} 万。",
        "severance": severance,
        "reason": reason,
        "detail": detail,
    }


# ========= 自动离职检查 =========

def check_auto_resignations(state: dict) -> list[dict]:
    """检查并处理自动离职的员工。"""
    resignations = []
    for emp in state.get("employees", []):
        if emp.get("status") not in ("active", None):
            continue
        loyalty = emp.get("loyalty", 70)
        if loyalty <= LOYALTY_AUTO_RESIGN and random.random() < 0.3:
            result = fire_employee(
                state, emp, "auto_resign", "忠诚度过低，员工自动离职", consume_ap=False
            )
            resignations.append({"emp": emp, "result": result})
    return resignations


# ========= 格式化 =========

def format_employee(emp: dict, state: dict = None) -> str:
    """格式化单个员工信息。"""
    name = emp.get("name", "???")
    role = emp.get("role", "???")
    role_cn = {"tech": "研发", "design": "设计", "marketing": "营销"}.get(role, role)
    ability = emp.get("ability", 60)
    salary = emp.get("salary", 0)
    loyalty = emp.get("loyalty", 70)
    status = emp.get("status", "active")
    skills = emp.get("skills", {})

    loyalty_emoji = "❤️" if loyalty > 60 else ("😐" if loyalty > 30 else "💔")
    status_emoji = "🟢" if status == "active" else "🔴"

    lines = [
        f"{status_emoji} {name} | {role_cn} | 💪{ability} | 💰{salary}万/月 | {loyalty_emoji} 忠诚 {loyalty}",
    ]
    if skills:
        skill_strs = [f"{SKILL_NAMES_CN.get(k,k)} Lv.{v}" for k, v in sorted(skills.items())]
        lines.append(f"  🎯 {', '.join(skill_strs)}")
    if loyalty <= LOYALTY_RESIGN_THRESHOLD:
        lines.append(f"  ⚠️ 忠诚度过低，有离职风险！")
    return "\n".join(lines)


def format_all_employees(state: dict) -> str:
    """格式化所有员工列表。"""
    employees = state.get("employees", [])
    active = [e for e in employees if e.get("status") in ("active", None)]
    inactive = [e for e in employees if e.get("status") not in ("active", None)]

    if not active and not inactive:
        return "👥 【员工列表】\n暂无员工。使用 /招聘 招募。"

    lines = [f"👥 【员工列表】({len(active)} 人在职)\n"]
    for emp in active:
        lines.append(format_employee(emp, state))
    if inactive:
        lines.append(f"\n历史 ({len(inactive)} 人):")
        for emp in inactive[-3:]:
            lines.append(f"  🔴 {emp.get('name','?')} ({emp.get('status','?')})")
    return "\n".join(lines)
