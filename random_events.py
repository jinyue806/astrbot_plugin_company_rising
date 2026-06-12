"""月度随机事件系统：天灾人祸 + 整活。"""

import random

# === 难度配置 ===

DIFFICULTY_EVENT = {
    "简单": {"chance": 0.25, "severity": [50, 30, 15, 5], "max_per_month": 1},
    "普通": {"chance": 0.35, "severity": [35, 35, 22, 8], "max_per_month": 1},
    "困难": {"chance": 0.50, "severity": [20, 30, 35, 15], "max_per_month": 2},
}

SEVERITY_LABELS = ["轻微", "中等", "严重", "灾难"]

# === 事件库 (28 个) ===
# severity: 0=轻微, 1=中等, 2=严重, 3=灾难
# effects: cash_delta / reputation_delta / churn_rate_delta / growth_rate_delta
#          loyalty_delta / progress_delta / fixed_cost_inflate / force_resign_count / ap_penalty

EVENT_POOL = [
    # --- 轻微 x10 ---
    {"id": "e01_bug_season", "name": "🐛 Bug 高发月", "severity": 0,
     "desc": "这个月 Bug 特别多，研发全员修 Bug",
     "effects": {"progress_delta": -5, "loyalty_delta": -2}},
    {"id": "e02_power_outage", "name": "⚡ 区域停电", "severity": 0,
     "desc": "办公楼停电一天，全员摸鱼",
     "effects": {"progress_delta": -3, "cash_delta": -0.1}},
    {"id": "e03_network_jitter", "name": "🌐 网络波动", "severity": 0,
     "desc": "公司网络抽风，远程办公效率下降",
     "effects": {"progress_delta": -2}},
    {"id": "e04_printer_jam", "name": "🖨️ 打印机卡纸事件", "severity": 0,
     "desc": "打印机又双叒叕卡纸了，行政修了一下午",
     "effects": {"cash_delta": -0.05}},
    {"id": "e05_supplier_delay", "name": "📦 供应商延期", "severity": 0,
     "desc": "关键供应商交货延期两周",
     "effects": {"progress_delta": -4}},
    {"id": "e06_bad_review", "name": "⭐ 差评风波", "severity": 0,
     "desc": "产品收到几条差评，声誉小降",
     "effects": {"reputation_delta": -3}},
    {"id": "e07_hr_typo", "name": "📝 HR 发错工资", "severity": 0,
     "desc": "HR 把工资算错了，多发了两千块",
     "effects": {"cash_delta": -0.2, "loyalty_delta": +2}},
    {"id": "e08_air_con_broken", "name": "❄️ 空调坏了", "severity": 0,
     "desc": "空调罢工，全员汗流浃背写代码",
     "effects": {"progress_delta": -2, "loyalty_delta": -3}},
    {"id": "e09_intern_leak", "name": "🤐 实习生泄密", "severity": 0,
     "desc": "实习生不小心把内部文档发到了群里",
     "effects": {"reputation_delta": -2}},
    {"id": "e10_tax_audit", "name": "📊 税务抽查", "severity": 0,
     "desc": "税务局例行抽查，虚惊一场",
     "effects": {"cash_delta": -0.3}},

    # --- 中等 x8 ---
    {"id": "e11_core_leave", "name": "🚪 核心员工跳槽", "severity": 1,
     "desc": "一名核心员工被大厂高薪挖走",
     "effects": {"force_resign_count": 1, "loyalty_delta": -5}},
    {"id": "e12_server_crash", "name": "💥 服务器宕机", "severity": 1,
     "desc": "生产环境服务器宕机 4 小时",
     "effects": {"progress_delta": -8, "cash_delta": -2, "reputation_delta": -5}},
    {"id": "e13_client_complaint", "name": "😡 大客户投诉", "severity": 1,
     "desc": "最大客户发飙要解约",
     "effects": {"churn_rate_delta": 0.03, "reputation_delta": -5}},
    {"id": "e14_office_flood", "name": "💧 办公室漏水", "severity": 1,
     "desc": "楼上漏水把办公室淹了",
     "effects": {"cash_delta": -3, "progress_delta": -5}},
    {"id": "e15_price_war", "name": "📉 行业价格战", "severity": 1,
     "desc": "竞品疯狂降价，客户被撬走",
     "effects": {"churn_rate_delta": 0.05, "growth_rate_delta": -0.02}},
    {"id": "e16_policy_change", "name": "📜 政策变动", "severity": 1,
     "desc": "行业新政策出台，合规成本增加",
     "effects": {"cash_delta": -5, "fixed_cost_inflate": 0.05}},
    {"id": "e17_media_crisis", "name": "📺 媒体负面报道", "severity": 1,
     "desc": "科技媒体发了篇负面文章",
     "effects": {"reputation_delta": -10, "growth_rate_delta": -0.01}},
    {"id": "e18_supply_chain", "name": "🚚 供应链中断", "severity": 1,
     "desc": "关键零部件断供，项目被迫暂停",
     "effects": {"progress_delta": -10, "cash_delta": -3}},

    # --- 严重 x5 ---
    {"id": "e19_ip_lawsuit", "name": "⚖️ 知识产权诉讼", "severity": 2,
     "desc": "被竞争对手起诉侵权！",
     "effects": {"cash_delta": -15, "reputation_delta": -15, "ap_penalty": 1}},
    {"id": "e20_data_breach", "name": "🔓 数据泄露", "severity": 2,
     "desc": "用户数据泄露事件，公关危机",
     "effects": {"reputation_delta": -20, "cash_delta": -10, "churn_rate_delta": 0.08}},
    {"id": "e21_economic_downturn", "name": "📉 经济下行", "severity": 2,
     "desc": "宏观经济恶化，融资困难",
     "effects": {"growth_rate_delta": -0.03, "churn_rate_delta": 0.05, "cash_delta": -8}},
    {"id": "e22_pandemic", "name": "🦠 突发疫情", "severity": 2,
     "desc": "突发公共卫生事件，全员居家",
     "effects": {"progress_delta": -15, "cash_delta": -5, "loyalty_delta": -5}},
    {"id": "e23_regulatory_fine", "name": "🏛️ 监管罚款", "severity": 2,
     "desc": "监管部门开出大额罚单",
     "effects": {"cash_delta": -20, "reputation_delta": -10, "fixed_cost_inflate": 0.08}},

    # --- 灾难 x3 ---
    {"id": "e24_investor_pullout", "name": "💔 投资人撤资", "severity": 3,
     "desc": "领投方突然撤资，现金流告急！",
     "effects": {"cash_delta": -30, "reputation_delta": -20, "growth_rate_delta": -0.05}},
    {"id": "e25_ceo_scandal", "name": "🗞️ CEO 丑闻", "severity": 3,
     "desc": "CEO 被曝出不当言论，舆论风暴",
     "effects": {"reputation_delta": -30, "churn_rate_delta": 0.10, "loyalty_delta": -15}},
    {"id": "e26_fire_disaster", "name": "🔥 办公室火灾", "severity": 3,
     "desc": "办公楼发生火灾，设备全部损毁",
     "effects": {"cash_delta": -40, "progress_delta": -25, "force_resign_count": 2}},

    # --- 整活 x2 ---
    {"id": "e27_paid_poop", "name": "💩 全员带薪拉屎月", "severity": 0,
     "desc": "本月全员厕所办公，效率拉胯但心情大好",
     "effects": {"loyalty_delta": +15, "progress_delta": -8, "cash_delta": -0.5}},
    {"id": "e28_cat_invasion", "name": "🐱 流浪猫入侵办公室", "severity": 0,
     "desc": "一群流浪猫溜进办公室，睡在服务器上",
     "effects": {"loyalty_delta": +10, "progress_delta": -3}},
]


