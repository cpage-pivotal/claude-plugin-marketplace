#!/usr/bin/env python3
"""
Render report_data.json (from compute_report_data.py) into a self-contained
HTML report.

Visual design ported from the "Cost Optimization Report.dc.html" Claude
Design mockup (project c0f6d1e9-566b-482b-9aae-81632d1c77b7, "FinOps Report
Redesign"). Two adaptations from that mockup, both required for this to run
as a self-contained Artifact:
  - No support.js / <x-dc> runtime -- that's Claude Design's editor-only
    component format. The layout/CSS is ported 1:1; the {{ }} / <sc-for>
    template holes become plain client-side JS (see RENDER_JS below).
  - No Google Fonts <link> -- Artifacts block outside network requests
    (fonts, CDNs, images). Newsreader/Public Sans fall back to system serif
    / sans-serif stacks. Font sizes, weights, and letter-spacing are
    unchanged, so the layout reads the same; only the exact typeface differs.
    If the user later hosts these fonts as data: URIs, swap them back in.

Usage:
  python3 build_report_html.py --data report_data.json --out report.html
"""
import argparse
import json


HEAD_STYLE = """
  html, body { margin:0; }
  body { background:#e7e4dd; font-family:"Public Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; -webkit-font-smoothing:antialiased; }
  a { color:#2a78d6; text-decoration:none; }
  a:hover { color:#1b5fb0; text-decoration:underline; }
  .serif { font-family:"Newsreader",ui-serif,Georgia,"Times New Roman",serif; }
"""

