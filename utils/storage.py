"""Storage path helpers for company-rising.

Keep all plugin data under AstrBot's plugin_data/astrbot_plugin_company_rising
directory. The fallback path intentionally matches the historical location.
"""

from pathlib import Path

PLUGIN_ID = "astrbot_plugin_company_rising"


def get_plugin_data_dir() -> Path:
    """Return the plugin data directory, creating it if needed."""
    for import_path in ("astrbot.api.star", "astrbot.api.all"):
        try:
            module = __import__(import_path, fromlist=["StarTools"])
            star_tools = getattr(module, "StarTools", None)
            if star_tools:
                raw = star_tools.get_data_dir(PLUGIN_ID)
                if raw:
                    path = Path(raw)
                    path.mkdir(parents=True, exist_ok=True)
                    return path
        except Exception:
            pass

    from astrbot.core.utils.astrbot_path import get_astrbot_data_path

    path = Path(get_astrbot_data_path()) / "plugin_data" / PLUGIN_ID
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_plugin_subdir(name: str) -> Path:
    """Return a named subdirectory under the plugin data directory."""
    path = get_plugin_data_dir() / name
    path.mkdir(parents=True, exist_ok=True)
    return path

