# 公司崛起 (astrbot_plugin_company_rising)

> 《公司崛起》文字商业模拟游戏 — 在 IM 中经营你的公司

AstrBot 插件，QQ / 微信 / Webchat 通用。LLM 驱动叙事 + **dbs 5 维商业逻辑** + **ontology 知识图谱** + file-based 存档。

---

## 玩法

注册一家公司 → 每月推进 → 招聘 / 研发 / 应对事件 → 追求估值与声誉，避免现金归零。

### 三步上手

1. `/启动游戏 <公司名> <行业编号> <特长编号>`（先空参数看提示）
2. 每月 `/公司 招聘` 看候选人 + `/公司 研发 <项目名>` 立项
3. `/公司 下一月` 推进时间（**唯一**时间推进入口）

---

## 指令速查

后台可见入口已收敛为 4 个：`/公司`、`/校园`、`/帮助`、`/真状态`。
旧直达命令仍兼容，例如 `/研发`、`/招聘`、`/下一月`、`/startgame`。

| 入口 | 作用 | 常用子命令 |
|---|---|---|
| `/启动游戏` | 直接注册公司 / 显示注册向导 | 兼容直达入口，不占后台可见指令 |
| `/公司` | 公司期操作 | `研发`、`招聘`、`录用`、`下一月`、`状态`、`融资`、`IPO` |
| `/公司` | 低频管理 | `办公室`、`团队`、`KPI`、`加薪`、`设施`、`成就`、`历史`、`重置` |
| `/校园` | 校园筹备期 | `开始`、`打工`、`做产品`、`比赛`、`社交`、`创业` |
| `/帮助` | 完整列表 | — |
| `/真状态` | 管理员 debug 代码真相 | — |

**AP（行动点）**：每月初 3 点，研发 -2，录用 -1。空了就等下月。

## 行业 & CEO 特长

| # | 行业 | dbs 风险画像 | PE 区间 |
|---|---|---|---|
| 1 | 游戏开发 | 竞争 9 极高，市场 8 高 | 15-25x |
| 2 | 互联网/SaaS | 竞争 8 高，市场 7 | 20-35x |
| 3 | 电力/能源 | 政策 9 极高 | 8-15x |
| 4 | 制造业 | 政策 6 竞争 7 | 10-18x |
| 5 | 医疗/生物 | 政策 9 极高，技术 8 | 15-30x |
| 6 | 零售/消费 | 竞争 9 极高，市场 8 | 10-20x |

| # | 特长 | 效果 |
|---|---|---|
| 1 | 技术领袖 | 研发产能 +2，技术突破概率 +20% |
| 2 | 商业奇才 | 谈判估值溢价 +20%，市场推广 +15% |
| 3 | 管理铁腕 | 员工忠诚下限 +20，每回合免费督促 1 次 |

---

## 架构

```
用户指令 (QQ/微信/Webchat)
    ↓
main.py  ← AstrBot 路由 + LLM 调用 + 切块发送
    ├─→ game_manager.py   统一导出游戏逻辑
    ├─→ game_prompts.py   LLM prompt 模板
    ├─→ game_state.py     file-based 持久化 + ontology 同步钩子
    ├─→ storage.py        插件数据目录 helper
    └─→ ontology_bridge.py → ontology skill (subprocess)
```

### dbs 集成说明

dbs 是 100% LLM-prompt 路由，**没有 Python API**。本插件不建 `dbs_bridge.py`，而把 dbs 的"商业模式诊断"思维（5 维风险）手工预焙到 `INDUSTRIES` 里：
- 每月 `next_month` 触发 → 随机选主题 → 从 `INDUSTRIES.dbs_seeds[theme]` 抽 1 个具体种子 → 注入 LLM prompt
- LLM 必须围绕种子展开事件，不能空想

效果：原本"市场波动"主题的随机事件，现在会被钉到"Steam 国区限价令收紧" / "宁德比亚迪跨界储能价格战"这类具体场景。

---

## 文件说明