RENDER_JS = r"""
const DATA = __DATA_JSON__;

const money = v => '$' + Math.round(v).toLocaleString('en-US');
const pctStr = (v, max) => (max ? (v / max * 100).toFixed(1) : 0) + '%';
const splitLoc = s => {
  const m = s.match(/^(.*?) \[(.*)\]$/);
  return { path: m ? m[1] : s, found: m ? m[2].split('.')[0] : '' };
};
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function renderBars(elId, items, { labelKey, valKey, valFmt, subKey, cols, gradient }) {
  const el = document.getElementById(elId);
  const max = Math.max(...items.map(d => d[valKey]), 1);
  el.innerHTML = items.map(d => `
    <div style="display:grid;grid-template-columns:${cols};align-items:center;gap:12px;">
      <div style="overflow:hidden;">
        <div style="font:500 13.5px/1.3 'Public Sans';color:#3a3a37;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${esc(d[labelKey])}">${esc(d[labelKey])}</div>
        ${subKey ? `<div style="font:450 11px/1 'Public Sans';color:#a19f95;margin-top:2px;">${esc(d[subKey])}</div>` : ''}
      </div>
      <div style="height:20px;background:#eeece6;border-radius:5px;overflow:hidden;"><div style="height:100%;width:${pctStr(d[valKey], max)};background:${gradient};border-radius:5px;"></div></div>
      <div style="text-align:right;font:600 13.5px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#52514e;">${valFmt(d[valKey])}</div>
    </div>
  `).join('');
}

function renderTable(elId, rows, renderRow) {
  document.getElementById(elId).innerHTML = rows.map(renderRow).join('');
}

const tdBase = 'padding:11px 16px;border-bottom:1px solid #eeece6;vertical-align:top;';

// Section 02 -- top orgs / top spaces
const orgsSrc = DATA.top_orgs_modeled.slice(0, 10);
renderBars('bars-orgs', orgsSrc, { labelKey: 'org', valKey: 'monthly_cost', valFmt: money, cols: '150px 1fr 78px', gradient: 'linear-gradient(90deg,#2a78d6,#5a9ae6)' });

const spacesSrc = DATA.top_spaces_modeled.slice(0, 10).map(d => {
  const l = splitLoc(d.location);
  return { ...d, pathLabel: l.path, sub: d.apps + ' apps' + (d.stopped ? ' · ' + d.stopped + ' stopped' : '') };
});
renderBars('bars-spaces', spacesSrc, { labelKey: 'pathLabel', valKey: 'monthly_cost', valFmt: money, subKey: 'sub', cols: '180px 1fr 78px', gradient: 'linear-gradient(90deg,#1baf7a,#4fc79a)' });

// Section 03 -- broken apps
renderTable('tbl-broken', DATA.tier1_broken_apps.items, d => {
  const l = splitLoc(d.location);
  const reasons = d.reasons.map(r => `<span style="font:500 11px/1.3 'Public Sans';color:#d03b3b;background:#fbeceb;border:1px solid #f2cfcc;border-radius:5px;padding:3px 7px;">${esc(r)}</span>`).join('');
  return `<tr>
    <td style="${tdBase}font-weight:500;color:#0b0b0b;">${esc(d.name)}</td>
    <td style="${tdBase}"><span style="color:#52514e;">${esc(l.path)}</span> <span style="font:500 10.5px/1 'Public Sans';color:#8f8d82;background:#eeece6;border-radius:4px;padding:2px 5px;">${esc(l.found)}</span></td>
    <td style="${tdBase}text-align:right;font-variant-numeric:tabular-nums;color:#52514e;">${d.instances}</td>
    <td style="${tdBase}"><div style="display:flex;flex-wrap:wrap;gap:4px;">${reasons}</div></td>
    <td style="${tdBase}text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:#0b0b0b;">${money(d.monthly_cost)}</td>
  </tr>`;
});

// Section 04 -- stale apps
renderTable('tbl-stale', DATA.tier2_stale_apps.items, d => {
  const l = splitLoc(d.location);
  return `<tr>
    <td style="${tdBase}font-weight:500;color:#0b0b0b;">${esc(d.name)}</td>
    <td style="${tdBase}"><span style="color:#52514e;">${esc(l.path)}</span> <span style="font:500 10.5px/1 'Public Sans';color:#8f8d82;background:#eeece6;border-radius:4px;padding:2px 5px;">${esc(l.found)}</span></td>
    <td style="${tdBase}text-align:right;font-variant-numeric:tabular-nums;color:#52514e;">${d.instances}</td>
    <td style="${tdBase}text-align:right;font-variant-numeric:tabular-nums;color:#eda100;font-weight:600;">${d.age_days}</td>
    <td style="${tdBase}color:#7a786f;font-size:12.5px;">${esc(d.stack || '—')}</td>
    <td style="${tdBase}text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:#0b0b0b;">${money(d.monthly_cost)}</td>
  </tr>`;
});
document.getElementById('stale-shown').textContent = DATA.tier2_stale_apps.items.length;
document.getElementById('stale-total').textContent = DATA.tier2_stale_apps.count;

// Section 05 -- orphaned services
const offSrc = Object.entries(DATA.tier1_orphaned_services.by_offering).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([k, v]) => ({ offering: k, count: v }));
renderBars('bars-offerings', offSrc, { labelKey: 'offering', valKey: 'count', valFmt: v => v + ' idle', cols: '280px 1fr 76px', gradient: 'linear-gradient(90deg,#eb6834,#f28b63)' });

renderTable('tbl-orphans', DATA.tier1_orphaned_services.items, d => {
  const l = splitLoc(d.location);
  // $0.00 is a real metered price (AI Models / Zero-Cost MCP cards are priced at
  // $0.00/instance-hr) -- only a null monthly_cost means we have no reading.
  const metered = d.metered !== undefined ? d.metered : d.monthly_cost != null;
  const noCard = d.has_rate_card === false;
  return `<tr>
    <td style="${tdBase}font-weight:500;color:#0b0b0b;">${esc(d.name)}</td>
    <td style="${tdBase}"><span style="color:#52514e;">${esc(l.path)}</span> <span style="font:500 10.5px/1 'Public Sans';color:#8f8d82;background:#eeece6;border-radius:4px;padding:2px 5px;">${esc(l.found)}</span></td>
    <td style="${tdBase}color:#52514e;">${esc(d.offering)}</td>
    <td style="${tdBase}color:#7a786f;font-size:12.5px;">${esc(d.plan)}</td>
    <td style="${tdBase}text-align:right;font-variant-numeric:tabular-nums;font-weight:600;color:${metered && d.monthly_cost ? '#0b0b0b' : '#a19f95'};">${metered ? money(d.monthly_cost) : (noCard ? 'no rate card' : 'no reading')}</td>
  </tr>`;
});
document.getElementById('orphan-shown').textContent = DATA.tier1_orphaned_services.items.length;
document.getElementById('orphan-total').textContent = DATA.tier1_orphaned_services.count;

// Section 06 -- rate cards
const rateRows = [
  { card: 'Application — instance-hour', price: '$' + DATA.rate_cards.application.appInstanceHours + ' / inst-hr' },
  { card: 'Application — memory GB-hour', price: '$' + DATA.rate_cards.application.appMemoryGbHours + ' / GB-hr' },
  ...Object.entries(DATA.rate_cards.service).map(([k, v]) => ({ card: k, price: '$' + v + ' / hr' }))
];
document.getElementById('rate-cards').innerHTML = rateRows.map(r => `
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:10px;padding:16px 18px;display:flex;justify-content:space-between;align-items:center;gap:14px;">
    <span style="font:450 13.5px/1.35 'Public Sans';color:#52514e;">${esc(r.card)}</span>
    <span style="font:600 14px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#0b0b0b;white-space:nowrap;">${esc(r.price)}</span>
  </div>
`).join('');
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = json.load(open(args.data))

    total_recoverable = round(
        data["tier1_broken_apps"]["total_monthly"]
        + data["tier2_stale_apps"]["total_monthly"]
        + data["tier1_orphaned_services"]["priced_total_monthly"],
        2,
    )
    annualized = round(total_recoverable * 12)
    flagged_count = (
        data["tier1_broken_apps"]["count"]
        + data["tier2_stale_apps"]["count"]
        + data["tier1_orphaned_services"]["count"]
    )

    foundations = data.get("foundations", {})
    foundation_names = sorted(set(foundations.values())) or ["Tanzu foundations"]
    foundation_badges = "".join(
        f'<span style="font:500 12.5px/1 \'Public Sans\';color:#52514e;background:#f4f2ec;border:1px solid #e4e2dc;border-radius:999px;padding:7px 12px;">{n}</span>'
        for n in foundation_names
    )
    foundation_footer_line = " · ".join(f"{n} ({g})" for g, n in foundations.items()) or "—"

    mc = data["metering_coverage"]
    org_pct = round(mc["orgs_nonzero_spend"] / mc["total_orgs"] * 100, 1) if mc["total_orgs"] else 0
    space_pct = round(mc["spaces_nonzero_spend"] / mc["total_spaces"] * 100, 1) if mc["total_spaces"] else 0
    svc_rate_card_count = mc.get("service_instances_with_rate_card")
    svc_pct = round(svc_rate_card_count / mc["paid_service_instances"] * 100, 1) if svc_rate_card_count is not None and mc["paid_service_instances"] else None

    generated_at = data.get("generated_at", "—")
    stale_days = data.get("stale_threshold_days", data["tier2_stale_apps"]["threshold_days"])

    fleet = data["fleet"]

    html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tanzu Foundation Cost Optimization Report</title>
<style>""" + HEAD_STYLE + """</style>
</head>
<body>

<div style="background:#e7e4dd;padding:40px 24px 72px;color:#0b0b0b;">
<div style="max-width:1140px;margin:0 auto;background:#fcfcfb;border:1px solid #e0ddd5;border-radius:16px;box-shadow:0 1px 2px rgba(30,26,18,.04),0 24px 60px -28px rgba(30,26,18,.22);overflow:hidden;">

<div style="height:5px;background:linear-gradient(90deg,#2a78d6 0%,#1baf7a 34%,#eda100 67%,#eb6834 100%);"></div>

<div style="padding:52px 56px 44px;">

<!-- MASTHEAD -->
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:40px;flex-wrap:wrap;">
  <div style="flex:1 1 480px;min-width:320px;">
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.16em;text-transform:uppercase;color:#eb6834;margin-bottom:18px;">FinOps Review &middot; Tanzu Platform</div>
    <h1 class="serif" style="font:500 44px/1.05 'Newsreader',serif;letter-spacing:-.015em;margin:0 0 16px;max-width:14ch;">Cost Optimization Report</h1>
    <p style="font:400 16px/1.55 'Public Sans';color:#52514e;margin:0;max-width:52ch;">A structural review of provisioned spend, waste, and metering blind spots across """ + str(fleet["foundations"]) + """ Tanzu foundation""" + ("s" if fleet["foundations"] != 1 else "") + """ &mdash; with the recoverable dollars ranked by confidence.</p>
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:22px;">
      """ + foundation_badges + """
      <span style="font:500 12.5px/1 'Public Sans';color:#52514e;background:#f4f2ec;border:1px solid #e4e2dc;border-radius:999px;padding:7px 12px;">Generated """ + generated_at + """</span>
      <span style="font:500 12.5px/1 'Public Sans';color:#52514e;background:#f4f2ec;border:1px solid #e4e2dc;border-radius:999px;padding:7px 12px;">""" + str(stale_days) + """&#8209;day staleness threshold</span>
    </div>
  </div>
  <div style="flex:0 0 auto;background:#0b0b0b;border-radius:14px;padding:26px 30px;min-width:236px;">
    <div style="font:600 11px/1 'Public Sans';letter-spacing:.14em;text-transform:uppercase;color:#8f8d82;margin-bottom:14px;">Recoverable now</div>
    <div class="serif" style="font:500 46px/1 'Newsreader',serif;color:#39d98a;font-variant-numeric:tabular-nums;letter-spacing:-.01em;">$""" + f"{total_recoverable:,.0f}" + """<span style="font:500 20px/1 'Public Sans';color:#8f8d82;">/mo</span></div>
    <div style="font:400 13.5px/1.5 'Public Sans';color:#c3c2b7;margin-top:12px;max-width:22ch;">Across confirmed, live-metered findings &mdash; before extending coverage.</div>
    <div style="height:1px;background:#2a2a26;margin:18px 0 14px;"></div>
    <div style="font:400 13px/1.5 'Public Sans';color:#8f8d82;">Annualized <span style="color:#fff;font-weight:600;">&approx; $""" + f"{annualized:,.0f}" + """</span></div>
  </div>
</div>

<!-- KPI ROW -->
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-top:40px;">
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;border-top:3px solid #1baf7a;">
    <div style="font:600 30px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#0b0b0b;">$""" + f"{total_recoverable:,.0f}" + """<span style="font-size:16px;color:#7a786f;font-weight:500;">/mo</span></div>
    <div style="font:450 13px/1.4 'Public Sans';color:#52514e;margin-top:8px;">Recoverable across confirmed findings</div>
  </div>
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;border-top:3px solid #2a78d6;">
    <div style="font:600 30px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#0b0b0b;">$""" + f"{fleet['modeled_monthly_app_cost']:,.0f}" + """<span style="font-size:16px;color:#7a786f;font-weight:500;">/mo</span></div>
    <div style="font:450 13px/1.4 'Public Sans';color:#52514e;margin-top:8px;">Modeled app footprint (list&#8209;rate)</div>
  </div>
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;border-top:3px solid #eda100;">
    <div style="font:600 30px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#0b0b0b;">$""" + f"{mc['live_metered_monthly_total']:,.0f}" + """<span style="font-size:16px;color:#7a786f;font-weight:500;">/mo</span></div>
    <div style="font:450 13px/1.4 'Public Sans';color:#52514e;margin-top:8px;">Live&#8209;metered spend (""" + str(mc["orgs_nonzero_spend"]) + " of " + str(mc["total_orgs"]) + """ orgs with spend)</div>
  </div>
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;border-top:3px solid #d03b3b;">
    <div style="font:600 30px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#d03b3b;">""" + str(flagged_count) + """</div>
    <div style="font:450 13px/1.4 'Public Sans';color:#52514e;margin-top:8px;">Flagged apps &amp; service instances</div>
  </div>
</div>

<!-- EXPLAINER -->
<div style="margin-top:34px;background:#f8f6f1;border:1px solid #e4e2dc;border-radius:12px;padding:24px 26px;">
  <div style="font:600 12px/1 'Public Sans';letter-spacing:.1em;text-transform:uppercase;color:#7a786f;margin-bottom:14px;">How to read this report</div>
  <p style="font:400 14px/1.6 'Public Sans';color:#52514e;margin:0 0 18px;max-width:88ch;">Tanzu Hub prices <b style="color:#0b0b0b;">provisioned capacity &times; time</b>, not usage &mdash; so an idle instance costs exactly as much as a busy one. Two rate cards apply: an Application card ($""" + str(data["rate_cards"]["application"]["appInstanceHours"]) + """/instance&#8209;hr + $""" + str(data["rate_cards"]["application"]["appMemoryGbHours"]) + """/GB&#8209;hr) and per&#8209;plan Service cards. Every dollar below is one of two kinds:</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;">
    <div style="border-left:3px solid #1baf7a;padding:2px 0 2px 16px;">
      <div style="font:600 14px/1.3 'Public Sans';color:#0b0b0b;margin-bottom:5px;">Live&#8209;metered</div>
      <div style="font:400 13.5px/1.55 'Public Sans';color:#52514e;">Read straight from Hub's own Telemetry. Reflects """ + str(mc["orgs_nonzero_spend"]) + " of " + str(mc["total_orgs"]) + """ organizations with nonzero spend today &mdash; see Data Coverage for what "coverage" means here.</div>
    </div>
    <div style="border-left:3px solid #2a78d6;padding:2px 0 2px 16px;">
      <div style="font:600 14px/1.3 'Public Sans';color:#0b0b0b;margin-bottom:5px;">Modeled</div>
      <div style="font:400 13.5px/1.55 'Public Sans';color:#52514e;">Computed here from each app's provisioned instances/memory &times; the platform's published unit price &mdash; list&#8209;rate exposure, not a bill.</div>
    </div>
  </div>
</div>

<!-- 01 DATA COVERAGE -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:32px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap;">
  <div style="flex:1 1 440px;">
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.12em;text-transform:uppercase;color:#7a786f;margin-bottom:12px;">01 &mdash; Data coverage</div>
    <h2 class="serif" style="font:500 27px/1.15 'Newsreader',serif;letter-spacing:-.01em;margin:0 0 12px;">Org &amp; space cost visibility is broad; service&#8209;offering coverage is not</h2>
    <p style="font:400 14.5px/1.6 'Public Sans';color:#52514e;margin:0;max-width:70ch;">Hub's Application Rate Card is Foundation&#8209;scoped, so nearly every org/space returns a real live figure (zero or otherwise) once queried correctly &mdash; the numbers below are <b style="color:#0b0b0b;">nonzero&#8209;spend counts</b>, not a priced/unpriced split. Service instances are different: an offering with <b style="color:#0b0b0b;">no Service Rate Card at all</b> stays permanently unpriced regardless of activity &mdash; that is the real, fixable gap.</p>
  </div>
  <span style="flex:0 0 auto;font:600 12px/1 'Public Sans';color:#d03b3b;background:#fbeceb;border:1px solid #f2cfcc;border-radius:999px;padding:8px 14px;">Service rate cards: the real gap</span>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px;margin-top:24px;">
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;">
    <div style="display:flex;justify-content:space-between;align-items:baseline;"><span style="font:600 24px/1 'Public Sans';font-variant-numeric:tabular-nums;">""" + str(mc["orgs_nonzero_spend"]) + """<span style="color:#a8a69c;font-weight:500;"> / """ + str(mc["total_orgs"]) + """</span></span><span style="font:600 13px/1 'Public Sans';color:#2a78d6;">""" + f"{org_pct}%" + """</span></div>
    <div style="font:450 13px/1 'Public Sans';color:#52514e;margin:10px 0 12px;">Orgs with nonzero live spend</div>
    <div style="height:8px;background:#e6e3db;border-radius:99px;overflow:hidden;"><div style="height:100%;width:""" + f"{org_pct}%" + """;background:#2a78d6;border-radius:99px;"></div></div>
  </div>
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;">
    <div style="display:flex;justify-content:space-between;align-items:baseline;"><span style="font:600 24px/1 'Public Sans';font-variant-numeric:tabular-nums;">""" + str(mc["spaces_nonzero_spend"]) + """<span style="color:#a8a69c;font-weight:500;"> / """ + str(mc["total_spaces"]) + """</span></span><span style="font:600 13px/1 'Public Sans';color:#2a78d6;">""" + f"{space_pct}%" + """</span></div>
    <div style="font:450 13px/1 'Public Sans';color:#52514e;margin:10px 0 12px;">Spaces with nonzero live spend</div>
    <div style="height:8px;background:#e6e3db;border-radius:99px;overflow:hidden;"><div style="height:100%;width:""" + f"{space_pct}%" + """;background:#2a78d6;border-radius:99px;"></div></div>
  </div>
  <div style="background:#f4f2ec;border:1px solid #e4e2dc;border-radius:12px;padding:20px 22px;">""" + (
    ("""
    <div style="display:flex;justify-content:space-between;align-items:baseline;"><span style="font:600 24px/1 'Public Sans';font-variant-numeric:tabular-nums;">""" + str(svc_rate_card_count) + """<span style="color:#a8a69c;font-weight:500;"> / """ + str(mc["paid_service_instances"]) + """</span></span><span style="font:600 13px/1 'Public Sans';color:#d03b3b;">""" + f"{svc_pct}%" + """</span></div>
    <div style="font:450 13px/1 'Public Sans';color:#52514e;margin:10px 0 12px;">Paid service instances under a rate card</div>
    <div style="height:8px;background:#e6e3db;border-radius:99px;overflow:hidden;"><div style="height:100%;width:""" + f"{svc_pct}%" + """;background:#d03b3b;border-radius:99px;"></div></div>"""
    ) if svc_pct is not None else """
    <div style="font:600 24px/1 'Public Sans';">&mdash;</div>
    <div style="font:450 13px/1 'Public Sans';color:#52514e;margin:10px 0 12px;">Service rate-card coverage not computed this run</div>"""
  ) + """
  </div>
</div>

<!-- 02 SPEND CONCENTRATION -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:32px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap;">
  <div style="flex:1 1 440px;">
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.12em;text-transform:uppercase;color:#7a786f;margin-bottom:12px;">02 &mdash; Concentration</div>
    <h2 class="serif" style="font:500 27px/1.15 'Newsreader',serif;letter-spacing:-.01em;margin:0 0 12px;">Where the modeled spend concentrates</h2>
    <p style="font:400 14.5px/1.6 'Public Sans';color:#52514e;margin:0;max-width:70ch;">Modeled monthly cost (instances &times; memory &times; rate card) from the current entity snapshot across all foundations in scope.</p>
  </div>
  <div style="flex:0 0 auto;text-align:right;">
    <div style="font:600 22px/1 'Public Sans';font-variant-numeric:tabular-nums;">$""" + f"{fleet['modeled_monthly_app_cost']:,.0f}" + """<span style="font-size:14px;color:#7a786f;font-weight:500;">/mo</span></div>
    <div style="font:450 12.5px/1 'Public Sans';color:#7a786f;margin-top:5px;">total modeled footprint</div>
  </div>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:36px;margin-top:26px;">
  <div>
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.06em;text-transform:uppercase;color:#7a786f;margin-bottom:16px;">Top organizations</div>
    <div id="bars-orgs" style="display:flex;flex-direction:column;gap:11px;"></div>
  </div>
  <div>
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.06em;text-transform:uppercase;color:#7a786f;margin-bottom:16px;">Top spaces</div>
    <div id="bars-spaces" style="display:flex;flex-direction:column;gap:11px;"></div>
  </div>
</div>

<!-- 03 BROKEN APPS -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:32px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap;">
  <div style="flex:1 1 440px;">
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.12em;text-transform:uppercase;color:#7a786f;margin-bottom:12px;">03 &mdash; Waste &middot; confirmed</div>
    <h2 class="serif" style="font:500 27px/1.15 'Newsreader',serif;letter-spacing:-.01em;margin:0 0 12px;">Broken &amp; wasted applications</h2>
    <p style="font:400 14.5px/1.6 'Public Sans';color:#52514e;margin:0;max-width:70ch;">STARTED, non&#8209;system apps structurally unable to do useful work &mdash; no routes to receive traffic, instances stuck below requested count, or crash&#8209;looping. Billed at full provisioned rate regardless.</p>
  </div>
  <div style="flex:0 0 auto;text-align:right;">
    <div style="font:600 22px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#d03b3b;">$""" + f"{data['tier1_broken_apps']['total_monthly']:,.0f}" + """<span style="font-size:14px;color:#7a786f;font-weight:500;">/mo</span></div>
    <div style="font:450 12.5px/1 'Public Sans';color:#7a786f;margin-top:5px;">""" + str(data["tier1_broken_apps"]["count"]) + """ apps flagged</div>
  </div>
</div>
<div style="overflow-x:auto;margin-top:20px;border:1px solid #e4e2dc;border-radius:12px;">
  <table style="width:100%;border-collapse:collapse;font:400 13.5px/1.4 'Public Sans';min-width:640px;">
    <thead><tr style="background:#f4f2ec;">
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Application</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Location</th>
      <th style="text-align:right;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Inst.</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Issue</th>
      <th style="text-align:right;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Modeled $/mo</th>
    </tr></thead>
    <tbody id="tbl-broken"></tbody>
  </table>
</div>

<!-- 04 STALE APPS -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:32px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap;">
  <div style="flex:1 1 440px;">
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.12em;text-transform:uppercase;color:#7a786f;margin-bottom:12px;">04 &mdash; Waste &middot; review</div>
    <h2 class="serif" style="font:500 27px/1.15 'Newsreader',serif;letter-spacing:-.01em;margin:0 0 12px;">Stale applications</h2>
    <p style="font:400 14.5px/1.6 'Public Sans';color:#52514e;margin:0;max-width:70ch;">STARTED apps with no deploy or update activity in over """ + str(stale_days) + """ days. Fully billed regardless of activity &mdash; a strong decommission signal.</p>
  </div>
  <div style="flex:0 0 auto;text-align:right;">
    <div style="font:600 22px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#eda100;">$""" + f"{data['tier2_stale_apps']['total_monthly']:,.0f}" + """<span style="font-size:14px;color:#7a786f;font-weight:500;">/mo</span></div>
    <div style="font:450 12.5px/1 'Public Sans';color:#7a786f;margin-top:5px;">""" + str(data["tier2_stale_apps"]["count"]) + """ apps flagged</div>
  </div>
</div>
<div style="overflow-x:auto;margin-top:20px;border:1px solid #e4e2dc;border-radius:12px;">
  <table style="width:100%;border-collapse:collapse;font:400 13.5px/1.4 'Public Sans';min-width:660px;">
    <thead><tr style="background:#f4f2ec;">
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Application</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Location</th>
      <th style="text-align:right;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Inst.</th>
      <th style="text-align:right;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Age (d)</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Stack</th>
      <th style="text-align:right;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Modeled $/mo</th>
    </tr></thead>
    <tbody id="tbl-stale"></tbody>
  </table>
</div>
<div style="font:450 12.5px/1.4 'Public Sans';color:#a19f95;margin-top:10px;">Showing top <span id="stale-shown"></span> of <span id="stale-total"></span> stale apps by modeled cost.</div>

<!-- 05 ORPHANED SERVICES -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:32px;display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap;">
  <div style="flex:1 1 440px;">
    <div style="font:600 12px/1 'Public Sans';letter-spacing:.12em;text-transform:uppercase;color:#7a786f;margin-bottom:12px;">05 &mdash; Waste &middot; services</div>
    <h2 class="serif" style="font:500 27px/1.15 'Newsreader',serif;letter-spacing:-.01em;margin:0 0 12px;">Orphaned service instances</h2>
    <p style="font:400 14.5px/1.6 'Public Sans';color:#52514e;margin:0;max-width:70ch;">Non&#8209;free service instances with zero bound applications &mdash; billed <code style="font:500 13px 'Public Sans';background:#f0eee8;padding:1px 6px;border-radius:4px;">serviceInstanceHours</code> for nothing. """ + str(data["tier1_orphaned_services"]["priced_count"]) + """ carry live per&#8209;instance spend ($""" + f"{data['tier1_orphaned_services']['priced_total_monthly']:,.0f}" + """/mo confirmed). A further """ + str(data["tier1_orphaned_services"].get("zero_priced_count", 0)) + """ meter at a real <b style="color:#0b0b0b;">$0.00</b> &mdash; their offering carries a rate card priced at zero, so they are idle waste in capacity terms but cost nothing today. Only """ + str(data["tier1_orphaned_services"].get("no_rate_card_count", 0)) + """ sit behind an offering with no rate card at all.</p>
  </div>
  <div style="flex:0 0 auto;text-align:right;">
    <div style="font:600 22px/1 'Public Sans';font-variant-numeric:tabular-nums;color:#eb6834;">""" + str(data["tier1_orphaned_services"]["count"]) + """<span style="font-size:14px;color:#7a786f;font-weight:500;"> / """ + str(data["tier1_orphaned_services"]["paid_offering_population"]) + """</span></div>
    <div style="font:450 12.5px/1 'Public Sans';color:#7a786f;margin-top:5px;">paid-plan instances, 0 bound apps</div>
  </div>
</div>
<div style="font:600 12px/1 'Public Sans';letter-spacing:.06em;text-transform:uppercase;color:#7a786f;margin:24px 0 16px;">Orphans by offering</div>
<div id="bars-offerings" style="display:flex;flex-direction:column;gap:11px;"></div>
<div style="overflow-x:auto;margin-top:26px;border:1px solid #e4e2dc;border-radius:12px;">
  <table style="width:100%;border-collapse:collapse;font:400 13.5px/1.4 'Public Sans';min-width:680px;">
    <thead><tr style="background:#f4f2ec;">
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Service instance</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Location</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Offering</th>
      <th style="text-align:left;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">Plan</th>
      <th style="text-align:right;font:600 11px/1 'Public Sans';letter-spacing:.04em;text-transform:uppercase;color:#7a786f;padding:12px 16px;border-bottom:1px solid #e4e2dc;">$/mo</th>
    </tr></thead>
    <tbody id="tbl-orphans"></tbody>
  </table>
</div>
<div style="font:450 12.5px/1.4 'Public Sans';color:#a19f95;margin-top:10px;">Showing top <span id="orphan-shown"></span> of <span id="orphan-total"></span> orphaned instances.</div>

<!-- 06 RATE CARDS -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:32px;">
  <div style="font:600 12px/1 'Public Sans';letter-spacing:.12em;text-transform:uppercase;color:#7a786f;margin-bottom:12px;">06 &mdash; Reference</div>
  <h2 class="serif" style="font:500 27px/1.15 'Newsreader',serif;letter-spacing:-.01em;margin:0 0 20px;">Rate cards in effect</h2>
</div>
<div id="rate-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;"></div>

<!-- FOOTER -->
<div style="border-top:1px solid #e4e2dc;margin-top:52px;padding-top:22px;font:400 12.5px/1.65 'Public Sans';color:#a19f95;">
  <div style="display:flex;flex-wrap:wrap;gap:6px 20px;margin-bottom:10px;">
    <span><b style="color:#7a786f;font-weight:600;">""" + str(fleet["apps_total"]) + """</b> apps &middot; """ + str(fleet["apps_nonsystem"]) + """ non-system &middot; """ + str(fleet["apps_started"]) + """ started &middot; """ + str(fleet["apps_stopped"]) + """ stopped</span>
    <span><b style="color:#7a786f;font-weight:600;">""" + str(fleet["services_total"]) + """</b> service instances</span>
    <span><b style="color:#7a786f;font-weight:600;">""" + str(fleet["orgs"]) + """</b> orgs across <b style="color:#7a786f;font-weight:600;">""" + str(fleet["spaces"]) + """</b> spaces</span>
  </div>
  <div>Foundations: """ + foundation_footer_line + """</div>
  <div>Source: Tanzu Hub GraphQL &mdash; entityQuery.typed.tanzu.tas, statsQuery Telemetry namespace</div>
</div>

</div>
</div>
</div>

<script>""" + RENDER_JS.replace("__DATA_JSON__", json.dumps(data)) + """</script>
</body>
</html>
"""

    open(args.out, "w").write(html)
    print(f"wrote {args.out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
