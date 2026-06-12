import json
import logging


from ..llm.ontology_bridge import OntologyBridge
from ..utils.constants import ACHIEVEMENTS
from ..utils.storage import get_plugin_data_dir

logger = logging.getLogger(__name__)

# File-based storage: data/plugin_data/astrbot_plugin_company_rising/{user_id}.json
_DATA_DIR = get_plugin_data_dir()

DEFAULT_STATE = {
    "meta": {
        "company": "未命名公司",
        "industry": "游戏开发",
        "time": "1年1月",
        "office": "A",
    },
    "finance": {
        "cash": 50.0,
        "fixed_cost": 2.0,
        "valuation": 50.0,
        "reputation": 0,
    },
    "ceo": {
        "ap": 3,
        "max_ap": 3,
        "trait": "技术领袖",
        "xp": 0,
        "level": 1,
        "talent_points": 0,
        "unlocked_talents": [],
    },
    "staff": {
        "tech": 0,
        "design": 0,
        "marketing": 0,
        "total_salary": 0.0,
    },
    "projects": [],
    "customers": {
        "count": 0,            # 当前客户数
        "arr_per_customer": 0.5,  # 每客户年订阅费 (万), 默认 0.5 万/年 = 416 元/月
        "churn_rate": 0.10,    # 月流失率 10%
        "growth_rate": 0.0,    # 月增长率 (受 rep/营销/项目影响)
        "history": [],         # [(month, count), ...] 折线图用
    },
    "log": [],
    "employees": [],  # 详细员工列表
}

CAMPUS_DEFAULT = {
    "meta": {"company": "", "industry": "", "time": "1年1月", "office": "A", "background": ""},
    "finance": {"cash": 0.0, "fixed_cost": 0.0, "valuation": 0.0, "reputation": 0},
    "ceo": {"ap": 0, "max_ap": 0, "trait": "", "xp": 0, "level": 0, "talent_points": 0, "unlocked_talents": []},
    "staff": {"tech": 0, "design": 0, "marketing": 0, "total_salary": 0.0},
    "projects": [],
    "customers": {"count": 0, "arr_per_customer": 0.5, "churn_rate": 0.10, "growth_rate": 0.0, "history": []},
    "log": [],
    "employees": [],
    "phase": "campus",
    "campus": {
        "background": "", "major": "1", "funding": "1", "direction": "1",
        "savings": 0, "reputation": 0, "network": 0,
        "has_partner": False, "has_investor": False,
        "tech_skill": 30, "marketing_skill": 30, "management_skill": 20,
        "months_played": 0,
        "hackathon_win": False, "dating": False,
        "background_revealed": False, "suspicion": 0,
        "titles": [], "products": [],
    },
}