def roll_monthly_event(state: dict) -> list[dict]:
    """月度随机事件，返回触发的事件列表。"""
    difficulty = state.get("meta", {}).get("difficulty", "普通")
    config = DIFFICULTY_EVENT.get(difficulty, DIFFICULTY_EVENT["普通"])

    # 频率配置覆盖
    freq = state.get("meta", {}).get("_event_frequency", "标准")
    freq_mult = {"关闭": 0, "低频": 0.5, "标准": 1.0, "高频": 1.5}.get(freq, 1.0)
    if freq_mult == 0:
        return []

    # 防重: 半年内不重复
    recent_ids = state.get("meta", {}).get("_recent_event_ids", [])
    if not isinstance(recent_ids, list):
        recent_ids = []

    # 前 2 月保护期不触发严重+
    month_idx = 0
    time_str = state.get("meta", {}).get("time", "1年1月")
    try:
        parts = time_str.replace("年", " ").replace("月", "").split()
        month_idx = (int(parts[0]) - 1) * 12 + int(parts[1])
    except (ValueError, IndexError):
        pass

    results = []
    for _ in range(config["max_per_month"]):
        if random.random() > config["chance"] * freq_mult:
            continue

        # 按 severity 权重选事件
        severity_weights = config["severity"]
        # 保护期: 前 2 月只触发轻微/中等
        if month_idx <= 2:
            severity_weights = [70, 30, 0, 0]

        total_w = sum(severity_weights)
        pick = random.randint(1, total_w)
        chosen_severity = 0
        cum = 0
        for i, w in enumerate(severity_weights):
            cum += w
            if pick <= cum:
                chosen_severity = i
                break

        # 从对应 severity 的事件中挑选（排除近期触发过的）
        candidates = [
            e for e in EVENT_POOL
            if e["severity"] == chosen_severity and e["id"] not in recent_ids
        ]
        if not candidates:
            candidates = [e for e in EVENT_POOL if e["severity"] == chosen_severity]
        if not candidates:
            continue

        event = random.choice(candidates)
        _apply_event(state, event)
        results.append(event)

        # 记录到防重列表
        recent_ids.append(event["id"])
        if len(recent_ids) > 6:
            recent_ids = recent_ids[-6:]

    state.setdefault("meta", {})["_recent_event_ids"] = recent_ids
    return results


