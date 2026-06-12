NORMAL_CANDIDATES = [
    {"name": "陈明远", "ability": 82, "role": "tech", "salary": 1.8, "trait": "技术狂热", "loyalty": 70},
    {"name": "赵雪琴", "ability": 78, "role": "tech", "salary": 1.5, "trait": "代码洁癖", "loyalty": 75},
    {"name": "林浩然", "ability": 91, "role": "tech", "salary": 2.5, "trait": "架构师思维", "loyalty": 60},
    {"name": "周鹏飞", "ability": 68, "role": "tech", "salary": 1.2, "trait": "加班狂魔", "loyalty": 80},
    {"name": "吴思远", "ability": 85, "role": "tech", "salary": 2.0, "trait": "技术嗅觉", "loyalty": 65},
    {"name": "郑小曼", "ability": 72, "role": "tech", "salary": 1.3, "trait": "细节控", "loyalty": 85},
    {"name": "孙逸飞", "ability": 95, "role": "tech", "salary": 3.0, "trait": "天才少年", "loyalty": 50},
    {"name": "黄志强", "ability": 62, "role": "tech", "salary": 1.0, "trait": "稳定可靠", "loyalty": 90},
    {"name": "何思颖", "ability": 76, "role": "tech", "salary": 1.6, "trait": "跨界灵感", "loyalty": 72},
    {"name": "马东来", "ability": 88, "role": "tech", "salary": 2.2, "trait": "行业人脉", "loyalty": 55},
    {"name": "李美玲", "ability": 80, "role": "design", "salary": 1.7, "trait": "审美独到", "loyalty": 73},
    {"name": "王子轩", "ability": 86, "role": "design", "salary": 2.1, "trait": "用户洞察", "loyalty": 68},
    {"name": "刘雨桐", "ability": 74, "role": "design", "salary": 1.4, "trait": "手速惊人", "loyalty": 78},
    {"name": "张云帆", "ability": 92, "role": "design", "salary": 2.8, "trait": "艺术嗅觉", "loyalty": 58},
    {"name": "杨小涵", "ability": 70, "role": "design", "salary": 1.2, "trait": "沟通达人", "loyalty": 82},
    {"name": "罗文杰", "ability": 84, "role": "design", "salary": 1.9, "trait": "叙事天才", "loyalty": 66},
    {"name": "徐志明", "ability": 66, "role": "design", "salary": 1.1, "trait": "任劳任怨", "loyalty": 88},
    {"name": "唐小雅", "ability": 90, "role": "design", "salary": 2.4, "trait": "跨界灵感", "loyalty": 62},
    {"name": "冯大伟", "ability": 76, "role": "design", "salary": 1.5, "trait": "行业人脉", "loyalty": 70},
    {"name": "曹思涵", "ability": 69, "role": "design", "salary": 1.2, "trait": "细节控", "loyalty": 85},
    {"name": "宋佳音", "ability": 81, "role": "marketing", "salary": 1.8, "trait": "口才了得", "loyalty": 72},
    {"name": "韩子龙", "ability": 88, "role": "marketing", "salary": 2.3, "trait": "行业人脉", "loyalty": 60},
    {"name": "高小琴", "ability": 74, "role": "marketing", "salary": 1.5, "trait": "谈判高手", "loyalty": 76},
    {"name": "秦少峰", "ability": 93, "role": "marketing", "salary": 3.2, "trait": "商业嗅觉", "loyalty": 52},
    {"name": "顾小白", "ability": 68, "role": "marketing", "salary": 1.2, "trait": "社交媒体达人", "loyalty": 84},
    {"name": "沈嘉豪", "ability": 78, "role": "marketing", "salary": 1.6, "trait": "渠道资源", "loyalty": 70},
    {"name": "许倩倩", "ability": 72, "role": "marketing", "salary": 1.3, "trait": "文案高手", "loyalty": 80},
    {"name": "丁一舟", "ability": 86, "role": "marketing", "salary": 2.0, "trait": "战略眼光", "loyalty": 64},
    {"name": "白雨荷", "ability": 64, "role": "marketing", "salary": 1.0, "trait": "亲和力MAX", "loyalty": 90},
    {"name": "陆子航", "ability": 83, "role": "marketing", "salary": 1.9, "trait": "技术狂热", "loyalty": 68},
]

# 技能初始化 (录用时自动应用)
SKILLS_BY_ROLE = {
    "tech": ["coding", "architecture", "testing", "devops", "security"],
    "design": ["ui", "ux", "research", "prototyping", "accessibility"],
    "marketing": ["sales", "seo", "brand", "content", "analytics"],
}

SKILL_NAMES_CN = {
    "coding": "编程", "architecture": "架构", "testing": "测试", "devops": "运维", "security": "安全",
    "ui": "界面", "ux": "体验", "research": "调研", "prototyping": "原型", "accessibility": "无障碍",
    "sales": "销售", "seo": "SEO", "brand": "品牌", "content": "内容", "analytics": "分析",
}
