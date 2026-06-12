import json
import random

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .candidates import NORMAL_CANDIDATES
from .game_manager import (
    ACHIEVEMENTS,
    CEO_TRAITS,
    INDUSTRIES,
    OFFICE_TYPES,
    advance_month,
    cancel_project,
    change_office,
    compute_runway,
    detect_easter_egg,
    format_achievements,
    format_history,
    format_panel,
    format_status,
    get_industry_by_name,
    get_office,
    level_emoji,
    list_company,
    raise_funding,
    recruit,
    start_dev,
    unlock_achievements,
    gain_xp,
    unlock_talent,
    get_available_talents,
    format_ceo_panel,
)
from .employee import (
    format_all_employees,
    format_employee,
    fire_employee,
    resignation_negotiate,
    adjust_loyalty,
    decay_loyalty,
    grow_skills,
    init_skills,
    check_auto_resignations,
    SKILLS_BY_ROLE,
    SKILL_NAMES_CN,
)
from .prompt_templates import (
    DEV_TONES,
    MONTHLY_THEMES,
    SYSTEM_PROMPT_CORE,
    SYSTEM_PROMPT_MONTHLY,
    build_dev_prompt,
    build_funding_prompt,
    build_ipo_prompt,
    build_monthly_prompt,
    build_office_prompt,
    build_recruit_prompt,
)
from .game_state import GameState
from .ontology_bridge import OntologyBridge, _run_onto, cmd_history
from .llm_service import LLMService, LLMRequest


class _RoutedEvent:
    def __init__(self, event: AstrMessageEvent, message_str: str):
        self._event = event
        self.message_str = message_str
        if hasattr(event, "unified_msg_origin"):
            self.unified_msg_origin = event.unified_msg_origin

    def __getattr__(self, name):
        return getattr(self._event, name)


