# AstrBot 插件工程实践摘记

本文记录 `data/plugins/` 中其他插件值得借鉴的做法，并标注《公司崛起》的采用状态。目标是沉淀长期工程规范，不替代玩家文档。

通用插件开发参考见：`../../PLUGIN_BEST_PRACTICES.md`。

## 已采用

### 命令组作为兼容入口

- 来源：`astrbot_plugin_livingmemory` 的 `/lmem ...`，`astrbot_plugin_essentials` 的 `/permission ...` / `/economy ...`。
- 可学点：复杂插件不要只堆顶级命令；命令组能把管理入口、主流程入口和兼容别名组织起来。
- 公司崛起状态：暂不采用。游戏命令已经偏多，新增低使用率命令组会增加页面噪音；继续保留现有中文顶级命令和少量英文 alias。

### 插件数据目录 helper

- 来源：`astrbot_plugin_history` 和 `astrbot_plugin_file_reader_pro` 都优先尝试官方数据目录 API，再回退到 `plugin_data`。
- 可学点：避免每个模块各自拼路径；框架 API 变动时只改一个 helper。
- 公司崛起采用：新增 `storage.py`，统一提供 `get_plugin_data_dir()` 和 `get_plugin_subdir()`，保持原存档目录不变。

### 生命周期清理

- 来源：`astrbot_plugin_livingmemory` 会取消后台任务，`astrbot_plugin_history` 会停止 WebUI。
- 可学点：插件停用时必须显式清理后台资源，避免重载后重复任务。
- 公司崛起采用：当前只清理 `_last_responses`。后续如果引入后台任务或 WebUI，必须在 `terminate()` 中关闭。

## 后续考虑

### 配置 schema 分组

- 来源：`astrbot_plugin_livingmemory`、`astrbot_plugin_self_learning`、`astrbot_plugin_essentials` 使用嵌套 object 分组。
- 可学点：配置数量上来后，按“基础玩法 / LLM / 员工 / 竞争 / 调试”分组更适合 WebUI。
- 公司崛起状态：暂不采用。当前保持平铺键，避免破坏已有配置；以后做大版本时再迁移。

### WebUI 或页面 API

- 来源：`astrbot_plugin_history` 提供 WebUI 浏览，`astrbot_plugin_self_learning` 注册插件页面。
- 可学点：数据量大的插件适合提供只读后台页面。
- 公司崛起状态：后续考虑做存档/结局录/公司面板 WebUI；本次不做。

### 事件钩子能力

- 来源：`astrbot_plugin_history` 使用消息和回复事件备份，`astrbot_plugin_context_undo` 使用 LLM 请求/响应钩子。
- 可学点：事件钩子适合做横切能力，不适合替代核心命令。
- 公司崛起状态：暂不采用。游戏状态变更必须仍由明确命令触发，避免玩家误操作。

### 自然语言触发

- 来源：`astrbot_plugin_context_undo` 支持“撤回/回滚”等口语触发。
- 可学点：高频、低歧义操作可以支持自然语言。
- 公司崛起状态：后续可以考虑“开公司”等低歧义触发；高风险操作仍必须保留明确命令。

## 不采用

### 过大的单文件主类

- 来源：部分插件将所有逻辑集中在一个 `main.py`。
- 风险：命令、业务、存储、LLM 调用混在一起，后期回归成本高。
- 公司崛起决策：继续保持业务模块拆分；本次只加轻量 wrapper，不继续复制业务逻辑进 `main.py`。

### 自动安装重依赖

- 来源：部分复杂插件有大量外部依赖或手动安装入口。
- 风险：游戏插件不应因为辅助功能阻塞核心玩法。
- 公司崛起决策：保持 stdlib 优先；可选能力失败时回退，不阻塞游戏。
