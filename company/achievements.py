from ..utils.constants import ACHIEVEMENTS
from ..utils.utils import parse_time_to_month_idx


def check_achievements(state: dict) -> list[str]:
    meta = state.get("meta", {})
    finance = state.get("finance", {})
    employees = state.get("employees", [])
    projects = state.get("projects", [])
    unlocked = set(meta.get("achievements", []))

    candidates = []
    if projects:
        candidates.append("first_dev")
    if len(employees) >= 1:
        candidates.append("first_hire")
    if meta.get("funding_rounds"):
        candidates.append("first_funding")
    if finance.get("cash", 0) >= 100:
        candidates.append("rich")
    if len(employees) >= 4:
        candidates.append("team_5")
    if finance.get("reputation", 0) >= 100:
        candidates.append("reputation_100")
    if meta.get("office", "A") in ("B", "C", "D"):
        candidates.append("office_up")
    if meta.get("ipo_status") == "listed":
        candidates.append("ipo")
    time_str = meta.get("time", "1年1月")
    months = parse_time_to_month_idx(time_str)
    if months >= 12:
        candidates.append("survivor")
    if months >= 36:
        candidates.append("veteran")

    return [c for c in candidates if c not in unlocked]


def unlock_achievements(state: dict) -> list[str]:
    if not state.get("meta", {}).get("_achievements_enabled", True):
        return []
    new = check_achievements(state)
    if new:
        meta = state.setdefault("meta", {})
        existing = list(meta.get("achievements", []))
        meta["achievements"] = existing + new
    return new


def format_achievements(state: dict) -> str:
    meta = state.get("meta", {})
    unlocked = set(meta.get("achievements", []))
    lines = ["🏆 【成就】\n"]
    for aid, (title, desc) in ACHIEVEMENTS.items():
        if aid in unlocked:
            lines.append(f"  ✅ {title} - {desc}")
        else:
            lines.append(f"  ⬜ {title} - {desc}")
    n = len(unlocked)
    total = len(ACHIEVEMENTS)
    lines.append(f"\n📊 解锁: {n}/{total} ({n*100//total}%)")
    return "\n".join(lines)
