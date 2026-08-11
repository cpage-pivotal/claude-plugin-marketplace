#!/usr/bin/env python3
"""
Work out which (serviceOfferingName, plan) pairs sit behind a ServicePlanGroup
that has a Service Rate Card attached -- i.e. which service instances CAN be
priced at all.

Why it is this convoluted:
  * `serviceOfferingName` in services.json is the marketplace DISPLAY name
    ("VMware Tanzu for Postgres"); rate cards attach to ServicePlanGroup
    entities keyed by the broker's service GUID. There is no direct join.
  * Plan names are NOT unique. ~18 distinct ServicePlanGroups are named
    "standard". Matching on the bare plan name marks unrelated, unpriced
    offerings as covered -- this shipped once already. Always key on the
    (offering, plan) tuple.
  * The chain ServiceInstance -> ServicePlan -> ServicePlanGroup cannot be
    walked in one query: 3 levels of nesting returns INTERNAL. Hence two hops.
  * Batching many ids into the ServicePlan hop also intermittently returns
    INTERNAL on particular plans, so hop 2 uses one entityId per alias.

Flow:
  1. resolve_plan_group_coverage.py emit-hop1 --data-dir D --out-dir Q
     -> Q/hop1_00.gql (+ Q/hop1_map.json).  Run them, save as Q/hop1_00.json
  2. resolve_plan_group_coverage.py emit-hop2 --out-dir Q
     -> Q/hop2_00.gql (+ Q/hop2_map.json).  Run them, save as Q/hop2_00.json
  3. resolve_plan_group_coverage.py assemble --out-dir Q \\
        --rate-cards rate_cards.json --out coverage.json

If an alias is missing from a response (Hub returned INTERNAL for that one),
it is reported and skipped rather than silently treated as uncovered.
"""
import argparse
import glob
import json
import os

ALIASES_PER_CALL = 10


def unwrap(doc):
    return doc.get("result", doc)


def load_services(data_dir):
    doc = unwrap(json.load(open(os.path.join(data_dir, "services.json"))))
    return doc["entityQuery"]["typed"]["tanzu"]["tas"]["serviceinstance"]["query"]["entities"]


def write_calls(out_dir, prefix, blocks):
    """blocks: list of (alias, graphql_fragment). Groups into aliased calls."""
    paths = []
    for i in range(0, len(blocks), ALIASES_PER_CALL):
        chunk = blocks[i:i + ALIASES_PER_CALL]
        body = " ".join(frag for _, frag in chunk)
        q = ("query { entityQuery { typed { tanzu { tas { %s } } } } }" % body)
        p = os.path.join(out_dir, f"{prefix}_{i // ALIASES_PER_CALL:02d}.gql")
        open(p, "w").write(q)
        paths.append(p)
    return paths


def cmd_emit_hop1(args):
    services = load_services(args.data_dir)
    # one representative instance per distinct (offering, plan) pair
    rep = {}
    for s in services:
        p = s["properties"]
        off = p.get("serviceOfferingName")
        if off == "user-provided":
            continue
        rep.setdefault((off, p.get("plan")), s["entityId"])

    blocks, amap = [], {}
    for n, (pair, eid) in enumerate(sorted(rep.items(), key=lambda kv: (kv[0][0] or "", kv[0][1] or ""))):
        alias = f"p{n}"
        amap[alias] = list(pair)
        blocks.append((alias,
            f'{alias}: serviceinstance {{ query(entityId: ["{eid}"]) {{ entities {{ '
            f'relationshipsOut {{ isContainedIn {{ tanzu_tas_serviceplan {{ entityId }} }} }} '
            f'}} }} }}'))

    os.makedirs(args.out_dir, exist_ok=True)
    paths = write_calls(args.out_dir, "hop1", blocks)
    json.dump(amap, open(os.path.join(args.out_dir, "hop1_map.json"), "w"), indent=1)
    print(f"{len(rep)} distinct (offering, plan) pairs -> {len(paths)} call(s) in {args.out_dir}")
    print("run each hop1_NN.gql, save the response as hop1_NN.json, then: emit-hop2")


