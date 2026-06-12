"""ontology 知识图谱同步桥接层。

将公司崛起的游戏状态同步到 ontology skill 的知识图谱中，
实现跨游戏存档、可查询的公司记忆。

用法：
    bridge = OntologyBridge()
    await bridge.sync_company(state)
    await bridge.sync_employee(state, "商务运营 B", "marketing", 0.45, 78)
    await bridge.sync_milestone(state, "里程碑名", "1年7月", "描述")
    await bridge.sync_event(state, "事件描述", "成功")
"""

import json
import os
import subprocess
import sys

ONTOLOGY_SKILL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "skills",
    "ontology",
)
ONTOLOGY_SCRIPT = os.path.join(ONTOLOGY_SKILL_DIR, "scripts", "ontology.py")


def _run_onto(*args: str) -> dict | list | None:
    """同步执行 ontology CLI 命令，返回解析后的 JSON 结果。"""
    cmd = [sys.executable, ONTOLOGY_SCRIPT] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ONTOLOGY_SKILL_DIR,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        if not output:
            return None
        return json.loads(output)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


class OntologyBridge:
    """公司崛起 ↔ ontology 同步桥。"""

    # ---------- 实体创建 / 更新 ----------

    def sync_company(self, state: dict) -> str | None:
        """创建或更新公司实体。返回 entity ID。"""
        company = state["meta"]["company"]
        industry = state["meta"]["industry"]
        time_str = state["meta"]["time"]
        cash = state["finance"]["cash"]
        reputation = state["finance"]["reputation"]
        status = "运营中" if cash > 0 else "破产"

        props = {
            "name": company,
            "industry": industry,
            "status": status,
            "time": time_str,
            "cash": cash,
            "reputation": reputation,
        }

        # 已有 ontology ID 则更新
        existing_id = state.get("_ontology_ids", {}).get("company")
        if existing_id:
            _run_onto(
                "update", "--id", existing_id,
                "--props", json.dumps(props, ensure_ascii=False),
            )
            return existing_id

        # 新建
        result = _run_onto("create", "--type", "Company",
                           "--props", json.dumps(props, ensure_ascii=False))
        if result and isinstance(result, dict):
            eid = result.get("id")
            state.setdefault("_ontology_ids", {})["company"] = eid
            return eid
        return None

    def sync_employee(self, state: dict, name: str, role: str,
                       salary: float, ability: int = 60,
                       loyalty: int = 70, skills: dict = None,
                       status: str = "active") -> str | None:
        """创建或更新员工实体并关联到公司。返回 employee ID。"""
        company_id = state.get("_ontology_ids", {}).get("company")
        if not company_id:
            return None

        props = {
            "name": name,
            "role": role,
            "salary": salary,
            "ability": ability,
            "loyalty": loyalty,
            "skills": skills or {},
            "status": status,
        }

        # 检查是否已有同名员工
        existing = _run_onto("query", "--type", "Employee",
                             "--where", json.dumps({"name": name}))
        if existing and isinstance(existing, list) and len(existing) > 0:
            eid = existing[0].get("id")
            _run_onto("update", "--id", eid,
                      "--props", json.dumps(props, ensure_ascii=False))
            return eid

        result = _run_onto("create", "--type", "Employee",
                           "--props", json.dumps(props, ensure_ascii=False))
        if result and isinstance(result, dict):
            eid = result.get("id")
            _run_onto("relate", "--from", company_id, "--rel", "hires", "--to", eid)
            return eid
        return None

    def sync_employee_event(self, state: dict, employee_name: str,
                            event_type: str, description: str) -> str | None:
        """同步员工事件（离职/辞退/加薪等）到图谱。"""
        company_id = state.get("_ontology_ids", {}).get("company")
        if not company_id:
            return None

        props = {
            "employee": employee_name,
            "event_type": event_type,
            "description": description,
            "time": state.get("meta", {}).get("time", ""),
        }
        result = _run_onto("create", "--type", "EmployeeEvent",
                           "--props", json.dumps(props, ensure_ascii=False))
        if result and isinstance(result, dict):
            eid = result.get("id")
            _run_onto("relate", "--from", company_id,
                      "--rel", "employee_event", "--to", eid)
            return eid
        return None

    def sync_milestone(self, state: dict, title: str, month: str,
                        description: str) -> str | None:
        """创建里程碑实体并关联到公司。"""
        company_id = state.get("_ontology_ids", {}).get("company")
        if not company_id:
            return None

        props = {"title": title, "month": month, "description": description}
        result = _run_onto("create", "--type", "Milestone",
                           "--props", json.dumps(props, ensure_ascii=False))
        if result and isinstance(result, dict):
            mid = result.get("id")
            _run_onto("relate", "--from", company_id, "--rel", "has_milestone", "--to", mid)
            return mid
        return None

    def sync_event(self, state: dict, description: str,
                    outcome: str = "") -> str | None:
        """创建游戏事件实体并关联到公司。"""
        company_id = state.get("_ontology_ids", {}).get("company")
        if not company_id:
            return None

        props = {"description": description, "outcome": outcome}
        result = _run_onto("create", "--type", "GameEvent",
                           "--props", json.dumps(props, ensure_ascii=False))
        if result and isinstance(result, dict):
            eid = result.get("id")
            _run_onto("relate", "--from", company_id,
                      "--rel", "happened_to", "--to", eid)
            return eid
        return None

    # ---------- 查询 ----------

    def query_team(self, state: dict) -> str:
        """查询公司当前团队，返回可读文本。"""
        company_id = state.get("_ontology_ids", {}).get("company")
        if not company_id:
            # fallback: 从 state 读
            staff = state.get("staff", {})
            employees = state.get("employees", [])
            lines = [f"设计{staff.get('design',0)}人 营销{staff.get('marketing',0)}人 技术{staff.get('tech',0)}人"]
            for e in employees:
                lines.append(f"  {e['name']}（{e['role']}）")
            return "\n".join(lines)

        result = _run_onto("related", "--id", company_id, "--rel", "hires")
        if not result or not isinstance(result, list):
            return "(无团队数据)"
        lines = []
        for item in result:
            e = item.get("entity", {})
            props = e.get("properties", {})
            lines.append(f"  {props.get('name','?')}（{props.get('role','?')}）💰{props.get('salary','?')}万")
        return "\n".join(lines) if lines else "(暂无员工)"

    def query_history(self, state: dict) -> str:
        """查询公司里程碑历史。"""
        company_id = state.get("_ontology_ids", {}).get("company")
        if not company_id:
            # fallback: 从 state log 读
            logs = state.get("log", [])
            return "\n".join(logs) if logs else "(无历史记录)"

        result = _run_onto("related", "--id", company_id, "--rel", "has_milestone")
        if not result or not isinstance(result, list):
            return "(无历史记录)"
        lines = []
        for item in result:
            e = item.get("entity", {})
            props = e.get("properties", {})
            lines.append(f"📅 {props.get('month','?')} {props.get('title','?')} — {props.get('description','')}")
        return "\n".join(lines) if lines else "(无历史记录)"

    def get_graph_size(self) -> int:
        """返回图谱文件行数（粗略的记录数）。"""
        path = os.path.join(ONTOLOGY_SKILL_DIR, "memory", "ontology", "graph.jsonl")
        try:
            with open(path) as f:
                return sum(1 for _ in f)
        except FileNotFoundError:
            return 0


# ---------- 快捷指令（供 main.py 调用）----------

async def cmd_history(state: dict) -> str:
    """/记忆 指令：查询公司完整历史。"""
    bridge = OntologyBridge()
    lines = ["🏢 公司档案\n"]
    lines.append(f"名称：{state['meta']['company']}")
    lines.append(f"行业：{state['meta']['industry']}")
    lines.append(f"时间：{state['meta']['time']}")
    lines.append(f"资金：{state['finance']['cash']}万")
    lines.append(f"声望：{state['finance']['reputation']}")
    lines.append("\n👥 团队：")
    lines.append(bridge.query_team(state))
    lines.append("\n📜 历史：")
    lines.append(bridge.query_history(state))
    lines.append(f"\n图谱记录数：{bridge.get_graph_size()}")
    return "\n".join(lines)
