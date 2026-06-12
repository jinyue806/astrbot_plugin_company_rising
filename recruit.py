def recruit(state: dict, candidate: dict) -> dict:
    if state["ceo"]["ap"] < 1:
        return {"ok": False, "msg": "⚠️ 行动点不足，无法招聘。"}
    role = candidate["role"]
    state["staff"][role] = state["staff"].get(role, 0) + 1
    state["staff"]["total_salary"] = round(
        state["staff"]["total_salary"] + candidate["salary"], 2
    )
    state["ceo"]["ap"] -= 1
    employee = dict(candidate)
    employee.setdefault("loyalty", 70)
    employee.setdefault("market_salary", employee.get("salary", 0))
    employee.setdefault("status", "active")
    state.setdefault("employees", []).append(employee)
    return {"ok": True, "msg": "", "employee": employee}
