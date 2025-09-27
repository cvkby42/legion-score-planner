from score_planner.planner import compute_total

def test_compute_total_basic():
    total, breakdown = compute_total(
        {"wallet": 100, "social": 50, "builder": 25},
        {"wallet": 500, "social": 300, "builder": 300},
        {"wallet": 1.0, "social": 1.0, "builder": 1.0},
    )
    assert int(total) == 175
    assert breakdown["wallet"]["capped"] == 100
