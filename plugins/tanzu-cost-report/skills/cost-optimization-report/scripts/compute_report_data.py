#!/usr/bin/env python3
"""
Turn raw Tanzu Hub GraphQL dumps into report_data.json for the cost
optimization report.

Expects a data directory containing (see SKILL.md for the exact queries
that produce each file):
  apps.json          - entityQuery.typed.tanzu.tas.application.query result
  services.json       - entityQuery.typed.tanzu.tas.serviceinstance.query result
  spaces.json          - entityQuery.typed.tanzu.tas.space.query result
  orgs.json            - {"entities": [{entityId, entityName, foundation}, ...]}
  foundations.json     - {"<guid>": "<display name>", ...}
  price_series.json    - {
                            "space_total_price": {entityId: daily_$},
                            "org_total_price": {entityId: daily_$},
                            "service_instance_price": {entityId: daily_$},
                            "app_rate_card": {"appInstanceHours": float, "appMemoryGbHours": float},
                            "service_rate_cards": {"<name>": unit_price, ...}
                          }
                          (values are DAILY totals -- see SKILL.md)

Usage:
  python3 compute_report_data.py --data-dir DIR --out report_data.json \\
      [--stale-days 120] [--now 2026-07-26]
"""
import argparse
import collections
import datetime
import json
import sys