@register("astrbot_plugin_company_rising", "YourName", "《公司崛起》文字商业模拟游戏", "v1.8.0")
class CompanyRisingPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        self.llm = LLMService(context, config)
        self.system_prompt = SYSTEM_PROMPT_CORE

    async def terminate(self):
        """插件卸载/停用时清理资源"""
        self.llm.clear()

    def _cfg(self, key: str, default=None):
        return self.config.get(key, default)

    def _cfg_bool(self, key: str, default: bool = True) -> bool:
        value = self._cfg(key, default)
        if isinstance(value, str):
            return value.lower() not in ("false", "0", "no", "off", "关闭", "否")
        return bool(value)

    def _cfg_int(self, key: str, default: int) -> int:
        try:
            return int(self._cfg(key, default))
        except (TypeError, ValueError):
            return default

    def _sync_runtime_config(self, state: dict, reset_ap: bool = False) -> None:
        meta = state.setdefault("meta", {})
        meta["_event_frequency"] = self._cfg("event_frequency", "标准")
        meta["_competitor_enabled"] = self._cfg_bool("competitor_enabled", True)
        meta["_kpi_enabled"] = self._cfg_bool("kpi_enabled", True)
        meta["_achievements_enabled"] = self._cfg_bool("enable_achievements", True)
        meta["_employee_skills_enabled"] = self._cfg_bool("enable_employee_skills", True)
        meta["_ontology_sync_enabled"] = self._cfg_bool("enable_ontology_sync", True)
        if state.get("phase") == "campus":
            state["ceo"] = {
                "ap": 0,
                "max_ap": 0,
                "trait": "",
                "xp": 0,
                "level": 0,
                "talent_points": 0,
                "unlocked_talents": [],
            }
            return
        max_ap = max(1, self._cfg_int("default_ap", 3))
        state.setdefault("ceo", {})["max_ap"] = max_ap
        if reset_ap:
            state["ceo"]["ap"] = max_ap

    @property
    def _monthly_system_prompt(self) -> str:
        return SYSTEM_PROMPT_CORE + "\n" + SYSTEM_PROMPT_MONTHLY

    def _chunk_text(self, text: str, max_chars: int = None) -> list[str]:
        """将长文本切块，返回字符串列表（不再 yield，兼容 async 环境）。"""
        if max_chars is None:
            max_chars = self._cfg("chunk_max_chars", 1500)
        if not text:
            return []
        chunks = []
        remaining = text.strip()
        while len(remaining) > max_chars:
            cut = remaining.rfind("\n", 0, max_chars)
            if cut < max_chars // 2:
                cut = remaining.rfind("。", 0, max_chars)
            if cut < max_chars // 2:
                cut = remaining.rfind("，", 0, max_chars)
            if cut < max_chars // 2:
                cut = max_chars
            else:
                cut += 1
            chunk = remaining[:cut].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[cut:].strip()
        if remaining:
            chunks.append(remaining)
        return chunks

    async def _llm_chat(self, prompt: str, event: AstrMessageEvent = None, dedup_key: str = None, system_prompt: str = None, state: dict = None) -> str:
        """LLM 调用（委托给 LLMService，签名扩展了 state 参数）"""
        sid = event.unified_msg_origin if event else None
        scene_overrides = state.get("meta", {}).get("_scene_config", {}) if state else {}
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt or self.system_prompt,
            temperature=self.llm.get_temperature_for(dedup_key, scene_overrides),
            max_tokens=self.llm.get_max_tokens_for(dedup_key, scene_overrides),
            session_id=sid,
        )
        try:
            if dedup_key:
                return await self.llm.chat_blocked(request, dedup_key)
            return await self.llm.chat(request)
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return ""

    def _data_footer(self, state: dict) -> str:
        """生成代码真相 footer, 拼在 LLM 月报后, 玩家永远看到真实数据。
        反幻觉 (防 LLM 编团队人数/金额/状态/客户数)。
        """
        finance = state.get("finance", {})
        meta = state.get("meta", {})
        cash = finance.get("cash", 0)
        rep = finance.get("reputation", 0)
        valuation = finance.get("valuation", 0)
        employees = state.get("employees", [])
        proj_total = len(state.get("projects", []))
        proj_done = sum(1 for p in state.get("projects", []) if p.get("status") == "completed")
        milestones = meta.get("last_milestones", [])
        runway_months = compute_runway(state)
        level = runway_months[2]
        cust = state.get("customers", {})
        cust_count = cust.get("count", 0)
        arr = round(cust_count * cust.get("arr_per_customer", 0.5), 2)
        cust_line = ""
        if cust_count > 0:
            cust_line = f"\n  👤 客户 {cust_count} | 💵 ARR {arr}万/年 ({round(arr/12, 2)}万/月) | 📉 流失 {int(cust.get('churn_rate', 0)*100)}%"
        return (
            "📊 数据事实 (代码核对 · 非 LLM 叙事):\n"
            f"  💰 现金 {cash:.1f}万 | ⭐ 声誉 {rep} | 💎 估值 {valuation:.0f}万\n"
            f"  👥 团队 {len(employees)+1}人 (CEO+{len(employees)}员工) | 🏢 {meta.get('office', '?')}"
            + cust_line + "\n"
            f"  📁 项目 {proj_done}/{proj_total} 完成"
            + (f" | 🏆 本月完成: {','.join(milestones)}" if milestones else "")
            + f" | {level_emoji(level)} 跑路 {runway_months[0]}月"
        )

    async def _get_gs(self, event: AstrMessageEvent) -> GameState:
        gs = GameState(self.context, event.get_sender_id())
        await gs.load()
        self._sync_runtime_config(gs.state)
        return gs

    def _company_phase_error(self, state: dict) -> str | None:
        if state.get("phase") != "campus":
            return None
        return (
            "⚠️ 还在校园筹备期，不能使用公司期指令。\n"
            "用 /校园 打工 /校园 做产品 /校园 比赛 /校园 社交 积累资源；条件成熟后用 /校园 创业 <公司名> <行业> 注册公司。"
        )

    async def _finish_campus_if_ended(self, gs: GameState, event: AstrMessageEvent) -> str | None:
        from .campus import check_win_lose
        result = check_win_lose(gs.state)
        if not result:
            return None

        from .campus_endings import FAILURE_ENDINGS, WIN_ENDINGS, format_ending, get_ending
        ending_id = result.get("ending")
        pool = WIN_ENDINGS if result.get("type") == "win" else FAILURE_ENDINGS
        if ending_id in pool:
            ending = {"type": result["type"], "ending": ending_id, **pool[ending_id]}
        else:
            ending = get_ending(gs.state, result.get("type") == "win")
            ending["type"] = result.get("type", ending.get("type", "lose"))

        message = format_ending(ending)
        from .ending_archive import save_ending
        save_ending(gs.state, event.get_sender_id(), message)
        await gs.delete()
        return message

    async def start_game(self, event: AstrMessageEvent):
        """启动公司崛起游戏，注册新公司"""
        parts = event.message_str.strip().split()
        company = parts[1] if len(parts) >= 2 else ""
        industry_num = parts[2] if len(parts) >= 3 else ""
        trait_num = parts[3] if len(parts) >= 4 else ""
        difficulty_num = parts[4] if len(parts) >= 5 else ""

        gs = await self._get_gs(event)
        if await gs.has_game():
            yield event.plain_result("⚠️ 你已经有一个进行中的游戏。输入 /公司 状态 查看。")
            event.stop_event(); return
        if not company:
            lines = [
                "🏢 【公司崛起】注册向导\n",
                "用法: /启动游戏 <公司名> <行业编号> <特长编号> [难度编号]\n",
                "📌 行业选择：",
            ]
            for k, v in INDUSTRIES.items():
                lines.append(f"  {k}. {v['name']} (PE {v['pe_min']}-{v['pe_max']}倍)")
            lines.append("\n🎯 CEO 特长：")
            for k, v in CEO_TRAITS.items():
                lines.append(f"  {k}. {v['name']} - {v['effect']}")
            lines.append("\n⚙️ 难度选择 (可选，默认 2 普通)：")
            lines.append("  1. 简单 - 现金 80万, 固定成本 1万/月, 客户 15, 声誉 10, 融资冷却 2月")
            lines.append("  2. 普通 - 现金 50万, 固定成本 2万/月, 客户 10, 声誉 0, 融资冷却 3月")
            lines.append("  3. 困难 - 现金 30万, 固定成本 3万/月, 客户 5, 声誉 -10, 融资冷却 4月")
            lines.append("\n💡 示例：/启动游戏 企鹅帝国 1 1 2")
            yield event.plain_result("\n".join(lines))
            event.stop_event(); return
        if industry_num not in INDUSTRIES:
            yield event.plain_result(f"⚠️ 行业编号无效。可选: {', '.join(INDUSTRIES.keys())}")
            event.stop_event(); return
        if trait_num not in CEO_TRAITS:
            yield event.plain_result(f"⚠️ 特长编号无效。可选: {', '.join(CEO_TRAITS.keys())}")
            event.stop_event(); return
        difficulty_map = {"1": "简单", "2": "普通", "3": "困难"}
        difficulty = difficulty_map.get(difficulty_num, self._cfg("default_difficulty", "普通"))
        ind_name = INDUSTRIES[industry_num]["name"]
        trait_name = CEO_TRAITS[trait_num]["name"]
        gs.reset(company=company, industry=ind_name, trait=trait_name, difficulty=difficulty)
        self._sync_runtime_config(gs.state, reset_ap=True)
        await gs.save()
        cash = gs.state["finance"]["cash"]
        max_ap = gs.state["ceo"]["max_ap"]
        msg = (
            f"🏢 注册成功！\n"
            f"公司：{company}\n"
            f"🏭 {ind_name} | 👤 {trait_name} | ⚙️ {difficulty}\n"
            f"💰 {cash:.0f} 万 | ⚡ {max_ap}/{max_ap} AP\n\n"
            f"可用指令：/公司 研发、/公司 招聘、/公司 下一月、/公司 面板、/公司 状态"
        )
        yield event.plain_result(msg)
        event.stop_event()

    async def dev(self, event: AstrMessageEvent):
        """启动研发项目"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        project_name = event.message_str.strip()[len("/研发"):].strip()
        if not project_name:
            yield event.plain_result("⚠️ 示例：/公司 研发 破晓引擎")
            event.stop_event(); return
        result = start_dev(gs.state, project_name)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        await gs.save()
        tone = random.choice(DEV_TONES)
        narrative = await self._llm_chat(build_dev_prompt(gs.state, project_name, tone), event, state=gs.state)
        if narrative:
            for chunk in self._chunk_text(narrative):
                yield event.plain_result(chunk)
        else:
            yield event.plain_result(f"✅ 立项《{project_name}》成功！")
        event.stop_event()

    async def cancel_project_cmd(self, event: AstrMessageEvent):
        """取消研发中的项目"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        # /项目取消 <项目名>
        rest = event.message_str.strip()[len("/项目取消"):].strip()
        if not rest:
            active = [p["name"] for p in gs.state.get("projects", []) if p.get("status") == "研发中"]
            if not active:
                yield event.plain_result("⚠️ 当前没有研发中的项目。")
            else:
                yield event.plain_result("⚠️ 用法: /公司 项目取消 <项目名>\n进行中的项目:\n" + "\n".join(f"  • {n}" for n in active))
            event.stop_event(); return
        result = cancel_project(gs.state, rest)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        await gs.save()
        msg = (
            f"🗑 项目「{rest}」已取消\n"
            f"💰 退还: {result['refund']}万 (取消时进度 {result['progress_at_cancel']}%)\n"
            f"⚡ AP -1"
        )
        yield event.plain_result(msg)
        event.stop_event()

    async def recruit_cmd(self, event: AstrMessageEvent):
        """招聘：展示候选人列表"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        if gs.state["ceo"]["ap"] < 1:
            yield event.plain_result("⚠️ 行动点不足，无法招聘。")
            event.stop_event(); return
        rep = gs.state["finance"]["reputation"]
        hire_bonus = get_office(gs.state)["hire_bonus"]
        min_ability = int(max(55, 55 + rep // 50) * (1 + hire_bonus))
        # 可选 role 过滤: /招聘 研发 / /招聘 设计 / /招聘 营销
        parts = event.message_str.strip().split()
        role_filter = None
        role_map = {"tech": "tech", "design": "design", "marketing": "marketing",
                    "研发": "tech", "设计": "design", "营销": "marketing",
                    "运营": "marketing", "市场": "marketing"}
        if len(parts) >= 2:
            arg = parts[1].lower()
            if arg in role_map:
                role_filter = role_map[arg]
            else:
                yield event.plain_result("⚠️ 岗位无效。可选: 研发 / 设计 / 营销")
                event.stop_event(); return
        pool = [c for c in NORMAL_CANDIDATES if c["ability"] >= min_ability]
        if role_filter:
            pool = [c for c in pool if c["role"] == role_filter]
        if len(pool) < 3:
            if role_filter:
                yield event.plain_result(f"⚠️ {role_filter} 池子空（< 3 人符合能力下限），换个岗位或 /跳过 等下月。")
                event.stop_event(); return
            pool = NORMAL_CANDIDATES
        candidates = random.sample(pool, min(3, len(pool)))
        role_emoji = {"tech": "🔧研发", "design": "🎨设计", "marketing": "📢营销"}
        lines = [f"【📋 本周候选人】{'（' + role_emoji.get(role_filter, '') + '）' if role_filter else ''}\n"]
        for i, c in enumerate(candidates):
            lines.append(f"{i+1}. {c['name']} | {role_emoji.get(c['role'], c['role'])} | 💪{c['ability']} | 💰{c['salary']}万 | {c['trait']}")
        lines.append(f"\n/公司 录用 1-3 录取，/公司 跳过 等下一批。AP: {gs.state['ceo']['ap']}")
        gs.state["_pending"] = candidates
        await gs.save()
        yield event.plain_result("\n".join(lines))
        event.stop_event()

    async def hire(self, event: AstrMessageEvent):
        """录用候选人"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        pending = gs.state.get("_pending", [])
        if not pending:
            yield event.plain_result("⚠️ 没有待录用的候选人。先 /公司 招聘。")
            event.stop_event(); return
        parts = event.message_str.strip().split()
        idx_str = parts[1] if len(parts) >= 2 else ""
        if not idx_str.isdigit() or int(idx_str) < 1 or int(idx_str) > len(pending):
            yield event.plain_result(f"⚠️ 请输入 1-{len(pending)}。")
            event.stop_event(); return
        candidate = pending[int(idx_str) - 1]
        result = recruit(gs.state, candidate)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        # 初始化技能
        hired_emp = result.get("employee", candidate)
        if gs.state.get("meta", {}).get("_employee_skills_enabled", True):
            init_skills(hired_emp)
        gain_xp(gs.state, "hire_success")
        gs.state["_pending"] = []
        await gs.save()
        narrative = await self._llm_chat(build_recruit_prompt(gs.state, candidate), event, state=gs.state)
        if narrative:
            for chunk in self._chunk_text(f"✅ 录用 {candidate['name']}！\n{narrative}"):
                yield event.plain_result(chunk)
        else:
            yield event.plain_result(f"✅ 录用 {candidate['name']}！")
        event.stop_event()

    async def skip(self, event: AstrMessageEvent):
        """跳过本轮招聘"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 你还没有游戏。使用 /启动游戏 创建公司，或 /校园 开始 进入校园筹备期。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        gs.state["_pending"] = []
        await gs.save()
        yield event.plain_result("⏭ 已跳过。下月再来 /公司 招聘。")
        event.stop_event()

    async def next_month(self, event: AstrMessageEvent):
        """推进到下一月，触发月报和事件"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司，或 /校园 开始 进入校园筹备期。")
            event.stop_event(); return
        if gs.state.get("phase") == "campus":
            yield event.plain_result(
                "⚠️ 还在校园筹备期，没有公司月报。\n"
                "用 /校园 打工 /校园 做产品 /校园 比赛 /校园 社交 推进时间；条件成熟后用 /校园 创业 <公司名> <行业> 注册公司。"
            )
            event.stop_event(); return
        result = advance_month(gs.state)
        await gs.save()
        if result.get("game_over"):
            from .ending_archive import save_ending
            save_ending(gs.state, event.get_sender_id(), result["msg"])
            yield event.plain_result(result["msg"])
            await gs.delete()
            event.stop_event(); return
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        # 新成就通知
        for aid in result.get("achievements", []):
            yield event.plain_result(f"🎉 成就解锁: {ACHIEVEMENTS[aid][0]} - {ACHIEVEMENTS[aid][1]}")
        uid = event.get_sender_id()
        dedup_key = f"monthly_{uid}"
        last_event = gs.state.get("_last_event", "")
        # 跑路警告（yellow ≤ 3 月 / red ≤ 1 月 / dead ≤ 0）
        runway, burn, level = compute_runway(gs.state)
        # 月报彩蛋：满足条件时强制覆盖本月 theme + event_seed
        easter_egg = detect_easter_egg(gs.state)
        if easter_egg:
            theme = easter_egg["theme"]
            event_seed = easter_egg["seed"]
            yield event.plain_result(f"{easter_egg['title']} 触发! {easter_egg['desc']}")
        else:
            # dbs 主题偏好：yellow/red 偏向"融资环境"和"成本压力"
            if level in ("yellow", "red"):
                theme_pool = ["融资环境", "成本压力"] + MONTHLY_THEMES
            else:
                theme_pool = MONTHLY_THEMES
            theme = random.choice(theme_pool)
            ind_data = get_industry_by_name(gs.state["meta"]["industry"])
            dbs_seeds = (ind_data.get("dbs_seeds") or {}).get(theme, []) if ind_data else []
            event_seed = random.choice(dbs_seeds) if dbs_seeds else None
        gs.state["_last_theme"] = theme
        dbs_risk = (get_industry_by_name(gs.state["meta"]["industry"]) or {}).get("dbs_risk")
        runway_warning = None
        if level == "red":
            runway_warning = f"{runway}（🟠 红色警报）"
        elif level == "yellow":
            runway_warning = f"{runway}（🟡 黄色预警）"
        # 业绩里程碑（上月完成的项目）
        last_milestones = gs.state.get("meta", {}).get("last_milestones", [])
        prompt = build_monthly_prompt(
            gs.state, theme=theme, last_event=last_event,
            event_seed=event_seed, dbs_risk=dbs_risk,
            runway_warning=runway_warning,
            last_milestones=last_milestones,
            random_events=result.get("random_events", []),
            competitor_events=result.get("competitor_events", []),
            employee_activities=result.get("employee_activities", []),
            kpi_results=result.get("kpi_results", []),
        )
        narrative = await self._llm_chat(prompt, event, dedup_key=dedup_key, system_prompt=self._monthly_system_prompt, state=gs.state)
        if narrative:
            gs.state["_last_event"] = narrative[-100:]
            await gs.save()
            chunks = self._chunk_text(narrative)
            # 业绩里程碑（先于警告 / 叙事）
            if last_milestones:
                ms_line = "🏆 业绩里程碑：上月「" + "」「".join(last_milestones) + f"」完成，声誉 +{20 * len(last_milestones)}！"
                yield event.plain_result(ms_line)
            if level in ("yellow", "red", "dead"):
                warn_icon = level_emoji(level)
                warn_line = f"{warn_icon} 跑路警告：现金 {gs.state['finance']['cash']}万 / 月烧 {burn}万 / 还剩 {runway} 个月"
                yield event.plain_result(warn_line)
            # 明确标注：以下是 LLM 月报叙事，非存档数据
            yield event.plain_result(f"📜 [GM 月报 · {gs.state['meta']['time']} · 非存档]")
            for chunk in chunks:
                yield event.plain_result(chunk)
            # 数据事实 footer (反 LLM 幻觉: 永远显示代码真相, 玩家可核对)
            if self._cfg("show_data_footer", True):
                yield event.plain_result(self._data_footer(gs.state))
            # 随机事件通知
            for re in result.get("random_events", []):
                yield event.plain_result(f"🎲 {re.get('name', '?')}: {re.get('desc', '')}")
            # 竞争对手动态通知
            for ce in result.get("competitor_events", []):
                if ce.get("fun"):
                    yield event.plain_result(f"🆚 {ce.get('competitor', '?')}: {ce.get('action', '?')}")
                else:
                    yield event.plain_result(
                        f"🆚 {ce.get('competitor', '?')}({ce.get('ceo_trait', '?')},Lv.{ce.get('ceo_level', '?')}) {ce.get('action', '?')}"
                    )
            # 员工活动通知
            for ea in result.get("employee_activities", []):
                yield event.plain_result(f"👷 {ea.get('desc', '')}")
            # KPI 考核通知
            for kr in result.get("kpi_results", []):
                status = kr.get("status", "?")
                icon = "✅" if "达标" in status else "❌"
                yield event.plain_result(f"📋 {icon} {kr.get('emp', '?')} KPI {status}")
            # 加薪要求通知
            try:
                from .employee_management import check_salary_demands
                demands = check_salary_demands(gs.state)
                for d in demands:
                    yield event.plain_result(
                        f"💰 {d['name']} 要求加薪 {d['demand']}万/月！用 /公司 加薪 {d['name']} <同意|拒绝|谈判>"
                    )
            except ImportError:
                pass
        else:
            yield event.plain_result(format_status(gs.state))
        event.stop_event()

    async def reset_game(self, event: AstrMessageEvent):
        """重置游戏存档"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 你还没有游戏。使用 /启动游戏 创建。")
            event.stop_event(); return
        await gs.delete()
        yield event.plain_result("🗑 存档已删除。使用 /启动游戏 重新开始。")
        event.stop_event()

    async def status(self, event: AstrMessageEvent):
        """查看公司状态摘要"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司，或 /校园 开始 进入校园筹备期。")
            event.stop_event(); return
        yield event.plain_result(format_status(gs.state))
        event.stop_event()

    async def panel(self, event: AstrMessageEvent):
        """查看详细面板数据"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        parts = event.message_str.strip().split()
        module = parts[1] if len(parts) >= 2 else ""
        if gs.state.get("phase") == "campus":
            yield event.plain_result(format_panel(gs.state, module))
            event.stop_event(); return
        if module in ("ceo", "天赋", "CEO"):
            yield event.plain_result(format_ceo_panel(gs.state))
        else:
            yield event.plain_result(format_panel(gs.state, module))
        event.stop_event()

    async def achievements_cmd(self, event: AstrMessageEvent):
        """查看成就进度"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result("⚠️ 校园筹备期没有公司成就。用 /公司 状态 查看校园进度。")
            event.stop_event(); return
        if not gs.state.get("meta", {}).get("_achievements_enabled", True):
            yield event.plain_result("🏆 成就系统已关闭。")
            event.stop_event(); return
        # /成就 也触发一次解锁检查 (兜底, 防 advance_month 漏掉)
        new = unlock_achievements(gs.state)
        if new:
            await gs.save()
            titles = [ACHIEVEMENTS[aid][0] for aid in new]
            yield event.plain_result("🎉 新成就解锁: " + " ".join(titles))
        yield event.plain_result(format_achievements(gs.state))
        event.stop_event()

    async def talent_cmd(self, event: AstrMessageEvent):
        """查看/解锁CEO天赋"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        parts = event.message_str.strip().split()
        if len(parts) < 2:
            # 显示天赋面板
            yield event.plain_result(format_ceo_panel(gs.state))
            event.stop_event(); return
        # 解锁天赋: /天赋 <天赋ID>
        talent_id = parts[1]
        result = unlock_talent(gs.state, talent_id)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        await gs.save()
        msg = (
            f"✅ 天赋解锁成功！\n"
            f"🌟 {result['talent_name']}\n"
            f"💎 剩余天赋点: {result['remaining_points']}"
        )
        yield event.plain_result(msg)
        event.stop_event()

    async def history_cmd(self, event: AstrMessageEvent):
        """查看历史月报事件"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result("📜 校园筹备期没有公司月报历史。用 /公司 状态 查看当前进度。")
            event.stop_event(); return
        # 可选参数: /历史 10 (最多 24)
        rest = event.message_str.strip()[len("/历史"):].strip()
        try:
            n = int(rest) if rest else 5
        except ValueError:
            n = 5
        n = max(1, min(24, n))
        yield event.plain_result(format_history(gs.state, n))
        event.stop_event()

    async def funding_cmd(self, event: AstrMessageEvent):
        """进行融资"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        result = raise_funding(gs.state)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        gain_xp(gs.state, "funding_success")
        await gs.save()
        runway, burn, level = compute_runway(gs.state)
        narrative = await self._llm_chat(build_funding_prompt(gs.state, result), event, state=gs.state)
        msg_lines = [
            "💰 种子轮融资成功！\n",
            f"💵 拿到现金：{result['raise_amount']}万",
            f"📊 投后估值：{result['valuation']}万",
            f"📉 股权稀释：{int(result['dilution']*100)}%",
            f"🔁 累计轮次：第 {result['rounds']} 轮",
            f"💰 当前现金：{gs.state['finance']['cash']}万",
            f"📈 跑路月数：{runway}月 ({level})",
        ]
        if narrative:
            msg_lines.append("\n" + narrative)
        for chunk in self._chunk_text("\n".join(msg_lines)):
            yield event.plain_result(chunk)
        event.stop_event()

    async def ipo_cmd(self, event: AstrMessageEvent):
        """公司IPO上市"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        if gs.state.get("meta", {}).get("ipo_status") == "listed":
            yield event.plain_result("🏆 公司已上市。")
            event.stop_event(); return
        result = list_company(gs.state)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        gain_xp(gs.state, "ipo_success")
        await gs.save()
        narrative = await self._llm_chat(build_ipo_prompt(gs.state, result), event, state=gs.state)
        msg_lines = [
            "🎉 IPO 上市成功！\n",
            f"📊 上市估值：{result['ipo_valuation']}万",
            f"💵 募资到账：{result['raise_amount']}万",
            f"💰 当前现金：{gs.state['finance']['cash']}万",
            f"⭐ 上市后声誉：{int(result['new_reputation'])}",
            f"🕒 上市时间：{gs.state['meta']['time']}",
        ]
        if narrative:
            msg_lines.append("\n" + narrative)
        for chunk in self._chunk_text("\n".join(msg_lines)):
            yield event.plain_result(chunk)
        event.stop_event()

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("真状态")
    async def debug_state_cmd(self, event: AstrMessageEvent):
        """代码真相：原始数据防LLM幻觉"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 先 /启动游戏 创建公司。")
            event.stop_event(); return
        if gs.state.get("phase") == "campus":
            from .campus import format_campus_status
            yield event.plain_result("🔍 【校园代码真相】\n" + format_campus_status(gs.state))
            event.stop_event(); return
        s = gs.state
        # 关键字段摘要 (避免输出整个 state 太长)
        total_staff = s['staff']['tech'] + s['staff']['design'] + s['staff']['marketing']
        emp_names = [e['name'] for e in s.get('employees', [])]
        proj_summary = [
            f"  {p['name']}: {p['status']} {p['progress']}%"
            for p in s.get('projects', [])
        ]
        runway, burn, level = compute_runway(s)
        lines = [
            f"🔍 【代码真相】{s['meta']['company']}",
            f"⏰ {s['meta']['time']} | 🏢 {s.get('meta', {}).get('office', 'A')}",
            f"💰 现金 {s['finance']['cash']}万 | 月烧 {burn}万 | 跑路 {runway}月 ({level})",
            f"⭐ 声誉 {s['finance']['reputation']} | 估值 {s['finance']['valuation']}万",
            f"⚡ AP {s['ceo']['ap']}/{s['ceo']['max_ap']} | 特长 {s['ceo']['trait']}",
            f"👥 团队计数: tech {s['staff']['tech']} / design {s['staff']['design']} / marketing {s['staff']['marketing']} (共 {total_staff})",
            f"📋 员工名册 ({len(emp_names)}): {', '.join(emp_names) if emp_names else '(无)'}",
            f"📁 项目 ({len(s.get('projects', []))}):",
            *(proj_summary if proj_summary else ["  (无)"]),
            f"🏆 IPO: {s.get('meta', {}).get('ipo_status', '未上市')}",
            "\n💡 如果 LLM 月报与以上数据冲突，以上为代码真相。",
        ]
        for chunk in self._chunk_text("\n".join(lines), max_chars=500):
            yield event.plain_result(chunk)
        event.stop_event()

    async def change_office_cmd(self, event: AstrMessageEvent):
        """升级/降级办公室"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        parts = event.message_str.strip().split()
        # 无参数：列出所有办公室选项 + 当前
        if len(parts) < 2:
            cur_key = gs.state.get("meta", {}).get("office", "A")
            cur = OFFICE_TYPES[cur_key]
            lines = [
                f"🏢 当前办公室：{cur['name']} | 月租 {cur['rent']}万\n",
                "📋 升级选项：\n",
            ]
            tier_label = ["🥉 凑合", "🥈 标准", "🥇 进阶", "💎 豪华"]
            for k, v in OFFICE_TYPES.items():
                marker = " 👈 当前" if k == cur_key else ""
                lines.append(
                    f"  {k}. {v['name']} | 月租 {v['rent']}万 | "
                    f"容量+{v['capacity_bonus']} | 声誉+{v['reputation_bonus']} | "
                    f"招聘+{int(v['hire_bonus']*100)}% | "
                    f"{tier_label[v['tier']]}{marker}"
                )
            lines.append("\n💡 升档装修费 = (新档 tier − 旧档 tier) × 0.4 万；降档免装修，押金不退")
            lines.append("📌 用法：/换办公室 B")
            for chunk in self._chunk_text("\n".join(lines)):
                yield event.plain_result(chunk)
            event.stop_event()
            return
        # 有参数：执行换办公室
        new_key = parts[1].upper()
        result = change_office(gs.state, new_key)
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        await gs.save()
        narrative = await self._llm_chat(build_office_prompt(gs.state, result), event, state=gs.state)
        msg_lines = [
            "🏢 办公室已更换！\n",
            f"📍 新址：{result['office_name']}",
            f"💰 月租：{result['rent']}万",
            f"📈 容量 +{result['capacity_bonus']}",
            f"👥 招聘加成 +{int(result['hire_bonus']*100)}%",
        ]
        if result["upgrade_cost"] > 0:
            msg_lines.append(f"💸 装修/搬迁：{result['upgrade_cost']}万")
        if result["reputation_bonus"] > 0:
            msg_lines.append(f"⭐ 声誉 +{result['reputation_bonus']}")
        if result["downgrade"]:
            msg_lines.append("⚠️ 降档了。押金不退，声誉加成清零。")
        if narrative:
            msg_lines.append("\n" + narrative)
        for chunk in self._chunk_text("\n".join(msg_lines)):
            yield event.plain_result(chunk)
        event.stop_event()

    async def llm_panel(self, event: AstrMessageEvent):
        """查看/管理 LLM 场景参数"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return

        parts = event.message_str.strip().split(maxsplit=4)
        sub = parts[1] if len(parts) >= 2 else ""
        scene_config = gs.state.setdefault("meta", {}).setdefault("_scene_config", {})

        if sub in ("设置", "set"):
            # /llm 设置 <scene> <param>=<value>
            if len(parts) < 4:
                yield event.plain_result("⚠️ 用法: /llm 设置 <场景> <参数>=<值>\n  例: /llm 设置 monthly temperature=0.8")
                event.stop_event(); return
            scene = parts[2]
            if scene not in self.llm.get_scene_keys():
                yield event.plain_result(f"⚠️ 未知场景: {scene} 可选: {' '.join(self.llm.get_scene_keys())}")
                event.stop_event(); return
            param_str = parts[3]
            if "=" not in param_str:
                yield event.plain_result("⚠️ 格式: <参数>=<值>，如 temperature=0.8")
                event.stop_event(); return
            key, value_str = param_str.split("=", 1)
            key = key.strip().lower()
            if key not in ("temperature", "max_tokens"):
                yield event.plain_result("⚠️ 参数名只能是 temperature 或 max_tokens")
                event.stop_event(); return
            try:
                value = float(value_str)
            except ValueError:
                yield event.plain_result(f"⚠️ 无法解析数值: {value_str}")
                event.stop_event(); return
            scene_config.setdefault(scene, {})[key] = value
            # 从默认值复制未设置的参数，方便面板展示完整信息
            defaults = self.llm.get_scene_defaults(scene)
            defaults.update(scene_config[scene])
            scene_config[scene] = defaults
            await gs.save()
            yield event.plain_result(f"✅ {scene}: {key} = {value}")
            event.stop_event(); return

        if sub in ("重置", "reset"):
            # /llm 重置 [scene] — 清空单个或全部
            if len(parts) >= 3:
                scene = parts[2]
                if scene in scene_config:
                    del scene_config[scene]
                yield event.plain_result(f"🔄 已重置 {scene} 为默认值")
            else:
                gs.state["meta"]["_scene_config"] = {}
                yield event.plain_result("🔄 已重置全部场景为默认值")
            await gs.save()
            event.stop_event(); return

        # 默认：显示面板
        from .llm_service import format_scene_panel
        yield event.plain_result(format_scene_panel(scene_config))
        event.stop_event()

    def _company_command_routes(self) -> dict:
        return {
            "启动": ("启动游戏", self.start_game),
            "启动游戏": ("启动游戏", self.start_game),
            "研发": ("研发", self.dev),
            "dev": ("研发", self.dev),
            "招聘": ("招聘", self.recruit_cmd),
            "recruit": ("招聘", self.recruit_cmd),
            "录用": ("录用", self.hire),
            "跳过": ("跳过", self.skip),
            "下一月": ("下一月", self.next_month),
            "推进": ("下一月", self.next_month),
            "next": ("下一月", self.next_month),
            "状态": ("状态", self.status),
            "status": ("状态", self.status),
            "面板": ("面板", self.panel),
            "融资": ("融资", self.funding_cmd),
            "fund": ("融资", self.funding_cmd),
            "IPO": ("IPO", self.ipo_cmd),
            "ipo": ("IPO", self.ipo_cmd),
            "重置": ("重置", self.reset_game),
            "取消": ("项目取消", self.cancel_project_cmd),
            "项目取消": ("项目取消", self.cancel_project_cmd),
            "成就": ("成就", self.achievements_cmd),
            "天赋": ("天赋", self.talent_cmd),
            "历史": ("历史", self.history_cmd),
            "办公室": ("换办公室", self.change_office_cmd),
            "换办公室": ("换办公室", self.change_office_cmd),
            "记忆": ("记忆", self.company_memory),
            "谁": ("谁", self.whois),
            "员工": ("团队", self.team_cmd),
            "团队": ("团队", self.team_cmd),
            "忠诚": ("忠诚度", self.loyalty_cmd),
            "忠诚度": ("忠诚度", self.loyalty_cmd),
            "离职": ("离职", self.resign_cmd),
            "辞退": ("辞退", self.fire_cmd),
            "技能": ("技能", self.skills_cmd),
            "结局": ("结局录", self.endings_list_cmd),
            "结局录": ("结局录", self.endings_list_cmd),
            "回顾": ("回顾", self.review_ending_cmd),
            "咨询": ("咨询", self.consult),
            "建议": ("咨询", self.consult),
            "kpi": ("KPI", self.kpi_cmd),
            "KPI": ("KPI", self.kpi_cmd),
            "加薪": ("加薪", self.give_raise_cmd),
            "考勤": ("考勤", self.attendance_cmd),
            "设施": ("设施", self.facility_cmd),
            "llm": ("llm", self.llm_panel),
            "场景": ("llm", self.llm_panel),
        }

    def _campus_command_routes(self) -> dict:
        return {
            "开始": ("startgame", self.start_campus),
            "启动": ("startgame", self.start_campus),
            "startgame": ("startgame", self.start_campus),
            "创业": ("创业", self.register_company),
            "打工": ("打工", self.part_time),
            "做产品": ("做产品", self.make_product),
            "产品": ("做产品", self.make_product),
            "比赛": ("比赛", self.competition),
            "社交": ("社交", self.network_cmd),
            "找合伙人": ("找合伙人", self.find_partner_cmd),
            "合伙人": ("找合伙人", self.find_partner_cmd),
            "相亲": ("相亲", self.dating),
            "选": ("选", self.choose_event),
            "选择": ("选", self.choose_event),
        }

    def _legacy_command_routes(self) -> dict:
        routes = {}
        routes.update(self._company_command_routes())
        routes.update(self._campus_command_routes())
        routes.update({
            "newgame": ("启动游戏", self.start_game),
            "开始": ("启动游戏", self.start_game),
            "help": ("帮助", self.help_cmd),
            "helpme": ("帮助", self.help_cmd),
        })
        return routes

    async def _dispatch_routed_command(
        self,
        event: AstrMessageEvent,
        command: str,
        rest: str,
        handler,
    ):
        routed_message = f"/{command} {rest}".strip()
        routed_event = _RoutedEvent(event, routed_message)
        async for chunk in handler(routed_event):
            yield chunk

    @filter.command("公司")
    async def company_cmd(self, event: AstrMessageEvent):
        """低频公司管理入口：/公司 <子命令>"""
        parts = event.message_str.strip().split(maxsplit=2)
        if len(parts) < 2:
            yield event.plain_result(self._company_command_menu())
            event.stop_event(); return

        sub = parts[1]
        rest = parts[2] if len(parts) >= 3 else ""
        routes = self._company_command_routes()
        route = routes.get(sub) or routes.get(sub.lower())
        if not route:
            yield event.plain_result(self._company_command_menu())
            event.stop_event(); return

        command, handler = route
        async for chunk in self._dispatch_routed_command(event, command, rest, handler):
            yield chunk

    def _company_command_menu(self) -> str:
        return (
            "🏢 【公司管理入口】\n"
            "用法：/公司 <子命令> [参数]\n\n"
            "⚙️ 运营：/公司 研发 <项目> | /公司 招聘 [研发|设计|营销] | /公司 录用 <编号> | /公司 跳过\n"
            "⏭ 推进：/公司 下一月 | /公司 融资 | /公司 IPO\n"
            "📊 数据：/公司 状态 | /公司 面板 [财务|团队|项目] | /公司 成就 | /公司 天赋 | /公司 历史 | /公司 记忆\n"
            "📁 项目：/公司 项目取消 <项目名>\n"
            "🏢 办公室：/公司 办公室 [A|B|C|D]\n"
            "👥 员工：/公司 团队 | /公司 忠诚度 | /公司 技能 <员工>\n"
            "🧾 人事：/公司 KPI ... | /公司 加薪 ... | /公司 离职 ... | /公司 辞退 <员工>\n"
            "🛠 建设：/公司 设施 [查看|购买 <名称>] | /公司 咨询 [问题] | /公司 考勤\n"
            "🎛 LLM：/公司 llm | /公司 场景 — 查看/调温度与 max_tokens\n"
            "🏁 结局：/公司 结局录 | /公司 回顾 <序号>\n"
            "🗑 存档：/公司 重置"
        )

    @filter.command("校园")
    async def campus_cmd(self, event: AstrMessageEvent):
        """校园筹备期入口：/校园 <子命令>"""
        parts = event.message_str.strip().split(maxsplit=2)
        if len(parts) < 2:
            yield event.plain_result(self._campus_command_menu())
            event.stop_event(); return

        sub = parts[1]
        rest = parts[2] if len(parts) >= 3 else ""
        routes = self._campus_command_routes()
        route = routes.get(sub) or routes.get(sub.lower())
        if not route:
            yield event.plain_result(self._campus_command_menu())
            event.stop_event(); return

        command, handler = route
        async for chunk in self._dispatch_routed_command(event, command, rest, handler):
            yield chunk

    def _campus_command_menu(self) -> str:
        return (
            "🎓 【校园筹备入口】\n"
            "用法：/校园 <子命令> [参数]\n\n"
            "🚀 开始：/校园 开始\n"
            "📆 行动：/校园 打工 | /校园 做产品 <名称> | /校园 比赛 | /校园 社交\n"
            "🤝 机会：/校园 找合伙人 | /校园 相亲 | /校园 选 <事件ID> <编号>\n"
            "🏢 注册：/校园 创业 <公司名> <行业>"
        )

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def compact_legacy_command_router(self, event: AstrMessageEvent):
        """Keep old direct commands usable without registering them as visible commands."""
        text = event.message_str.strip()
        if not text.startswith("/"):
            return

        parts = text[1:].split(maxsplit=1)
        if not parts:
            return
        command = parts[0]
        if command in {"公司", "校园", "帮助", "真状态"}:
            return

        rest = parts[1] if len(parts) >= 2 else ""
        routes = self._legacy_command_routes()
        route = routes.get(command) or routes.get(command.lower())
        if not route:
            return

        routed_command, handler = route
        async for chunk in self._dispatch_routed_command(event, routed_command, rest, handler):
            yield chunk

    @filter.command("帮助")
    async def help_cmd(self, event: AstrMessageEvent):
        """显示全部指令帮助"""
        lines = [
            "📖 【公司崛起】—— 文字商业模拟游戏\n",
            "🎮 后台可见入口已收敛为：/公司、/校园、/帮助、/真状态。\n",
            "🎮 旧写法仍兼容：/启动游戏、/研发、/招聘、/下一月、/startgame 等还能直接用。\n",
            "🏢 公司期：你是创始人/CEO，用 AP 决策，/公司 下一月 推进公司月报。\n",
            "🎓 校园期：还没有公司、CEO、AP 或公司现金，用校园行动推进月份。\n",
            "💰 公司期核心资源：现金、声誉、AP、团队、客户/ARR。\n",
            "⚠️ 现金 < 0 触发 5 种结局（收购/合并/负债/口碑/破产）。\n",
            "",
            "🚀 开局：",
            "  /启动游戏 <公司> <行业编号> <特长编号> [难度] — 直接进入公司期",
            "  /校园 开始 — 进入校园筹备期",
            "",
            "🏢 公司管理入口：",
            "  /公司 — 查看公司期菜单",
            "  /公司 研发 <项目名> | 招聘 [研发|设计|营销] | 录用 <编号> | 跳过",
            "  /公司 下一月 | 状态 | 面板 [财务|团队|项目|竞争对手] | 融资 | IPO",
            "  /公司 项目取消 <项目名> — 取消研发",
            "  /公司 办公室 [A|B|C|D] — 升级/降档办公室",
            "  /公司 团队 | 忠诚度 | 技能 <员工> — 员工信息",
            "  /公司 KPI ... | 加薪 ... | 离职 ... | 辞退 <员工> — 人事管理",
            "  /公司 成就 | 天赋 | 历史 | 记忆 | 咨询 | 设施 | 考勤 — 低频功能",
            "  /公司 llm | 场景 — 查看/调节 LLM 温度与 max_tokens",
            "  /公司 结局录 | 回顾 <序号> — 历史结局",
            "",
            "🎓 校园筹备入口：",
            "  /校园 — 查看校园期菜单",
            "  /校园 打工 | 做产品 <名称> | 比赛 | 社交 | 找合伙人 | 相亲",
            "  /校园 选 <事件ID> <编号>",
            "  /校园 创业 <公司名> <行业> — 条件成熟后进入公司期",
            "",
            "🛠️ 调试：",
            "  /真状态 — 代码真相（防 LLM 幻觉对比）",
            "  /公司 重置 — 删除存档重新开始",
            "  /帮助 — 此列表",
        ]
        yield event.plain_result("\n".join(lines))
        event.stop_event()

    async def company_memory(self, event: AstrMessageEvent):
        """查询公司图谱档案"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        text = await cmd_history(gs.state)
        for chunk in self._chunk_text(text):
            yield event.plain_result(chunk)
        event.stop_event()

    async def whois(self, event: AstrMessageEvent):
        """查询员工能力信息"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        name = event.message_str.strip()[len("/谁"):].strip()
        if not name:
            yield event.plain_result("⚠️ 示例：/谁 林哥")
            event.stop_event(); return
        bridge = OntologyBridge()
        company_id = gs.state.get("_ontology_ids", {}).get("company")
        if not company_id:
            yield event.plain_result("⚠️ 图谱尚未同步。先执行 /公司 下一月 触发同步。")
            event.stop_event(); return
        result = _run_onto("query", "--type", "Employee",
                           "--where", json.dumps({"name": name}))
        if result and isinstance(result, list) and len(result) > 0:
            emp = result[0].get("properties", {})
            lines = [
                f"👤 {emp.get('name')}",
                f"  岗位：{emp.get('role')}",
                f"  能力：{emp.get('ability')}",
                f"  薪资：{emp.get('salary')}万/月",
            ]
            for chunk in self._chunk_text("\n".join(lines)):
                yield event.plain_result(chunk)
        else:
            yield event.plain_result(f"⚠️ 未找到员工「{name}」，试试全名。")
        event.stop_event()

    async def team_cmd(self, event: AstrMessageEvent):
        """查看团队详细信息"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        yield event.plain_result(format_all_employees(gs.state))
        event.stop_event()

    async def loyalty_cmd(self, event: AstrMessageEvent):
        """查看员工忠诚度报告"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        employees = [e for e in gs.state.get("employees", []) if e.get("status") == "active"]
        if not employees:
            yield event.plain_result("👥 暂无员工。")
            event.stop_event(); return
        lines = ["👥 【员工忠诚度报告】\n"]
        for emp in employees:
            loyalty = emp.get("loyalty", 70)
            risk = "💔 危险" if loyalty < 20 else ("⚠️ 低" if loyalty < 40 else "😊 正常")
            lines.append(f"{emp['name']}: {loyalty}/100 {risk}")
        low_count = sum(1 for e in employees if e.get("loyalty", 70) < 40)
        if low_count > 0:
            lines.append(f"\n⚠️ {low_count} 人忠诚度低于 40，考虑加薪挽留或 /公司 辞退 处理。")
        yield event.plain_result("\n".join(lines))
        event.stop_event()

    async def resign_cmd(self, event: AstrMessageEvent):
        """员工离职谈判"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        parts = event.message_str.strip().split(maxsplit=2)
        if len(parts) < 3:
            yield event.plain_result(
                "⚠️ 用法：/离职 <员工名> <操作>\n"
                "操作：加薪（支付3个月工资挽留）| 威胁（60%成功但风险大）| 接受（放行）"
            )
            event.stop_event(); return
        name = parts[1]
        action = parts[2]
        emp = next((e for e in gs.state.get("employees", []) if e["name"] == name), None)
        if not emp:
            yield event.plain_result(f"⚠️ 未找到员工「{name}」。")
            event.stop_event(); return
        if action not in ("加薪", "威胁", "接受"):
            yield event.plain_result("⚠️ 操作无效，可选：加薪 / 威胁 / 接受")
            event.stop_event(); return
        action_map = {"加薪": "raise", "威胁": "threat", "接受": "accept"}
        result = resignation_negotiate(gs.state, emp, action_map[action])
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        await gs.save()
        yield event.plain_result(result["msg"])
        event.stop_event()

    async def fire_cmd(self, event: AstrMessageEvent):
        """辞退员工"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        name = event.message_str.strip()[len("/辞退"):].strip()
        if not name:
            yield event.plain_result("⚠️ 用法：/公司 辞退 <员工名>")
            event.stop_event(); return
        emp = next((e for e in gs.state.get("employees", []) if e["name"] == name), None)
        if not emp:
            yield event.plain_result(f"⚠️ 未找到员工「{name}」。")
            event.stop_event(); return
        result = fire_employee(gs.state, emp, "fired")
        if not result["ok"]:
            yield event.plain_result(result["msg"])
            event.stop_event(); return
        await gs.save()
        lines = [
            f"✅ 已辞退 {name}",
            f"💸 赔偿：{result['severance']}万（N+1=3个月工资）",
            f"👥 团队士气 -10",
        ]
        if result.get("detail"):
            lines.append(f"📝 {result['detail']}")
        yield event.plain_result("\n".join(lines))
        event.stop_event()

    async def skills_cmd(self, event: AstrMessageEvent):
        """查看员工技能详情"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return
        name = event.message_str.strip()[len("/技能"):].strip()
        if not name:
            yield event.plain_result("⚠️ 用法：/技能 <员工名>")
            event.stop_event(); return
        emp = next((e for e in gs.state.get("employees", []) if e["name"] == name), None)
        if not emp:
            yield event.plain_result(f"⚠️ 未找到员工「{name}」。")
            event.stop_event(); return
        skills = emp.get("skills", {})
        if not skills:
            yield event.plain_result(f"⚠️ {name} 尚未初始化技能。")
            event.stop_event(); return
        lines = [f"🎯 {name} 技能面板:\n"]
        for skill_name, level in sorted(skills.items()):
            cn = SKILL_NAMES_CN.get(skill_name, skill_name)
            bar = "\u2588" * int(level * 2) + "\u2591" * (10 - int(level * 2))
            lines.append(f"  {cn}: Lv.{level:.1f} {bar}")
        total = sum(skills.values())
        avg = total / len(skills)
        lines.append(f"\n  总计: {total:.1f} | 均值: {avg:.1f}")
        yield event.plain_result("\n".join(lines))
        event.stop_event()

    async def endings_list_cmd(self, event: AstrMessageEvent):
        """List all archived endings for current user."""
        from .ending_archive import list_endings, format_endings_list
        uid = event.get_sender_id()
        endings = list_endings(uid)
        yield event.plain_result(format_endings_list(endings))
        event.stop_event()

    async def review_ending_cmd(self, event: AstrMessageEvent):
        """Review a specific archived ending: /\u56de\u987e [index]"""
        from .ending_archive import list_endings, get_ending, format_ending_detail, format_endings_list
        uid = event.get_sender_id()
        rest = event.message_str.strip()[len("/回顾"):].strip()
        if not rest:
            endings = list_endings(uid)
            yield event.plain_result(format_endings_list(endings))
            event.stop_event(); return
        try:
            idx = int(rest)
        except ValueError:
            yield event.plain_result("⚠️ 请输入数字序号。用 /公司 结局录 查看列表。")
            event.stop_event(); return
        ending = get_ending(uid, idx)
        if not ending:
            endings = list_endings(uid)
            yield event.plain_result(
                f"⚠️ 序号 {idx} 不存在。共 {len(endings)} 个结局。"
            )
            event.stop_event(); return
        for chunk in self._chunk_text(format_ending_detail(ending)):
            yield event.plain_result(chunk)
        event.stop_event()

    # ==================== 校园模式 ====================

    async def start_campus(self, event: AstrMessageEvent):
        """校园筹备期启动"""
        if not self._cfg("enable_campus_mode", True):
            yield event.plain_result("⚠️ 校园模式已关闭。管理员可在配置中启用。")
            event.stop_event(); return
        gs = await self._get_gs(event)
        if await gs.has_game():
            yield event.plain_result("⚠️ 你已经有一个进行中的游戏。输入 /公司 重置 清档后重来。")
            event.stop_event(); return

        from .game_state import CAMPUS_DEFAULT
        import copy
        gs.state = copy.deepcopy(CAMPUS_DEFAULT)
        self._sync_runtime_config(gs.state, reset_ap=True)

        from .campus import roll_background
        bg = roll_background()
        gs.state["campus"]["background"] = bg
        gs.state["meta"]["background"] = bg

        await gs.save()
        yield event.plain_result(
            "🎓 欢迎来到【校园筹备期】！\n\n"
            "你还是学生，还没有公司，也没有公司启动资金。\n"
            "接下来 48 个月，用时间换积蓄、产品、人脉和一点不稳定的名声。\n\n"
            "💡 使用 /校园 打工 /校园 做产品 /校园 比赛 /校园 社交 积累资源\n"
            "💡 条件成熟后，使用 /校园 创业 <公司名> <行业> 注册公司\n"
            "💡 使用 /公司 状态 查看当前进度"
        )
        event.stop_event()

    async def register_company(self, event: AstrMessageEvent):
        """注册公司：/创业 <公司名> <行业>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus import check_promotion_eligibility, campus_to_company
        result = check_promotion_eligibility(gs.state)
        if not result["ok"]:
            yield event.plain_result("❌ 晋升条件不足：\n" + "\n".join(f"  · {m}" for m in result["missing"]))
            event.stop_event(); return

        parts = event.message_str.strip().split(maxsplit=2)
        if len(parts) < 3:
            yield event.plain_result("⚠️ 用法：/校园 创业 <公司名> <行业>\n💡 例如：/校园 创业 公司崛起 游戏开发")
            event.stop_event(); return

        company_name = parts[1]
        industry_name = parts[2]

        from .constants import INDUSTRIES
        industry = None
        for k, v in INDUSTRIES.items():
            if industry_name in v.get("name", "") or industry_name == k:
                industry = k
                break
        if not industry:
            yield event.plain_result(f"⚠️ 未找到行业「{industry_name}」。\n💡 可选行业：游戏开发、SaaS、电商、AI、教育")
            event.stop_event(); return
        industry_display = INDUSTRIES[industry]["name"]

        result = campus_to_company(gs.state, company_name, industry_display)
        if not result["ok"]:
            yield event.plain_result("⚠️ 转换失败")
            event.stop_event(); return

        await gs.save()
        yield event.plain_result(
            f"🎉 公司注册完成，正式进入公司期！\n\n"
            f"🏢 公司：{company_name}\n"
            f"🏭 行业：{industry_display}\n"
            f"💰 启动资金：{result['cash']}万（{result.get('cash_sources', '校园积累')}）\n"
            f"🎭 创始人特质：{result['trait']}\n"
            f"⭐ 天赋点：{result['talent_points']}\n"
            f"📊 股权稀释：{result['equity_loss']*100:.0f}%\n\n"
            f"💡 使用 /公司 状态 查看公司详情"
        )
        event.stop_event()

    async def part_time(self, event: AstrMessageEvent):
        """打工赚钱：/打工 <tutor/freelance/intern>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus import do_part_time
        parts = event.message_str.strip().split()
        job_type = parts[1] if len(parts) >= 2 else "freelance"

        result = do_part_time(gs.state, job_type)
        campus = gs.state.get("campus", {})
        campus["months_played"] = campus.get("months_played", 0) + 1

        await gs.save()
        yield event.plain_result(
            f"💰 打工完成！\n"
            f"  收入：+{result['earnings']}万\n"
            f"  声望：+{result['reputation']}\n"
            f"  总积蓄：{campus.get('savings', 0):.1f}万"
        )
        ending_msg = await self._finish_campus_if_ended(gs, event)
        if ending_msg:
            yield event.plain_result(ending_msg)
        event.stop_event()

    async def make_product(self, event: AstrMessageEvent):
        """做产品：/做产品 <产品名>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus import do_product
        parts = event.message_str.strip().split(maxsplit=1)
        product_name = parts[1] if len(parts) >= 2 else "未命名产品"

        result = do_product(gs.state, product_name)
        campus = gs.state.get("campus", {})
        campus["months_played"] = campus.get("months_played", 0) + 1

        await gs.save()
        if result["success"]:
            yield event.plain_result(
                f"✅ 产品「{product_name}」开发成功！\n"
                f"  声望 +10 | 当前声望：{campus.get('reputation', 0)}"
            )
        else:
            yield event.plain_result(
                f"❌ 产品「{product_name}」开发失败...\n"
                f"  损失 -1万 | 当前积蓄：{campus.get('savings', 0):.1f}万"
            )
        ending_msg = await self._finish_campus_if_ended(gs, event)
        if ending_msg:
            yield event.plain_result(ending_msg)
        event.stop_event()

    async def competition(self, event: AstrMessageEvent):
        """参加比赛：/比赛"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus import do_competition
        result = do_competition(gs.state)
        campus = gs.state.get("campus", {})
        campus["months_played"] = campus.get("months_played", 0) + 1

        await gs.save()
        if result["won"]:
            yield event.plain_result(
                f"🏆 比赛获胜！\n"
                f"  奖金 +{result['prize']}万 | 声望 +{result['reputation']}\n"
                f"  总积蓄：{campus.get('savings', 0):.1f}万"
            )
        else:
            yield event.plain_result(
                f"😅 比赛惜败...\n"
                f"  声望 +{result['reputation']}"
            )
        ending_msg = await self._finish_campus_if_ended(gs, event)
        if ending_msg:
            yield event.plain_result(ending_msg)
        event.stop_event()

    async def network_cmd(self, event: AstrMessageEvent):
        """社交拓展人脉：/社交"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus import do_network
        result = do_network(gs.state)
        campus = gs.state.get("campus", {})
        campus["months_played"] = campus.get("months_played", 0) + 1

        await gs.save()
        lines = [f"🤝 社交完成！人脉 +{result['gain']}"]
        if result.get("found_partner"):
            lines.append("🎉 找到了一个合伙人！")
        yield event.plain_result("\n".join(lines))
        ending_msg = await self._finish_campus_if_ended(gs, event)
        if ending_msg:
            yield event.plain_result(ending_msg)
        event.stop_event()

    async def find_partner_cmd(self, event: AstrMessageEvent):
        """找合伙人：/找合伙人"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus import find_partner
        result = find_partner(gs.state)
        campus = gs.state.get("campus", {})
        campus["months_played"] = campus.get("months_played", 0) + 1

        await gs.save()
        yield event.plain_result(result.get("msg", "操作完成"))
        ending_msg = await self._finish_campus_if_ended(gs, event)
        if ending_msg:
            yield event.plain_result(ending_msg)
        event.stop_event()

    async def dating(self, event: AstrMessageEvent):
        """相亲事件：/相亲"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。使用 /公司 状态 查看公司。")
            event.stop_event(); return

        from .campus_events import get_available_events, apply_event_choice
        events = get_available_events(gs.state)
        dating_events = [e for e in events if e["id"].startswith("mom_") or e["id"] in ("investor_date", "rich_date", "pushy_parents")]
        if not dating_events:
            yield event.plain_result("😅 目前没有相亲机会，继续 /校园 社交 拓展人脉吧！")
            event.stop_event(); return

        event_choice = random.choice(dating_events)
        choices_text = "\n".join(f"  {i+1}. {c['text']}" for i, c in enumerate(event_choice["choices"]))
        yield event.plain_result(
            f"💕 {event_choice['title']}\n"
            f"{event_choice['desc']}\n\n"
            f"{choices_text}\n\n"
            f"💡 使用 /校园 选 {event_choice['id']} <1-{len(event_choice['choices'])}> 选择\n"
            f"📌 事件ID: {event_choice['id']}"
        )
        event.stop_event()

    async def choose_event(self, event: AstrMessageEvent):
        """选择事件选项：/选 <事件ID> <选项号>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /校园 开始 进入校园模式。")
            event.stop_event(); return
        if gs.state.get("phase") == "company":
            yield event.plain_result("⚠️ 你已经进入公司期了。校园事件选项已不可用。")
            event.stop_event(); return

        parts = event.message_str.strip().split()
        if len(parts) < 3:
            yield event.plain_result("⚠️ 用法：/校园 选 <事件ID> <选项号>\n💡 例如：/校园 选 hackathon 1")
            event.stop_event(); return

        event_id = parts[1]
        try:
            choice_idx = int(parts[2]) - 1
        except ValueError:
            yield event.plain_result("⚠️ 选项号必须是数字。")
            event.stop_event(); return

        from .campus_events import apply_event_choice
        result = apply_event_choice(gs.state, event_id, choice_idx)

        await gs.save()
        if result["ok"]:
            yield event.plain_result(f"✅ {result['event']} - 选择：{result['choice']}")
            ending_msg = await self._finish_campus_if_ended(gs, event)
            if ending_msg:
                yield event.plain_result(ending_msg)
        else:
            yield event.plain_result(f"⚠️ {result['msg']}")
        event.stop_event()

    # ====================================================================
    # 新增指令: /咨询 /KPI /加薪 /考勤 /设施
    # ====================================================================

    async def consult(self, event: AstrMessageEvent):
        """付费咨询: 1 AP + 2 万顾问费，AI 给战略建议"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return

        if gs.state["ceo"]["ap"] < 1:
            yield event.plain_result("⚠️ 行动点不足。")
            event.stop_event(); return
        if gs.state["finance"]["cash"] < 2:
            yield event.plain_result("⚠️ 现金不足 2 万顾问费。")
            event.stop_event(); return

        gs.state["ceo"]["ap"] -= 1
        gs.state["finance"]["cash"] -= 2

        question = event.message_str.strip()
        for prefix in ("/咨询", "咨询", "/consult", "consult", "/建议", "建议"):
            if question.startswith(prefix):
                question = question[len(prefix):].strip()
                break
        if not question:
            question = "当前公司最大风险和下一步建议"

        # 构建摘要
        s = gs.state
        summary = (
            f"时间:{s['meta']['time']} | 现金:{s['finance']['cash']}万 | "
            f"声誉:{s['finance']['reputation']} | AP:{s['ceo']['ap']}\n"
            f"项目:{len([p for p in s['projects'] if p.get('status')=='研发中'])}个研发中 | "
            f"员工:{len([e for e in s.get('employees',[]) if e.get('status') in ('active',None)])}人\n"
        )
        competitors = s.get("meta", {}).get("competitors", [])
        if competitors:
            comp_info = "; ".join(f"{c['name']}(Lv.{c['ceo']['level']})" for c in competitors[:2])
            summary += f"竞争对手: {comp_info}\n"

        prompt = (
            f"你是商业顾问。玩家问: 「{question}」\n"
            f"公司数据:\n{summary}\n"
            "80 字内给出战略建议，用 1. 2. 列两点。"
        )
        advice = await self._llm_chat(prompt, event, system_prompt="你是商业顾问，回答简洁专业。", state=gs.state)
        await gs.save()
        if advice:
            yield event.plain_result(f"🧠 【付费咨询 · -1AP -2万】\n{advice}")
        else:
            yield event.plain_result("⚠️ 顾问沉默了，已扣费但无建议。")
        event.stop_event()

    async def kpi_cmd(self, event: AstrMessageEvent):
        """设定 KPI: /KPI <员工> <指标> <目标> 或 /KPI 取消 <员工>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return

        parts = event.message_str.strip().split()
        if len(parts) < 2:
            yield event.plain_result(
                "⚠️ 用法:\n"
                "  /KPI <员工名> <指标> <目标>\n"
                "  /KPI 取消 <员工名>\n"
                "指标可选: progress(进度) / loyalty(忠诚度) / skill_avg(技能均值)"
            )
            event.stop_event(); return

        from .employee_management import set_kpi, cancel_kpi

        if parts[1] == "取消":
            if len(parts) < 3:
                yield event.plain_result("⚠️ 用法: /公司 KPI 取消 <员工名>")
                event.stop_event(); return
            result = cancel_kpi(gs.state, parts[2])
        elif len(parts) >= 4:
            emp_name = parts[1]
            metric = parts[2]
            try:
                target = float(parts[3])
            except ValueError:
                yield event.plain_result("⚠️ 目标值必须是数字。")
                event.stop_event(); return
            reward = parts[4] if len(parts) > 4 else "raise_0.5"
            penalty = parts[5] if len(parts) > 5 else "warning"
            result = set_kpi(gs.state, emp_name, metric, target, reward=reward, penalty=penalty)
        else:
            yield event.plain_result(
                "⚠️ 用法: /KPI <员工名> <指标> <目标> [奖励] [惩罚]\n"
                "奖励: raise_0.5(加薪) / bonus_2(奖金)\n"
                "惩罚: warning(警告) / salary_cut_0.3(降薪)"
            )
            event.stop_event(); return

        await gs.save()
        yield event.plain_result(result["msg"])
        event.stop_event()

    async def give_raise_cmd(self, event: AstrMessageEvent):
        """加薪: /加薪 <员工> <金额> 或 /加薪 <员工> <同意|拒绝|谈判>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return

        parts = event.message_str.strip().split()
        if len(parts) < 3:
            yield event.plain_result("⚠️ 用法:\n  /公司 加薪 <员工名> <金额>\n  /公司 加薪 <员工名> <同意|拒绝|谈判>")
            event.stop_event(); return

        emp_name = parts[1]
        action_str = parts[2]

        from .employee_management import give_raise, handle_salary_demand, _find_employee
        emp = _find_employee(gs.state, emp_name)
        if not emp:
            yield event.plain_result(f"⚠️ 没找到员工「{emp_name}」。")
            event.stop_event(); return

        if action_str in ("同意", "拒绝", "谈判"):
            result = handle_salary_demand(gs.state, emp, {"同意": "accept", "拒绝": "refuse", "谈判": "negotiate"}[action_str])
        else:
            try:
                amount = float(action_str)
            except ValueError:
                yield event.plain_result("⚠️ 金额必须是数字，或使用 同意/拒绝/谈判。")
                event.stop_event(); return
            result = give_raise(gs.state, emp_name, amount)

        await gs.save()
        yield event.plain_result(result["msg"])
        event.stop_event()

    async def attendance_cmd(self, event: AstrMessageEvent):
        """查看本月员工活动摘要"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return

        log = gs.state.get("log", [])
        if not log:
            yield event.plain_result("📋 【考勤】\n暂无记录，运行 /公司 下一月 后查看。")
            event.stop_event(); return

        last = log[-1]
        activities = last.get("employee_activities", [])
        kpi = last.get("kpi_results", [])
        events = last.get("random_events", [])

        lines = [f"📋 【考勤 · {gs.state['meta']['time']}】\n"]
        if activities:
            lines.append("👷 员工动态:")
            for a in activities:
                lines.append(f"  {a.get('desc', '')}")
        if kpi:
            lines.append("📊 KPI 考核:")
            for k in kpi:
                icon = "✅" if "达标" in k.get("status", "") else "❌"
                lines.append(f"  {icon} {k.get('emp', '?')} {k.get('status', '?')}")
        if events:
            lines.append("🎲 随机事件:")
            for e in events:
                lines.append(f"  {e.get('name', '?')}: {e.get('desc', '')}")
        if len(lines) == 1:
            lines.append("本月平静，无事发生。")

        yield event.plain_result("\n".join(lines))
        event.stop_event()

    async def facility_cmd(self, event: AstrMessageEvent):
        """设施: /设施 查看 或 /设施 购买 <名称>"""
        gs = await self._get_gs(event)
        if not await gs.has_game():
            yield event.plain_result("⚠️ 请先 /启动游戏 创建公司。")
            event.stop_event(); return
        phase_error = self._company_phase_error(gs.state)
        if phase_error:
            yield event.plain_result(phase_error)
            event.stop_event(); return

        parts = event.message_str.strip().split()
        from .employee_management import list_facilities, buy_facility, FACILITIES

        if len(parts) < 3 or parts[1] not in ("购买", "买", "建设"):
            # 显示列表
            lines = [list_facilities(gs.state), "\n可建设设施:"]
            for name, fac in FACILITIES.items():
                tier_names = {0: "A档", 1: "B档", 2: "C档", 3: "D档"}
                lines.append(
                    f"  {name} | 建设 {fac['cost']}万 | 月维护 {fac['maintenance']}万 | "
                    f"需{tier_names.get(fac['office_tier'], '?')}+ | {fac['desc']}"
                )
            lines.append("\n用法: /公司 设施 购买 <名称>")
            yield event.plain_result("\n".join(lines))
            event.stop_event(); return

        facility_name = parts[2]
        result = buy_facility(gs.state, facility_name)
        await gs.save()
        yield event.plain_result(result["msg"])
        event.stop_event()
