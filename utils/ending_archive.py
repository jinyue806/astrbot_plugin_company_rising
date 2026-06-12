"""End-game archive: save & recall game endings."""

import json
import logging
from datetime import datetime

from .storage import get_plugin_subdir

logger = logging.getLogger(__name__)

# Archive directory
_ARCHIVE_DIR = get_plugin_subdir("endings")


def save_ending(state: dict, user_id: str, ending_text: str) -> bool:
    """Save a game-ending snapshot to the archive."""
    meta = state.get("meta", {})
    finance = state.get("finance", {})
    ceo = state.get("ceo", {})
    campus = state.get("campus", {})
    customers = state.get("customers", {})

    phase = state.get("phase", "company")
    months = campus.get("months_played", 0) if phase == "campus" else _calc_months(meta)

    snapshot = {
        "user_id": user_id,
        "company": meta.get("company", ""),
        "industry": meta.get("industry", ""),
        "time": meta.get("time", ""),
        "difficulty": meta.get("difficulty", "普通"),
        "phase": phase,
        "finance": {
            "cash": finance.get("cash", 0),
            "valuation": finance.get("valuation", 0),
            "reputation": finance.get("reputation", 0),
        },
        "ceo_trait": ceo.get("trait", ""),
        "ceo_level": ceo.get("level", 1),
        "employee_count": len(state.get("employees", [])),
        "projects_completed": sum(
            1 for p in state.get("projects", []) if p.get("status") == "completed"
        ),
        "customers": customers.get("count", 0),
        "ipo": meta.get("ipo_status", "未上市"),
        "months_played": months,
        "ending_text": ending_text,
        "campus_background": campus.get("background", "") if phase == "campus" else "",
        "campus_titles": campus.get("titles", []) if phase == "campus" else [],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = _ARCHIVE_DIR / f"{user_id}_{ts}.json"
    try:
        tmp = file_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(file_path)
        logger.info(f"Ending archived: {file_path.name}")
        return True
    except OSError as e:
        logger.warning(f"Ending archive failed: {e}")
        return False


def _calc_months(meta: dict) -> int:
    """Parse time string like '3Y5M' to total months."""
    time_str = meta.get("time", "")
    years = months = 0
    try:
        if "年" in time_str:
            parts = time_str.split("年")
            years = int(parts[0])
            time_str = parts[1]
        if "月" in time_str:
            months = int(time_str.replace("月", ""))
    except (ValueError, IndexError):
        pass
    if years <= 0:
        return months
    return (years - 1) * 12 + months


def list_endings(user_id: str) -> list[dict]:
    """List all archived endings for a user, sorted by time descending."""
    endings = []
    for fp in sorted(_ARCHIVE_DIR.glob(f"{user_id}_*.json"), reverse=True):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            data["_file"] = fp.name
            endings.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return endings


def get_ending(user_id: str, index: int) -> dict | None:
    """Get a specific ending by 1-based index (1 = most recent)."""
    endings = list_endings(user_id)
    if 1 <= index <= len(endings):
        return endings[index - 1]
    return None


def format_endings_list(endings: list[dict]) -> str:
    """Format a list of endings as a summary table."""
    if not endings:
        return f"\U0001f4dc 暂无结局存档。游戏结束后会自动归档！"

    lines = [
        f"\U0001f4dc 【结局录】共 "
        + str(len(endings))
        + " 局：:\n"
    ]
    for i, e in enumerate(endings, 1):
        mode = (
            "\U0001f393 校园" if e.get("phase") == "campus"
            else "\U0001f3e2 公司"
        )
        lines.append(
            f"  {i}. {e.get('company', '?')} | {e.get('industry', '?')}"
            f" | {mode}"
            f" | {e.get('difficulty', '?')}"
            f" | {e.get('time', '?')}"
            f" | \U0001f4b0 {e.get('finance', {}).get('cash', 0):.1f}万"
        )
    lines.append(
        f"\n\U0001f4a1 用 /回顾 <序号> 查看详细回顾"
    )
    return "\n".join(lines)


def format_ending_detail(ending: dict) -> str:
    """Format a single ending as a detailed review."""
    phase = ending.get("phase", "company")
    mode_label = (
        "\U0001f393 校园_MODE"
        if phase == "campus"
        else "\U0001f3e2 公司_MODE"
    )

    lines = [
        "\u2550" * 36,
        f"\U0001f451 {ending.get('company', '?')} - 结局回顾",
        "\u2550" * 36,
        f"  \U0001f3ae 模式: {mode_label}",
        f"  \U0001f3ed 行业: {ending.get('industry', '?')}",
        f"  \u2699\ufe0f 难度: {ending.get('difficulty', '?')}",
        f"  \u23f0 时长: {ending.get('months_played', 0)} 个月 ({ending.get('time', '?')})",
        "",
        f"  \U0001f4b0 最终现金: {ending.get('finance', {}).get('cash', 0):.1f}万",
        f"  \U0001f48e 估值: {ending.get('finance', {}).get('valuation', 0):.0f}万",
        f"  \u2b50 声誉: {ending.get('finance', {}).get('reputation', 0)}",
        f"  \U0001f465 团队: {ending.get('employee_count', 0)}人",
        f"  \U0001f4c1 已完成项目: {ending.get('projects_completed', 0)}",
        f"  \U0001f464 客户: {ending.get('customers', 0)}",
        f"  \U0001f3c6 IPO: {ending.get('ipo', '?')}",
    ]

    titles = ending.get("campus_titles", [])
    if titles:
        lines.append(f"  \U0001f396 称号: {', '.join(titles)}")
    bg = ending.get("campus_background", "")
    if bg:
        lines.append(f"  \U0001f3e0 家庭背景: {bg}")

    lines.append("")
    lines.append("\u2500" * 36)
    lines.append(ending.get("ending_text", ""))
    lines.append("\u2550" * 36)
    ts = ending.get("timestamp", "")
    if ts:
        lines.append(f"\U0001f4c5 归档时间: {ts}")

    return "\n".join(lines)
