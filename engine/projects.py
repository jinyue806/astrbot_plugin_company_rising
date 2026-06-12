from ..utils.utils import get_office
from ..company.ceo import get_talent_effects


def calc_capacity(state: dict) -> dict:
    staff = state["staff"]
    office = get_office(state)
    talent_effects = get_talent_effects(state)
    capacity_bonus = talent_effects.get("capacity_bonus", 0)
    cap = {
        "tech": 1 + staff["tech"] * 3 + office["capacity_bonus"] + capacity_bonus,
        "design": 1 + staff["design"] * 3 + office["capacity_bonus"] + capacity_bonus,
        "marketing": 1 + staff["marketing"] * 3 + office["capacity_bonus"] + capacity_bonus,
    }
    if state["ceo"]["trait"] == "技术领袖":
        cap["tech"] += 2
    # 天赋: 市场洞察 → 营销产能 ×1.5
    marketing_eff = talent_effects.get("marketing_efficiency", 0)
    if marketing_eff > 0:
        cap["marketing"] = int(cap["marketing"] * (1 + marketing_eff))
    return cap


def start_dev(state: dict, project_name: str) -> dict:
    if state["ceo"]["ap"] < 2:
        return {"ok": False, "msg": "⚠️ 行动点不足（需要 2 AP），请等下个月恢复。"}
    talent_effects = get_talent_effects(state)
    dev_cost_reduction = talent_effects.get("dev_cost_reduction", 0)
    cost = max(1, 10 - dev_cost_reduction)
    if state["finance"]["cash"] < cost:
        return {"ok": False, "msg": f"⚠️ 现金不足 {cost} 万，无法启动新研发项目。"}
    # 天赋: 并行项目上限
    parallel_bonus = talent_effects.get("parallel_projects", 0)
    max_projects = 2 + parallel_bonus
    active_count = sum(1 for p in state.get("projects", []) if p.get("status") == "研发中")
    if active_count >= max_projects:
        return {"ok": False, "msg": f"⚠️ 并行项目已达上限 ({max_projects})，请等现有项目完成或取消。"}
    state["ceo"]["ap"] -= 2
    state["finance"]["cash"] -= cost
    revenue_est = 30 + state["finance"]["reputation"]
    state["projects"].append({
        "name": project_name,
        "progress": 0,
        "status": "研发中",
        "revenue": revenue_est,
    })
    return {"ok": True, "msg": ""}


def cancel_project(state: dict, project_name: str) -> dict:
    if state["ceo"]["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足，无法取消项目。"}
    for p in state.get("projects", []):
        if p.get("name") == project_name:
            if p.get("status") == "completed":
                return {"ok": False, "msg": f"⚠️ 项目「{project_name}」已交付, 不可取消。"}
            if p.get("status") == "已取消":
                return {"ok": False, "msg": f"⚠️ 项目「{project_name}」已取消。"}
            progress = p.get("progress", 0)
            if progress >= 80:
                return {"ok": False, "msg": f"⚠️ 项目「{project_name}」已完成 {progress}%, 沉没成本太高, 建议等交付。"}
            refund = round(10 * (1 - progress / 100), 1)
            state["finance"]["cash"] += refund
            state["ceo"]["ap"] -= 1
            p["status"] = "已取消"
            return {
                "ok": True,
                "msg": "",
                "refund": refund,
                "progress_at_cancel": progress,
            }
    return {"ok": False, "msg": f"⚠️ 没找到项目「{project_name}」。用 /面板 项目 查看。"}


def list_projects(state: dict, only_active: bool = True) -> list[dict]:
    out = []
    for p in state.get("projects", []):
        if only_active and p.get("status") in ("completed", "已取消"):
            continue
        out.append(p)
    return out


def ascii_progress_bar(value: float, total: float, width: int = 10,
                        filled: str = "▓", empty: str = "░",
                        with_pct: bool = False) -> str:
    if total <= 0:
        ratio = 0
    else:
        ratio = max(0.0, min(1.0, value / total))
    n_filled = int(ratio * width + 0.5)
    n_empty = width - n_filled
    bar = filled * n_filled + empty * n_empty
    if with_pct:
        bar += f" {int(ratio * 100)}%"
    return bar
