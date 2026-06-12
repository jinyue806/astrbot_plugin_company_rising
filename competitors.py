"""竞争对手系统：含 CEO 特长/天赋 + 难度加成。"""

import random

# === 难度加成配置 ===

DIFFICULTY_COMPETITOR_MOD = {
    "简单": {"strength_mult": 0.7, "aggression_mult": 0.6, "talent_speed": 0.5, "max_level": 5},
    "普通": {"strength_mult": 1.0, "aggression_mult": 1.0, "talent_speed": 1.0, "max_level": 7},
    "困难": {"strength_mult": 1.3, "aggression_mult": 1.4, "talent_speed": 1.5, "max_level": 10},
}

# === CEO 特长分支 ===

CEO_TRAITS = {
    "技术领袖": {"branch": "tech", "talents": ["t1_rapid_dev", "t2_tech_breakthrough"]},
    "商业奇才": {"branch": "biz", "talents": ["t1_funding_master", "t2_market_insight"]},
    "管理铁腕": {"branch": "mgmt", "talents": ["t1_loyal_leader", "t2_crisis_manager"]},
}

# === 对手 CEO 名字池 ===

CEO_NAME_POOL = [
    "陈明远", "李晓峰", "王雪晴", "张伟杰", "刘思琪",
    "赵子龙", "孙小红", "周天宇", "吴昊然", "郑思远",
    "林志远", "黄嘉豪", "何雅琴", "马腾云", "罗思诚",
]

# === 公司名称池 ===

COMPANY_NAME_POOL = [
    "云竞科技", "数据先锋", "星辰互联", "极光智能", "蓝图创新",
    "腾飞科技", "博创数码", "智源未来", "锐思软件", "领航信息",
]

# === 对手整活事件 (15% 概率) ===

COMPETITOR_FUN_EVENTS = [
    {"id": "cf01", "name": "对手 CEO 被曝劈腿", "effects": {"reputation_delta": -15}},
    {"id": "cf02", "name": "对手产品大翻车", "effects": {"strength_delta": -10, "player_growth_delta": 0.01}},
    {"id": "cf03", "name": "对手员工集体罢工", "effects": {"strength_delta": -5}},
    {"id": "cf04", "name": "对手 CEO 上综艺节目", "effects": {"reputation_delta": +20}},
    {"id": "cf05", "name": "对手被监管部门罚款", "effects": {"cash_delta": -20}},
]


def init_competitors(state: dict) -> list[dict]:
    """初始化竞争对手，根据难度生成 1-3 个。"""
    difficulty = state.get("meta", {}).get("difficulty", "普通")
    mod = DIFFICULTY_COMPETITOR_MOD.get(difficulty, DIFFICULTY_COMPETITOR_MOD["普通"])

    count = {"简单": 1, "普通": 2, "困难": 3}.get(difficulty, 2)
    competitors = []

    used_names = set()
    used_companies = set()

    for _ in range(count):
        ceo_name = random.choice([n for n in CEO_NAME_POOL if n not in used_names] or CEO_NAME_POOL)
        used_names.add(ceo_name)
        company_name = random.choice([c for c in COMPANY_NAME_POOL if c not in used_companies] or COMPANY_NAME_POOL)
        used_companies.add(company_name)

        trait = random.choice(list(CEO_TRAITS.keys()))
        base_strength = random.randint(30, 60)
        strength = int(base_strength * mod["strength_mult"])

        competitors.append({
            "name": company_name,
            "ceo": {
                "name": ceo_name,
                "trait": trait,
                "level": 1,
                "xp": 0,
                "unlocked_talents": [],
            },
            "strength": min(100, strength),
            "aggression": round(random.uniform(0.3, 0.7) * mod["aggression_mult"], 2),
            "market_share": round(random.uniform(0.05, 0.15), 2),
            "cash": round(random.uniform(50, 120) * mod["strength_mult"], 1),
            "reputation": random.randint(20, 50),
        })

    state.setdefault("meta", {})["competitors"] = competitors
    return competitors


