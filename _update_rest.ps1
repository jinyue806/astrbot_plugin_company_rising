$skillDir = "\\192.168.5.66@5005\DavWWWRoot\JY\docker\AstrBot\data\skills\company-rising"
$pluginDir = "\\192.168.5.66@5005\DavWWWRoot\JY\docker\AstrBot\data\plugins\astrbot_plugin_company_rising"

# ===== state-schema.md: add new fields =====
$ss = Get-Content "$skillDir\references\state-schema.md" -Encoding UTF8 -Raw
$newFields = @"

    "competitors": [  # v1.7 竞争对手
        {
            "name": str,
            "ceo": {"name": str, "trait": str, "level": int, "xp": int, "unlocked_talents": [str]},
            "strength": int, "aggression": float, "market_share": float,
            "cash": float, "reputation": int,
        }
    ],
    "facilities": [str],  # v1.7 已建设施 (食堂/健身房/HR/法务/秘书/茶水间/游戏室)
    "customers": {  # 客户数据
        "count": int, "arr_per_customer": float, "churn_rate": float,
        "growth_rate": float, "history": [(str, int)],
    },
"@
# Insert before "_last_event"
$ss = $ss -replace '    "_last_event":', "$newFields`n    `"_last_event`":"
# Add employee kpi field
$ss = $ss -replace '"skills": \{', "`"kpi`": dict | None,  # v1.7 KPI 数据`n            `"skills`": {"
# Add meta fields
$metaNew = @"
        "_recent_event_ids":  [str],  # v1.7 近 6 月事件ID防重
        "_event_frequency":   "关闭|低频|标准|高频",  # v1.7 事件频率
"@
$ss = $ss -replace '        "ipo_pre_valuation":', "$metaNew`n        `"ipo_pre_valuation`":"
[System.IO.File]::WriteAllText("$skillDir\references\state-schema.md", $ss, [System.Text.Encoding]::UTF8)
Write-Host "state-schema.md updated"

# ===== traceability.md: add new system mappings =====
$traceAdd = @"

## v1.7 新系统 -> 代码

| 系统 | 文件 | 核心函数 |
|---|---|---|
| 随机事件 (28个) | ``random_events.py`` | ``roll_monthly_event()``, ``_apply_event()`` |
| 竞争对手 (CEO天赋/难度) | ``competitors.py`` | ``init_competitors()``, ``advance_competitors()``, ``_apply_competitor_action()`` |
| 员工 KPI | ``employee_management.py`` | ``set_kpi()``, ``evaluate_kpis()`` |
| 员工活动 (20种整活) | ``employee_management.py`` | ``roll_employee_activities()``, ``_apply_activity()`` |
| 加薪系统 | ``employee_management.py`` | ``check_salary_demands()``, ``give_raise()``, ``handle_salary_demand()`` |
| 公司设施 (7种) | ``employee_management.py`` | ``buy_facility()``, ``apply_facilities()``, ``get_facility_effects()`` |
| 数值平衡 | ``advance_month.py`` | 声誉衰减, 收入递减, 规模管理费 |
| 天赋补全 | 各文件 | 15/21 空转天赋效果落地 |
"@
Add-Content "$skillDir\references\traceability.md" -Value $traceAdd -Encoding UTF8
Write-Host "traceability.md updated"

# ===== nano.md: update state summary =====
$nano = Get-Content "$skillDir\nano.md" -Encoding UTF8 -Raw
$nano = $nano -replace '- 团队: CEO\(AP 3/3\) \+ tech/design/marketing 计数 \+ 员工白名单\(含忠诚度/技能\)', '- 团队: CEO(AP 3/3) + tech/design/marketing 计数 + 员工白名单(含忠诚度/技能/KPI)'
$nano = $nano -replace '- 项目: 名称 \+ 进度 \+ 状态 \+ 预计收入', "- 项目: 名称 + 进度 + 状态 + 预计收入`n- 竞争对手: 名称/CEO特长等级/实力/市场份额`n- 设施: 食堂/健身房/HR/法务/秘书/茶水间/游戏室"
$nano = $nano -replace '- 28 指令', '- 33 指令'
$nano = $nano -replace '28 指令: references/commands.md', '33 指令: references/commands.md'
[System.IO.File]::WriteAllText("$skillDir\nano.md", $nano, [System.Text.Encoding]::UTF8)
Write-Host "nano.md updated"

# ===== SKILL.md: add rule 9 =====
$skill = Get-Content "$skillDir\SKILL.md" -Encoding UTF8 -Raw
$skill = $skill -replace '## 8 条铁律', '## 9 条铁律'
$skill = $skill -replace '8\. \*\*校园期必\*\*在毕业倒计时时提醒玩家时间紧迫', "8. **校园期必**在毕业倒计时时提醒玩家时间紧迫`n9. **必**在月报中引用具体员工名和竞争对手动态，不能只说'某员工'或'某对手'"
[System.IO.File]::WriteAllText("$skillDir\SKILL.md", $skill, [System.Text.Encoding]::UTF8)
Write-Host "SKILL.md updated"

# ===== _conf_schema.json: add new config items =====
$conf = Get-Content "$pluginDir\_conf_schema.json" -Encoding UTF8 -Raw
$newConf = $conf.TrimEnd("}`n") + @",
  "event_frequency": {
    "type": "string",
    "description": "随机事件频率",
    "hint": "每月随机事件的触发频率。关闭=无事件，低频=50%概率，标准=正常，高频=1.5倍。",
    "default": "标准",
    "options": ["关闭", "低频", "标准", "高频"]
  },
  "competitor_enabled": {
    "type": "bool",
    "description": "启用竞争对手系统",
    "hint": "启用后会有 1-3 个竞争对手（根据难度），每月行动影响玩家。",
    "default": true
  },
  "kpi_enabled": {
    "type": "bool",
    "description": "启用员工 KPI 系统",
    "hint": "启用后可以用 /KPI 给员工设定考核目标，月度自动评估。",
    "default": true
  }
}
"@
[System.IO.File]::WriteAllText("$pluginDir\_conf_schema.json", $newConf, [System.Text.Encoding]::UTF8)
Write-Host "_conf_schema.json updated"

# ===== pyproject.toml: version bump =====
$toml = Get-Content "$pluginDir\pyproject.toml" -Encoding UTF8 -Raw
$toml = $toml -replace 'version = "1\.6\.0"', 'version = "1.7.0"'
[System.IO.File]::WriteAllText("$pluginDir\pyproject.toml", $toml, [System.Text.Encoding]::UTF8)
Write-Host "pyproject.toml updated"

Write-Host "All skill/config/version files updated!"