def read_alias_results(out_dir, prefix, leaf_keys):
    """-> {alias: entityId} pulling the leaf entityId out of each alias block."""
    # exclude the sidecar alias map, which shares the hopN_ prefix
    found = {}
    files = [p for p in sorted(glob.glob(os.path.join(out_dir, f"{prefix}_*.json")))
             if not p.endswith("_map.json")]
    if not files:
        raise SystemExit(f"no {prefix}_*.json in {out_dir} -- run the .gql files and save responses first")
    for path in files:
        doc = unwrap(json.load(open(path)))
        tas = doc["entityQuery"]["typed"]["tanzu"]["tas"]
        for alias, block in tas.items():
            ents = (block or {}).get("query", {}).get("entities") or []
            if not ents:
                continue
            node = ents[0]["relationshipsOut"]["isContainedIn"]
            for k in leaf_keys:
                node = (node or {}).get(k) if isinstance(node, dict) else None
                if node is None:
                    break
            if isinstance(node, dict) and node.get("entityId"):
                found[alias] = node["entityId"]
    return found


def cmd_emit_hop2(args):
    amap = json.load(open(os.path.join(args.out_dir, "hop1_map.json")))
    plans = read_alias_results(args.out_dir, "hop1", ["tanzu_tas_serviceplan"])

    missing = sorted(set(amap) - set(plans))
    if missing:
        print(f"! {len(missing)} pair(s) got no ServicePlan back (Hub INTERNAL); "
              f"they will be treated as unresolved: "
              + ", ".join("/".join(str(x) for x in amap[m]) for m in missing[:5]))

    blocks, amap2 = [], {}
    for alias, plan_id in sorted(plans.items()):
        amap2[alias] = amap[alias]
        blocks.append((alias,
            f'{alias}: serviceplan {{ query(entityId: ["{plan_id}"]) {{ entities {{ '
            f'relationshipsOut {{ isContainedIn {{ tanzu_platform_serviceplangroup {{ entityId }} }} }} '
            f'}} }} }}'))

    paths = write_calls(args.out_dir, "hop2", blocks)
    json.dump(amap2, open(os.path.join(args.out_dir, "hop2_map.json"), "w"), indent=1)
    print(f"{len(plans)} plan(s) -> {len(paths)} call(s). Save responses as hop2_NN.json, then: assemble")


def cmd_assemble(args):
    amap2 = json.load(open(os.path.join(args.out_dir, "hop2_map.json")))
    groups = read_alias_results(args.out_dir, "hop2", ["tanzu_platform_serviceplangroup"])

    plat = unwrap(json.load(open(args.rate_cards)))["entityQuery"]["typed"]["tanzu"]["platform"]
    carded = set()
    for e in plat.get("serviceratecard", {}).get("query", {}).get("entities", []):
        rel = ((e.get("relationshipsOut") or {}).get("isAssociatedWith") or {})
        for g in (rel.get("tanzu_platform_serviceplangroup") or {}).get("entities", []) or []:
            carded.add(g["entityId"])
    if not carded:
        raise SystemExit("no ServicePlanGroups attached to any rate card -- did the "
                         "rate-cards query include relationshipsOut.isAssociatedWith?")

    covered, uncovered, unresolved = [], [], []
    for alias, pair in amap2.items():
        gid = groups.get(alias)
        if gid is None:
            unresolved.append(pair)
        elif gid in carded:
            covered.append(pair)
        else:
            uncovered.append(pair)

    out = {"service_plan_group_coverage": {
        "covered_offering_plan_pairs": sorted(covered),
        "note": "every (offering, plan) pair whose ServicePlanGroup has an attached "
                "Service Rate Card; resolved per-offering via ServiceInstance -> "
                "ServicePlan -> ServicePlanGroup, never by bare plan name",
        "uncovered_offering_plan_pairs": sorted(uncovered),
        "unresolved_offering_plan_pairs": sorted(unresolved),
        "rate_carded_plan_groups": len(carded),
    }}
    json.dump(out, open(args.out, "w"), indent=1)
    print(f"{len(covered)} covered · {len(uncovered)} no rate card · "
          f"{len(unresolved)} unresolved -> {args.out}")
    if uncovered:
        print("  no rate card: " + ", ".join(f"{o}/{p}" for o, p in sorted(uncovered)[:10]))
    if unresolved:
        print("  ! unresolved pairs are excluded from covered; re-run their hop queries "
              "individually if the count matters")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("emit-hop1"); a.add_argument("--data-dir", required=True)
    a.add_argument("--out-dir", required=True); a.set_defaults(fn=cmd_emit_hop1)

    b = sub.add_parser("emit-hop2"); b.add_argument("--out-dir", required=True)
    b.set_defaults(fn=cmd_emit_hop2)

    c = sub.add_parser("assemble"); c.add_argument("--out-dir", required=True)
    c.add_argument("--rate-cards", required=True); c.add_argument("--out", required=True)
    c.set_defaults(fn=cmd_assemble)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