def _get_competitor_talent_effects(comp: dict) -> dict:
    """获取对手 CEO 已解锁天赋的效果。"""
    from .constants import TALENT_TREE
    effects = {}
    trait = comp["ceo"]["trait"]
    trait_info = CEO_TRAITS.get(trait, {})
    branch = trait_info.get("branch", "tech")
    branch_data = TALENT_TREE.get(branch, {})

    for talent_id in comp["ceo"].get("unlocked_talents", []):
        talent = branch_data.get("talents", {}).get(talent_id, {})
        for k, v in talent.get("effect", {}).items():
            effects[k] = effects.get(k, 0) + v
    return effects


def advance_competitors(state: dict) -> list[dict]:
    """月度竞争对手推进，返回本月发生的事件列表。"""
    if not state.get("meta", {}).get("competitors"):
        init_competitors(state)

    competitors = state.get("meta", {}).get("competitors", [])
    if not competitors:
        return []

    difficulty = state.get("meta", {}).get("difficulty", "普通")
    mod = DIFFICULTY_COMPETITOR_MOD.get(difficulty, DIFFICULTY_COMPETITOR_MOD["普通"])
    player_rep = state.get("finance", {}).get("reputation", 0)
    talent_effects = {}
    try:
        from .ceo import get_talent_effects
        talent_effects = get_talent_effects(state)
    except ImportError:
        pass

    events = []

    for comp in competitors:
        # === 月度成长 ===
        xp_gain = int(5 * mod["talent_speed"])
        comp["ceo"]["xp"] = comp["ceo"].get("xp", 0) + xp_gain
        _try_level_up(comp, mod)

        # Strength 增长
        comp["strength"] = min(100, comp["strength"] + random.randint(1, 3))

        # === 月度行为 ===
        action_prob = comp["aggression"] * mod["aggression_mult"] * (1 + player_rep / 200)
        action_prob = min(0.9, action_prob)

        # 玩家天赋: competitor_defense 降低对手行动概率
        comp_defense = talent_effects.get("competitor_defense", 0)
        if comp_defense > 0:
            action_prob *= (1 - comp_defense)

        comp_effects = _get_competitor_talent_effects(comp)

        if random.random() < action_prob:
            action = _pick_action(comp, comp_effects)
            if action:
                _apply_competitor_action(state, comp, action, comp_effects)
                events.append({"competitor": comp["name"], "action": action["name"],
                               "ceo_trait": comp["ceo"]["trait"], "ceo_level": comp["ceo"]["level"]})

        # === 15% 整活事件 ===
        if random.random() < 0.15:
            fun = random.choice(COMPETITOR_FUN_EVENTS)
            fe = fun.get("effects", {})
            if "reputation_delta" in fe:
                comp["reputation"] = max(0, comp["reputation"] + fe["reputation_delta"])
            if "strength_delta" in fe:
                comp["strength"] = max(0, min(100, comp["strength"] + fe["strength_delta"]))
            if "cash_delta" in fe:
                comp["cash"] = max(0, comp["cash"] + fe["cash_delta"])
            if "player_growth_delta" in fe:
                cust = state.get("customers", {})
                cust["growth_rate"] = max(0, cust.get("growth_rate", 0) + fe["player_growth_delta"])
            events.append({"competitor": comp["name"], "action": fun["name"], "fun": True})

    return events


def _try_level_up(comp: dict, mod: dict) -> None:
    """尝试给对手 CEO 升级。"""
    from .constants import CEO_LEVEL_XP
    max_level = mod.get("max_level", 7)
    level = comp["ceo"].get("level", 1)
    xp = comp["ceo"].get("xp", 0)

    while level < max_level:
        needed = CEO_LEVEL_XP.get(level + 1, 99999)
        if xp >= needed:
            level += 1
            comp["ceo"]["level"] = level
            # 解锁天赋
            trait_info = CEO_TRAITS.get(comp["ceo"]["trait"], {})
            talents = trait_info.get("talents", [])
            talent_idx = level // 3  # 3 级解锁 1 级天赋, 6 级解锁 2 级
            if talent_idx < len(talents):
                tid = talents[talent_idx]
                if tid not in comp["ceo"].get("unlocked_talents", []):
                    comp["ceo"].setdefault("unlocked_talents", []).append(tid)
        else:
            break


