#!/usr/bin/env python3
"""
Generate ready-to-paste `queryStats` GraphQL batches for the cost report's
live-price pull (SKILL.md Phase 1, step 7).

Why this exists: the entityId-batched form of queryStats is the only query
shape that doesn't silently cap at 5 series (see references/hub-graphql.md), but it means
pasting hundreds of 110-character VRNs by hand. This builds them.

Hard limits encoded here:
  * <=20 entityIds per queryStats call -- above that Hub returns a clean
    BAD_REQUEST ("Cannot query for more than 20 entity ids ...").
  * Several such calls are aliased into one request (b0, b1, ...) to cut
    round trips. --per-call controls how many.

Telemetry quirks encoded here:
  * intervalMins is ignored for the Telemetry namespace -- it always returns
    daily points -- but it must still be supplied.
  * A time window is required; without startTime/endTime the call returns [].
  * A 1-day window yields 2 points; the LAST one is today's daily total.

Usage:
  python3 gen_stats_queries.py --data-dir DIR --out-dir DIR \\
      [--start 2026-07-26] [--end 2026-07-27] \\
      [--services orphaned|paid] [--per-call 7]

Save each response to <out-dir>/<same basename>.json, then feed the directory
to parse_stats_results.py -- that script infers the metric from the filename,
so do not rename the files.
"""
import argparse
import json
import os

BATCH = 20  # Hub's hard cap per queryStats call

METRICS = {
    "org_total_price": "Organization",
    "space_total_price": "Space",
    "service_instance_price": "ServiceInstance",
}


def load(path, *keys):
    d = json.load(open(path))
    d = d.get("result", d)
    for k in keys:
        d = d[k]
    return d


def entity_ids(data_dir, services_scope):
    orgs = [o["entityId"] for o in json.load(open(f"{data_dir}/orgs.json"))["entities"]]

    spaces = [e["entityId"] for e in load(
        f"{data_dir}/spaces.json", "entityQuery", "typed", "tanzu", "tas",
        "space", "query", "entities")]

    svc_entities = load(
        f"{data_dir}/services.json", "entityQuery", "typed", "tanzu", "tas",
        "serviceinstance", "query", "entities")
    paid = [e for e in svc_entities
            if e["properties"].get("serviceOfferingName") != "user-provided"]
    if services_scope == "orphaned":
        svc = [e["entityId"] for e in paid
               if (e["properties"].get("boundAppCount") or 0) == 0]
    else:
        svc = [e["entityId"] for e in paid]

    return {"org_total_price": orgs,
            "space_total_price": spaces,
            "service_instance_price": svc}


def build_calls(metric, ids, start, end, per_call):
    batches = [ids[i:i + BATCH] for i in range(0, len(ids), BATCH)]
    calls = []
    for i in range(0, len(batches), per_call):
        parts = []
        for j, b in enumerate(batches[i:i + per_call]):
            idlist = ",".join(f'"{x}"' for x in b)
            parts.append(
                f'b{j}: queryStats(entityId: [{idlist}] '
                f'input: {{namespace: "Telemetry", queryString: "{metric}", '
                f'startTime: "{start}T00:00:00.000Z", endTime: "{end}T00:00:00.000Z", '
                f'intervalMins: 1440}}) '
                f'{{ entity {{ entityId }} stats {{ data }} }}'
            )
        calls.append("query { statsQuery { " + " ".join(parts) + " } }")
    return calls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--start", default=None, help="ISO date, default: --end minus 1 day")
    ap.add_argument("--end", default=None, help="ISO date, default: UTC today")
    ap.add_argument("--services", choices=["orphaned", "paid"], default="paid",
                    help="'paid' (all non-user-provided, the safe default) or "
                         "'orphaned' (0 bound apps only -- SKILL.md's stated minimum, "
                         "but it understates the metering-coverage tile)")
    ap.add_argument("--per-call", type=int, default=7,
                    help="how many 20-id batches to alias into one request")
    args = ap.parse_args()

    import datetime
    end = args.end or datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    start = args.start or (datetime.date.fromisoformat(end) - datetime.timedelta(days=1)).isoformat()

    os.makedirs(args.out_dir, exist_ok=True)
    ids = entity_ids(args.data_dir, args.services)

    manifest = {}
    for metric, id_list in ids.items():
        calls = build_calls(metric, id_list, start, end, args.per_call)
        for k, q in enumerate(calls):
            name = f"{metric}_{k:02d}.gql"
            open(f"{args.out_dir}/{name}", "w").write(q)
        manifest[metric] = {"entities": len(id_list), "calls": len(calls)}
        print(f"{metric}: {len(id_list)} ids -> {len(calls)} call(s)")

    manifest["_window"] = {"start": start, "end": end,
                           "services_scope": args.services}
    json.dump(manifest, open(f"{args.out_dir}/manifest.json", "w"), indent=1)
    print(f"\nwrote {args.out_dir}/  (save each response as <basename>.json alongside)")


if __name__ == "__main__":
    main()
