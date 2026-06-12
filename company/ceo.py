from ..utils.constants import TALENT_TREE, CEO_LEVEL_XP


def get_xp_for_action(action: str) -> int:
    """返回各动作对应的 XP 值。"""
    xp_map = {
        'project_complete': 20,
        'funding_success': 15,
        'ipo_success': 50,
        'hire_success': 5,
        'monthly_survival': 5,
        'achievement_unlock': 10,
    }
    return xp_map.get(action, 0)


def get_ceo_branch(trait: str) -> str:
    """根据 CEO 特质返回天赋分支键。"""
    trait_map = {
        '技术领袖': 'tech',
        '商业奇才': 'biz',
        '管理铁腕': 'mgmt',
    }
    return trait_map.get(trait, 'tech')


def calculate_level(xp: int) -> int:
    """根据累计 XP 计算等级 (1-10)。"""
    for level in range(10, 0, -1):
        if xp >= CEO_LEVEL_XP[level]:
            return level
    return 1


def gain_xp(state: dict, action: str) -> dict:
    """增加 CEO XP，检查升级，返回变化信息。"""
    xp_gain = get_xp_for_action(action)
    if xp_gain == 0:
        return {"ok": True, "xp_gain": 0, "leveled_up": False, "new_level": state["ceo"].get("level", 1)}

    ceo = state["ceo"]
    ceo.setdefault("xp", 0)
    ceo.setdefault("level", 1)
    ceo.setdefault("talent_points", 0)
    ceo.setdefault("unlocked_talents", [])

    old_level = ceo["level"]
    ceo["xp"] += xp_gain
    new_level = calculate_level(ceo["xp"])

    result = {
        "ok": True,
        "xp_gain": xp_gain,
        "total_xp": ceo["xp"],
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": False,
        "talent_points_gained": 0,
    }

    if new_level > old_level:
        ceo["level"] = new_level
        levels_gained = new_level - old_level
        ceo["talent_points"] = ceo.get("talent_points", 0) + levels_gained
        result["leveled_up"] = True
        result["new_level"] = new_level
        result["talent_points_gained"] = levels_gained

    return result


def get_available_talents(state: dict) -> list[str]:
    """返回当前可解锁的天赋 ID 列表。"""
    ceo = state["ceo"]
    branch = get_ceo_branch(ceo["trait"])
    tree = TALENT_TREE[branch]["talents"]
    unlocked = set(ceo.get("unlocked_talents", []))

    available = []
    for tid, talent in tree.items():
        if tid in unlocked:
            continue
        req = talent.get("requires")
        if req and req not in unlocked:
            continue
        if talent["tier"] > ceo["talent_points"] + len(unlocked):
            continue
        available.append(tid)
    return available


def unlock_talent(state: dict, talent_id: str) -> dict:
    """解锁指定天赋，消耗 1 天赋点。"""
    ceo = state["ceo"]
    branch = get_ceo_branch(ceo["trait"])
    tree = TALENT_TREE[branch]["talents"]

    if talent_id not in tree:
        return {"ok": False, "msg": f"⚠️ 天赋 {talent_id} 不存在。"}

    if talent_id in ceo.get("unlocked_talents", []):
        return {"ok": False, "msg": f"⚠️ 天赋 {talent_id} 已解锁。"}

    talent = tree[talent_id]
    req = talent.get("requires")
    unlocked = set(ceo.get("unlocked_talents", []))

    if req and req not in unlocked:
        return {"ok": False, "msg": f"⚠️ 需先解锁前置天赋。"}

    if ceo["talent_points"] <= 0:
        return {"ok": False, "msg": "⚠️ 天赋点不足。"}

    # 解锁
    ceo.setdefault("unlocked_talents", []).append(talent_id)
    ceo["talent_points"] -= 1

    return {
        "ok": True,
        "msg": "",
        "talent_id": talent_id,
        "talent_name": tree[talent_id]["name"],
        "remaining_points": ceo["talent_points"],
    }


def get_talent_effects(state: dict) -> dict:
    """汇总所有已解锁天赋的效果，返回合并后的效果字典。"""
    ceo = state["ceo"]
    branch = get_ceo_branch(ceo["trait"])
    tree = TALENT_TREE[branch]["talents"]
    unlocked = ceo.get("unlocked_talents", [])

    combined = {}
    for tid in unlocked:
        if tid in tree:
            effect = tree[tid].get("effect", {})
            for k, v in effect.items():
                if k in combined:
                    if isinstance(v, (int, float)) and isinstance(combined[k], (int, float)):
                        combined[k] += v
                    else:
                        combined[k] = v  # 后者覆盖
                else:
                    combined[k] = v
    return combined


def format_ceo_panel(state: dict) -> str:
    """格式化 CEO 面板显示。"""
    ceo = state["ceo"]
    branch_key = get_ceo_branch(ceo["trait"])
    branch = TALENT_TREE[branch_key]

    # XP 进度条
    current_xp = ceo["xp"]
    current_level = ceo["level"]
    next_level_xp = CEO_LEVEL_XP.get(current_level + 1, CEO_LEVEL_XP[10])
    current_level_xp = CEO_LEVEL_XP[current_level]

    if current_level >= 10:
        xp_bar = "MAX"
        xp_progress = "MAX"
    else:
        progress = current_xp - current_level_xp
        total = next_level_xp - current_level_xp
        pct = int(progress * 100 / total) if total > 0 else 100
        xp_progress = f"{progress}/{total} ({pct}%)"

    lines = [
        f"👑 【CEO 面板】",
        f"  特质：{ceo['trait']} ({branch['name']}分支)",
        f"  等级：Lv.{ceo['level']} (XP: {current_xp} / {next_level_xp if current_level < 10 else 'MAX'})",
        f"  进度：{xp_progress}",
        f"  天赋点：{ceo['talent_points']} 可用",
        "",
        "🌳 天赋树 ({branch['name']}分支)：",
    ]

    tree = TALENT_TREE[branch_key]["talents"]
    unlocked = set(ceo.get("unlocked_talents", []))

    for tid, talent in tree.items():
        status = "✅" if tid in unlocked else ("🔓" if tid in get_available_talents({"ceo": ceo}) else "🔒")
        req = talent.get("requires")
        req_str = f" (需: {tree[req]['name']})" if req and req not in unlocked else ""
        lines.append(f"  {status} T{talent['tier']}. {talent['name']}{req_str}")
        lines.append(f"      {talent['desc']}")

    lines.append(f"\n💡 输入 /天赋 <天赋ID> 解锁 (消耗 1 天赋点)")
    return "\n".join(lines)