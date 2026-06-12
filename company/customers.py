from .ceo import get_talent_effects


def update_customers(state: dict) -> dict:
    cust = state.setdefault("customers", {
        "count": 0, "arr_per_customer": 0.5, "churn_rate": 0.10,
        "growth_rate": 0.0, "history": [],
    })
    if cust["count"] == 0 and cust["growth_rate"] == 0:
        return {"ok": True, "msg": "", "delta": 0, "arr": 0, "count": 0, "monthly_arr": 0, "churned": 0, "new": 0}

    churned = int(cust["count"] * cust["churn_rate"])
    if cust["growth_rate"] <= 0:
        auto_growth = 0
        rep = state["finance"].get("reputation", 0)
        talent_effects = get_talent_effects(state)
        # 天赋: 客户增长加成
        cust_growth_bonus = talent_effects.get("customer_growth_bonus", 0)
        if rep >= 50:
            auto_growth += rep // 50
        if cust_growth_bonus > 0:
            auto_growth = int(auto_growth * (1 + cust_growth_bonus))
        if state["staff"].get("marketing", 0) > 0:
            # 天赋: 营销效率加成
            marketing_eff = talent_effects.get("marketing_efficiency", 0)
            auto_growth += 5 * (1 + marketing_eff)
        if sum(1 for p in state.get("projects", []) if p.get("status") == "completed") > 0:
            auto_growth += 3
        cust["growth_rate"] = auto_growth
        if cust["count"] == 0 and auto_growth > 0:
            cust["count"] = 10
            churned = 0

    new_customers = int(cust["count"] * cust["growth_rate"] / 100)
    # Task 2: 客户增长对数衰减——防止后期爆炸
    if cust["count"] > 50:
        growth_cap = max(2, 50 // max(1, cust["count"] // 20))
        new_customers = min(new_customers, growth_cap)
    cust["count"] = max(0, cust["count"] - churned + new_customers)
    arr = round(cust["count"] * cust["arr_per_customer"], 2)
    monthly_arr = round(arr / 12, 2)

    hist = cust.setdefault("history", [])
    hist.append((state["meta"]["time"], cust["count"]))
    if len(hist) > 24:
        del hist[:-24]

    return {
        "ok": True, "msg": "",
        "delta": new_customers - churned,
        "churned": churned,
        "new": new_customers,
        "count": cust["count"],
        "arr": arr,
        "monthly_arr": monthly_arr,
    }
