"""公司崛起 - 文字商业模拟游戏 AstrBot 插件

插件启动时自动将 skill/ 部署到 data/skills/company-rising/，
让 AI 知道如何当好游戏 GM。

文档:
- README.md
- CHANGELOG.md
- bench/ (token 优化套件)
- bench/validate_plugin.py (静态校验)
- bench/run_evals.py (动态测试)
"""

import shutil
from pathlib import Path

_plugin_dir = Path(__file__).resolve().parent
_skill_source = _plugin_dir / "skill"
_skill_target = _plugin_dir.parent.parent / "skills" / "company-rising"

if _skill_source.exists():
    _skill_target.mkdir(parents=True, exist_ok=True)
    for src in _skill_source.rglob("*"):
        if src.is_file():
            rel = src.relative_to(_skill_source)
            dst = _skill_target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
