"""校园事件库：15 校园事件 + 4 相亲事件 + 3 富二代暴露事件。"""

import random

# ========= 校园事件 =========

CAMPUS_EVENTS = [
    {
        "id": "hackathon",
        "title": "校园黑客松",
        "desc": "学校举办黑客松比赛，冠军奖金 5 万 + 投资人路演机会",
        "choices": [
            {"text": "全力参赛", "effects": {"tech": 5, "reputation": 10, "savings": 5, "hackathon_win": True}},
            {"text": "派合伙人去应付", "effects": {"reputation": -5}},
            {"text": "不参加，专心产品", "effects": {"savings": 2}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 2,
    },
    {
        "id": "roommate_conflict",
        "title": "室友矛盾",
        "desc": "你的创业吵到了室友，他要求你停止或者搬出去",
        "choices": [
            {"text": "道歉并买隔音棉", "effects": {"savings": -0.2, "network": 3}},
            {"text": "搬到创业孵化器", "effects": {"savings": -0.5, "reputation": 5}},
            {"text": "说服室友加入", "effects": {"has_partner": True, "tech": 3}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 1,
    },
    {
        "id": "professor_offer",
        "title": "导师橄榄枝",
        "desc": "你的专业导师看好你的项目，提出用实验室资源换 5% 股份",
        "choices": [
            {"text": "接受", "effects": {"tech": 10, "equity_loss": 0.05}},
            {"text": "婉拒", "effects": {}},
            {"text": "谈判到 3%", "effects": {"tech": 8, "equity_loss": 0.03, "management": 3}},
        ],
        "condition": lambda s: s.get("campus", {}).get("tech_skill", 0) >= 40,
    },
    {
        "id": "compete_offer",
        "title": "大厂 Offer",
        "desc": "你拿到了某大厂的实习 Offer，月薪 3 万，但会耽误创业",
        "choices": [
            {"text": "拒绝，继续创业", "effects": {"reputation": 10, "network": 5}},
            {"text": "接受，兼职创业", "effects": {"savings": 3, "burn_rate": 0.5}},
            {"text": "谈远程实习", "effects": {"savings": 1.5}},
        ],
        "condition": lambda s: s.get("campus", {}).get("tech_skill", 0) >= 50,
    },
    {
        "id": "dorm_party",
        "title": "宿舍聚餐",
        "desc": "室友们想一起吃个饭，你请客还是AA？",
        "choices": [
            {"text": "请客（收买人心）", "effects": {"savings": -0.3, "network": 5}},
            {"text": "AA制", "effects": {"network": 2}},
            {"text": "不去，写代码", "effects": {"tech": 3, "network": -3}},
        ],
        "condition": lambda s: True,
    },
    {
        "id": "investor_canteen",
        "title": "食堂偶遇投资人",
        "desc": "你在食堂吃着8块钱的套餐，对面坐下来一个投资人...",
        "choices": [
            {"text": "假装在谈几个亿的项目", "effects": {"reputation": 10, "risk": "可能穿帮"}},
            {"text": "坦诚相待，展示产品", "effects": {"network": 15, "has_investor": True}},
            {"text": "赶紧吃完跑路", "effects": {}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 3,
    },
    {
        "id": "library_kicked",
        "title": "图书馆占座",
        "desc": "你为了写代码在图书馆占了8小时的座，结果被管理员赶走...",
        "choices": [
            {"text": "据理力争", "effects": {"reputation": -10, "title": "刺头"}},
            {"text": "认怂道歉", "effects": {}},
            {"text": "转移到咖啡厅", "effects": {"savings": -0.2}},
        ],
        "condition": lambda s: True,
    },
    {
        "id": "mentor_exploit",
        "title": "导师的免费劳动力",
        "desc": "你的导师发现你在创业，让你帮他做一个项目\"练练手\"...",
        "choices": [
            {"text": "答应（换实验室资源）", "effects": {"tech": 5, "months_played": -1}},
            {"text": "委婉拒绝", "effects": {"reputation": -5}},
            {"text": "开价5000", "effects": {"savings": 0.5, "reputation": -3}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 2,
    },
    {
        "id": "roommate_join",
        "title": "室友要加入",
        "desc": "你的室友看到你创业，也想加入...",
        "choices": [
            {"text": "欢迎加入（送20%股份）", "effects": {"has_partner": True, "tech": 3}},
            {"text": "婉拒（\"我一个人能行\"）", "effects": {"network": -10}},
            {"text": "让他先写个Demo试试", "effects": {"tech": 5}},
        ],
        "condition": lambda s: not s.get("campus", {}).get("has_partner", False),
    },
    {
        "id": "pitch_fail",
        "title": "路演翻车",
        "desc": "你在投资人面前做路演，PPT做得很炫但被问到核心数据...",
        "choices": [
            {"text": "硬着头皮编数据", "effects": {"reputation": -20}},
            {"text": "坦诚说还在验证", "effects": {"reputation": 5}},
            {"text": "反问\"你觉得呢？\"", "effects": {"reputation": 10, "risk": "高风险"}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 4,
    },
    {
        "id": "paper_deadline",
        "title": "论文deadline撞产品deadline",
        "desc": "你的毕业论文和产品上线撞期了...",
        "choices": [
            {"text": "先做产品（可能延毕）", "effects": {"tech": 10, "reputation": 5}},
            {"text": "先写论文", "effects": {"reputation": 3}},
            {"text": "两边都做", "effects": {"tech": 3, "reputation": 3, "title": "时间管理大师"}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 20,
    },
    {
        "id": "server_ban",
        "title": "用学校服务器被封IP",
        "desc": "你用学校服务器跑产品，被网管封了IP...",
        "choices": [
            {"text": "认怂道歉", "effects": {"reputation": -3}},
            {"text": "找学校IT部门求情", "effects": {"network": 5}},
            {"text": "自己买云服务器", "effects": {"savings": -1, "tech": 3}},
        ],
        "condition": lambda s: s.get("campus", {}).get("tech_skill", 0) >= 40,
    },
    {
        "id": "thesis_defense",
        "title": "毕业设计就是自己的产品",
        "desc": "你把毕业设计定为自己的创业产品...",
        "choices": [
            {"text": "答辩时被问\"这不就是个Demo吗？\"", "effects": {"reputation": -5, "title": "勇气可嘉"}},
            {"text": "顺利通过", "effects": {"tech": 5, "reputation": 10}},
            {"text": "被要求重做", "effects": {"months_played": -1}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 24,
    },
    {
        "id": "internet Celebrity",
        "title": "创业Vlog火了",
        "desc": "你随手拍的创业日常Vlog在网上火了...",
        "choices": [
            {"text": "继续拍，当网红", "effects": {"reputation": 20, "savings": 2}},
            {"text": "删掉，专注创业", "effects": {"reputation": 5}},
            {"text": "趁热度融资", "effects": {"reputation": 15, "has_investor": True}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 6,
    },
    {
        "id": "compete_copy",
        "title": "竞品抄袭",
        "desc": "有人抄了你的创意，做了一个一模一样的产品...",
        "choices": [
            {"text": "发公开信谴责", "effects": {"reputation": 10}},
            {"text": "加速迭代，甩开他们", "effects": {"tech": 8}},
            {"text": "法律维权（花钱）", "effects": {"savings": -2, "reputation": 5}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 5,
    },
]

# ========= 相亲事件 =========

DATING_EVENTS = [
    {
        "id": "mom_matchmaking",
        "title": "妈妈安排的相亲",
        "desc": "你妈说\"隔壁王阿姨的女儿不错，去见见\"...",
        "choices": [
            {"text": "去相亲", "effects": {"dating": True, "months_played": -1}},
            {"text": "拒绝", "effects": {"reputation": -5}},
            {"text": "说\"等我创业成功再说\"", "effects": {"reputation": -3}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 12,
    },
    {
        "id": "investor_date",
        "title": "相亲对象是投资人",
        "desc": "相亲对象竟然是天使投资人...",
        "choices": [
            {"text": "趁机聊项目", "effects": {"reputation": 10, "has_investor": True}},
            {"text": "认真谈恋爱", "effects": {"dating": True, "network": 10}},
            {"text": "尴尬离场", "effects": {"title": "社恐"}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 18,
    },
    {
        "id": "rich_date",
        "title": "相亲对象是富二代",
        "desc": "相亲对象竟然是富二代...",
        "choices": [
            {"text": "坦白你也是富二代", "effects": {"dating": True, "savings": 10}},
            {"text": "装作普通人", "effects": {"dating": True}},
            {"text": "说\"我们不合适\"", "effects": {"title": "真·独立"}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 20,
    },
    {
        "id": "pushy_parents",
        "title": "被催婚N次",
        "desc": "你已经被催婚超过5次了...",
        "choices": [
            {"text": "找个演员假扮女友", "effects": {"savings": -0.5}},
            {"text": "说\"我已经有女朋友了\"", "effects": {"reputation": 5}},
            {"text": "拉黑妈妈电话", "effects": {"reputation": -10}},
        ],
        "condition": lambda s: s.get("campus", {}).get("months_played", 0) >= 24,
    },
]

# ========= 富二代暴露事件 =========

RICH_KID_EVENTS = [
    {
        "id": "porsche_campus",
        "title": "保时捷停宿舍楼下",
        "desc": "你妈让你周末开保时捷回家，结果停在宿舍楼下被拍了...",
        "choices": [
            {"text": "发朋友圈说是借的", "effects": {"suspicion": 20, "title": "爱面子"}},
            {"text": "赶紧开走不解释", "effects": {"suspicion": 30}},
            {"text": "干脆说是自己的", "effects": {"suspicion": 50, "title": "真·富二代"}},
        ],
        "condition": lambda s: s.get("campus", {}).get("background") == "富二代",
    },
    {
        "id": "mom_soup",
        "title": "妈妈送汤",
        "desc": "你妈开车来给你送汤，被同学看到是劳斯莱斯...",
        "choices": [
            {"text": "跟同学说\"那是我阿姨\"", "effects": {"suspicion": 40}},
            {"text": "坦白身份", "effects": {"reveal": True, "suspicion": 100}},
            {"text": "汤分给同学喝，不解释", "effects": {"suspicion": 20, "network": 5}},
        ],
        "condition": lambda s: s.get("campus", {}).get("background") == "富二代",
    },
    {
        "id": "team_visit",
        "title": "团建去你家",
        "desc": "团队说要去团建，你说\"来我家吧\"...",
        "choices": [
            {"text": "同意（暴露别墅）", "effects": {"reveal": True, "suspicion": 100}},
            {"text": "改去火锅店", "effects": {"savings": -0.5, "suspicion": 10}},
            {"text": "说\"我家太小了\"", "effects": {"suspicion": 30}},
        ],
        "condition": lambda s: s.get("campus", {}).get("background") == "富二代",
    },
]


def get_available_events(state: dict) -> list:
    campus = state.get("campus", {})
    all_events = []

    for e in CAMPUS_EVENTS:
        if e["condition"](state):
            all_events.append(e)

    for e in DATING_EVENTS:
        if e["condition"](state):
            all_events.append(e)

    if campus.get("background") == "富二代" and not campus.get("background_revealed"):
        for e in RICH_KID_EVENTS:
            if e["condition"](state):
                all_events.append(e)

    return all_events


def apply_event_choice(state: dict, event_id: str, choice_idx: int) -> dict:
    campus = state.get("campus", {})
    event = next((e for e in get_available_events(state) if e["id"] == event_id), None)
    if not event:
        return {"ok": False, "msg": "事件不存在或当前不可选"}
    if choice_idx < 0 or choice_idx >= len(event["choices"]):
        return {"ok": False, "msg": "选项无效"}

    choice = event["choices"][choice_idx]
    effects = choice.get("effects", {})

    for key, val in effects.items():
        if key == "tech":
            campus["tech_skill"] = campus.get("tech_skill", 30) + val
        elif key == "marketing":
            campus["marketing_skill"] = campus.get("marketing_skill", 30) + val
        elif key == "management":
            campus["management_skill"] = campus.get("management_skill", 20) + val
        elif key == "reputation":
            campus["reputation"] = campus.get("reputation", 0) + val
        elif key == "savings":
            campus["savings"] = campus.get("savings", 0) + val
        elif key == "network":
            campus["network"] = campus.get("network", 0) + val
        elif key == "has_partner":
            campus["has_partner"] = True
        elif key == "has_investor":
            campus["has_investor"] = True
        elif key == "hackathon_win":
            campus["hackathon_win"] = True
        elif key == "dating":
            campus["dating"] = True
        elif key == "reveal":
            campus["background_revealed"] = True
        elif key == "suspicion":
            campus["suspicion"] = campus.get("suspicion", 0) + val
            if campus["suspicion"] >= 100:
                campus["background_revealed"] = True
        elif key == "title":
            titles = campus.get("titles", [])
            if val not in titles:
                titles.append(val)
            campus["titles"] = titles
        elif key == "months_played":
            campus["months_played"] = campus.get("months_played", 0) + val
        elif key == "equity_loss":
            campus["equity_loss"] = campus.get("equity_loss", 0) + val
        elif key == "burn_rate":
            campus["burn_rate"] = campus.get("burn_rate", 0) + val

    return {"ok": True, "event": event["title"], "choice": choice["text"]}
