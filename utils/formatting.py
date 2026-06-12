from .constants import ACHIEVEMENTS
from ..company.finance import compute_runway
from ..engine.projects import ascii_progress_bar, calc_capacity
from .utils import get_office, level_emoji


def format_history(state: dict, n: int = 5) -> str:
    log = state.get("log", [])
    if not log:
        return "📜 【历史】\n暂无历史记录。运行 /下一月 推进游戏后会累积。"
    lines = [f"📜 【历史 · 最近 {min(n, len(log))} 月】\n"]
    for entry in log[-n:][::-1]:
        lines.append(f"  📅 {entry['time']}")
        if entry.get("event"):
            lines.append(f"     {entry['event']}")
        if entry.get("milestones"):
            ms = "、".join(entry["milestones"])
            lines.append(f"     🏆 完成: {ms}")
        if entry.get("revenue") and entry["revenue"] > 0:
            lines.append(f"     💰 收入: +{entry['revenue']}万")
        if entry.get("achievements"):
            for aid in entry["achievements"]:
                if aid in ACHIEVEMENTS:
                    lines.append(f"     🎉 解锁: {ACHIEVEMENTS[aid][0]}")
    return "\n".join(lines)


def format_status(state: dict) -> str:
    if state.get("phase") == "campus":
        from ..campus.campus import format_campus_status
        return format_campus_status(state)

    s = state
    proj_count = len([p for p in s["projects"] if p.get("status") != "completed"])
    total_staff = s['staff']['tech'] + s['staff']['design'] + s['staff']['marketing']
    office_name = get_office(s)["name"]
    runway, burn, level = compute_runway(s)
    base = (
        f"📊 {s['meta']['company']} ({s['meta']['time']}) | "
        f"🏢 {office_name} | "
        f"💰 {s['finance']['cash']}万 | "
        f"⚡ AP {s['ceo']['ap']}/{s['ceo']['max_ap']} | "
        f"📁 {proj_count}个研发中 | "
        f"👥 {total_staff}人 | "
        f"⭐ {s['finance']['reputation']}"
    )
    if level != "safe":
        base += f" | {level_emoji(level)} 跑路 {runway}月"
    if s.get("meta", {}).get("ipo_status") == "listed":
        base += " | 🏆 已上市"
    return base


def format_panel_finance(state: dict) -> str:
    s = state
    cap = calc_capacity(state)
    office = get_office(s)
    runway, burn, level = compute_runway(s)
    emoji = level_emoji(level)
    warn_line = ""
    if level != "safe":
        warn_line = f"\n{emoji} 跑路警告：现金 {s['finance']['cash']}万 / 月烧 {burn}万 / 还剩 {runway} 个月"
    return (
        f"【财务概览】{s['meta']['company']}\n"
        f"💰 现金：{s['finance']['cash']}万\n"
        f"📉 月固定支出：{s['finance']['fixed_cost']}万\n"
        f"🏢 办公室租金：{office['rent']}万 ({office['name']})\n"
        f"👥 月薪资：{s['staff']['total_salary']}万\n"
        f"🏦 估值：{s['finance']['valuation']}万"
        f"{' 🏆 已上市' if s.get('meta', {}).get('ipo_status') == 'listed' else ''}\n"
        f"⭐ 声誉：{s['finance']['reputation']}\n"
        f"⚡ 月产能：🔧{cap['tech']} 🎨{cap['design']} 📢{cap['marketing']}"
        f"{warn_line}"
    )


def format_panel_team(state: dict) -> str:
    s = state
    total = s['staff']['tech'] + s['staff']['design'] + s['staff']['marketing']
    return (
        f"【团队概览】总人数 {total}\n"
        f"🔧 研发：{s['staff']['tech']}人\n"
        f"🎨 设计：{s['staff']['design']}人\n"
        f"📢 营销：{s['staff']['marketing']}人\n"
        f"💰 月薪总额：{s['staff']['total_salary']}万\n"
        f"👤 CEO 特长：{s['ceo']['trait']}"
    )


def format_panel_project(state: dict) -> str:
    s = state
    if not s["projects"]:
        return "【项目】暂无研发中的项目。使用 /研发 <名称> 启动。"
    lines = ["【项目列表】"]
    completed_revenue = 0
    for p in s["projects"]:
        status = p.get("status", "研发中")
        bar = ascii_progress_bar(p.get("progress", 0), 100, width=10)
        line = f"  📁 {p['name']} | {bar} {p.get('progress', 0)}% | {status}"
        if status == "研发中":
            line += f" | 预计收入 {p.get('revenue', 30)}万"
        else:
            line += f" | 已收入 {p.get('revenue', 30)}万"
            completed_revenue += p.get("revenue", 30)
        lines.append(line)
    if completed_revenue:
        lines.append(f"\n📈 累计项目总收入：{completed_revenue}万")
    return "\n".join(lines)


def format_panel(state: dict, module: str = "") -> str:
    if state.get("phase") == "campus":
        from ..campus.campus import format_campus_status
        return format_campus_status(state)

    if module == "财务":
        return format_panel_finance(state)
    if module == "团队":
        return format_panel_team(state)
    if module == "项目":
        return format_panel_project(state)
    if module == "竞争对手":
        try:
            from ..engine.competitors import format_competitors
            return format_competitors(state)
        except ImportError:
            return "🆚 【竞争对手】\n竞争对手系统未启用。"
    return format_status(state)
