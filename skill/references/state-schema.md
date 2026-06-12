# 状态 Schema · 传给 LLM 的字段

`state` dict 喂入 `build_*_prompt()` 时, 关键字段:

```python
state = {
    "phase": "campus" | "company",  # 当前阶段

    "meta": {
        "company":    "公司名 (测试公司)",
        "industry":   "行业名 (互联网/SaaS)",
        "time":       "X年Y月 (1年7月)",
        "office":     "A/B/C/D 办公室档",
        "campus_origin": True,  # 是否从校园模式毕业
        "background": "普通/中产/富二代",  # 隐藏背景 (失败时揭晓)
        "last_milestones":     ["上月完成项目名"],
        "_synced_milestone_names": ["已同步到 ontology 的项目名"],
        "_last_funding_idx":   int,  # 月索引, 融资冷却用
        "funding_rounds":      int,
        "ipo_status":          "listed" | None,
        "ipo_time":            "X年Y月",
        "_recent_event_ids":  [str],  # v1.7
        "_event_frequency":   str,  # v1.7
        "competitors": [
            {
                "name": str,
                "ceo": {"name": str, "trait": str, "level": int, "xp": int, "unlocked_talents": [str]},
                "strength": int,
                "aggression": float,
                "market_share": float,
                "cash": float,
                "reputation": int,
            }
        ],  # v1.7 竞争对手, 懒加载生成
        "ipo_pre_valuation":   float,
    },
    "finance": {
        "cash":        float,  # 单位: 万
        "fixed_cost":  float,
        "valuation":   float,
        "reputation":  int,
    },
    "ceo": {
        "ap":      int,  # 行动点 (0-3)
        "max_ap":  int,
        "trait":   "技术领袖" | "商业奇才" | "管理铁腕",
        "xp":      int,  # CEO 经验值
        "level":   int,  # CEO 等级 (1-10)
        "talent_points": int,  # 可用天赋点
        "unlocked_talents": [str],  # 已解锁天赋 ID
    },
    "staff": {
        "tech":          int,
        "design":        int,
        "marketing":     int,
        "total_salary":  float,
    },
    "projects": [
        {"name": str, "progress": int 0-100, "status": "研发中"|"completed"|"已取消", "revenue": float}
    ],
    "employees": [  # 团队白名单 — LLM 叙事严格限这里
        {
            "name": str,
            "role": "tech"|"design"|"marketing",
            "salary": float,
            "ability": int,
            "status": "active"|"fired"|"voluntary"|"auto_resign",
            "loyalty": int,  # 0-100, <20 警告, <10 自动离职
            "kpi": dict | None,  # v1.7 KPI
            "skills": {  # 5 项技能
                "编程": float, "架构": float, ...  # 0-5
            }
        }
    ],
    "campus": {  # 校园模式专用 (phase="campus" 时)
        "background": "普通/中产/富二代",
        "major": "1/2/3",  # 专业选择
        "funding": "1/2/3",  # 旧字段，校园期不再作为凭空启动资金来源
        "direction": "1/2/3",  # 创业方向
        "savings": float,  # 积蓄 (万)
        "reputation": int,  # 声望
        "network": int,  # 人脉
        "has_partner": bool,
        "has_investor": bool,
        "tech_skill": int,  # 技术能力
        "marketing_skill": int,
        "management_skill": int,
        "months_played": int,  # 已过月数
        "hackathon_win": bool,
        "dating": bool,
        "background_revealed": bool,  # 失败时才 True
        "suspicion": int,  # 富二代暴露度 (100=暴露)
        "titles": [str],  # 已解锁称号
        "products": [str],  # 已完成产品
    },

    "facilities": [str],  # v1.7
    "customers": dict,  # v1.7
    "_last_event":     str,  # 月报最后 100 字, 用于下月防重复
    "_last_theme":     str,  # 上月主题
    "_pending":        [dict],  # 候选人待录用
}
```

## 喂 LLM 时的"叙事可见" vs "内部字段"

**可见** (LLM 看到):
- meta.company / industry / time / office / last_milestones
- finance.cash / reputation
- ceo.ap
- staff.tech / design / marketing
- projects[].name / progress / status
- employees[].name / role / status
- _last_event (作为"上月事件")

**不可见** (LLM 拿不到, 防作弊):
- _synced_milestone_names
- _last_funding_idx
- _ontology_ids
- 完整 valuation / fixed_cost (LLM 看 cash 和 rep 就够, 估值不参与叙事)
- _pending (候选人, 录用后才进 employees)
- campus.background (隐藏背景, 失败时才揭晓)
- employees[].loyalty / skills (内部数值, LLM 只通过事件感知)