| 文件 | 职责 | 行数 |
|---|---|---|
| `main.py` | AstrBot 指令路由、LLM 调用、切块发送 |
| `game_manager.py` | 游戏逻辑统一导出 |
| `game_prompts.py` | LLM prompt 模板 |
| `game_state.py` | file-based 状态存取 + ontology 同步钩子 |
| `storage.py` | 插件数据目录 helper |
| `ontology_bridge.py` | 插件 ↔ ontology skill 的 CLI 桥 |
| `metadata.yaml` | AstrBot 插件元数据 | ~14 |
| `docs/best-practices.md` | 从其他 AstrBot 插件沉淀的工程实践 |

---

## 知识图谱

公司 / 员工 / 里程碑 / 事件都同步到 `data/skills/ontology/memory/ontology/graph.jsonl`。

```
Company (comp_xxx)
  ├─ hires → Employee
  ├─ has_milestone → Milestone
  └─ happened_to → GameEvent
```

**Schema**：`Company` / `Employee` / `GameProject` / `Milestone` / `GameEvent`

**同步时机**：每次 `save()` 自动触发（Bug 1 修复后），失败不阻塞游戏。

**查询**：`/记忆` 看完整图谱档案，`/谁 <员工名>` 看具体员工。

---

## 文件存储

- **目录**：`{astrbot_data}/plugin_data/astrbot_plugin_company_rising/`
- **存档**：`{user_id}.json`
- **结局归档**：`endings/{user_id}_{timestamp}.json`
- **路径解析**：`storage.py` 优先使用 AstrBot 官方 `StarTools.get_data_dir()`，失败时回退到历史 `plugin_data` 路径。

> 历史教训：插件自有存档不要依赖 framework KV API；file-based 存储更稳定，框架 KV 留给框架状态。

---

## 工程文档

- [AstrBot 插件工程实践摘记](docs/best-practices.md)

---

## 已知限制

- **dbs 无 Python API**：dbs_seeds 144 条都是手工预焙，加新行业要手动维护
- **30 候选人有限**：无 LLM 补生成
- **跨游戏存档不共享 CEO 特长**：每个存档独立
- **平台图片支持不统一**：`/面板` 目前纯文字，QQ/微信支持图片，webchat 待验证
- **去重阈值 0.75 偏严**：`_is_duplicate` 字符集合重合 > 0.75 直接丢弃，可能误杀短回复
- **降档不退押金**：换更低档办公室不退款，避免刷钱；但声誉加成不会回扣

## 跑路警告

`compute_runway(state)` 实时算 `cash / monthly_burn`，三档显示：

| Level | 触发 | 表现 |
|---|---|---|
| `safe` | > 3 月 | 无标记 |
| `yellow` | 1-3 月 | `⚠️ 跑路 X月` + 月报带紧迫感 |
| `red` | ≤ 1 月 | `🔴 跑路 X月` + 月报带强烈紧迫感 + 选项里必有"砍成本/找钱/加收入" |
| `dead` | ≤ 0 | 破产（game_over） |

`monthly_burn = fixed_cost + office_rent + total_salary`，不含项目一次性投入。**这意味着**：元宝集团（cash 8 万 / 2 员工 / A 城中村）当前 2.7 月跑路，月报会标 ⚠️ 并强制 LLM 给出涉及"砍/找/加"的选项。

## 办公室系统（4 档）

| 档 | 名称 | 月租(万) | 容量+ | 声誉+ | 招聘+ | 适合度 |
|---|---|---|---|---|---|---|
| A | 城中村共享工位 | 0.05 | 0 | 0 | 0% | 凑合 |
| B | 联合办公空间 | 0.35 | +1 | 0 | +5% | 标准 |
| C | 科技园孵化器 | 0.20 | +1 | +5 | +10% | **进阶（推荐）** |
| D | 甲级写字楼 | 1.20 | +3 | +10 | +15% | 豪华（烧钱） |

**升档装修费** = (新档 tier − 旧档 tier) × 0.4 万（A→C 装修 0.8 万，A→D 装修 1.2 万）。
**降档**：0 装修费，押金不退，声誉加成不回扣（防刷钱）。

---

## 路线图