def _apply_event(state: dict, event: dict) -> None:
    """将事件效果应用到 state。"""
    from .ceo import get_talent_effects
    effects = event.get("effects", {})
    talent_effects = get_talent_effects(state)
    crisis_reduction = talent_effects.get("crisis_reduction", 0)

    # 天赋减免伤害
    def _reduce_negative(val: float) -> float:
        if val < 0 and crisis_reduction > 0:
            return val * (1 - crisis_reduction)
        return val

    finance = state.setdefault("finance", {})
    if "cash_delta" in effects:
        finance["cash"] = finance.get("cash", 0) + _reduce_negative(effects["cash_delta"])
    if "reputation_delta" in effects:
        finance["reputation"] = max(0, finance.get("reputation", 0) + _reduce_negative(effects["reputation_delta"]))

    customers = state.setdefault("customers", {})
    if "churn_rate_delta" in effects:
        customers["churn_rate"] = max(0, min(1, customers.get("churn_rate", 0.1) + _reduce_negative(effects["churn_rate_delta"])))
    if "growth_rate_delta" in effects:
        customers["growth_rate"] = max(0, customers.get("growth_rate", 0) + _reduce_negative(effects["growth_rate_delta"]))

    if "progress_delta" in effects:
        delta = _reduce_negative(effects["progress_delta"])
        for p in state.get("projects", []):
            if p.get("status") == "研发中":
                p["progress"] = max(0, min(100, p["progress"] + delta))
                break  # 只影响第一个进行中的项目

    if "loyalty_delta" in effects:
        delta = _reduce_negative(effects["loyalty_delta"])
        for emp in state.get("employees", []):
            if emp.get("status") in ("active", None):
                emp["loyalty"] = max(0, min(100, emp.get("loyalty", 70) + int(delta)))

    if "fixed_cost_inflate" in effects:
        finance["fixed_cost"] = finance.get("fixed_cost", 0) * (1 + effects["fixed_cost_inflate"])

    if "ap_penalty" in effects:
        state.setdefault("ceo", {})["ap"] = max(0, state["ceo"].get("ap", 0) - effects["ap_penalty"])

    if "force_resign_count" in effects:
        from .employee import fire_employee

        count = effects["force_resign_count"]
        active_emps = [e for e in state.get("employees", []) if e.get("status") in ("active", None)]
        random.shuffle(active_emps)
        for emp in active_emps[:count]:
            fire_employee(state, emp, "auto_resign", event.get("name", ""), consume_ap=False)
