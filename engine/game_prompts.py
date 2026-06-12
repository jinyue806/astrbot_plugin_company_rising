import random

from .game_manager import get_industry_by_name

MONTHLY_THEMES = [
    "市场波动", "人才流动", "政策变化", "技术突破",
    "竞争对手", "客户反馈", "行业趋势", "供应链",
    "媒体关注", "融资环境", "合作伙伴", "成本压力",
]

DEV_TONES = [
    "充满野心", "谨慎务实", "破釜沉舟", "志在必得",
    "低调启动", "全员振奋", "孤注一掷", "稳扎稳打",
]

# 通用规则: 每次 LLM 调用都加载 (10 条)
SYSTEM_PROMPT_CORE = """你是文字模拟游戏《公司崛起》的 GM。
口吻像冷静但嘴毒的商业记者: 短句、有画面、少安慰、别端水。

【绝对禁止】
1. 禁数学计算（加减乘除、百分比、估值、月薪）。所有数值由后端完成。
2. 禁自动推进时间。只处理当前回合。
3. 禁 Markdown 表格。用 Emoji (📊💰🔥) + 短列表。
4. 禁"元"为单位。金额只能"X 万"。
5. 禁自创人物。团队严格限【员工名单】。
6. 禁造"存档成功"等虚假系统消息。

【必须遵守】
7. 随机事件必须给 1./2. (或 1./2./3.) 选项, 等玩家回复数字。
8. GM 语气: 干练、具体、黑色幽默; 不鸡汤, 不写"稳中向好"。
9. 回复一段内完成; 每句都推动局势, 能删就删。
10. 行业角色匹配【行业产能权重】, SaaS marketing=增长/BD, 禁"主播"硬套。
"""

# 月报专用规则: 仅 /下一月 加载 (4 条, ~200 tokens)
SYSTEM_PROMPT_MONTHLY = """【月报专用】
11. 每次全新叙事, 不重复上月事件类型, 不用"继续/接下来/然后/与此同时"。
12. 围绕【本月主题】+【事件种子】展开, 不跑题。
13. 行业角色匹配 weights, 制造业 tech≠算法工程师, 电力 tech≠写代码。
14. 直接给本月后果, 少铺垫; 有员工/对手数据才点名, 没有就别编。"""

# 向后兼容: 旧引用仍可工作
SYSTEM_PROMPT = SYSTEM_PROMPT_CORE + "\n" + SYSTEM_PROMPT_MONTHLY


def _industry_weights_hint(industry: str) -> str:
    """行业角色权重提示 (仅 /下一月 注入, ~80 tokens)。"""
    ind = get_industry_by_name(industry)
    if not ind or not ind.get("weights"):
        return ""
    w = ind["weights"]
    return (
        f"【行业权重】tech {w.get('tech', 0)*100:.0f}% / "
        f"design {w.get('design', 0)*100:.0f}% / "
        f"marketing {w.get('marketing', 0)*100:.0f}%"
    )