- [x] **Phase 1: dbs 商业骨架** — 5 维风险 + 144 事件种子（2026-06-07）
- [x] **Phase 1.5: 融资 / 跑路警告 / 办公室** — `/融资` + 4 档跑路表盘 + 4 档办公室（2026-06-07）
- [x] **Phase 1.6: 上市 / 业绩里程碑 / 主题偏好** — `/IPO` + 项目 rep+20 + yellow 偏融资（2026-06-07）
- [ ] **Phase 2: ontology 完整化** — 每月自动创建 Milestone + GameEvent；员工离职/辞退同步
- [ ] **Phase 3: novel-agent 三段式叙事** — 月报从单段变 setup → conflict → choice
- [ ] **Phase 4: ian-xiaohei 月报配图** — 根据盈亏自动选视觉主题
- [ ] **Phase 5: 自我进化** — `/反馈` + self-improving 学习，越玩越懂你
- [ ] **二期功能**：自定义行业 / LLM 补候选人

详见 [enhancement-plan.md](../company-rising-enhancement-plan.md)。

---

## 开发 / 调试

```bash
# 语法 check
python -c "import ast; [ast.parse(open(f, encoding='utf-8').read()) for f in ['main.py','game_manager.py','game_prompts.py','game_state.py','ontology_bridge.py','candidates.py']]"

# 测 dbs 注入
python -c "import sys; sys.path.insert(0, '.'); from game_prompts import build_monthly_prompt; from game_manager import get_industry_by_name; g = get_industry_by_name('游戏开发'); print(build_monthly_prompt({'meta':{'company':'X','industry':'游戏开发','time':'1年1月'},'finance':{'cash':50,'reputation':0},'ceo':{'ap':3},'projects':[],'staff':{'tech':0,'design':0,'marketing':0}}, theme='市场波动', event_seed='Steam 国区限价令收紧', dbs_risk=g['dbs_risk']))"

# 查 ontology 图谱大小
wc -l ../data/skills/ontology/memory/ontology/graph.jsonl
```

### 加新行业

在 `game_manager.INDUSTRIES` 加一条：
```python
"7": {
    "name": "新行业",
    "weights": {"tech": 0.4, "design": 0.3, "marketing": 0.3},
    "pe_min": 10, "pe_max": 20,
    "dbs_risk": {"tech": 5, "market": 5, "policy": 5, "competition": 5, "finance": 5},
    "dbs_seeds": {
        "市场波动": ["种子 1", "种子 2"],
        "人才流动": [...],
        # 必须覆盖全部 12 个主题
    },
},
```

---

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)

---

## 文件结构

```
astrbot_plugin_company_rising/
├── skill/                  AI GM 行为指令
│   ├── SKILL.md
│   ├── nano.md
│   └── references/
├── docs/                   文档
│   ├── README.md
│   ├── CHANGELOG.md
│   ├── 更新记录.md
│   └── best-practices.md
├── engine/                 游戏核心
│   ├── game_manager.py     核心逻辑 + 模块路由
│   ├── game_state.py       游戏状态读写
│   ├── game_prompts.py     LLM 提示词
│   ├── advance_month.py    时间推进
│   ├── events.py           事件检测
│   ├── projects.py         项目管理
│   ├── competitors.py      竞争对手
│   └── random_events.py    随机事件
├── company/                公司经营
│   ├── ceo.py              CEO 系统 / 天赋
│   ├── finance.py          财务 / 融资 / IPO
│   ├── employee.py         员工基类
│   ├── employee_management.py  员工深度管理
│   ├── recruit.py          招聘
│   ├── customers.py        客户
│   ├── candidates.py       候选人生成
│   └── achievements.py     成就
├── campus/                 校园模式
│   ├── campus.py           主逻辑
│   ├── campus_events.py    事件
│   └── campus_endings.py   结局
├── llm/                    AI 服务
│   ├── llm_service.py      LLM 调用封装
│   ├── prompt_templates.py 提示词模板
│   └── ontology_bridge.py  知识图谱桥接
├── utils/                  工具库
│   ├── formatting.py       格式化展示
│   ├── storage.py          文件存储
│   ├── utils.py            通用工具函数
│   ├── constants.py        常量
│   ├── endings.py          游戏结束结局
│   └── ending_archive.py   结局归档
├── __init__.py             插件入口 + 自动部署
├── main.py                 主入口（事件路由 + 指令处理）
├── metadata.yaml           插件元数据
├── _conf_schema.json       配置 schema
├── pyproject.toml          项目配置
└── .gitignore
```