def parse_dt(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def load(data_dir, name, path):
    try:
        return json.load(open(f"{data_dir}/{name}"))
    except FileNotFoundError:
        sys.exit(f"missing {data_dir}/{name} -- see SKILL.md for the query that produces it")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stale-days", type=int, default=120)
    ap.add_argument("--now", default=None, help="ISO date, defaults to UTC today")
    args = ap.parse_args()

    now = (
        datetime.datetime.fromisoformat(args.now).replace(tzinfo=datetime.timezone.utc)
        if args.now
        else datetime.datetime.now(datetime.timezone.utc)
    )
    cutoff = now - datetime.timedelta(days=args.stale_days)

    d = args.data_dir
    apps = load(d, "apps.json", d)["result"]["entityQuery"]["typed"]["tanzu"]["tas"]["application"]["query"]["entities"]
    services = load(d, "services.json", d)["result"]["entityQuery"]["typed"]["tanzu"]["tas"]["serviceinstance"]["query"]["entities"]
    spaces = load(d, "spaces.json", d)["result"]["entityQuery"]["typed"]["tanzu"]["tas"]["space"]["query"]["entities"]
    orgs = load(d, "orgs.json", d)["entities"]
    foundations = load(d, "foundations.json", d)
    prices = load(d, "price_series.json", d)

    org_name = {o["entityId"]: o["entityName"] for o in orgs}

    space_by_guid = {}
    for s in spaces:
        p = s["properties"]
        guid = s["entityId"].split(":")[-1]
        space_by_guid[guid] = {
            "entityId": s["entityId"], "name": s["entityName"], "foundation": p["foundation"],
            "orgGUID": p.get("organizationGUID"), "totalAppCount": p.get("totalAppCount"),
            "totalMemoryLimitMB": p.get("totalMemoryLimitMB"),
            "totalServiceInstanceCount": p.get("totalServiceInstanceCount"),
        }

    def org_id_for_space(sp):
        return f"vrn/provider:TAS/instance:{sp['foundation']}/Organization:{sp['orgGUID']}"

    def org_of_space(guid):
        sp = space_by_guid.get(guid)
        if not sp:
            return None
        return org_name.get(org_id_for_space(sp), "?")

    def space_display(guid):
        sp = space_by_guid.get(guid)
        if not sp:
            return f"unknown-space:{guid}"
        oname = org_of_space(guid)
        fname = foundations.get(sp["foundation"], sp["foundation"])
        return f"{oname}/{sp['name']} [{fname}]"

    APP_INST_RATE = prices["app_rate_card"]["appInstanceHours"]
    APP_MEM_RATE = prices["app_rate_card"]["appMemoryGbHours"]
    HOURS_PER_MONTH = 730

    def app_monthly_cost(p):
        inst = p.get("instanceCount") or 0
        mem_gb = (p.get("totalMemoryLimitMB") or 0) / 1024
        return inst * HOURS_PER_MONTH * APP_INST_RATE + inst * mem_gb * HOURS_PER_MONTH * APP_MEM_RATE

    out = {}

    nonsys = [a for a in apps if not a["properties"].get("systemApp")]
    started = [a for a in nonsys if a["properties"].get("state") == "STARTED"]
    stopped = [a for a in nonsys if a["properties"].get("state") == "STOPPED"]
    out["fleet"] = {
        "foundations": len(foundations),
        "orgs": len(orgs),
        "spaces": len(spaces),
        "apps_total": len(apps),
        "apps_nonsystem": len(nonsys),
        "apps_started": len(started),
        "apps_stopped": len(stopped),
        "services_total": len(services),
        "modeled_monthly_app_cost": round(sum(app_monthly_cost(a["properties"]) for a in nonsys), 2),
    }

    # NOTE on semantics: presence in a price_series dict means "queryable" (the
    # entityId-batched query returned data, including legitimate $0 rows); a nonzero
    # value means "has live spend today." These are different questions -- see
    # references/hub-graphql.md's "sum by (...) silently caps at 5 series" note. Org/space coverage
    # is reported as nonzero-spend counts, since virtually every org/space is
    # queryable once the query bug is avoided (the Application Rate Card is
    # typically Foundation-scoped, covering everything under it). Service instances
    # are the one place a real "no rate card exists" gap can occur.
    org_prices = prices["org_total_price"]
    space_prices = prices["space_total_price"]
    svc_prices = prices["service_instance_price"]
    org_nonzero = sum(1 for v in org_prices.values() if v)
    live_org_daily_total = sum(org_prices.values())

    # Spaces may be reported either as a full per-entity dict (space_total_price) or,
    # when the full sweep wasn't re-run, as verified aggregate counts
    # (space_coverage_summary) -- prefer the latter if present since it's still a
    # directly-measured number, just not broken out per-entity.
    space_summary = prices.get("space_coverage_summary")
    if space_summary:
        space_queried = space_summary["queried"]
        space_nonzero = space_summary["nonzero"]
    else:
        space_queried = len(space_prices)
        space_nonzero = sum(1 for v in space_prices.values() if v)

    # Match on (offering, plan) tuples, not plan name alone: plan names like
    # "standard" or "proxy" are reused across many unrelated offerings backed by
    # different ServicePlanGroup entities, so bare-name matching would falsely mark
    # an unrelated, still-unpriced offering as covered just because some other
    # offering with the same generic plan name has a rate card.
    coverage_cfg = prices.get("service_plan_group_coverage", {})
    covered_pairs = {tuple(p) for p in coverage_cfg.get("covered_offering_plan_pairs", [])}
    paid_services = [s for s in services if s["properties"].get("serviceOfferingName") != "user-provided"]
    services_with_rate_card = [
        s for s in paid_services
        if (s["properties"].get("serviceOfferingName"), s["properties"].get("plan")) in covered_pairs
    ] if covered_pairs else []

    out["metering_coverage"] = {
        "orgs_queried": len(org_prices),
        "orgs_nonzero_spend": org_nonzero,
        "total_orgs": len(orgs),
        "spaces_queried": space_queried,
        "spaces_nonzero_spend": space_nonzero,
        "total_spaces": len(spaces),
        "service_instances_queried": len(svc_prices),
        "service_instances_nonzero_spend": sum(1 for v in svc_prices.values() if v),
        "paid_service_instances": len(paid_services),
        "service_instances_with_rate_card": len(services_with_rate_card) if covered_pairs else None,
        "live_metered_monthly_total": round(live_org_daily_total * 30, 2),
    }

    # Tier 1: broken apps (routeless / phantom instances / crash-looping), deduped
    waste_apps = {}
    for a in apps:
        p = a["properties"]
        if p.get("systemApp") or p.get("state") != "STARTED":
            continue
        inst = p.get("instanceCount") or 0
        running = p.get("runningInstanceCount") or 0
        crashed = p.get("crashedInstanceCount") or 0
        routes = p.get("routes") or []
        reasons = []
        if not routes and inst > 0:
            reasons.append("no routes")
        if inst > running:
            reasons.append(f"{running}/{inst} instances running")
        if crashed > 0:
            reasons.append(f"{crashed} crashed")
        if reasons:
            waste_apps[a["entityId"]] = {
                "name": a["entityName"], "location": space_display(p.get("spaceGUID")),
                "instances": inst, "monthly_cost": round(app_monthly_cost(p), 2), "reasons": reasons,
            }
    tier1_list = sorted(waste_apps.values(), key=lambda x: -x["monthly_cost"])
    out["tier1_broken_apps"] = {
        "count": len(tier1_list),
        "total_monthly": round(sum(x["monthly_cost"] for x in tier1_list), 2),
        "items": tier1_list[:25],
    }

    # Tier 2: stale started apps
    stale = []
    for a in apps:
        p = a["properties"]
        if p.get("systemApp") or p.get("state") != "STARTED":
            continue
        upd = parse_dt(p.get("updatedAt"))
        if upd and upd < cutoff:
            stale.append({
                "name": a["entityName"], "location": space_display(p.get("spaceGUID")),
                "instances": p.get("instanceCount"), "age_days": (now - upd).days,
                "monthly_cost": round(app_monthly_cost(p), 2), "stack": p.get("stack"),
            })
    stale.sort(key=lambda x: -x["age_days"])
    out["tier2_stale_apps"] = {
        "count": len(stale),
        "total_monthly": round(sum(x["monthly_cost"] for x in stale), 2),
        "threshold_days": args.stale_days,
        "items": stale[:25],
    }

    # Tier 1b: orphaned services (paid offerings, 0 bound apps)
    orphaned = []
    by_offering = collections.Counter()
    for s in services:
        p = s["properties"]
        offering = p.get("serviceOfferingName")
        if offering == "user-provided":
            continue
        if p.get("boundAppCount") == 0:
            # A $0.00 reading is a REAL metered price, not a missing one -- several
            # offerings (AI Models, the Zero-Cost MCP servers) are deliberately
            # priced at $0.00/instance-hr. Test for presence in the dict, never
            # truthiness of the value, or those instances get mislabelled
            # "unmetered" in the report even though they carry a rate card.
            eid = s["entityId"]
            live_price = prices["service_instance_price"].get(eid)
            metered = eid in prices["service_instance_price"]
            has_rate_card = (offering, p.get("plan")) in covered_pairs if covered_pairs else None
            orphaned.append({
                "name": s["entityName"], "location": space_display(p.get("spaceGUID")),
                "offering": offering, "plan": p.get("plan"),
                "monthly_cost": round(live_price * 30, 2) if metered else None,
                "metered": metered,
                "has_rate_card": has_rate_card,
            })
            by_offering[offering] += 1
    orphaned.sort(key=lambda x: -(x["monthly_cost"] or 0))
    out["tier1_orphaned_services"] = {
        "count": len(orphaned),
        "priced_total_monthly": round(sum(x["monthly_cost"] for x in orphaned if x["monthly_cost"]), 2),
        # instances carrying real spend (> $0) vs. instances that returned any
        # reading at all (including a legitimate $0) -- two different questions
        "priced_count": sum(1 for x in orphaned if x["monthly_cost"]),
        "metered_count": sum(1 for x in orphaned if x["metered"]),
        "zero_priced_count": sum(1 for x in orphaned if x["metered"] and not x["monthly_cost"]),
        "no_rate_card_count": sum(1 for x in orphaned if x["has_rate_card"] is False),
        "paid_offering_population": sum(1 for s in services if s["properties"].get("serviceOfferingName") != "user-provided"),
        "by_offering": dict(by_offering.most_common()),
        "items": orphaned[:25],
    }

    # Top spaces / orgs by modeled cost
    space_cost = collections.defaultdict(float)
    space_apps = collections.defaultdict(int)
    space_stopped = collections.defaultdict(int)
    org_cost = collections.defaultdict(float)
    for a in apps:
        p = a["properties"]
        if p.get("systemApp"):
            continue
        g = p.get("spaceGUID")
        cost = app_monthly_cost(p)
        space_cost[g] += cost
        space_apps[g] += 1
        if p.get("state") != "STARTED":
            space_stopped[g] += 1
        org_cost[org_of_space(g)] += cost

    out["top_spaces_modeled"] = [
        {"location": space_display(g), "monthly_cost": round(c, 2), "apps": space_apps[g], "stopped": space_stopped[g]}
        for g, c in sorted(space_cost.items(), key=lambda x: -x[1])[:15]
    ]
    out["top_orgs_modeled"] = [
        {"org": o, "monthly_cost": round(c, 2)} for o, c in sorted(org_cost.items(), key=lambda x: -x[1])[:15]
    ]
    out["live_metered_orgs"] = sorted(
        [{"org": org_name.get(oid, "?"), "monthly_cost": round(daily * 30, 2)} for oid, daily in prices["org_total_price"].items()],
        key=lambda x: -x["monthly_cost"],
    )

    out["rate_cards"] = {"application": prices["app_rate_card"], "service": prices["service_rate_cards"]}
    out["foundations"] = foundations
    out["generated_at"] = now.date().isoformat()
    out["stale_threshold_days"] = args.stale_days

    json.dump(out, open(args.out, "w"), indent=2)
    print(f"wrote {args.out}")
    print(json.dumps(out["fleet"], indent=2))
    print(json.dumps(out["metering_coverage"], indent=2))


if __name__ == "__main__":
    main()
