"""Re-export hub: all public symbols available as `game_manager.xxx` for backward compat."""

from .constants import *          # INDUSTRIES, CEO_TRAITS, OFFICE_TYPES, ACHIEVEMENTS, LEVEL_EMOJI
from .endings import GAME_OVER_ENDINGS
from .achievements import check_achievements, unlock_achievements, format_achievements
from .projects import calc_capacity, start_dev, cancel_project, list_projects, ascii_progress_bar
from .events import detect_easter_egg, should_make_headline, format_headline
from .customers import update_customers
from .utils import get_industry_by_name, get_office, get_office_rent, level_emoji, parse_time_to_month_idx, increment_month
from .finance import raise_funding, list_company, compute_runway, change_office
from .formatting import format_status, format_panel, format_panel_finance, format_panel_team, format_panel_project, format_history
from .advance_month import advance_month
from .recruit import recruit
from .ceo import gain_xp, unlock_talent, get_available_talents, get_talent_effects, format_ceo_panel, calculate_level, get_ceo_branch
from .employee import (
    format_all_employees, format_employee, fire_employee,
    resignation_negotiate, adjust_loyalty, decay_loyalty,
    grow_skills, init_skills, check_auto_resignations,
    SKILLS_BY_ROLE, SKILL_NAMES_CN,
)
from .campus import (
    roll_background, check_promotion_eligibility, campus_to_company,
    do_part_time, do_product, do_competition, do_network, find_partner,
    check_win_lose, format_campus_status, format_promotion_check,
    MAJOR_OPTIONS, FUNDING_OPTIONS, DIRECTION_OPTIONS,
)
from .campus_events import get_available_events, apply_event_choice
from .campus_endings import get_unlocked_titles, format_titles, get_ending, format_ending
from .random_events import roll_monthly_event, EVENT_POOL
from .competitors import init_competitors, advance_competitors, format_competitors
from .employee_management import (
    set_kpi, cancel_kpi, evaluate_kpis, roll_employee_activities,
    check_salary_demands, handle_salary_demand, give_raise,
    buy_facility, list_facilities, apply_facilities, get_facility_effects,
    FACILITIES,
)