def _pick_action(comp: dict, comp_effects: dict) -> dict:
    """根据对手特征选择行动。"""
    aggression = comp.get("aggression", 0.5)
    level = comp["ceo"].get("level", 1)
    strength = comp.get("strength", 50)

    actions = []

    # 价格战
    if aggression > 0.4:
        actions.append({"name": "发起价格战", "type": "price_war",
                        "effects": {"churn_rate_delta": 0.03, "growth_rate_delta": -0.02},
                        "talent_boost": "t2_market_insight"})
    # 挖人
    actions.append({"name": "挖人", "type": "poach",
                    "effects": {"loyalty_delta": -10},
                    "talent_boost": "t1_loyal_leader"})
    # 抄袭
    actions.append({"name": "抄袭产品", "type": "copy",
                    "effects": {"progress_delta": -10},
                    "talent_boost": "t1_rapid_dev"})
    # 抢客户
    actions.append({"name": "抢夺客户", "type": "steal_customer",
                    "effects": {"customer_delta": -1},
                    "talent_boost": "t2_market_insight"})
    # 融资扩张
    if strength < 80:
        actions.append({"name": "融资扩张", "type": "fundraise",
                        "effects": {"strength_delta": 10},
                        "talent_boost": "t1_funding_master"})
    # 发布新品
    if level >= 4:
        actions.append({"name": "发布新品", "type": "launch",
                        "effects": {"growth_rate_delta": -0.01},
                        "talent_boost": "t2_tech_breakthrough"})

    return random.choice(actions) if actions else None


def _apply_competitor_action(state: dict, comp: dict, action: dict,
                             comp_effects: dict) -> None:
    """应用对手行动效果到玩家 state。"""
    effects = action.get("effects", {})
    boost_id = action.get("talent_boost", "")
    boost_mult = 1.5 if boost_id in comp["ceo"].get("unlocked_talents", []) else 1.0

    finance = state.get("finance", {})
    customers = state.get("customers", {})

    if "churn_rate_delta" in effects:
        val = effects["churn_rate_delta"] * boost_mult
        customers["churn_rate"] = max(0, min(1, customers.get("churn_rate", 0.1) + val))
    if "growth_rate_delta" in effects:
        val = effects["growth_rate_delta"] * boost_mult
        customers["growth_rate"] = max(0, customers.get("growth_rate", 0) + val)
    if "loyalty_delta" in effects:
        # 天赋 t1_loyal_leader 的对手挖不动
        if "t1_loyal_leader" in comp["ceo"].get("unlocked_talents", []):
            pass  # 对手员工不流失 → 但这里是对手挖玩家，所以玩家的人才防御无效
        emps = [e for e in state.get("employees", []) if e.get("status") in ("active", None)]
        if emps:
            target = random.choice(emps)
            target["loyalty"] = max(0, target.get("loyalty", 70) + effects["loyalty_delta"])
    if "progress_delta" in effects:
        val = effects["progress_delta"] * boost_mult
        projects = [p for p in state.get("projects", []) if p.get("status") == "研发中"]
        if projects:
            target = random.choice(projects)
            target["progress"] = max(0, min(100, target["progress"] + val))
    if "customer_delta" in effects:
        delta = effects["customer_delta"] * boost_mult
        customers["count"] = max(0, customers.get("count", 0) + int(delta))
    if "strength_delta" in effects:
        val = effects["strength_delta"] * boost_mult
        comp["strength"] = min(100, max(0, comp["strength"] + int(val)))


def format_competitors(state: dict) -> str:
    """格式化竞争对手信息面板。"""
    competitors = state.get("meta", {}).get("competitors", [])
    if not competitors:
        return "🆚 【竞争对手】\n暂无竞争对手。"

    lines = [f"🆚 【竞争对手】({len(competitors)} 家)\n"]
    for comp in competitors:
        ceo = comp.get("ceo", {})
        talent_str = ""
        if ceo.get("unlocked_talents"):
            talent_str = f" | 🎯 天赋:{len(ceo['unlocked_talents'])}个"
        lines.append(
            f"  🏢 {comp['name']} | CEO: {ceo.get('name', '?')}({ceo.get('trait', '?')})"
            f" | Lv.{ceo.get('level', 1)}{talent_str}"
        )
        lines.append(
            f"     💪 实力:{comp.get('strength', 0)} | 😤 攻击性:{comp.get('aggression', 0):.0%}"
            f" | 📊 市场份额:{comp.get('market_share', 0):.0%} | ⭐ 声誉:{comp.get('reputation', 0)}"
        )
    return "\n".join(lines)
