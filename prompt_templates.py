"""Prompt 模板系统 — 结构化模板定义 + 兼容函数

架构：
  PromptTemplate  数据类：id, name, content, temperature, max_tokens
  TEMPLATES       模块级注册表
  render()        快捷渲染
  build_*_prompt  与原签名一致的兼容函数（内部调用 render()）

用法：
  from .prompt_templates import render, TEMPLATES
  prompt = render('monthly', time='2026-06', cash=50, ...)
  template = TEMPLATES['dev']  # 拿配置参数
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PromptTemplate:
    """结构化提示词模板"""
    id: str                             # 唯一标识
    name: str                           # 显示名称
    content: str                        # 模板内容（python str.format 风格）
    temperature: float = 0.85           # 默认温度
    max_tokens: int = 500               # 默认最大 token 数
    scene_type: str = ""                # 场景分类：monthly/dev/funding/recruit/office/ipo/consult
    tags: list = field(default_factory=list)  # 标签


# ============================================================
# 模板内容（与 game_prompts.py 原 prompt 完全一致）
# ============================================================

TEMPLATES: dict[str, PromptTemplate] = {}

def _register(t: PromptTemplate):
    TEMPLATES[t.id] = t


_register(PromptTemplate(
    id="monthly",
    name="月报叙事",
    content=(
        "时间:{time} | 现金:{cash}万 | 声誉:{reputation} | AP:{ap}\n"
        "团队:{employees}\n"
        "项目:{projects}\n"
        "{extras}\n\n"
        "任务:\n"
        "1. 月末战报 + 事件 + 2 个选项, 总计 ≤ 400 字 (含标点)\n"
        "2. 围绕【{theme}】写 1 个行业事件, 别写通用鸡汤\n"
        "3. 选项格式: 1.xxx  2.xxx; 一个保守, 一个冒险\n"
        "4. 有员工/对手数据就点名; 没有数据绝不编名\n"
    ),
    temperature=0.85, max_tokens=600,
    scene_type="monthly",
    tags=["monthly", "narrative", "events"],
))

_register(PromptTemplate(
    id="dev",
    name="立项现场",
    content=(
        "{time} 现金 {cash}万 | "
        "CEO 立项《{project}》(2AP + 10万) 基调:{tone}\n"
        "50 字内写立项现场: 一个具体动作 + 一句冷幽默。"
    ),
    temperature=0.7, max_tokens=100,
    scene_type="dev",
    tags=["dev", "project"],
))

_register(PromptTemplate(
    id="recruit",
    name="录用叙事",
    content=(
        "候选人:{name} | {role} | "
        "能力{ability} | 期望{salary}万/月 | "
        "特质:{trait}\n"
        "30 字内介绍: 具体、带刺, 不夸成救世主。"
    ),
    temperature=0.7, max_tokens=80,
    scene_type="recruit",
    tags=["recruit", "employee"],
))

_register(PromptTemplate(
    id="funding",
    name="融资庆祝",
    content=(
        "种子轮融资成功! 拿到 {amount}万 "
        "(估值 {valuation}万, 稀释 {dilution}%, "
        "第 {rounds} 轮, 现金 {cash}万, 行业 {industry})\n"
        "60 字内: 领投方类型 + 签约桌上的一个细节; 别写宏大愿景。"
    ),
    temperature=0.8, max_tokens=150,
    scene_type="funding",
    tags=["funding", "finance"],
))

_register(PromptTemplate(
    id="office",
    name="换办公室",
    content=(
        "{direction}办公室 → {office_name} "
        "(月租 {rent}万, 装修 {cost}万, 现金 {cash}万, "
        "行业 {industry}, 员工 {emp_count}人)\n"
        "60 字内写搬家现场: 门口、工位或房租压力三选一。"
    ),
    temperature=0.7, max_tokens=100,
    scene_type="office",
    tags=["office", "facility"],
))

_register(PromptTemplate(
    id="ipo",
    name="IPO 敲钟",
    content=(
        "IPO 敲钟! 估值 {valuation}万, 募资 {amount}万, "
        "现金 {cash}万, 声誉 {reputation}, "
        "行业 {industry}\n"
        "80 字内: 敲钟地点 + CEO 内部信一句话; 庆祝要克制, 别像新闻稿。"
    ),
    temperature=0.8, max_tokens=150,
    scene_type="ipo",
    tags=["ipo", "finance"],
))

_register(PromptTemplate(
    id="consult",
    name="付费咨询",
    content=(
        "你是商业顾问. 玩家问: 「{question}」\n"
        "公司数据:\n{summary}\n"
        "80 字内给出战略建议, 用 1. 2. 列两点。"
    ),
    temperature=0.6, max_tokens=200,
    scene_type="consult",
    tags=["consult", "strategy"],
))


# ============================================================
# 快捷渲染
# ============================================================

def render(template_id: str, **kwargs) -> str:
    """按 template_id 渲染模板"""
    t = TEMPLATES.get(template_id)
    if not t:
        raise KeyError(f"Unknown template: {template_id}")
    return t.content.format(**kwargs)


# ============================================================
# 兼容函数（与原 game_prompts.py 签名一致，内部调用模板）
# ============================================================

# 将 original_import 所需的符号转发
# from .game_manager import get_industry_by_name  — 保留在 game_prompts.py 中

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

SYSTEM_PROMPT_MONTHLY = """【月报专用】
11. 每次全新叙事, 不重复上月事件类型, 不用"继续/接下来/然后/与此同时"。
12. 围绕【本月主题】+【事件种子】展开, 不跑题。
13. 行业角色匹配 weights, 制造业 tech≠算法工程师, 电力 tech≠写代码。
14. 直接给本月后果, 少铺垫; 有员工/对手数据才点名, 没有就别编。"""

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


def build_monthly_prompt(
    state: dict,
    theme: str = None,
    last_event: str = "",
    event_seed: str = None,
    dbs_risk: dict = None,
    runway_warning: str = None,
    last_milestones: list = None,
    random_events: list = None,
    competitor_events: list = None,
    employee_activities: list = None,
    kpi_results: list = None,
) -> str:
    """生成月报 prompt（保持原签名，内部调用模板）"""
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

    if random_events:
        re_texts = [f"{e.get('name','?')}({e.get('desc','')[:20]})" for e in random_events]
        extras.append(f"🎲本月事件: {'; '.join(re_texts)}")
    if competitor_events:
        ce_texts = [f"{e.get('competitor','?')}{e.get('action','?')}" for e in competitor_events[:2]]
        extras.append(f"🆚竞争对手: {'; '.join(ce_texts)}")
    if employee_activities:
        ea_texts = [f"{e.get('emp','?')}:{e.get('activity','?')}" for e in employee_activities[:2]]
        extras.append(f"👷员工动态: {'; '.join(ea_texts)}")
    if kpi_results:
        kr_texts = [f"{e.get('emp','?')}{e.get('status','?')}" for e in kpi_results[:2]]
        extras.append(f"📋KPI: {'; '.join(kr_texts)}")

    extras_joined = " | ".join(extras)

    return render(
        "monthly",
        time=year_month,
        cash=cash,
        reputation=reputation,
        ap=ap,
        theme=theme,
        employees=emp_lines,
        projects=projects_str,
        extras=extras_joined,
    )


def build_dev_prompt(state: dict, project_name: str, tone: str = None) -> str:
    """立项 prompt（兼容函数）"""
    if tone is None:
        tone = random.choice(DEV_TONES)
    return render(
        "dev",
        time=state["meta"]["time"],
        cash=state["finance"]["cash"],
        project=project_name,
        tone=tone,
    )


def build_recruit_prompt(state: dict, candidate: dict) -> str:
    """录用 prompt（兼容函数）"""
    role_map = {"tech": "研发", "design": "设计", "marketing": "营销"}
    role = role_map.get(candidate["role"], candidate["role"])
    return render(
        "recruit",
        name=candidate["name"],
        role=role,
        ability=candidate["ability"],
        salary=candidate["salary"],
        trait=candidate.get("trait", "无"),
    )


def build_funding_prompt(state: dict, funding_result: dict) -> str:
    """融资 prompt（兼容函数）"""
    return render(
        "funding",
        amount=funding_result["raise_amount"],
        valuation=funding_result["valuation"],
        dilution=int(funding_result["dilution"] * 100),
        rounds=funding_result["rounds"],
        cash=state["finance"]["cash"],
        industry=state["meta"]["industry"],
    )


def build_office_prompt(state: dict, office_result: dict) -> str:
    """换办公室 prompt（兼容函数）"""
    direction = "降档" if office_result.get("downgrade") else "升档"
    emp = state["staff"]["tech"] + state["staff"]["design"] + state["staff"]["marketing"]
    return render(
        "office",
        direction=direction,
        office_name=office_result["office_name"],
        rent=office_result["rent"],
        cost=office_result.get("upgrade_cost", 0),
        cash=state["finance"]["cash"],
        industry=state["meta"]["industry"],
        emp_count=emp,
    )


def build_ipo_prompt(state: dict, ipo_result: dict) -> str:
    """IPO prompt（兼容函数）"""
    return render(
        "ipo",
        valuation=ipo_result["ipo_valuation"],
        amount=ipo_result["raise_amount"],
        cash=state["finance"]["cash"],
        reputation=int(ipo_result["new_reputation"]),
        industry=state["meta"]["industry"],
    )
