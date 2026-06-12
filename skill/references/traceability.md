# Traceability · 规则到代码

> 只记录文件和函数，不写行号。`main.py` 和游戏模块仍在快速变化，行号很容易过期。

## LLM 边界与文案

| 规则 | 落地 |
|---|---|
| 禁数学计算、禁推时间、禁 Markdown 表格、禁元单位、禁自创人物 | `game_prompts.py` 的 `SYSTEM_PROMPT_CORE` |
| 月报防循环、不跑题、不复读玩家操作 | `game_prompts.py` 的 `SYSTEM_PROMPT_MONTHLY` |
| 行业角色匹配 | `game_prompts.py` 的 `_industry_weights_hint()` 和 `build_monthly_prompt()` |
| 员工白名单 | `game_prompts.py` 的 `build_monthly_prompt()` 读取 `state["employees"]` |
| 反 AI 腔、GM 短句黑色幽默 | `game_prompts.py` prompt 文案 + `SKILL.md` / `nano.md` |
| LLM 失败回退 | `main.py` 的 `_llm_chat()` 调用方回退到 `format_status()` 等后端文本 |
| 数据事实 footer | `main.py` 的 `_data_footer()` |

## 路由层

| 指令组 | 落地 |
|---|---|
| 注册、研发、招聘、录用、推进、状态、面板 | `main.py` 的 `start_game()` / `dev()` / `recruit_cmd()` / `hire()` / `next_month()` / `status()` / `panel()` |
| 融资、IPO、办公室 | `main.py` 的 `funding_cmd()` / `ipo_cmd()` / `change_office_cmd()` |
| CEO 天赋 | `main.py` 的 `talent_cmd()`，`ceo.py` |
| 员工深度 | `main.py` 的 `team_cmd()` / `loyalty_cmd()` / `resign_cmd()` / `fire_cmd()` / `skills_cmd()` |
| v1.7 员工管理 | `main.py` 的 `kpi_cmd()` / `give_raise_cmd()` / `attendance_cmd()` / `facility_cmd()`，`employee_management.py` |
| 付费咨询 | `main.py` 的 `consult()` |
| 校园模式 | `main.py` 的 `start_campus()` / `register_company()` / `part_time()` / `make_product()` / `competition()` / `network_cmd()` / `find_partner_cmd()` / `dating()` / `choose_event()` |
| 结局归档 | `main.py` 的 `endings_list_cmd()` / `review_ending_cmd()`，`ending_archive.py` |
| 图谱查询 | `main.py` 的 `company_memory()` / `whois()`，`ontology_bridge.py` |

## 游戏状态与持久化

| 行为 | 落地 |
|---|---|
| 默认公司状态 | `game_state.py` 的 `DEFAULT_STATE` |
| 默认校园状态 | `game_state.py` 的 `CAMPUS_DEFAULT` |
| mutable default 隔离 | `game_state.py` 的 `GameState.__init__()` 和 `reset()` 使用 `copy.deepcopy()` |
| file-based 存储 | `game_state.py` 的 `_read_file()` / `_write_file()` / `load()` / `save()` / `delete()` |
| 本体同步开关 | `main.py` 的 `_sync_runtime_config()` 写 `meta._ontology_sync_enabled`，`game_state.py` 的 `save()` 消费 |
| 旧存档兼容 | 新模块通过 `setdefault()` 和 `.get()` 访问新增字段 |

## 公司期核心系统

| 系统 | 落地 |
|---|---|
| 月份推进 | `advance_month.py` 的 `advance_month()`，`utils.py` 的 `increment_month()` |
| 跑路计算 | `finance.py` 的 `compute_runway()` |
| 融资 | `finance.py` 的 `raise_funding()` |
| IPO | `finance.py` 的 `list_company()` |
| 办公室 | `finance.py` 的 `change_office()`，`constants.py` 的 `OFFICE_TYPES` |
| 项目研发、取消、产能 | `projects.py` 的 `start_dev()` / `cancel_project()` / `calc_capacity()` |
| 客户和 ARR | `customers.py` 的 `update_customers()` |
| 成就 | `achievements.py` 的 `check_achievements()` / `unlock_achievements()` / `format_achievements()` |
| 失败结局 | `endings.py` 的 `GAME_OVER_ENDINGS` |
| 历史日志 | `formatting.py` 的 `format_history()`，`advance_month.py` 写 `state["log"]` |

## v1.7 深度系统

| 系统 | 落地 |
|---|---|
| 天赋消费端 | `projects.py` / `finance.py` / `employee.py` / `customers.py` / `advance_month.py` |
| 数值防膨胀 | `advance_month.py` 的声誉衰减、项目收入递减、规模管理费；`customers.py` 的增长衰减 |
| 随机事件 | `random_events.py` 的 `roll_monthly_event()` / `_apply_event()` |
| 竞争对手 | `competitors.py` 的 `init_competitors()` / `advance_competitors()` / `format_competitors()` |
| 员工忠诚、技能、离职 | `employee.py` |
| KPI、加薪、设施、员工活动 | `employee_management.py` |
| 配置项同步 | `main.py` 的 `_sync_runtime_config()` |

## 校园模式

| 系统 | 落地 |
|---|---|
| 隐藏背景、晋升、校园操作 | `campus.py` |
| 校园事件和相亲 | `campus_events.py` |
| 校园结局和称号 | `campus_endings.py` |
| 校园转公司 | `campus.py` 的 `campus_to_company()`，`main.py` 的 `register_company()` |

## 测试与校验

| 目标 | 落地 |
|---|---|
| 静态校验 | `bench/validate_plugin.py` |
| 动态回归 | `bench/run_evals.py` |
| PowerShell UTF-8 包装 | `bench/run_unicode.ps1` |
| token 基线 | `bench/baseline.py` / `bench/after.py` / `bench/baseline.md` |
