#!/usr/bin/env python3
"""
Turn saved `queryStats` responses into price_series.json -- no hand
transcription of values.

Reads every *.json in --results whose filename starts with a known metric
name (that is how gen_stats_queries.py names its .gql files, so keep the
basenames when you save each response). Accepts either the raw
gql_execute_safe envelope ({"ok":true,"result":{...}}) or a bare
{"statsQuery":{...}}.

CRITICAL semantics, do not "simplify" these:
  * PRESENCE in the output dict means "Telemetry returned a reading for this
    entity". VALUE means "how much it costs". They are different questions.
  * A reading of 0 is a REAL price -- several offerings are deliberately
    priced at $0.00/instance-hr. It is recorded as 0, never dropped. An
    entity that returned no series at all is simply absent.
  * The last data point in the series is today's daily total. Telemetry
    always returns daily points regardless of intervalMins.

Usage:
  python3 parse_stats_results.py --results DIR --out price_series.json \\
      [--rate-cards rate_cards.json] [--coverage coverage.json]

--rate-cards takes the saved response of the applicationratecard /
serviceratecard query (SKILL.md Phase 1 step 6). --coverage takes the output
of resolve_plan_group_coverage.py assemble. Both are optional here but
required by compute_report_data.py, so supply them for a complete file.
"""
import argparse
import glob
import json
import os
import re

METRICS = ["org_total_price", "space_total_price", "service_instance_price"]


def unwrap(doc):
    return doc.get("result", doc)


def metric_for(basename):
    for m in METRICS:
        if basename.startswith(m):
            return m
    return None


def parse_stats_file(path):
    """-> [(entityId, latest_value)] across every alias in the response."""
    doc = unwrap(json.load(open(path)))
    sq = doc.get("statsQuery")
    if not sq:
        raise SystemExit(f"{path}: no statsQuery in response (did the query error?)")
    out = []
    for alias, entries in sq.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            eid = (e.get("entity") or {}).get("entityId")
            stats = e.get("stats") or []
            if not eid or not stats:
                continue
            data = stats[0].get("data") or []
            if not data:
                continue
            out.append((eid, data[-1]))
    return out


VRN_RE = re.compile(r'"(vrn/[^"]+)"')


def requested_ids(json_path):
    """entityIds asked for, read from the sibling .gql.

    Needed because a queryStats response omits entities entirely when Telemetry
    has no series for them -- so "absent from the response" alone cannot
    distinguish "we never asked" (a bug in the pull) from "we asked and the
    platform had nothing" (a real metering gap). Only the query text knows.
    """
    gql = json_path[:-len(".json")] + ".gql"
    if not os.path.exists(gql):
        return None
    return set(VRN_RE.findall(open(gql).read()))


def parse_rate_cards(path):
    plat = unwrap(json.load(open(path)))["entityQuery"]["typed"]["tanzu"]["platform"]

    app = {}
    app_entities = plat.get("applicationratecard", {}).get("query", {}).get("entities", [])
    if len(app_entities) > 1:
        print(f"  ! {len(app_entities)} application rate cards found; the report "
              f"assumes one platform-wide. Using '{app_entities[0].get('entityName')}'.")
    if app_entities:
        p = app_entities[0]["properties"]
        app = {"appInstanceHours": (p.get("appInstanceHours") or {}).get("unitPrice"),
               "appMemoryGbHours": (p.get("appMemoryGbHours") or {}).get("unitPrice")}

    svc = {}
    for e in plat.get("serviceratecard", {}).get("query", {}).get("entities", []):
        price = (e["properties"].get("serviceInstanceHours") or {}).get("unitPrice")
        svc[e["entityName"]] = price
    return app, svc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, help="directory of saved response .json files")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rate-cards", default=None)
    ap.add_argument("--coverage", default=None)
    ap.add_argument("--base", default=None,
                    help="existing price_series.json to merge into. Metrics with no "
                         "response files in --results are carried over untouched; "
                         "metrics that DO have files fully replace the base's copy. "
                         "Use when re-pulling one metric without re-querying the rest.")
    args = ap.parse_args()

    series = {m: {} for m in METRICS}
    seen_files = 0
    dupes = 0
    files_per_metric = {m: 0 for m in METRICS}
    queried = {m: set() for m in METRICS}
    unknown_requested = False

    for path in sorted(glob.glob(os.path.join(args.results, "*.json"))):
        base = os.path.basename(path)
        if base == "manifest.json":
            continue
        metric = metric_for(base)
        if metric is None:
            continue
        seen_files += 1
        files_per_metric[metric] += 1
        req = requested_ids(path)
        if req is None:
            unknown_requested = True
        else:
            queried[metric] |= req
        for eid, val in parse_stats_file(path):
            if eid in series[metric] and series[metric][eid] != val:
                dupes += 1
            series[metric][eid] = val

    if seen_files == 0:
        raise SystemExit(
            f"no metric-named .json files in {args.results}. Save each response using "
            f"the basename of its .gql (e.g. org_total_price_00.json).")

    if args.base:
        out = json.load(open(args.base))
        carried = []
        for m in METRICS:
            if files_per_metric[m]:
                out[m] = series[m]
            else:
                carried.append(f"{m} ({len(out.get(m, {}))} entities)")
        if carried:
            print(f"  carried over from --base: {', '.join(carried)}")
    else:
        out = dict(series)

    prev_q = (json.load(open(args.base)).get("_queried", {}) if args.base else {})
    out["_queried"] = {
        m: sorted(queried[m] if files_per_metric[m] else set(prev_q.get(m, [])))
        for m in METRICS
    }

    if args.rate_cards:
        app, svc = parse_rate_cards(args.rate_cards)
        out["app_rate_card"] = app
        out["service_rate_cards"] = svc

    if args.coverage:
        cov = json.load(open(args.coverage))
        out["service_plan_group_coverage"] = cov.get("service_plan_group_coverage", cov)

    json.dump(out, open(args.out, "w"), indent=1)

    print(f"parsed {seen_files} response file(s) -> {args.out}")
    for m in METRICS:
        d = out.get(m, {})
        zeros = sum(1 for v in d.values() if v == 0)
        print(f"  {m}: {len(d)} entities with a reading "
              f"({sum(1 for v in d.values() if v)} nonzero, {zeros} at a real $0.00)")
    for m in METRICS:
        q, got = len(out["_queried"][m]), len(out.get(m, {}))
        if q and q > got:
            print(f"  {m}: {q - got} of {q} queried entities returned no series at all "
                  f"(a real metering gap, not a missing query)")
    if unknown_requested:
        print("  ! some response files had no sibling .gql; queried-vs-returned "
              "cannot be distinguished for those")
    if dupes:
        print(f"  ! {dupes} entity/metric pairs appeared in more than one file with "
              f"differing values; last file won. Check for overlapping batches.")
    if not args.rate_cards and "app_rate_card" not in out:
        print("  ! no --rate-cards: price_series.json is incomplete for compute_report_data.py")
    if not args.coverage and "service_plan_group_coverage" not in out:
        print("  ! no --coverage: service-instance rate-card coverage will report as unknown")


if __name__ == "__main__":
    main()
