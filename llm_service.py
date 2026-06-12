"""LLM 调用服务 — 抽离 _llm_chat 为独立服务

职责：
- Provider 解析（按配置或自动选择）
- 核心 text_chat 调用
- 去重（原 _llm_chat dedup_key 逻辑）
- 按场景选择 temperature/max_tokens（支持运行时覆写）

用法（带去重）：
  req = LLMRequest(prompt=..., system_prompt=...)
  text = await llm.chat_blocked(req, "monthly_xxx")

用法（无去重）：
  req = LLMRequest(prompt=..., system_prompt=...)
  text = await llm.chat(req)

运行时覆写场景参数：
  # main.py 传 state.meta._scene_config 进去
  t = llm.get_temperature_for("monthly_xxx", scene_overrides)
  k = llm.get_max_tokens_for("monthly_xxx", scene_overrides)
"""

from dataclasses import dataclass, field
from typing import Optional

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.star import Context


# ============================================================
# 默认场景参数（硬编码 baseline，可被运行时覆写）
# ============================================================

SCENE_PARAMS: dict[str, dict] = {
    "monthly": {"temperature": 0.85, "max_tokens": 600},
    "dev": {"temperature": 0.7, "max_tokens": 100},
    "recruit": {"temperature": 0.7, "max_tokens": 80},
    "funding": {"temperature": 0.8, "max_tokens": 150},
    "office": {"temperature": 0.7, "max_tokens": 100},
    "ipo": {"temperature": 0.8, "max_tokens": 150},
    "consult": {"temperature": 0.6, "max_tokens": 200},
}

SCENE_NAMES: dict[str, str] = {
    "monthly": "月报叙事",
    "dev": "立项现场",
    "recruit": "录用叙事",
    "funding": "融资庆祝",
    "office": "换办公室",
    "ipo": "IPO 敲钟",
    "consult": "付费咨询",
}

SCENE_KEYS = sorted(SCENE_PARAMS.keys())


def _resolve_scene_key(scene_key: Optional[str]) -> str:
    """从 dedup_key 提取场景基础 id（如 'monthly_xxx' → 'monthly'）"""
    if not scene_key:
        return ""
    for prefix in SCENE_PARAMS:
        if scene_key.startswith(prefix):
            return prefix
    return ""


# ============================================================
# 面板格式化
# ============================================================

def format_scene_panel(overrides: dict = None) -> str:
    """格式化场景参数面板文字"""
    if overrides is None:
        overrides = {}
    lines = ["🎛️ 【LLM 场景参数面板】\n"]
    for sid in SCENE_KEYS:
        name = SCENE_NAMES.get(sid, sid)
        defaults = SCENE_PARAMS[sid]
        ovr = overrides.get(sid, {})
        temp = ovr.get("temperature", defaults["temperature"])
        toks = ovr.get("max_tokens", defaults["max_tokens"])
        flag = " ✏️" if ovr else ""
        lines.append(f"  {sid:10s} {name}  🌡{temp}  📝{toks}  tokens{flag}")
    lines.append("\n用法：")
    lines.append("  /llm 设置 <场景> <参数>=<值>")
    lines.append("  /llm 重置 [场景]")
    lines.append(f"  场景: {' '.join(SCENE_KEYS)}")
    lines.append("  参数: temperature / max_tokens")
    return "\n".join(lines)


# ============================================================
# 请求 / 服务
# ============================================================

@dataclass
class LLMRequest:
    """LLM 请求参数"""
    prompt: str
    system_prompt: str = ""
    temperature: float = 0.85
    max_tokens: int = 500
    session_id: str = ""


class LLMService:
    """LLM 调用服务"""

    def __init__(self, context: Context, config: dict):
        self.context = context
        self.config = config or {}
        self._last_responses: dict[str, str] = {}

    # ---- 生命周期 ----

    def clear(self):
        """清理去重状态（插件卸载时调用）"""
        self._last_responses.clear()

    # ---- 公共方法 ----

    async def chat(self, request: LLMRequest) -> str:
        """核心 LLM 调用"""
        provider = await self._resolve_provider(request.session_id)
        if not provider:
            return ""

        response = await provider.text_chat(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return getattr(response, "completion_text", "") or ""

    async def chat_blocked(self, request: LLMRequest, dedup_key: str) -> str:
        """带去重的 LLM 调用"""
        text = await self.chat(request)
        if text and self._is_duplicate(dedup_key, text):
            return ""
        if text:
            self._last_responses[dedup_key] = text
        return text

    # ---- 场景参数（接受运行时覆写） ----

    def get_temperature_for(self, scene_key: Optional[str],
                            overrides: dict = None) -> float:
        """按场景返回 temperature（先查覆写，再查默认，最后回退配置）"""
        if overrides is None:
            overrides = {}
        base = _resolve_scene_key(scene_key)
        if base:
            ov = overrides.get(base, {}).get("temperature")
            if ov is not None:
                return ov
            if base in SCENE_PARAMS:
                return SCENE_PARAMS[base].get("temperature",
                    self._cfg("llm_temperature", 0.85))
        return self._cfg("llm_temperature", 0.85)

    def get_max_tokens_for(self, scene_key: Optional[str],
                           overrides: dict = None) -> int:
        """按场景返回 max_tokens（先查覆写，再查默认，最后回退配置）"""
        if overrides is None:
            overrides = {}
        base = _resolve_scene_key(scene_key)
        if base:
            ov = overrides.get(base, {}).get("max_tokens")
            if ov is not None:
                return ov
            if base in SCENE_PARAMS:
                return SCENE_PARAMS[base].get("max_tokens",
                    self._cfg("llm_max_tokens", 500))
        return self._cfg("llm_max_tokens", 500)

    def get_scene_defaults(self, scene_id: str) -> dict:
        """返回某场景的默认参数"""
        return dict(SCENE_PARAMS.get(scene_id, {}))

    @staticmethod
    def get_scene_keys() -> list[str]:
        return list(SCENE_KEYS)

    # ---- 内部方法 ----

    async def _resolve_provider(self, session_id: str):
        """解析 LLM provider"""
        provider_id = self._cfg("llm_provider", "")
        if provider_id and hasattr(self.context, "get_provider_by_id"):
            try:
                provider = self.context.get_provider_by_id(provider_id)
                if provider:
                    return provider
            except Exception as e:
                logger.warning(f"指定 LLM provider 不可用: {provider_id} ({e})")
        try:
            return self.context.get_using_provider(session_id)
        except Exception as e:
            logger.error(f"无法获取 LLM provider: {e}")
            return None

    def _is_duplicate(self, key: str, text: str) -> bool:
        """检查是否为重复响应（原 _is_duplicate）"""
        prev = self._last_responses.get(key)
        if not prev or len(text) < 20:
            return False
        overlap = len(set(text) & set(prev)) / max(len(set(text)), 1)
        return overlap > 0.75

    def _cfg(self, key: str, default=None):
        return self.config.get(key, default)
