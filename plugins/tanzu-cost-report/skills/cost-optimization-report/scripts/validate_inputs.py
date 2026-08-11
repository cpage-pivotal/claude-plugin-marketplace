#!/usr/bin/env python3
"""
Preflight the cost-report inputs before compute_report_data.py runs.

This exists because every wrong number this report has published came from an
input problem that looked fine downstream. Each check below corresponds to a
bug that actually shipped:

  E1  partial service_instance_price pull  -- a stale 5-entry dict was carried
      across regenerations, so dozens of priced instances rendered "unmetered"
  E2  orphaned instances never queried     -- the rows the report is *about*
      silently show no price
  W1  entity/price snapshot drift          -- prices from a different day than
      the entity dump
  W2  entities missing from a price dict   -- the group-by query cap (5 series)
      or a short batch, showing up as absent orgs/spaces
  W3  offerings with no rate card          -- the real, fixable finding; worth
      printing so it is never mistaken for a query gap

Exit status: 1 if any ERROR fired, else 0. Warnings never fail the run.

Usage:
  python3 validate_inputs.py --data-dir DIR [--max-age-hours 36] [--strict]
"""
import argparse
import datetime
import json
import os
import sys

ERRORS = []
WARNINGS = []
NOTES = []


def err(code, msg):
    ERRORS.append(f"[{code}] {msg}")


def warn(code, msg):
    WARNINGS.append(f"[{code}] {msg}")


def note(msg):
    NOTES.append(msg)


