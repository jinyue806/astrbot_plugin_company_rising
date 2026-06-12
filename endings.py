GAME_OVER_ENDINGS = [
    (lambda s: s["finance"]["reputation"] >= 100
                and len(s.get("employees", [])) >= 3,
     "🏆 大厂收购结局: 你的产品和团队被腾讯盯上, 开了个 1 亿的 offer。CEO 套现离场, 团队全员入职, 公司并入鹅厂 CDG。Game Over。"),
    (lambda s: s["finance"]["reputation"] >= 50
                and any(p.get("status") == "completed" for p in s.get("projects", [])),
     "🤝 战略合并结局: 你的产品方向被同行看上了, 谈了一轮 strategic merger, 创始人 + 团队都过去当 BU, 独立品牌保留。Game Over。"),
    (lambda s: s["finance"]["cash"] < -10,
     "💀 资金链断裂 + 巨额负债: 投资方撤资, 供应商上门讨债, 银行账户被冻结, 法人被列入失信名单。Game Over。"),
    (lambda s: s["finance"]["reputation"] < 20,
     "📉 口碑崩坏结局: 产品上线被骂上热搜, 客户集体退款, 媒体跟踪报道, 团队集体辞职。Game Over。"),
    (lambda s: True,
     "💀 资金链断裂！公司破产，游戏结束。"),
]
