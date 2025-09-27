"""
score_planner.planner
Educational CLI to plan improvements to a Legion-style merit score.
This is NOT affiliated with Legion and NOT an attempt to reverse-engineer its system.
"""

from __future__ import annotations
import argparse, json, sys, math, pathlib, datetime

DEFAULT_LIMITS = {
    "wallet": 500,
    "social": 300,
    "builder": 300
}

DEFAULT_WEIGHTS = {
    "wallet": 1.0,
    "social": 1.0,
    "builder": 1.0
}

CONFIG_PATH = pathlib.Path.home() / ".legion_score_planner" / "config.json"


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # default config
    cfg = {"limits": DEFAULT_LIMITS, "weights": DEFAULT_WEIGHTS}
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return cfg


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def compute_total(components, limits, weights):
    total = 0.0
    breakdown = {}
    for k, v in components.items():
        capped = clamp(v, 0, limits.get(k, v))
        score = capped * weights.get(k, 1.0)
        breakdown[k] = {"input": v, "capped": capped, "weighted": score}
        total += score
    return clamp(total, 0, sum(limits.values())), breakdown


def recommend_actions(components, limits, target):
    """Simple heuristics. We push where headroom is largest and suggest safe, ToS-compliant actions."""
    recs = []
    now = datetime.date.today().isoformat()

    # Headroom per component
    headroom = {k: max(0, limits[k] - components.get(k, 0)) for k in limits}
    # Sort by most headroom
    prio = sorted(headroom.items(), key=lambda x: x[1], reverse=True)

    for comp, space in prio:
        if space <= 0:
            continue
        if comp == "wallet":
            recs.append({
                "component": "wallet",
                "idea": "Increase quality on-chain activity (non-wash). Provide liquidity, deposit to reputable DeFi, bridge L2s prudently, interact with real protocols you actually use.",
                "notes": "Avoid spam/airdrops-only behavior; maintain security hygiene (hardware wallet, approvals)."
            })
        elif comp == "social":
            recs.append({
                "component": "social",
                "idea": "Strengthen authentic community signals: long-form threads, helpful replies, public dashboards, credible followers.",
                "notes": "Do NOT buy followers/engagement; that risks disqualification."
            })
        elif comp == "builder":
            recs.append({
                "component": "builder",
                "idea": "Contribute to open-source: PRs, issues, docs; maintain GitHub streaks; verifiable commits tied to your identity.",
                "notes": "Prefer impactful contributions over volume."
            })

    # If target provided, compute gap
    current_total, _ = compute_total(components, limits, {"wallet":1,"social":1,"builder":1})
    gap = max(0, target - current_total) if target else None
    return {"date": now, "headroom": headroom, "gap": gap, "actions": recs}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Heuristic planner for Legion-style score improvements.")
    parser.add_argument("--wallet", type=float, default=0, help="Current wallet/on-chain score (0-500 default cap)")
    parser.add_argument("--social", type=float, default=0, help="Current social/community score (0-300 default cap)")
    parser.add_argument("--builder", type=float, default=0, help="Current builder/contributor score (0-300 default cap)")
    parser.add_argument("--target", type=float, default=None, help="Target total score (0-1000)")
    parser.add_argument("--export", type=str, default=None, help="Export plan to file (json|md) based on extension")
    args = parser.parse_args(argv)

    cfg = load_config()
    limits = cfg.get("limits", DEFAULT_LIMITS)
    weights = cfg.get("weights", DEFAULT_WEIGHTS)

    components = {"wallet": args.wallet, "social": args.social, "builder": args.builder}
    total, breakdown = compute_total(components, limits, weights)
    plan = recommend_actions(components, limits, args.target)

    result = {
        "components": components,
        "limits": limits,
        "weights": weights,
        "total": total,
        "breakdown": breakdown,
        "plan": plan
    }

    if args.export:
        out = pathlib.Path(args.export)
        if out.suffix.lower() == ".json":
            out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        elif out.suffix.lower() == ".md":
            md = ["# Legion Score Plan (Heuristic)",
                  f"**Total (heuristic):** {total:.1f} / {sum(limits.values())}",
                  "## Breakdown"]
            for k, v in breakdown.items():
                md.append(f"- **{k.capitalize()}**: input={v['input']} → capped={v['capped']} → weighted={v['weighted']}")
            md.append("## Actions")
            for a in plan["actions"]:
                md.append(f"- **{a['component'].capitalize()}**: {a['idea']}  \n  _{a['notes']}_")
            out.write_text("\n".join(md), encoding="utf-8")
        else:
            print(f"Unknown export extension: {out.suffix}", file=sys.stderr)
            sys.exit(2)

    # Default stdout summary
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