class GameState:
    def __init__(self, context, user_id: str):
        self.context = context
        self.user_id = user_id
        self.key = f"company_rising_{user_id}"
        self._file_path = _DATA_DIR / f"{user_id}.json"
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)

    def _read_file(self) -> dict | None:
        if not self._file_path.exists():
            return None
        try:
            text = self._file_path.read_text(encoding="utf-8")
            return json.loads(text)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"read file failed: {self._file_path} {e}")
            return None

    def _write_file(self, data: dict) -> bool:
        try:
            tmp = self._file_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._file_path)
            return True
        except OSError as e:
            logger.warning(f"write file failed: {self._file_path} {e}")
            return False

    async def load(self):
        """从文件加载游戏状态。"""
        raw = self._read_file()
        if raw and isinstance(raw, dict):
            self.state = raw

    async def save(self):
        """保存游戏状态到文件，末尾同步到 ontology。"""
        self._write_file(self.state)
        if self.state.get("phase") == "campus":
            return
        if not self.state.get("meta", {}).get("_ontology_sync_enabled", True):
            return
        # 同步到 ontology 知识图谱
        try:
            bridge = OntologyBridge()
            bridge.sync_company(self.state)
            for emp in self.state.get("employees", []):
                bridge.sync_employee(
                    self.state,
                    emp["name"],
                    emp["role"],
                    emp["salary"],
                    emp.get("ability", 60),
                    emp.get("loyalty", 70),
                    emp.get("skills", {}),
                    emp.get("status", "active"),
                )
            meta = self.state.setdefault("meta", {})
            
            # 统一里程碑同步：收集所有类型的新里程碑
            synced = set(meta.get("_synced_milestone_names", []))
            new_milestones = []
            
            # 1. 项目完成里程碑
            for title in meta.get("last_milestones", []):
                if title not in synced:
                    new_milestones.append({
                        "title": title,
                        "type": "project_complete",
                        "desc": f"项目「{title}」交付 +20 声誉",
                    })
            
            # 2. 融资里程碑
            funding_rounds = meta.get("funding_rounds", 0)
            for i in range(1, funding_rounds + 1):
                key = f"funding_round_{i}"
                if key not in synced:
                    new_milestones.append({
                        "title": key,
                        "type": "funding",
                        "desc": f"完成第 {i} 轮融资",
                    })
            
            # 3. IPO 里程碑
            if meta.get("ipo_status") == "listed" and "ipo" not in synced:
                new_milestones.append({
                    "title": "ipo",
                    "type": "ipo",
                    "desc": f"成功 IPO 上市，估值 {meta.get('ipo_pre_valuation', '?')} 万",
                })
            
            # 4. 办公室升级里程碑
            office = meta.get("office", "A")
            office_key = f"office_{office}"
            if office_key not in synced:
                office_names = {"A": "城中村共享工位", "B": "联合办公空间", "C": "科技园孵化器", "D": "甲级写字楼"}
                new_milestones.append({
                    "title": office_key,
                    "type": "office_upgrade",
                    "desc": f"搬入 {office_names.get(office, office)}",
                })
            
            # 5. 首位员工里程碑
            if len(self.state.get("employees", [])) >= 1 and "first_hire" not in synced:
                new_milestones.append({
                    "title": "first_hire",
                    "type": "first_hire",
                    "desc": "招募首位员工",
                })
            
            # 6. 成就里程碑
            for aid in meta.get("achievements", []):
                if f"achievement_{aid}" not in synced:
                    ach = ACHIEVEMENTS.get(aid, ("", ""))[0]
                    new_milestones.append({
                        "title": f"achievement_{aid}",
                        "type": "achievement",
                        "desc": f"解锁成就：{ach}",
                    })

            # 7. 员工事件里程碑 (首次辞退/离职)
            emp_events = meta.get("_emp_events", [])
            for evt in emp_events:
                if evt not in synced:
                    new_milestones.append({
                        "title": evt,
                        "type": "employee_event",
                        "desc": f"员工事件：{evt}",
                    })
            
            # 执行同步
            for ms in new_milestones:
                ms_id = bridge.sync_milestone(self.state, ms["title"], meta.get("time", ""), ms["desc"])
                if ms_id:
                    synced.add(ms["title"])
            
            if new_milestones:
                meta["_synced_milestone_names"] = list(synced)
        except Exception:
            pass

    async def delete(self):
        """删除游戏状态文件。"""
        try:
            if self._file_path.exists():
                self._file_path.unlink()
        except OSError as e:
            logger.warning(f"file delete failed: {e}")

    def reset(self, company: str = "未命名公司", industry: str = "游戏开发", trait: str = "技术领袖", difficulty: str = "普通"):
        import copy
        self.state = copy.deepcopy(DEFAULT_STATE)
        self.state["meta"]["company"] = company
        self.state["meta"]["industry"] = industry
        self.state["ceo"]["trait"] = trait
        self.state["ceo"]["xp"] = 0
        self.state["ceo"]["level"] = 1
        self.state["ceo"]["talent_points"] = 0
        self.state["ceo"]["unlocked_talents"] = []
        self.state["meta"]["difficulty"] = difficulty

        # 难度调整
        if difficulty == "简单":
            self.state["finance"]["cash"] = 80.0
            self.state["finance"]["fixed_cost"] = 1.0
            self.state["customers"]["count"] = 15
            self.state["finance"]["reputation"] = 10
            self.state["meta"]["_funding_cooldown"] = 2
        elif difficulty == "困难":
            self.state["finance"]["cash"] = 30.0
            self.state["finance"]["fixed_cost"] = 3.0
            self.state["customers"]["count"] = 5
            self.state["finance"]["reputation"] = -10
            self.state["meta"]["_funding_cooldown"] = 4
        else:  # 普通 (默认)
            self.state["finance"]["cash"] = 50.0
            self.state["finance"]["fixed_cost"] = 2.0
            self.state["customers"]["count"] = 10
            self.state["finance"]["reputation"] = 0
            self.state["meta"]["_funding_cooldown"] = 3

        # 确保员工列表存在（兼容旧存档）
        if "employees" not in self.state:
            self.state["employees"] = []

    async def has_game(self) -> bool:
        """检查是否有进行中的游戏 (公司名非默认)。"""
        raw = self._read_file()
        if not raw or not isinstance(raw, dict):
            return False
        if raw.get("phase") == "campus":
            return True
        try:
            company = raw.get("meta", {}).get("company", "")
            return bool(company and company != "未命名公司")
        except (AttributeError, TypeError):
            return False
