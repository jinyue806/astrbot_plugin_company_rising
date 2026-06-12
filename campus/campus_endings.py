"""校园结局库：12 种结局 + 称号系统。"""

import random

# ========= 失败结局 =========

FAILURE_ENDINGS = {
    "real_unemployment": {
        "title": "真·打工人·已婚",
        "desc": "创业失败，你成了真正的打工人。你妈给你安排了相亲，对方说\"有房吗？你说没有。她说\"那我们不合适。你最后娶了隔壁村的小芳，每月工资上交，周末钓鱼。",
        "funny_detail": "你发现隔壁村小芳的爸爸是你的房东。",
        "background": "普通",
    },
    "exam_grind": {
        "title": "考公上岸",
        "desc": "你爸妈说\"当初让你考公你非不听\"，你现在在某县城当公务员，每天朝九晚五，工资3500，稳定得像退休。",
        "funny_detail": "你发现你的科长是你的大学同学。",
        "background": "中产",
    },
    "inherit_fortune": {
        "title": "回家继承家产+结婚",
        "desc": "创业失败，你回家继承了家产。你爸说\"当初不让你创业你非不听\"。你最后娶了联姻对象，生了三个孩子，每天开着保时捷去钓鱼。你最后悔的事是：当初为什么没把公司做大？你最开心的事是：终于不用创业了。",
        "funny_detail": "你发现联姻对象的公司市值比你爸的还大。",
        "background": "富二代",
    },
    "drop_out": {
        "title": "论文逃兵",
        "desc": "你退学创业，最后公司倒闭了，你连毕业证都没有。你发现隔壁班的小明已经当上了CEO，而你连简历都写不出来。",
        "funny_detail": "你发现小明的公司就是你之前实习的那家。",
        "background": "普通",
    },
    "sleep_in_class": {
        "title": "课都不上了",
        "desc": "你为了创业课都不上了，最后学校通知你：再不来上课就退学处理。你发现自己已经挂了8门课...",
        "funny_detail": "你的代课同学比你更了解你的专业。",
        "background": "普通",
    },
    "roommate_betrayal": {
        "title": "合伙人跑路",
        "desc": "你的合伙人带着你的核心代码跑路了，你发现他新公司的产品和你的一模一样。你最后只能看着他成功，自己成了\"创业失败\"的典型案例。",
        "funny_detail": "你发现他新公司的投资人就是你之前拒绝的那个。",
        "background": "普通",
    },
}

# ========= 胜利结局 =========

WIN_ENDINGS = {
    "ipo": {
        "title": "纳斯达克上市",
        "desc": "你的公司成功IPO了！你成了最年轻的CEO。你站在纳斯达克敲钟，背后是你的团队和投资人。你终于实现了梦想！",
        "funny_detail": "你发现敲钟的那个按钮其实是个鼠标垫。",
        "background": "any",
    },
    "funding": {
        "title": "融资成功",
        "desc": "你的公司拿到了B轮融资，估值10亿。你终于可以不用再为钱发愁了。你终于可以安心创业了。",
        "funny_detail": "你发现投资人其实也是你的粉丝。",
        "background": "any",
    },
    "wall_street": {
        "title": "华尔街之狼",
        "desc": "你的公司被大厂收购了，你套现了几个亿。你最后成了投资人，专门投学生项目。你最后悔的事是：当初为什么没把公司做大？",
        "funny_detail": "你发现你投的下一个项目就是你当年的竞品。",
        "background": "any",
    },
    "vlog_star": {
        "title": "创业Vlog博主",
        "desc": "你的创业Vlog火了，你成了百万粉丝博主。你最后发现：当博主比创业轻松多了。你最后悔的事是：当初为什么没早点当博主？",
        "funny_detail": "你发现你最火的视频就是你创业失败的那期。",
        "background": "any",
    },
    "big_company": {
        "title": "大厂offer",
        "desc": "你的创业虽然失败了，但你的经历让你拿到了大厂offer。你最后成了大厂高管，年薪百万。你最后悔的事是：当初为什么没早点进大厂？",
        "funny_detail": "你发现你的面试官就是你当年实习的那家公司的HR。",
        "background": "any",
    },
    "teach_startup": {
        "title": "创业导师",
        "desc": "你成了创业导师，专门教学生做项目。你最后发现：教别人创业比自己创业轻松多了。你最后悔的事是：当初为什么没早点当导师？",
        "funny_detail": "你发现你的学生就是你当年的竞争对手。",
        "background": "any",
    },
}