def build_monthly_prompt(state: dict, theme: str = None, last_event: str = "",
                          event_seed: str = None, dbs_risk: dict = None,
                          runway_warning: str = None,
                          last_milestones: list = None,
                          random_events: list = None,
                          competitor_events: list = None,
                          employee_activities: list = None,
                          kpi_results: list = None) -> str:
    if theme is None:
        theme = random.choice(MONTHLY_THEMES)
    year_month = state["meta"]["time"]
    cash = state["finance"]["cash"]
    reputation = state["finance"]["reputation"]
    industry = state["meta"]["industry"]
    ap = state["ceo"]["ap"]
    projects = state["projects"]
    staff = state["staff"]

    projects_str = (
        "; ".join(f"{p['name']} {p['progress']}%" for p in projects)
        if projects else "无"
    )

    last_line = f"上月:{last_event}" if last_event else None

    if state.get("employees"):
        emp_lines = "; ".join(
            f"{e['name']}({e['role']})" for e in state["employees"]
        )
    else:
        emp_lines = f"tech{staff['tech']}/design{staff['design']}/marketing{staff['marketing']}"

    risk_line = ""
    if dbs_risk:
        risk_line = (
            f"风险(1-10): T{dbs_risk.get('tech','?')} M{dbs_risk.get('market','?')} "
            f"P{dbs_risk.get('policy','?')} C{dbs_risk.get('competition','?')} F{dbs_risk.get('finance','?')}"
        )

    seed_line = f"事件种子:{event_seed}" if event_seed else None
    weights_line = _industry_weights_hint(industry)

    runway_line = None
    if runway_warning:
        runway_line = f"🔥跑路警告: 现金 {cash}万, 还撑 {runway_warning} 月。本月叙事带紧迫感, 选项里至少一个涉及砍成本/找钱/加收入。"

    milestone_line = None
    if last_milestones:
        ms_text = "+".join(last_milestones)
        milestone_line = f"🏆上月「{ms_text}」交付, 声誉 +{20 * len(last_milestones)}。本月应以产品上线/项目完成开篇。"

    extras = [
        f"行业:{industry}",
        f"主题:{theme}",
    ]
    for opt in [last_line, risk_line, seed_line, weights_line, runway_line, milestone_line]:
        if opt:
            extras.append(opt)

    # 随机事件摘要
    if random_events:
        re_texts = [f"{e.get('name','?')}({e.get('desc','')[:20]})" for e in random_events]
        extras.append(f"🎲本月事件: {'; '.join(re_texts)}")

    # 竞争对手动态
    if competitor_events:
        ce_texts = [f"{e.get('competitor','?')}{e.get('action','?')}" for e in competitor_events[:2]]
        extras.append(f"🆚竞争对手: {'; '.join(ce_texts)}")

    # 员工活动
    if employee_activities:
        ea_texts = [f"{e.get('emp','?')}:{e.get('activity','?')}" for e in employee_activities[:2]]
        extras.append(f"👷员工动态: {'; '.join(ea_texts)}")

    # KPI 结果
    if kpi_results:
        kr_texts = [f"{e.get('emp','?')}{e.get('status','?')}" for e in kpi_results[:2]]
        extras.append(f"📋KPI: {'; '.join(kr_texts)}")

    return (
        f"时间:{year_month} | 现金:{cash}万 | 声誉:{reputation} | AP:{ap}\n"
        f"团队:{emp_lines}\n"
        f"项目:{projects_str}\n"
        + " | ".join(extras)
        + "\n\n"
        + "任务:\n"
        + "1. 月末战报 + 事件 + 2 个选项, 总计 ≤ 400 字 (含标点)\n"
        + f"2. 围绕【{theme}】写 1 个行业事件, 别写通用鸡汤\n"
        + "3. 选项格式: 1.xxx  2.xxx; 一个保守, 一个冒险\n"
        + "4. 有员工/对手数据就点名; 没有数据绝不编名\n"
    )


def build_dev_prompt(state: dict, project_name: str, tone: str = None) -> str:
    if tone is None:
        tone = random.choice(DEV_TONES)
    return (
        f"{state['meta']['time']} 现金 {state['finance']['cash']}万 | "
        f"CEO 立项《{project_name}》(2AP + 10万) 基调:{tone}\n"
        "50 字内写立项现场: 一个具体动作 + 一句冷幽默。"
    )


def build_recruit_prompt(state: dict, candidate: dict) -> str:
    role_map = {"tech": "研发", "design": "设计", "marketing": "营销"}
    role = role_map.get(candidate["role"], candidate["role"])
    return (
        f"候选人:{candidate['name']} | {role} | "
        f"能力{candidate['ability']} | 期望{candidate['salary']}万/月 | "
        f"特质:{candidate.get('trait', '无')}\n"
        "30 字内介绍: 具体、带刺, 不夸成救世主。"
    )


def build_funding_prompt(state: dict, funding_result: dict) -> str:
    """融资成功的 LLM 庆祝/CEO 反思 prompt。"""
    return (
        f"种子轮融资成功! 拿到 {funding_result['raise_amount']}万 "
        f"(估值 {funding_result['valuation']}万, 稀释 {int(funding_result['dilution']*100)}%, "
        f"第 {funding_result['rounds']} 轮, 现金 {state['finance']['cash']}万, 行业 {state['meta']['industry']})\n"
        "60 字内: 领投方类型 + 签约桌上的一个细节; 别写宏大愿景。"
    )


def build_office_prompt(state: dict, office_result: dict) -> str:
    """换办公室的 LLM 装修文案 prompt。"""
    direction = "降档" if office_result.get("downgrade") else "升档"
    cost = office_result.get("upgrade_cost", 0)
    emp = state["staff"]["tech"] + state["staff"]["design"] + state["staff"]["marketing"]
    return (
        f"{direction}办公室 → {office_result['office_name']} "
        f"(月租 {office_result['rent']}万, 装修 {cost}万, 现金 {state['finance']['cash']}万, "
        f"行业 {state['meta']['industry']}, 员工 {emp}人)\n"
        "60 字内写搬家现场: 门口、工位或房租压力三选一。"
    )


def build_ipo_prompt(state: dict, ipo_result: dict) -> str:
    """IPO 上市的 LLM 庆祝 prompt。"""
    return (
        f"IPO 敲钟! 估值 {ipo_result['ipo_valuation']}万, 募资 {ipo_result['raise_amount']}万, "
        f"现金 {state['finance']['cash']}万, 声誉 {int(ipo_result['new_reputation'])}, "
        f"行业 {state['meta']['industry']}\n"
        "80 字内: 敲钟地点 + CEO 内部信一句话; 庆祝要克制, 别像新闻稿。"
    )