def load(d, name, *keys):
    path = os.path.join(d, name)
    if not os.path.exists(path):
        raise SystemExit(f"missing {path} -- see SKILL.md for the query that produces it")
    doc = json.load(open(path))
    doc = doc.get("result", doc)
    for k in keys:
        doc = doc[k]
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--max-age-hours", type=float, default=36.0)
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as errors")
    args = ap.parse_args()
    d = args.data_dir

    apps = load(d, "apps.json", "entityQuery", "typed", "tanzu", "tas", "application", "query", "entities")
    services = load(d, "services.json", "entityQuery", "typed", "tanzu", "tas", "serviceinstance", "query", "entities")
    spaces = load(d, "spaces.json", "entityQuery", "typed", "tanzu", "tas", "space", "query", "entities")
    orgs = json.load(open(os.path.join(d, "orgs.json")))["entities"]
    prices = json.load(open(os.path.join(d, "price_series.json")))

    org_prices = prices.get("org_total_price", {})
    space_prices = prices.get("space_total_price", {})
    svc_prices = prices.get("service_instance_price", {})

    paid = [s for s in services if s["properties"].get("serviceOfferingName") != "user-provided"]
    orphaned = [s for s in paid if (s["properties"].get("boundAppCount") or 0) == 0]

    note(f"{len(apps)} apps · {len(services)} service instances "
         f"({len(paid)} paid, {len(orphaned)} orphaned) · {len(orgs)} orgs · {len(spaces)} spaces")

    # --- E1: is the service price pull plausibly complete? -------------------
    queried = sum(1 for s in paid if s["entityId"] in svc_prices)
    pct = queried / len(paid) * 100 if paid else 0
    if queried == 0:
        err("E1", "service_instance_price has no entries for any paid instance -- "
                  "the pull never happened or the file is stale")
    elif queried < len(paid) * 0.10:
        err("E1", f"service_instance_price covers only {queried} of {len(paid)} paid "
                  f"instances ({pct:.0f}%). This is the stale-dict failure mode; re-pull "
                  f"before trusting any 'unmetered' count.")
    elif queried < len(paid):
        warn("W0", f"service_instance_price covers {queried} of {len(paid)} paid instances "
                   f"({pct:.0f}%). Fine if you scoped to orphaned deliberately, but the "
                   f"metering-coverage tile will understate reality.")

    # --- E2: every orphaned instance must have been queried ------------------
    # "no reading" splits two ways, and only the query text can tell them apart:
    # never queried (a bug in the pull -> ERROR) vs. queried and Telemetry had
    # nothing (a real metering gap -> WARN). parse_stats_results.py records the
    # requested ids in _queried for exactly this.
    queried_svc = set(prices.get("_queried", {}).get("service_instance_price", []))
    missing_orph = [s for s in orphaned if s["entityId"] not in svc_prices]
    if missing_orph:
        cov = prices.get("service_plan_group_coverage", {})
        pairs = {tuple(p) for p in cov.get("covered_offering_plan_pairs", [])}
        never_asked = [s for s in missing_orph if s["entityId"] not in queried_svc] \
            if queried_svc else missing_orph
        asked_no_data = [s for s in missing_orph if s not in never_asked]
        carded = [s for s in never_asked
                  if (s["properties"].get("serviceOfferingName"),
                      s["properties"].get("plan")) in pairs]
        if carded:
            err("E2", f"{len(carded)} orphaned instance(s) were never queried despite "
                      f"having a rate card -- re-run the relevant gen_stats_queries.py "
                      f"batch; do not publish a report that calls them unmetered.")
        elif never_asked and not queried_svc:
            err("E2", f"{len(never_asked)} of {len(orphaned)} orphaned instances have no "
                      f"price reading and no _queried record exists, so this cannot be "
                      f"distinguished from a missing query. Re-parse with "
                      f"parse_stats_results.py so _queried is populated.")
        if asked_no_data:
            carded_nd = sum(1 for s in asked_no_data
                            if (s["properties"].get("serviceOfferingName"),
                                s["properties"].get("plan")) in pairs)
            warn("W5", f"{len(asked_no_data)} orphaned instance(s) were queried but "
                       f"Telemetry returned no series ({carded_nd} of them have a rate "
                       f"card -- likely provisioned too recently to have metered, or a "
                       f"real metering gap worth raising with the platform team).")

    # --- W1: snapshot drift --------------------------------------------------
    try:
        svc_mtime = os.path.getmtime(os.path.join(d, "services.json"))
        price_mtime = os.path.getmtime(os.path.join(d, "price_series.json"))
        drift_h = abs(svc_mtime - price_mtime) / 3600
        if drift_h > args.max_age_hours:
            warn("W1", f"services.json and price_series.json were written "
                       f"{drift_h:.1f}h apart (limit {args.max_age_hours}h) -- entity and "
                       f"price snapshots may not describe the same estate.")
        newest = max(svc_mtime, price_mtime)
        age_h = (datetime.datetime.now().timestamp() - newest) / 3600
        if age_h > args.max_age_hours:
            warn("W1", f"newest input is {age_h:.1f}h old; the report will be stamped today.")
    except OSError:
        pass

    # --- W2: entities absent from the price dicts ----------------------------
    for label, entities, pricedict in (
            ("orgs", [o["entityId"] for o in orgs], org_prices),
            ("spaces", [s["entityId"] for s in spaces], space_prices)):
        missing = [e for e in entities if e not in pricedict]
        if missing:
            warn("W2", f"{len(missing)} of {len(entities)} {label} have no price reading. "
                       f"If this is ~5 per call, you used a `sum by (...)` group-by query "
                       f"instead of the entityId form -- see references/hub-graphql.md.")

    # --- W3: offerings with genuinely no rate card ---------------------------
    cov = prices.get("service_plan_group_coverage")
    if not cov:
        warn("W3", "no service_plan_group_coverage in price_series.json -- rate-card "
                   "coverage cannot be computed; run resolve_plan_group_coverage.py")
    else:
        pairs = {tuple(p) for p in cov.get("covered_offering_plan_pairs", [])}
        uncovered = {}
        for s in paid:
            key = (s["properties"].get("serviceOfferingName"), s["properties"].get("plan"))
            if key not in pairs:
                uncovered[key] = uncovered.get(key, 0) + 1
        if uncovered:
            listed = ", ".join(f"{o}/{p} ({n})" for (o, p), n in
                               sorted(uncovered.items(), key=lambda kv: -kv[1])[:8])
            note(f"offerings with NO rate card ({sum(uncovered.values())} instances): {listed}")
        # sanity: bare plan names must not be the matching key
        bare = [p for p in pairs if not isinstance(p, tuple) or len(p) != 2]
        if bare:
            err("E3", "covered_offering_plan_pairs contains non-(offering, plan) entries. "
                      "Plan names like 'standard' collide across offerings; matching on "
                      "them alone marks unpriced offerings as covered.")

    # --- rate cards present --------------------------------------------------
    if not prices.get("app_rate_card", {}).get("appInstanceHours"):
        err("E4", "app_rate_card.appInstanceHours missing -- every modeled cost will be wrong")

    # --- report --------------------------------------------------------------
    for n in NOTES:
        print(f"  · {n}")
    for w in WARNINGS:
        print(f"  WARN  {w}")
    for e in ERRORS:
        print(f"  ERROR {e}")

    if ERRORS:
        print(f"\n{len(ERRORS)} error(s) -- fix before publishing.")
        return 1
    if WARNINGS and args.strict:
        print(f"\n{len(WARNINGS)} warning(s), --strict.")
        return 1
    print(f"\nOK ({len(WARNINGS)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
