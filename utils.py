from .constants import INDUSTRIES, LEVEL_EMOJI, OFFICE_TYPES


def increment_month(state: dict) -> str:
    year_month = state["meta"]["time"]
    year_str, month_str = year_month.split("年")
    year = int(year_str)
    month = int(month_str.replace("月", ""))
    month += 1
    if month > 12:
        month = 1
        year += 1
    return f"{year}年{month}月"


def parse_time_to_month_idx(time_str: str) -> int:
    year_str, month_str = time_str.split("年")
    year = int(year_str)
    month = int(month_str.replace("月", ""))
    return (year - 1) * 12 + month


def get_office(state: dict) -> dict:
    key = state.get("meta", {}).get("office", "A")
    return OFFICE_TYPES.get(key, OFFICE_TYPES["A"])


def get_office_rent(state: dict) -> float:
    return get_office(state)["rent"]


def get_industry_by_name(name: str) -> dict | None:
    for v in INDUSTRIES.values():
        if v["name"] == name:
            return v
    return None


def level_emoji(level: str) -> str:
    return LEVEL_EMOJI.get(level, "❓")