# ========= 称号系统 =========

TITLES = {
    "画饼大师": {"condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 10, "desc": "连续10个月没赚钱"},
    "路演翻车王": {"condition": lambda s: s.get("campus", {}).get("titles", []).count("路演翻车") >= 3, "desc": "路演翻车3次以上"},
    "论文逃兵": {"condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 12 and s.get("campus", {}).get("background") == "普通", "desc": "创业超过12个月"},
    "时间管理大师": {"condition": lambda s: "时间管理大师" in s.get("campus", {}).get("titles", []), "desc": "两边都做"},
    "真·独立": {"condition": lambda s: "真·独立" in s.get("campus", {}).get("titles", []), "desc": "拒绝相亲对象是富二代"},
    "社恐": {"condition": lambda s: "社恐" in s.get("campus", {}).get("titles", []), "desc": "相亲尴尬离场"},
    "爱面子": {"condition": lambda s: "爱面子" in s.get("campus", {}).get("titles", []), "desc": "保时捷说借的"},
    "真·富二代": {"condition": lambda s: "真·富二代" in s.get("campus", {}).get("titles", []), "desc": "保时捷说是自己的"},
    "勇气可嘉": {"condition": lambda s: "勇气可嘉" in s.get("campus", {}).get("titles", []), "desc": "毕业设计被问\"这不就是个Demo吗？\""},
    "刺头": {"condition": lambda s: "刺头" in s.get("campus", {}).get("titles", []), "desc": "据理力争管理员"},
    "课都不上了": {"condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 6 and s.get("campus", {}).get("tech_skill", 0) >= 60, "desc": "创业6个月以上，技术不错"},
    "保时捷车主": {"condition": lambda s: s.get("campus", {}).get("background") == "富二代" and s.get("campus", {}).get("suspicion", 0) >= 80, "desc": "富二代暴露度80以上"},
    "创业Vlog博主": {"condition": lambda s: s.get("campus", {}).get("titles", []).count("创业Vlog") >= 3, "desc": "拍了3次Vlog"},
    "投资人之友": {"condition": lambda s: s.get("campus", {}).get("has_investor", False) and s.get("campus", {}).get("network", 0) >= 50, "desc": "有投资人且人脉50+"},
    "真·打工魂": {"condition": lambda s: s.get("campus", {}).get("savings", 0) >= 10 and not s.get("campus", {}).get("has_partner", False), "desc": "积蓄10万以上，没合伙人"},
}


def get_unlocked_titles(state: dict) -> list:
    unlocked = []
    campus = state.get("campus", {})
    already = set(campus.get("titles", []))

    for title, info in TITLES.items():
        if title not in already:
            try:
                if info["condition"](state):
                    already.add(title)
                    campus.setdefault("titles", []).append(title)
                    unlocked.append(title)
            except Exception:
                pass

    return list(already)


def format_titles(state: dict) -> str:
    titles = get_unlocked_titles(state)
    if not titles:
        return "🏆 暂无称号\n💡 完成特定成就可解锁称号"
    lines = ["🏆 已解锁称号："]
    for t in titles:
        info = TITLES.get(t, {})
        desc = info.get("desc", "")
        lines.append(f"  · {t}（{desc}）")
    return "\n".join(lines)


def get_ending(state: dict, win: bool) -> dict:
    campus = state.get("campus", {})
    background = campus.get("background", "普通")

    if win:
        available = []
        for eid, info in WIN_ENDINGS.items():
            if info["background"] in ("any", background):
                available.append((eid, info))
        if not available:
            available = [("funding", WIN_ENDINGS["funding"])]
        eid, info = random.choice(available)
        return {"ending": eid, **info}
    else:
        ending_by_background = {
            "普通": "real_unemployment",
            "中产": "exam_grind",
            "富二代": "inherit_fortune",
        }
        eid = ending_by_background.get(background, "real_unemployment")
        return {"ending": eid, **FAILURE_ENDINGS[eid]}


def format_ending(ending: dict) -> str:
    lines = [
        "═" * 40,
        f"{'🎉' if ending.get('type') == 'win' else '💀'} {ending.get('title', '?')}",
        "═" * 40,
        ending.get("desc", ""),
        "",
        f"💡 {ending.get('funny_detail', '')}",
        "═" * 40,
    ]
    return "\n".join(lines)
