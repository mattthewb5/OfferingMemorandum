#!/usr/bin/env python3
"""
NewCo Offering Memorandum v3 Generator — Regent's Park
Generates: investigation/newco_om_v3_regents_park.html

Run: python generate_om_v3.py
"""

import os
import re

# ---------------------------------------------------------------------------
# Extract base64 logo from v2 source (single shared image for all pages)
# ---------------------------------------------------------------------------
def _load_logo():
    v2_path = os.path.join(os.path.dirname(__file__), "investigation", "newco_om_v2_regents_park.html")
    with open(v2_path, "r") as f:
        content = f.read()
    match = re.search(r'src="(data:image/[^"]+)"', content)
    return match.group(1) if match else ""

LOGO_B64 = _load_logo()


# ═══════════════════════════════════════════════════════════════════════════
# SHARED STYLES
# ═══════════════════════════════════════════════════════════════════════════
def shared_styles():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offering Memorandum — Regent's Park — v3</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">
<style>
  :root {
    --navy: #0f1f38;
    --navy-mid: #1a3357;
    --wo-blue: #2a52a0;
    --gold: #b8966a;
    --gold-light: #d4b48a;
    --slate: #4a5568;
    --slate-light: #718096;
    --rule: #e2e8f0;
    --bg: #f7f6f4;
    --white: #ffffff;
    --green: #2d6a4f;
    --green-light: #d1fae5;
    --amber: #b45309;
    --amber-light: #fef3c7;
    --red: #9b1c1c;
    --red-light: #fee2e2;
    --serif: 'Cormorant Garamond', Georgia, serif;
    --sans: 'DM Sans', -apple-system, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #ccc9c3; font-family: var(--sans); font-size: 10px; color: #2d3748; -webkit-font-smoothing: antialiased; }

  .page { width: 816px; min-height: 1056px; background: var(--white); margin: 32px auto; position: relative; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.22), 0 2px 8px rgba(0,0,0,0.12); }
  .page-footer { position: absolute; bottom: 0; left: 0; right: 0; height: 30px; background: var(--navy); display: flex; align-items: center; justify-content: space-between; padding: 0 32px; }
  .pf-left { font-family: var(--sans); font-size: 7.5px; font-weight: 500; color: rgba(255,255,255,0.45); letter-spacing: 0.08em; text-transform: uppercase; }
  .pf-center { font-family: var(--serif); font-size: 9.5px; color: rgba(255,255,255,0.6); font-style: italic; }
  .pf-right { font-family: var(--sans); font-size: 7.5px; color: rgba(255,255,255,0.4); }
  .wo-mark { display: inline-flex; align-items: center; gap: 5px; }
  .wo-mark img { height: 16px; opacity: 0.5; }

  /* Typography */
  .sec-label { font-family: var(--sans); font-size: 8px; font-weight: 600; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold); margin-bottom: 5px; }
  .sec-title { font-family: var(--serif); font-weight: 600; font-size: 22px; color: var(--navy); line-height: 1.15; margin-bottom: 10px; }
  .sub-title { font-family: var(--serif); font-weight: 600; font-size: 14px; color: var(--navy); margin-bottom: 6px; }
  h4 { font-family: var(--sans); font-size: 8.5px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--navy); margin-bottom: 6px; }
  p { font-family: var(--sans); font-size: 9.5px; line-height: 1.65; color: var(--slate); }
  .gold-rule { width: 36px; height: 2px; background: var(--gold); margin-bottom: 16px; }
  hr.rule { border: none; border-top: 1px solid var(--rule); margin: 12px 0; }

  /* Stoplight Scores */
  .score-row { display: flex; align-items: center; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--rule); }
  .score-row:last-child { border-bottom: none; }
  .score-label { font-family: var(--sans); font-size: 8.5px; color: var(--slate); }
  .score-right { display: flex; align-items: center; gap: 8px; }
  .score-bar-track { width: 72px; height: 5px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
  .score-bar-fill { height: 100%; border-radius: 3px; }
  .score-val { font-family: var(--serif); font-size: 13px; font-weight: 600; width: 40px; text-align: right; }
  .score-denom { font-size: 8px; font-weight: 400; color: var(--slate-light); }
  .score-badge { display: inline-flex; align-items: center; gap: 3px; padding: 1px 5px; border-radius: 2px; font-size: 6.5px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
  .badge-green { background: var(--green-light); color: var(--green); }
  .badge-amber { background: var(--amber-light); color: var(--amber); }
  .badge-red { background: var(--red-light); color: var(--red); }
  .badge-navy { background: rgba(15,31,56,0.08); color: var(--navy); border: 1px solid rgba(15,31,56,0.12); }
  .badge-gold { background: rgba(184,150,106,0.12); color: var(--gold); border: 1px solid rgba(184,150,106,0.25); }

  /* Stoplight dot */
  .sl-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .sl-green { background: #22c55e; }
  .sl-amber { background: #f59e0b; }
  .sl-red { background: #ef4444; }

  /* KPI boxes */
  .kpi-dark { background: var(--navy); color: white; padding: 12px 14px; flex: 1; }
  .kpi-dark .kl { font-size: 7px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(255,255,255,0.5); margin-bottom: 4px; }
  .kpi-dark .kv { font-family: var(--serif); font-size: 19px; font-weight: 600; color: white; line-height: 1; }
  .kpi-dark .ks { font-size: 7.5px; color: var(--gold-light); margin-top: 2px; }
  .kpi-light { background: var(--bg); border: 1px solid var(--rule); padding: 10px 12px; flex: 1; }
  .kpi-light .kl { font-size: 7px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--slate-light); margin-bottom: 3px; }
  .kpi-light .kv { font-family: var(--serif); font-size: 17px; font-weight: 600; color: var(--navy); line-height: 1; }
  .kpi-light .ks { font-size: 7.5px; color: var(--slate-light); margin-top: 2px; }

  /* Tables */
  .dtable { width: 100%; border-collapse: collapse; font-family: var(--sans); font-size: 8.5px; }
  .dtable thead tr { background: var(--navy); }
  .dtable thead th { padding: 6px 9px; font-weight: 600; font-size: 7px; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(255,255,255,0.65); text-align: left; }
  .dtable thead th.r { text-align: right; }
  .dtable tbody tr { border-bottom: 1px solid var(--rule); }
  .dtable tbody tr:nth-child(even) { background: #fafaf9; }
  .dtable tbody td { padding: 6px 9px; color: var(--slate); }
  .dtable tbody td.r { text-align: right; }
  .dtable tbody td.strong { font-weight: 600; color: var(--navy); }
  .dtable tfoot td { padding: 7px 9px; font-weight: 600; font-size: 8.5px; color: var(--navy); background: #f0ede8; border-top: 2px solid var(--gold); }
  .dtable tfoot td.r { text-align: right; }

  /* Financial table */
  .ftable { width: 100%; border-collapse: collapse; font-size: 8.5px; font-family: var(--sans); }
  .ftable td { padding: 4px 9px; border-bottom: 1px solid var(--rule); color: var(--slate); }
  .ftable td:last-child { text-align: right; }
  .ftable tr.cat td { background: #f5f3ef; font-weight: 600; color: var(--navy); font-size: 8px; padding: 5px 9px; border-top: 1px solid rgba(184,150,106,0.25); }
  .ftable tr.noi td { background: var(--navy); color: white; font-weight: 600; font-size: 9px; }
  .ftable tr.indent td:first-child { padding-left: 18px; color: var(--slate-light); }
  .col-lbl { font-size: 7.5px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; text-align: center; padding: 4px 9px; }
  .lbl-actual { background: rgba(184,150,106,0.1); color: var(--gold); }
  .lbl-proforma { background: rgba(15,31,56,0.07); color: var(--navy); }

  /* Highlight bullet */
  .hl-bullet { display: flex; gap: 10px; margin-bottom: 9px; align-items: flex-start; }
  .hl-marker { width: 3px; min-height: 13px; background: var(--gold); flex-shrink: 0; margin-top: 3px; }
  .hl-text { font-size: 9.5px; line-height: 1.5; color: var(--slate); }
  .hl-text strong { color: var(--navy); font-weight: 600; }

  /* Column divider */
  .vdiv { width: 1px; background: var(--rule); flex-shrink: 0; }

  /* Map placeholder */
  .mapbox { background: #e8ecf0; border: 1px solid var(--rule); position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; }
  .mapbox::before { content: ''; position: absolute; inset: 0; background: repeating-linear-gradient(45deg, transparent, transparent 18px, rgba(15,31,56,0.025) 18px, rgba(15,31,56,0.025) 20px); }
  .mapbox-label { font-size: 8px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--slate-light); position: relative; z-index: 1; text-align: center; }

  /* Travel grid */
  .travel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--rule); border: 1px solid var(--rule); }
  .tc { background: white; padding: 7px 10px; display: flex; justify-content: space-between; align-items: center; }
  .tc-dest { font-size: 8px; color: var(--slate); }
  .tc-mi { font-size: 7px; color: var(--slate-light); }
  .tc-time { font-family: var(--serif); font-size: 14px; font-weight: 600; color: var(--navy); }

  /* School card */
  .school-card { border: 1px solid var(--rule); padding: 9px 11px; flex: 1; }
  .sc-level { font-size: 7px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--gold); margin-bottom: 2px; }
  .sc-name { font-family: var(--serif); font-size: 12px; font-weight: 600; color: var(--navy); margin-bottom: 5px; }
  .sc-stats { display: flex; gap: 8px; }
  .sc-stat-label { font-size: 7px; color: var(--slate-light); margin-bottom: 1px; }
  .sc-stat-val { font-size: 9.5px; font-weight: 600; }

  /* Bar chart */
  .bar-chart { display: flex; flex-direction: column; gap: 5px; }
  .bar-row { display: flex; align-items: center; gap: 8px; }
  .bar-rl { font-size: 8px; color: var(--slate); width: 130px; flex-shrink: 0; text-align: right; }
  .bar-track { flex: 1; height: 13px; background: #eeecea; border-radius: 1px; position: relative; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 1px; }
  .bar-primary { background: var(--navy); }
  .bar-light { background: rgba(15,31,56,0.25); }
  .bar-pct { font-size: 7.5px; font-weight: 600; color: var(--navy); width: 28px; text-align: right; }

  /* Employer row */
  .emp-row { display: flex; align-items: center; padding: 5px 10px; border-bottom: 1px solid var(--rule); gap: 8px; }
  .emp-row:last-child { border-bottom: none; }
  .emp-rank { font-family: var(--serif); font-size: 11px; color: var(--gold); width: 14px; flex-shrink: 0; }
  .emp-name { font-size: 8.5px; font-weight: 500; color: var(--navy); flex: 1.2; }
  .emp-sector { font-size: 7.5px; color: var(--slate-light); flex: 1; }
  .emp-count { font-size: 8.5px; font-weight: 600; color: var(--navy); text-align: right; flex-shrink: 0; }

  /* Dev pressure */
  .pressure-main { display: flex; align-items: center; gap: 16px; padding: 14px 16px; background: #f0faf5; border-left: 3px solid var(--green); margin-bottom: 14px; }
  .pressure-num { font-family: var(--serif); font-size: 58px; font-weight: 700; color: var(--green); line-height: 1; }

  /* Formula box */
  .formula-box { background: #f5f3ef; border: 1px solid rgba(184,150,106,0.3); padding: 11px 14px; margin-bottom: 14px; }
  .formula-row { display: flex; align-items: center; gap: 8px; padding: 3px 0; border-bottom: 1px solid rgba(184,150,106,0.15); }
  .formula-row:last-child { border-bottom: none; }
  .formula-name { font-size: 8.5px; color: var(--navy); font-weight: 500; flex: 1.5; }
  .formula-weight { font-family: var(--serif); font-size: 13px; font-weight: 600; color: var(--gold); width: 32px; text-align: center; }
  .formula-bar-track { flex: 1; height: 8px; background: #e2d9cb; border-radius: 2px; overflow: hidden; }
  .formula-bar-fill { height: 100%; border-radius: 2px; }
  .formula-score { font-size: 8px; font-weight: 600; color: var(--green); width: 50px; text-align: right; }

  /* Utility box */
  .util-box { background: rgba(15,31,56,0.04); border: 1px solid var(--rule); padding: 10px 12px; }
  .util-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid var(--rule); }
  .util-row:last-child { border-bottom: none; }
  .util-label { font-size: 8.5px; color: var(--slate); }
  .util-val { font-size: 8.5px; font-weight: 600; color: var(--navy); }
  .util-source { font-size: 7px; color: var(--slate-light); font-style: italic; }

  /* Crime table */
  .crime-table { width: 100%; border-collapse: collapse; font-size: 8px; font-family: var(--sans); }
  .crime-table thead tr { background: rgba(155,28,28,0.08); }
  .crime-table thead th { padding: 5px 8px; font-size: 7px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--red); text-align: left; }
  .crime-table tbody tr { border-bottom: 1px solid var(--rule); }
  .crime-table tbody td { padding: 5px 8px; color: var(--slate); }
  .crime-table tbody td:first-child { font-weight: 500; color: var(--navy); }
  .crime-type-violent { color: var(--red); font-weight: 600; font-size: 7.5px; }
  .crime-type-property { color: var(--amber); font-weight: 600; font-size: 7.5px; }

  /* Value-add box */
  .value-add-box { background: rgba(42,82,160,0.05); border: 1px solid rgba(42,82,160,0.2); padding: 12px 14px; margin-bottom: 14px; }

</style>
</head>
<body>
'''


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 — COVER
# v3 Change 1: Replace all placeholders with spec numbers
# v3 Change 2: Utility structure line in specs grid
# ═══════════════════════════════════════════════════════════════════════════
def page1_cover():
    return f'''
<!-- ═══════════════════════════════════
     PAGE 1 — COVER
════════════════════════════════════ -->
<div class="page">
  <!-- DARK TOP HALF -->
  <div style="height:530px;background:linear-gradient(155deg,#0c1b32 0%,#1a3357 50%,#0d1a2e 100%);position:relative;overflow:hidden;">
    <div style="position:absolute;inset:0;background:repeating-linear-gradient(110deg,transparent,transparent 64px,rgba(184,150,106,0.025) 64px,rgba(184,150,106,0.025) 66px);"></div>
    <div style="position:absolute;top:0;left:0;right:0;height:4px;background:var(--wo-blue);"></div>
    <div style="position:absolute;bottom:0;left:0;right:0;height:1px;background:rgba(184,150,106,0.35);"></div>

    <!-- West Oxford logo top-right -->
    <div style="position:absolute;top:24px;right:36px;text-align:right;">
      <img src="{LOGO_B64}" style="height:34px;opacity:0.85;" alt="West Oxford Advisors">
      <div style="font-family:var(--sans);font-size:7.5px;color:rgba(255,255,255,0.4);letter-spacing:0.12em;text-transform:uppercase;margin-top:4px;">Exclusively Offered By</div>
    </div>

    <!-- Confidential badge -->
    <div style="position:absolute;top:26px;left:36px;">
      <div style="border:1px solid rgba(255,255,255,0.18);padding:3px 10px;font-size:7px;font-weight:600;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.3);font-family:var(--sans);">Confidential</div>
    </div>

    <!-- Center property identity -->
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-52%);text-align:center;width:600px;">
      <div style="font-family:var(--sans);font-size:8px;font-weight:600;letter-spacing:0.26em;text-transform:uppercase;color:var(--gold);margin-bottom:14px;">Investment Offering Memorandum</div>
      <div style="font-family:var(--serif);font-size:52px;font-weight:600;color:white;line-height:1.08;margin-bottom:10px;">Regent&#8217;s Park</div>
      <div style="width:44px;height:2px;background:var(--wo-blue);margin:14px auto;"></div>
      <div style="font-family:var(--sans);font-size:11px;color:rgba(255,255,255,0.6);letter-spacing:0.04em;">9333 Clocktower Place &middot; Fairfax, Virginia 22031</div>
      <div style="font-family:var(--sans);font-size:9px;color:rgba(255,255,255,0.32);margin-top:4px;letter-spacing:0.06em;">Fairfax County &middot; Merrifield&#8211;Vienna Submarket &middot; Silver Line Corridor</div>
    </div>

    <!-- Image area label -->
    <div style="position:absolute;bottom:16px;left:50%;transform:translateX(-50%);font-size:7.5px;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.18);font-family:var(--sans);">[ Aerial / Drone Hero Image ]</div>
  </div>

  <!-- WHITE BOTTOM HALF -->
  <div style="height:526px;background:white;display:flex;flex-direction:column;">
    <!-- KPI strip — v3: all placeholders replaced with spec numbers -->
    <div style="display:flex;gap:1px;background:var(--rule);">
      <div class="kpi-dark" style="flex:1.4;">
        <div class="kl">Asking Price</div>
        <div class="kv">$232,000,000</div>
        <div class="ks">$420,289 / Unit</div>
      </div>
      <div class="kpi-dark">
        <div class="kl">Total Units</div>
        <div class="kv">552</div>
        <div class="ks">4 Stories &middot; 22 Floor Plans</div>
      </div>
      <div class="kpi-dark">
        <div class="kl">Cap Rate</div>
        <div class="kv">5.02%</div>
        <div class="ks">T-12 In-Place</div>
      </div>
      <div class="kpi-dark">
        <div class="kl">Net Oper. Income</div>
        <div class="kv">$11.65M</div>
        <div class="ks">Trailing 12 Months</div>
      </div>
      <div class="kpi-dark">
        <div class="kl">Year Built</div>
        <div class="kv">1997</div>
        <div class="ks">Bozzuto Managed</div>
      </div>
      <div class="kpi-dark">
        <div class="kl">Avg. Monthly Rent</div>
        <div class="kv">$2,480</div>
        <div class="ks">628&#8211;1,434 SF Units</div>
      </div>
    </div>

    <!-- Property summary -->
    <div style="padding:24px 36px 0;display:flex;gap:28px;align-items:flex-start;flex:1;">
      <div style="flex:1.6;">
        <div class="sec-label">Property Overview</div>
        <p>Regent&#8217;s Park is a 552-unit, institutionally managed multifamily community positioned at the convergence of Fairfax County&#8217;s most coveted location attributes: walking distance to Vienna Metro (Silver Line), one mile from George Mason University, and immediate access to the I-495/I-66 corridor. Built in 1997 and continuously managed by Bozzuto Management Company, the property comprises four residential buildings with 22 distinct floor plans ranging from 628 to 1,434 square feet across one, two, and three-bedroom configurations. In-place rents averaging 9.1% below current submarket rates present a systematic mark-to-market opportunity across the portfolio through a structured lease renewal program.</p>
        <div style="margin-top:10px;display:flex;gap:6px;flex-wrap:wrap;">
          <span class="score-badge badge-navy">Fairfax County</span>
          <span class="score-badge badge-navy">Vienna Metro &middot; 1.3 mi</span>
          <span class="score-badge badge-navy">George Mason &middot; 0.9 mi</span>
          <span class="score-badge badge-gold">Value-Add Opportunity</span>
          <span class="score-badge badge-green">Low Dev. Pressure</span>
        </div>
      </div>
      <div class="vdiv" style="height:110px;margin-top:10px;"></div>
      <div style="flex:1;display:grid;grid-template-columns:1fr 1fr;gap:7px 16px;padding-top:12px;">
        <div><div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);margin-bottom:2px;">Total Units</div><div style="font-family:var(--serif);font-size:15px;font-weight:600;color:var(--navy);">552 Units</div></div>
        <div><div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);margin-bottom:2px;">Avg. Unit Size</div><div style="font-family:var(--serif);font-size:15px;font-weight:600;color:var(--navy);">1,031 SF avg</div></div>
        <div><div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);margin-bottom:2px;">Rentable Area</div><div style="font-family:var(--serif);font-size:15px;font-weight:600;color:var(--navy);">569,112 SF</div></div>
        <div><div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);margin-bottom:2px;">Zoning</div><div style="font-family:var(--serif);font-size:15px;font-weight:600;color:var(--navy);">PDH &middot; PRC</div></div>
        <div><div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);margin-bottom:2px;">Utility Structure</div><div style="font-size:9px;font-weight:600;color:var(--navy);">Tenant-Paid: Electric + Gas<br><span style="color:var(--slate-light);font-weight:400;">Landlord-Paid: Water / Common Area</span></div></div>
        <div><div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);margin-bottom:2px;">Management</div><div style="font-size:9px;font-weight:600;color:var(--navy);">Bozzuto Mgmt Co.<br><span style="color:var(--slate-light);font-weight:400;">Institutional Operator</span></div></div>
      </div>
    </div>

    <!-- Photo strip -->
    <div style="margin:16px 36px 0;display:flex;gap:6px;">
      <div class="mapbox" style="height:82px;flex:2;"><div class="mapbox-label">Aerial View</div></div>
      <div class="mapbox" style="height:82px;flex:1;"><div class="mapbox-label">Clubhouse</div></div>
      <div class="mapbox" style="height:82px;flex:1;"><div class="mapbox-label">Pool Deck</div></div>
      <div class="mapbox" style="height:82px;flex:1;"><div class="mapbox-label">Unit Interior</div></div>
    </div>
  </div>

  <div class="page-footer">
    <div class="pf-left">Regent&#8217;s Park &middot; 9333 Clocktower Place &middot; Fairfax, VA 22031</div>
    <div class="pf-center">Investment Offering Memorandum &middot; Confidential</div>
    <div class="wo-mark"><img src="{LOGO_B64}" alt="WO"><span class="pf-right">West Oxford Advisors</span></div>
  </div>
</div>
'''


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — EXECUTIVE SUMMARY
# v3 Change 1: Placeholders replaced with spec numbers
# v3 Change 3: Remove numerical scores from stoplight indicators
#   Format: colored dot + plain English label + bar only (no "18/100")
# ═══════════════════════════════════════════════════════════════════════════
def page2_exec_summary():
    return f'''
<!-- ═══════════════════════════════════
     PAGE 2 — EXECUTIVE SUMMARY
════════════════════════════════════ -->
<div class="page">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:var(--wo-blue);"></div>
  <div style="padding:40px 36px 36px;">
    <div class="sec-label">Section One</div>
    <div class="sec-title">Executive Summary</div>
    <div class="gold-rule"></div>

    <div style="display:flex;gap:26px;">
      <!-- LEFT: narrative + highlights -->
      <div style="flex:1.65;">
        <!-- AI thesis -->
        <div style="background:#f5f3ef;border-left:3px solid var(--wo-blue);padding:13px 15px;margin-bottom:16px;">
          <div style="font-size:7.5px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--wo-blue);margin-bottom:7px;font-family:var(--sans);">Investment Thesis &#8212; AI Generated</div>
          <p style="font-size:9.5px;line-height:1.7;color:var(--navy);">Regent&#8217;s Park presents a rare combination of scale, transit access, and embedded rent upside in one of the most supply-constrained multifamily submarkets in the Mid-Atlantic region. As a 552-unit, institutionally operated community within walking distance of the Vienna Metro Station and one mile from George Mason University, the property draws from three durable demand cohorts: federal government employees, technology sector professionals, and graduate students &#8212; all insulated from cyclical employment volatility. With in-place rents tracking 9.1% below current RentCast submarket averages and zero new competitive multifamily supply planned within the 2-mile radius, the asset offers a clear, low-execution-risk path to value creation through systematic mark-to-market lease renewals.</p>
          <div style="font-size:7px;color:rgba(42,82,160,0.55);margin-top:7px;font-style:italic;font-family:var(--sans);">&#8857; Synthesized by NewCo AI Platform from permit, zoning, demographic, and market data &middot; March 2026</div>
        </div>

        <!-- Value-add thesis box — v3: populated with spec numbers -->
        <div class="value-add-box" style="margin-bottom:16px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
            <div style="font-size:8px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--wo-blue);font-family:var(--sans);">$19.6M Embedded Value &#8212; 9.1% Mark-to-Market Opportunity</div>
            <span class="score-badge badge-gold">RentCast Market Data</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
            <div style="padding:8px 10px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:3px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">1 BR / 1 BA (184 units)</div>
              <div style="font-size:8.5px;color:var(--slate);">In-Place: <strong style="color:var(--navy);">$2,130</strong></div>
              <div style="font-size:8.5px;color:var(--slate);">Market Avg: <strong style="color:var(--green);">$2,340</strong></div>
              <div style="font-size:8px;color:var(--wo-blue);font-weight:600;margin-top:3px;">Gap: $210 (9.0%)</div>
            </div>
            <div style="padding:8px 10px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:3px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">2 BR / 2 BA (268 units)</div>
              <div style="font-size:8.5px;color:var(--slate);">In-Place: <strong style="color:var(--navy);">$2,710</strong></div>
              <div style="font-size:8.5px;color:var(--slate);">Market Avg: <strong style="color:var(--green);">$2,980</strong></div>
              <div style="font-size:8px;color:var(--wo-blue);font-weight:600;margin-top:3px;">Gap: $270 (9.1%)</div>
            </div>
            <div style="padding:8px 10px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:3px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">3 BR / 2 BA (100 units)</div>
              <div style="font-size:8.5px;color:var(--slate);">In-Place: <strong style="color:var(--navy);">$3,980</strong></div>
              <div style="font-size:8.5px;color:var(--slate);">Market Avg: <strong style="color:var(--green);">$4,380</strong></div>
              <div style="font-size:8px;color:var(--wo-blue);font-weight:600;margin-top:3px;">Gap: $400 (9.1%)</div>
            </div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);margin-top:7px;font-style:italic;">~331 below-market units &times; $247/unit/month avg gap &times; 12 = $980,964/yr additional NOI. At 5.0% cap rate = $19.6M implied embedded value.</div>
        </div>

        <h4 style="margin-bottom:10px;">Investment Highlights</h4>

        <div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text"><strong>Vienna Metro Access &#8212; Institutional Rent Premium:</strong> Vienna/Fairfax-GMU Metro station 1.3 miles from property. Silver Line access to Tysons Corner, Reston, Arlington, and Union Station. NoVA research consistently documents 10&#8211;20% rent premium for walkable Metro proximity, directly supporting above-market rent capture on unit turnover.</div></div>

        <div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text"><strong>George Mason University Demand Engine:</strong> GMU at 0.9 miles enrolls 39,000+ students with 7,500+ employees. Graduate student and faculty housing demand provides recession-resistant occupancy floor. University enrollment has grown consistently regardless of broader economic cycles.</div></div>

        <div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text"><strong>Supply-Constrained Location &#8212; Zero Competing Pipeline:</strong> Development Pressure Score of 18/100 (Low). PDH/PRC zoning with Comprehensive Plan designation unchanged. No new multifamily permits within 2-mile radius in trailing 24 months. Fairfax County&#8217;s development review process makes competitive supply additions a 5&#8211;7 year horizon at minimum.</div></div>

        <div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text"><strong>Top-Tier School District &#8212; Family Tenant Retention:</strong> Served by Woodson High School (88% SOL), Frost Middle (81%), and Mantua Elementary (84%) &#8212; all consistently above Virginia SOL state averages. School quality is the #1 stated retention driver for family renters in Fairfax County surveys.</div></div>

        <div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text"><strong>Inova Fairfax Hospital &#8212; Healthcare Anchor (3.3 mi):</strong> One of the region&#8217;s premier healthcare facilities drives consistent demand from medical professionals and health system employees. Inova Health System employment has grown +206% since 2009 (to 26,000+ employees), creating sustained multifamily demand within the care radius.</div></div>

        <div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text"><strong>Deep, Diversified Employment &#8212; Recession-Resistant Demand:</strong> 3-mile median household income of $159,400 (2.1&times; national median). Federal government (28,126 county employees), FCPS, George Mason University, and the Tysons/Merrifield technology corridor provide multi-sector employment insulation unavailable in single-industry markets.</div></div>
      </div>

      <div class="vdiv"></div>

      <!-- RIGHT: metrics + scores -->
      <div style="flex:1;display:flex;flex-direction:column;gap:12px;">

        <div>
          <h4 style="margin-bottom:7px;">Key Financial Metrics</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--rule);border:1px solid var(--rule);">
            <div class="kpi-light"><div class="kl">Asking Price</div><div class="kv">$232M</div></div>
            <div class="kpi-light"><div class="kl">T-12 Cap Rate <span style="text-transform:none;letter-spacing:0;">(Actual)</span></div><div class="kv">5.02%</div></div>
            <div class="kpi-light"><div class="kl">Pro Forma Cap Rate</div><div class="kv">5.26%</div><div class="ks">Stabilized YR 1</div></div>
            <div class="kpi-light"><div class="kl">T-12 NOI <span style="text-transform:none;letter-spacing:0;">(Actual)</span></div><div class="kv">$11.65M</div></div>
            <div class="kpi-light"><div class="kl">Total Units</div><div class="kv">552</div></div>
            <div class="kpi-light"><div class="kl">Price / Unit</div><div class="kv">$420,289</div></div>
          </div>
          <div style="font-size:7px;color:var(--red);font-weight:600;padding:4px 0;font-family:var(--sans);">&#9888; Cap rate labels distinguish T-12 Actual vs. Pro Forma throughout this document.</div>
        </div>

        <hr class="rule">

        <!-- Stoplight scores — v3 Change 3: NO numerical scores on exec summary -->
        <div>
          <h4 style="margin-bottom:9px;">NewCo Location Intelligence Scores</h4>
          <div>
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot sl-green"></div><div class="score-label">Location Quality &#8212; <strong>Strong</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:78%;"></div></div>
                <span class="score-badge badge-green">Strong</span>
              </div>
            </div>
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot sl-green"></div><div class="score-label">Crime Safety &#8212; <strong>Safe</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:71%;background:var(--green);"></div></div>
                <span class="score-badge badge-green">Safe</span>
              </div>
            </div>
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot sl-green"></div><div class="score-label">Convenience &#8212; <strong>Excellent</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:82%;"></div></div>
                <span class="score-badge badge-green">Excellent</span>
              </div>
            </div>
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot sl-green"></div><div class="score-label">Medical Access &#8212; <strong>Top Tier</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:88%;background:var(--green);"></div></div>
                <span class="score-badge badge-green">Top Tier</span>
              </div>
            </div>
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot sl-green"></div><div class="score-label">Development Pressure &#8212; <strong>Low &middot; Supply Constrained</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:18%;background:var(--green);"></div></div>
                <span class="score-badge badge-green">Low &#10003;</span>
              </div>
            </div>
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot sl-amber"></div><div class="score-label">Transit Score &#8212; <strong>Good / Car Needed</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:64%;background:var(--amber);"></div></div>
                <span class="score-badge badge-amber">Good</span>
              </div>
            </div>
          </div>
          <div style="font-size:7px;color:var(--slate-light);margin-top:5px;font-style:italic;">&#x1F7E2; Green = strong investment attribute &middot; &#x1F7E1; Amber = consider in underwriting &middot; &#x1F534; Red = risk factor</div>
        </div>

        <hr class="rule">

        <!-- Property specs -->
        <div>
          <h4 style="margin-bottom:7px;">Property Details</h4>
          <div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate-light);">Address</span><span style="font-size:8px;color:var(--navy);font-weight:500;">9333 Clocktower Pl.</span></div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate-light);">Submarket</span><span style="font-size:8px;color:var(--navy);font-weight:500;">Merrifield&#8211;Vienna</span></div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate-light);">Zoning</span><span style="font-size:8px;color:var(--navy);font-weight:500;">PDH &middot; Planned Dev. Housing</span></div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate-light);">Metro Station</span><span style="font-size:8px;color:var(--navy);font-weight:500;">Vienna/Fairfax-GMU &#8212; 1.3 mi</span></div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate-light);">Year Built / Mgr.</span><span style="font-size:8px;color:var(--navy);font-weight:500;">1997 / Bozzuto Mgmt</span></div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;"><span style="font-size:8px;color:var(--slate-light);">Utility Structure</span><span style="font-size:8px;color:var(--navy);font-weight:500;">Tenant: Elec+Gas | LL: Water</span></div>
          </div>
        </div>

      </div>
    </div>
  </div>

  <div class="page-footer">
    <div class="pf-left">Executive Summary</div>
    <div class="pf-center">Regent&#8217;s Park &middot; Fairfax, Virginia 22031</div>
    <div style="display:flex;align-items:center;gap:10px;"><div class="wo-mark"><img src="{LOGO_B64}" alt="WO"><span class="pf-right">West Oxford Advisors</span></div><span class="pf-right">Page 2</span></div>
  </div>
</div>
'''


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 — FINANCIAL ANALYSIS
# v3 Change 1: Full financial model from spec
# v3 Change 2: Reframe utility section — landlord benchmark only, no EIA tenant estimates
# v3 Change 4: Replace credibility warning with gray footnote
# ═══════════════════════════════════════════════════════════════════════════
def page3_financial():
    return f'''
<!-- ═══════════════════════════════════
     PAGE 3 — FINANCIAL ANALYSIS
════════════════════════════════════ -->
<div class="page">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:var(--wo-blue);"></div>
  <div style="padding:40px 36px 36px;">
    <div class="sec-label">Section Two</div>
    <div class="sec-title">Financial Analysis</div>
    <div class="gold-rule"></div>

    <!-- Unit Mix Table — v3: full spec data -->
    <h4 style="margin-bottom:7px;">Unit Mix &amp; In-Place Rents</h4>
    <table class="dtable" style="margin-bottom:5px;">
      <thead>
        <tr>
          <th>Unit Type</th>
          <th class="r">Count</th>
          <th class="r">Pct</th>
          <th class="r">Avg SF</th>
          <th class="r">In-Place Rent</th>
          <th class="r">Mkt Rent (RentCast)</th>
          <th class="r">Gap</th>
        </tr>
      </thead>
      <tbody>
        <tr><td class="strong">1 BR / 1 BA</td><td class="r">184</td><td class="r">33%</td><td class="r">728</td><td class="r">$2,130</td><td class="r" style="color:var(--green);">$2,340</td><td class="r" style="color:var(--wo-blue);">$210 (9.0%)</td></tr>
        <tr><td class="strong">2 BR / 2 BA</td><td class="r">268</td><td class="r">49%</td><td class="r">1,064</td><td class="r">$2,710</td><td class="r" style="color:var(--green);">$2,980</td><td class="r" style="color:var(--wo-blue);">$270 (9.1%)</td></tr>
        <tr><td class="strong">3 BR / 2 BA</td><td class="r">100</td><td class="r">18%</td><td class="r">1,434</td><td class="r">$3,980</td><td class="r" style="color:var(--green);">$4,380</td><td class="r" style="color:var(--wo-blue);">$400 (9.1%)</td></tr>
      </tbody>
      <tfoot>
        <tr><td><strong>Portfolio</strong></td><td class="r"><strong>552</strong></td><td class="r"></td><td class="r"><strong>1,031 avg</strong></td><td class="r"><strong>$2,480 avg</strong></td><td class="r"><strong style="color:var(--green);">$2,727 avg</strong></td><td class="r"><strong style="color:var(--wo-blue);">$247 (9.1%)</strong></td></tr>
      </tfoot>
    </table>
    <div style="font-size:7.5px;color:var(--slate-light);font-style:italic;margin-bottom:16px;">Full 552-unit rent roll available upon execution of confidentiality agreement. Market rent data sourced via RentCast API for ZIP 22031.</div>

    <!-- Income/Expense two column + Utility benchmark -->
    <div style="display:flex;gap:14px;margin-bottom:14px;">
      <!-- Two-col financials — v3: fully populated from spec -->
      <div style="flex:1.8;">
        <div style="display:flex;gap:1px;background:var(--rule);">
          <div style="flex:1;">
            <div class="col-lbl lbl-actual">&#9888; Trailing 12-Month Actuals &#8212; T-12</div>
            <table class="ftable">
              <tbody>
                <tr><td>Gross Potential Rent</td><td>$16,428,000</td></tr>
                <tr class="indent"><td>Vacancy Loss (4.5%)</td><td style="color:#9b1c1c;">($739,000)</td></tr>
                <tr class="indent"><td>Credit / Bad Debt (0.5%)</td><td style="color:#9b1c1c;">($82,000)</td></tr>
                <tr class="cat"><td>Effective Gross Income</td><td>$15,607,000</td></tr>
                <tr><td style="padding-top:6px;">Real Estate Taxes</td><td>($1,385,000)</td></tr>
                <tr><td>Insurance</td><td>($345,000)</td></tr>
                <tr><td>Repairs &amp; Maintenance</td><td>($580,000)</td></tr>
                <tr><td>Property Management (5%)</td><td>($780,000)</td></tr>
                <tr><td>Utilities &#8212; Landlord-Paid</td><td>($485,000)</td></tr>
                <tr><td>Administrative</td><td>($245,000)</td></tr>
                <tr><td>Reserves ($250/unit)</td><td>($138,000)</td></tr>
                <tr class="noi"><td>Net Operating Income</td><td>$11,649,000</td></tr>
              </tbody>
            </table>
          </div>
          <div style="flex:1;">
            <div class="col-lbl lbl-proforma">Pro Forma Year 1 &#8212; Stabilized</div>
            <table class="ftable">
              <tbody>
                <tr><td>Gross Potential Rent</td><td>$16,940,000</td></tr>
                <tr class="indent"><td>Vacancy Loss (5.0%)</td><td style="color:#9b1c1c;">($847,000)</td></tr>
                <tr class="indent"><td>Credit / Bad Debt (0.5%)</td><td style="color:#9b1c1c;">($85,000)</td></tr>
                <tr class="cat"><td>Effective Gross Income</td><td>$15,890,000</td></tr>
                <tr><td style="padding-top:6px;">Real Estate Taxes</td><td>($1,415,000)</td></tr>
                <tr><td>Insurance</td><td>($355,000)</td></tr>
                <tr><td>Repairs &amp; Maintenance</td><td>($590,000)</td></tr>
                <tr><td>Property Management (5%)</td><td>($795,000)</td></tr>
                <tr><td>Utilities &#8212; Landlord-Paid</td><td>($495,000)</td></tr>
                <tr><td>Administrative</td><td>($250,000)</td></tr>
                <tr><td>Reserves ($250/unit)</td><td>($138,000)</td></tr>
                <tr class="noi"><td>Net Operating Income</td><td style="color:var(--gold-light);">$12,200,000</td></tr>
              </tbody>
            </table>
          </div>
        </div>
        <!-- v3 Change 4: Gray footnote replaces red credibility warning -->
        <div style="background:rgba(15,31,56,0.04);border:1px solid var(--rule);padding:5px 10px;margin-top:4px;">
          <div style="font-size:7.5px;color:var(--slate);font-style:italic;line-height:1.6;"><em>Metric labeling convention: All figures are labeled T-12 Actual or Pro Forma YR1 throughout this document. Mixing trailing actuals with forward projections without clear labels is the most common source of OM credibility errors in the industry (PropRise, 2024). Pro Forma assumes 3.5% rent growth on below-market units at lease renewal.</em></div>
        </div>
      </div>

      <!-- Utility benchmark sidebar — v3 Change 2: landlord benchmark only -->
      <div style="flex:0.8;display:flex;flex-direction:column;gap:10px;">
        <div>
          <h4 style="margin-bottom:7px;">Landlord Utility Expense Benchmark</h4>
          <div class="util-box">
            <div style="font-size:7.5px;color:var(--slate-light);font-style:italic;margin-bottom:6px;">Landlord-paid utilities: water, sewer, and common area electric. Benchmarked against NoVA multifamily industry averages.</div>
            <div class="util-row">
              <div><div class="util-label">Subject Property (T-12)</div><div class="util-source">$485,000 / 552 units</div></div>
              <div class="util-val">$879/unit/yr</div>
            </div>
            <div class="util-row">
              <div><div class="util-label">NoVA MF Benchmark (Low)</div><div class="util-source">Industry average range</div></div>
              <div class="util-val">$820/unit/yr</div>
            </div>
            <div class="util-row">
              <div><div class="util-label">NoVA MF Benchmark (High)</div><div class="util-source">Industry average range</div></div>
              <div class="util-val">$960/unit/yr</div>
            </div>
            <div class="util-row" style="border-top:2px solid var(--gold);margin-top:4px;padding-top:6px;">
              <div><div class="util-label" style="font-weight:600;color:var(--navy);">Assessment</div><div class="util-source">$879 within $820&#8211;$960 range</div></div>
              <div class="util-val" style="color:var(--green);">Within Normal Range</div>
            </div>
          </div>
          <div style="font-size:7px;color:var(--slate-light);font-style:italic;margin-top:4px;line-height:1.55;">Utility expense ($485,000 T-12 Actual) reflects landlord-paid water, sewer, and common area electric only &#8212; approximately $879/unit/year. Individual unit electric and gas are metered directly to tenants by Dominion Energy and Washington Gas respectively and do not appear in the property&#8217;s operating statement.</div>
        </div>

        <div>
          <h4 style="margin-bottom:7px;">5-Year Cash Flow Projection</h4>
          <table style="width:100%;border-collapse:collapse;font-size:8px;font-family:var(--sans);">
            <thead>
              <tr style="background:var(--navy);">
                <th style="padding:5px 7px;font-size:7px;letter-spacing:0.08em;text-transform:uppercase;color:rgba(255,255,255,0.6);text-align:left;font-weight:600;">Metric</th>
                <th style="padding:5px 7px;font-size:7px;color:rgba(255,255,255,0.6);text-align:right;font-weight:600;">YR1</th>
                <th style="padding:5px 7px;font-size:7px;color:rgba(255,255,255,0.6);text-align:right;font-weight:600;">YR3</th>
                <th style="padding:5px 7px;font-size:7px;color:rgba(255,255,255,0.6);text-align:right;font-weight:600;">YR5</th>
              </tr>
            </thead>
            <tbody>
              <tr style="border-bottom:1px solid var(--rule);"><td style="padding:5px 7px;color:var(--navy);">EGI</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">$15.89M</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">$16.51M</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">$17.16M</td></tr>
              <tr style="border-bottom:1px solid var(--rule);"><td style="padding:5px 7px;color:var(--navy);">NOI</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">$12.20M</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">$12.73M</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">$13.29M</td></tr>
              <tr style="border-bottom:1px solid var(--rule);"><td style="padding:5px 7px;color:var(--navy);">Debt Svc</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">($5.99M)</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">($5.99M)</td><td style="padding:5px 7px;text-align:right;color:var(--slate);">($5.99M)</td></tr>
              <tr style="background:#f0ede8;"><td style="padding:5px 7px;font-weight:600;color:var(--navy);">Cash Flow</td><td style="padding:5px 7px;text-align:right;font-weight:600;color:var(--green);">$6.22M</td><td style="padding:5px 7px;text-align:right;font-weight:600;color:var(--green);">$6.75M</td><td style="padding:5px 7px;text-align:right;font-weight:600;color:var(--green);">$7.30M</td></tr>
            </tbody>
          </table>
          <div style="font-size:7px;color:var(--slate-light);font-style:italic;margin-top:4px;">Assumes 65% LTV financing at 6.25% interest, 30-yr amortization. DSCR: 1.38&times;. Pro Forma only.</div>
        </div>

        <!-- Key Metrics sidebar -->
        <div style="background:var(--bg);border:1px solid var(--rule);padding:8px 10px;">
          <h4 style="margin-bottom:5px;">Key Metrics</h4>
          <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate);">Asking Price</span><span style="font-size:8px;font-weight:600;color:var(--navy);">$232,000,000</span></div>
          <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate);">Price / Unit</span><span style="font-size:8px;font-weight:600;color:var(--navy);">$420,289</span></div>
          <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate);">T-12 Cap Rate</span><span style="font-size:8px;font-weight:600;color:var(--navy);">5.02%</span></div>
          <div style="display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid var(--rule);"><span style="font-size:8px;color:var(--slate);">Pro Forma Cap Rate</span><span style="font-size:8px;font-weight:600;color:var(--navy);">5.26%</span></div>
          <div style="display:flex;justify-content:space-between;padding:3px 0;"><span style="font-size:8px;color:var(--slate);">OpEx Ratio</span><span style="font-size:8px;font-weight:600;color:var(--navy);">25.4%</span></div>
        </div>
      </div>
    </div>

    <!-- CRE Comps — v3: populated with spec data -->
    <h4 style="margin-bottom:7px;">Comparable Sales &#8212; Multifamily / Commercial</h4>
    <div style="background:#fafaf8;border:1px solid var(--rule);padding:10px 14px;">
      <div style="display:flex;gap:20px;align-items:flex-start;">
        <div style="flex:1;">
          <div style="font-size:8.5px;font-weight:600;color:var(--navy);margin-bottom:4px;">Commercial Sales Comps &#8212; Vienna/Merrifield Submarket</div>
          <p style="font-size:8.5px;line-height:1.6;">Multifamily building sales comparables sourced from Virginia RETR deed transfer records via Fairfax County GIS parcel layer cross-reference. Recent transactions in the Vienna/Merrifield submarket demonstrate institutional pricing consistent with the subject property&#8217;s asking basis.</p>
        </div>
        <div style="flex:0.6;padding:8px 10px;background:rgba(42,82,160,0.05);border:1px solid rgba(42,82,160,0.15);">
          <div style="font-size:7.5px;font-weight:600;color:var(--wo-blue);margin-bottom:5px;letter-spacing:0.08em;text-transform:uppercase;">Data Sources</div>
          <div style="font-size:8px;color:var(--slate);line-height:1.8;">&#10003; Virginia RETR (deed transfers)<br>&#10003; Fairfax Co. Land Records GIS<br>&#8857; CREXi (activation pending)<br>&#8857; ATTOM multifamily (pending)</div>
        </div>
      </div>
      <table class="dtable" style="margin-top:10px;">
        <thead>
          <tr>
            <th>Property Name / Address</th>
            <th class="r">Units</th>
            <th class="r">Sale Price</th>
            <th class="r">Price / Unit</th>
            <th class="r">Est. Cap</th>
            <th>Sale Date</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          <tr><td class="strong">Halstead Square, 2729 Merrilee Dr</td><td class="r">438</td><td class="r">$178,500,000</td><td class="r">$407,534</td><td class="r">5.1%</td><td>Jun 2024</td><td><span class="score-badge badge-navy">Virginia RETR</span></td></tr>
          <tr><td class="strong">Avalon Mosaic, 2987 District Ave</td><td class="r">317</td><td class="r">$134,200,000</td><td class="r">$423,344</td><td class="r">4.9%</td><td>Feb 2024</td><td><span class="score-badge badge-navy">Virginia RETR</span></td></tr>
          <tr><td class="strong">Prosperity Flats, 2700 Dorr Ave</td><td class="r">186</td><td class="r">$74,800,000</td><td class="r">$402,151</td><td class="r">5.3%</td><td>Oct 2023</td><td><span class="score-badge badge-navy">Virginia RETR</span></td></tr>
        </tbody>
      </table>
    </div>

  </div>
  <div class="page-footer">
    <div class="pf-left">Financial Analysis</div>
    <div class="pf-center">Regent&#8217;s Park &middot; Fairfax, Virginia 22031</div>
    <div style="display:flex;align-items:center;gap:10px;"><div class="wo-mark"><img src="{LOGO_B64}" alt="WO"><span class="pf-right">West Oxford Advisors</span></div><span class="pf-right">Page 3</span></div>
  </div>
</div>
'''


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 — DEVELOPMENT INTELLIGENCE
# v3 Change 3: Numerical score (18/100) and formula breakdown belong HERE
# v3: Replace percentile claim with county context language from spec
# v3 Change 1: Fill all placeholders with spec data
# ═══════════════════════════════════════════════════════════════════════════
def page4_development():
    return f'''
<!-- ═══════════════════════════════════
     PAGE 4 — DEVELOPMENT INTELLIGENCE
════════════════════════════════════ -->
<div class="page">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:var(--wo-blue);"></div>
  <div style="padding:40px 36px 36px;">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:4px;">
      <div><div class="sec-label">Section Three &#9733; NewCo Exclusive</div>
      <div class="sec-title">Development Intelligence</div>
      <div class="gold-rule"></div></div>
      <span class="score-badge badge-navy" style="margin-top:8px;font-size:7.5px;">Data Not Available in Any Competing OM Platform</span>
    </div>

    <div style="display:flex;gap:20px;">
      <!-- LEFT COL -->
      <div style="flex:1.1;">
        <!-- Score display — v3: numerical score 18/100 belongs HERE -->
        <div class="pressure-main">
          <div>
            <div class="pressure-num">18</div>
            <div style="font-size:8px;color:var(--slate-light);">out of 100</div>
          </div>
          <div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;"><div class="sl-dot sl-green"></div><div style="font-family:var(--serif);font-size:15px;font-weight:600;color:var(--green);">Low Development Pressure</div></div>
            <p style="font-size:8.5px;line-height:1.6;color:var(--slate);">Minimal competing development activity within the 2-mile radius. No new multifamily permits filed in the trailing 24 months. Existing PDH/PRC zoning and Fairfax County&#8217;s lengthy entitlement process create a substantial barrier to competitive supply additions &#8212; protecting in-place NOI and supporting rent growth.</p>
            <div style="margin-top:6px;display:flex;gap:5px;">
              <span class="score-badge badge-green">Investor Positive</span>
              <span class="score-badge badge-navy">Supply Constrained</span>
              <span class="score-badge badge-navy">5&#8211;7 Yr Barrier to Entry</span>
            </div>
          </div>
        </div>

        <!-- Formula breakdown — v3: THIS is where scores belong -->
        <div class="formula-box">
          <div style="font-size:8px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--navy);margin-bottom:8px;font-family:var(--sans);">Score Methodology &#8212; 5-Component Composite</div>
          <div class="formula-row">
            <div class="formula-name">Permit Volume (# near property vs. county baseline)</div>
            <div class="formula-weight">30%</div>
            <div class="formula-bar-track"><div class="formula-bar-fill" style="width:20%;background:var(--green);"></div></div>
            <div class="formula-score">Low</div>
          </div>
          <div class="formula-row">
            <div class="formula-name">Permit Recency (last 12 mo. vs. 24 mo. total)</div>
            <div class="formula-weight">20%</div>
            <div class="formula-bar-track"><div class="formula-bar-fill" style="width:15%;background:var(--green);"></div></div>
            <div class="formula-score">Low</div>
          </div>
          <div class="formula-row">
            <div class="formula-name">Permit Type (residential/new vs. commercial alt.)</div>
            <div class="formula-weight">20%</div>
            <div class="formula-bar-track"><div class="formula-bar-fill" style="width:25%;background:var(--amber);"></div></div>
            <div class="formula-score">Low-Med</div>
          </div>
          <div class="formula-row">
            <div class="formula-name">Proximity (distance from nearest permit activity)</div>
            <div class="formula-weight">15%</div>
            <div class="formula-bar-track"><div class="formula-bar-fill" style="width:12%;background:var(--green);"></div></div>
            <div class="formula-score">Low</div>
          </div>
          <div class="formula-row">
            <div class="formula-name">Planning Zone (Comp Plan growth center distance)</div>
            <div class="formula-weight">15%</div>
            <div class="formula-bar-track"><div class="formula-bar-fill" style="width:18%;background:var(--green);"></div></div>
            <div class="formula-score">Low</div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);margin-top:7px;font-style:italic;">Score: 0 = No pressure (supply constrained &middot; investor positive) | 100 = Extreme pressure (competing supply imminent)</div>
        </div>

        <!-- Fairfax context — v3: filled with spec data, county context language -->
        <div style="background:#f5f3ef;border:1px solid rgba(184,150,106,0.25);padding:10px 12px;">
          <div style="font-size:8px;font-weight:600;color:var(--navy);margin-bottom:6px;font-family:var(--sans);">Fairfax County Context &#8212; 41,504 Total Permits in Database</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div style="padding:7px 9px;background:white;border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:20px;font-weight:600;color:var(--navy);">13</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Permits within 2 mi.<br>(last 24 months)</div>
            </div>
            <div style="padding:7px 9px;background:white;border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:20px;font-weight:600;color:var(--green);">0</div>
              <div style="font-size:7.5px;color:var(--slate-light);">New multifamily permits<br>within 2 mi.</div>
            </div>
            <div style="padding:7px 9px;background:white;border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:20px;font-weight:600;color:var(--slate);">9</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Commercial alt. permits<br>(non-competing)</div>
            </div>
            <div style="padding:7px 9px;background:white;border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:20px;font-weight:600;color:var(--navy);">1.8 mi</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Nearest permit activity<br>to subject property</div>
            </div>
          </div>
          <!-- v3: County context language replaces percentile claim -->
          <div style="font-size:7.5px;color:var(--slate);font-style:italic;margin-top:8px;line-height:1.55;">13 permits within 2-mile radius vs. Fairfax County permit database of 41,504 total permits for similarly-zoned parcels. Zero new multifamily permits filed within 2 miles in the trailing 24 months.</div>
        </div>
      </div>

      <!-- RIGHT COL -->
      <div style="flex:1;display:flex;flex-direction:column;gap:14px;">

        <!-- Development map -->
        <div>
          <h4 style="margin-bottom:6px;">Development Activity Map (2-Mile Radius)</h4>
          <div class="mapbox" style="height:200px;flex-direction:column;gap:8px;">
            <div class="mapbox-label">Interactive Development Map<br><span style="font-size:7px;opacity:0.7;">Permit locations &middot; Metro station &middot; Growth centers</span></div>
          </div>
          <div style="font-size:7px;color:var(--slate-light);margin-top:4px;">
            &#x1F535; Subject Property &nbsp;|&nbsp; &#x1F534; Active permits (residential) &nbsp;|&nbsp; &#x1F7E1; Commercial permits &nbsp;|&nbsp; &#x24C2; Metro station &nbsp;|&nbsp; &#8212; Comp Plan growth boundary
          </div>
        </div>

        <!-- Permit activity chart — v3: filled with spec data -->
        <div>
          <h4 style="margin-bottom:7px;">Permit Activity by Type &#8212; 2-Mile Radius, 24 Months</h4>
          <div class="bar-chart">
            <div class="bar-row">
              <div class="bar-rl">New Residential</div>
              <div class="bar-track"><div class="bar-fill bar-primary" style="width:0%;"></div></div>
              <div class="bar-pct">0</div>
            </div>
            <div class="bar-row">
              <div class="bar-rl">Commercial Alteration</div>
              <div class="bar-track"><div class="bar-fill bar-primary" style="width:69%;"></div></div>
              <div class="bar-pct">9</div>
            </div>
            <div class="bar-row">
              <div class="bar-rl">Residential Renovation</div>
              <div class="bar-track"><div class="bar-fill bar-light" style="width:31%;"></div></div>
              <div class="bar-pct">4</div>
            </div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);font-style:italic;margin-top:5px;">Commercial alteration permits indicate area economic activity without introducing residential competition. Total: 13 permits within 2-mi radius, 24-month period.</div>
        </div>

        <!-- Zoning intel — v3: filled placeholders -->
        <div style="background:rgba(15,31,56,0.04);border:1px solid var(--rule);padding:10px 12px;">
          <h4 style="margin-bottom:7px;">Zoning Intelligence &#9733;</h4>
          <div style="display:flex;flex-direction:column;gap:4px;">
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);">
              <span style="font-size:8px;color:var(--slate);">Current Zoning Classification</span>
              <span style="font-size:8px;font-weight:600;color:var(--navy);">PDH / PRC</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);">
              <span style="font-size:8px;color:var(--slate);">Comp Plan Designation</span>
              <span style="font-size:8px;font-weight:600;color:var(--navy);">Medium Res / Suburban</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--rule);">
              <span style="font-size:8px;color:var(--slate);">Distance to Growth Center</span>
              <span style="font-size:8px;font-weight:600;color:var(--green);">1.8 mi &#8212; Outside</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:4px 0;">
              <span style="font-size:8px;color:var(--slate);">Upzoning Risk Assessment</span>
              <span style="font-size:8px;font-weight:600;color:var(--green);">Low &#8212; Stable Designation</span>
            </div>
          </div>
          <p style="font-size:8px;color:var(--slate);line-height:1.55;margin-top:8px;">Fairfax County&#8217;s PDH designation requires Planned Development approval for any density increases &#8212; a multi-year entitlement process that serves as an effective barrier to rapid competing development. The Comp Plan&#8217;s suburban residential designation for this area has not changed in the most recent General Plan update cycle.</p>
        </div>

      </div>
    </div>
  </div>
  <div class="page-footer">
    <div class="pf-left">Development Intelligence</div>
    <div class="pf-center">Regent&#8217;s Park &middot; Fairfax, Virginia 22031</div>
    <div style="display:flex;align-items:center;gap:10px;"><div class="wo-mark"><img src="{LOGO_B64}" alt="WO"><span class="pf-right">West Oxford Advisors</span></div><span class="pf-right">Page 4</span></div>
  </div>
</div>
'''


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 — MARKET OVERVIEW  (was page 6 in v2, now page 5 per task spec)
# Note: The task says page5_market() and page6_location(). The v2 had
# page 5 = Location Analysis and page 6 = Market Overview. The task
# build order says: page5_market, page6_location. We follow the task order.
# v3: Fill all placeholders with spec data
# ═══════════════════════════════════════════════════════════════════════════
def page5_market():
    return f'''
<!-- ═══════════════════════════════════
     PAGE 5 — MARKET OVERVIEW
════════════════════════════════════ -->
<div class="page">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:var(--wo-blue);"></div>
  <div style="padding:40px 36px 36px;">
    <div class="sec-label">Section Four</div>
    <div class="sec-title">Market Overview</div>
    <div class="gold-rule"></div>

    <div style="display:flex;gap:20px;">
      <!-- LEFT COL -->
      <div style="flex:1;display:flex;flex-direction:column;gap:14px;">

        <!-- Demographic KPIs — v3: all placeholders filled -->
        <div>
          <h4 style="margin-bottom:8px;">Demographic Snapshot &#8212; 3-Mile Radius (Census ACS 5-Year)</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">
            <div style="padding:10px 12px;background:var(--navy);color:white;">
              <div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:4px;">Median HH Income</div>
              <div style="font-family:var(--serif);font-size:22px;font-weight:600;">$159,400</div>
              <div style="font-size:7.5px;color:var(--gold-light);">2.1&times; National Median</div>
            </div>
            <div style="padding:10px 12px;background:var(--navy);color:white;">
              <div style="font-size:7px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:4px;">Population (3-mi)</div>
              <div style="font-family:var(--serif);font-size:22px;font-weight:600;">128,400</div>
              <div style="font-size:7.5px;color:var(--gold-light);">+4.2% 5-yr growth</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">Bachelor&#8217;s Degree+</div>
              <div style="font-family:var(--serif);font-size:16px;font-weight:600;color:var(--navy);">62%</div>
              <div style="font-size:7.5px;color:var(--slate-light);">vs. 41% VA statewide</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">Median Age</div>
              <div style="font-family:var(--serif);font-size:16px;font-weight:600;color:var(--navy);">38 yrs</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Prime renter cohort 25&#8211;44</div>
            </div>
          </div>
        </div>

        <!-- Income distribution — v3: filled with spec data -->
        <div>
          <h4 style="margin-bottom:7px;">Household Income Distribution &#8212; 3-Mile Radius</h4>
          <div class="bar-chart">
            <div class="bar-row"><div class="bar-rl">$200,000+</div><div class="bar-track"><div class="bar-fill bar-primary" style="width:28%;"></div></div><div class="bar-pct">28%</div></div>
            <div class="bar-row"><div class="bar-rl">$150,000&#8211;$200,000</div><div class="bar-track"><div class="bar-fill bar-primary" style="width:19%;"></div></div><div class="bar-pct">19%</div></div>
            <div class="bar-row"><div class="bar-rl">$100,000&#8211;$150,000</div><div class="bar-track"><div class="bar-fill bar-primary" style="width:24%;"></div></div><div class="bar-pct">24%</div></div>
            <div class="bar-row"><div class="bar-rl">$75,000&#8211;$100,000</div><div class="bar-track"><div class="bar-fill bar-light" style="width:14%;"></div></div><div class="bar-pct">14%</div></div>
            <div class="bar-row"><div class="bar-rl">&lt;$75,000</div><div class="bar-track"><div class="bar-fill bar-light" style="width:15%;"></div></div><div class="bar-pct">15%</div></div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);margin-top:4px;font-style:italic;">Source: U.S. Census ACS 5-Year Estimates. 71% of households earn $100K+, supporting premium multifamily rents.</div>
        </div>

        <!-- Fairfax market summary -->
        <div style="background:rgba(42,82,160,0.05);border:1px solid rgba(42,82,160,0.2);padding:11px 13px;">
          <h4 style="margin-bottom:7px;color:var(--wo-blue);">Fairfax County Multifamily Market Context</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:7px;">
            <div style="padding:6px 8px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">Avg. Mkt. Cap Rate</div>
              <div style="font-size:11px;font-weight:600;color:var(--navy);">5.1% T-12</div>
            </div>
            <div style="padding:6px 8px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">Avg. Price / Unit</div>
              <div style="font-size:11px;font-weight:600;color:var(--navy);">$411K</div>
            </div>
            <div style="padding:6px 8px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">County Vacancy Rate</div>
              <div style="font-size:11px;font-weight:600;color:var(--green);">4.5%</div>
            </div>
            <div style="padding:6px 8px;background:white;border:1px solid rgba(42,82,160,0.15);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">12-Mo Rent Growth</div>
              <div style="font-size:11px;font-weight:600;color:var(--green);">+3.8%</div>
            </div>
          </div>
          <p style="font-size:8.5px;line-height:1.6;color:var(--slate);">Fairfax County&#8217;s multifamily market benefits from federal government employment stability, technology sector growth anchored by the Amazon HQ2 spillover effect, and structural supply constraints from the county&#8217;s development approval process. The Merrifield&#8211;Vienna submarket consistently outperforms the broader county averages due to Metro proximity and George Mason University demand.</p>
          <div style="font-size:7.5px;color:var(--slate-light);margin-top:5px;font-style:italic;">Source: Serafin Real Estate NoVA Market Reports Q1 2023&#8211;Q3 2025; Fairfax County DTA 2025 Assessments</div>
        </div>

      </div>

      <!-- RIGHT COL -->
      <div style="flex:1;display:flex;flex-direction:column;gap:14px;">

        <!-- Major employers -->
        <div>
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:7px;">
            <h4 style="margin-bottom:0;">Major Employers &#9733; (18-Year Historical Data)</h4>
            <span class="score-badge badge-gold">NewCo Exclusive</span>
          </div>
          <div style="border:1px solid var(--rule);">
            <div class="emp-row" style="background:#f5f3ef;">
              <div class="emp-rank">#</div>
              <div style="font-size:7px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);flex:1.2;">Employer</div>
              <div style="font-size:7px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);flex:1;">Sector</div>
              <div style="font-size:7px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--slate-light);text-align:right;flex-shrink:0;">Employees</div>
            </div>
            <div class="emp-row"><div class="emp-rank">1</div><div class="emp-name">Fairfax County Gov&#8217;t</div><div class="emp-sector">Public Administration</div><div class="emp-count">28,126</div></div>
            <div class="emp-row"><div class="emp-rank">2</div><div class="emp-name">Fairfax County Public Schools</div><div class="emp-sector">Education</div><div class="emp-count">25,000+</div></div>
            <div class="emp-row"><div class="emp-rank">3</div><div class="emp-name">Inova Health System</div><div class="emp-sector">Healthcare</div><div class="emp-count">26,000+</div></div>
            <div class="emp-row"><div class="emp-rank">4</div><div class="emp-name">George Mason University</div><div class="emp-sector">Higher Education</div><div class="emp-count">7,500+</div></div>
            <div class="emp-row"><div class="emp-rank">5</div><div class="emp-name">Booz Allen Hamilton</div><div class="emp-sector">Defense / Consulting</div><div class="emp-count">~13,000</div></div>
            <div class="emp-row"><div class="emp-rank">6</div><div class="emp-name">Leidos Holdings</div><div class="emp-sector">Defense Technology</div><div class="emp-count">~8,500</div></div>
            <div class="emp-row"><div class="emp-rank">7</div><div class="emp-name">DXC Technology</div><div class="emp-sector">IT Services</div><div class="emp-count">~6,000</div></div>
            <div class="emp-row"><div class="emp-rank">8</div><div class="emp-name">Capital One Financial</div><div class="emp-sector">Financial Services</div><div class="emp-count">~5,500</div></div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);margin-top:4px;font-style:italic;">&#9733; NewCo employer database covers 18 years of Fairfax County employment data. Recession-resistant government, healthcare, and defense employers account for majority of regional employment base.</div>
        </div>

        <!-- Amenities snapshot — v3: filled with spec data -->
        <div>
          <h4 style="margin-bottom:7px;">Nearby Amenities &#8212; Google Places (1-Mile Radius)</h4>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;">
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">34</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Restaurants</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">6</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Grocery / Market</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">8</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Fitness / Gym</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">5</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Parks / Trails</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">11</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Coffee Shops</div>
            </div>
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">22</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Retail Shops</div>
            </div>
          </div>
        </div>

        <!-- Data attribution -->
        <div style="border:1px solid var(--rule);padding:11px 13px;margin-top:auto;">
          <div style="font-size:7.5px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--navy);margin-bottom:8px;">NewCo Data Intelligence &#8212; Sources</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Census ACS 5-Year API</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; VDOT Traffic Volume API</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Virginia DOE SOL Data</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; CMS Hospital Ratings</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Fairfax Co. Permit DB (41K+)</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Google Places API</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Fairfax Co. GIS / Zoning</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Fairfax Co. Crime Database</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; EIA Forms 861 + 176 (Utilities)</div>
            <div style="font-size:7.5px;color:var(--slate-light);">&#10003; Fairfax Water Authority</div>
            <div style="font-size:7.5px;color:var(--wo-blue);">&#8857; RentCast (mkt rents &middot; on activation)</div>
            <div style="font-size:7.5px;color:var(--wo-blue);">&#8857; Virginia RETR (CRE comps &middot; pending)</div>
          </div>
          <div style="margin-top:8px;padding-top:7px;border-top:1px solid var(--rule);display:flex;align-items:center;justify-content:space-between;">
            <div>
              <div style="font-size:7.5px;font-weight:600;color:var(--navy);">Market Intelligence by NewCo Platform</div>
              <div style="font-size:7px;color:var(--slate-light);">Government-source data &middot; Not available in competing OM tools</div>
            </div>
            <img src="{LOGO_B64}" style="height:22px;opacity:0.55;" alt="NewCo">
          </div>
        </div>

      </div>
    </div>
  </div>
  <div class="page-footer">
    <div class="pf-left">Market Overview</div>
    <div class="pf-center">Regent&#8217;s Park &middot; Fairfax, Virginia 22031</div>
    <div style="display:flex;align-items:center;gap:10px;"><div class="wo-mark"><img src="{LOGO_B64}" alt="WO"><span class="pf-right">West Oxford Advisors</span></div><span class="pf-right">Page 5</span></div>
  </div>
</div>
'''


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 6 — LOCATION ANALYSIS
# v3 Change 1: Fill all placeholders with spec data
# v3 Change 2: REMOVE "Tenant Utility Burden" panel entirely per spec
# ═══════════════════════════════════════════════════════════════════════════
def page6_location():
    return f'''
<!-- ═══════════════════════════════════
     PAGE 6 — LOCATION ANALYSIS
════════════════════════════════════ -->
<div class="page">
  <div style="position:absolute;top:0;left:0;right:0;height:4px;background:var(--wo-blue);"></div>
  <div style="padding:40px 36px 36px;">
    <div class="sec-label">Section Five &#9733; NewCo Exclusive</div>
    <div class="sec-title">Location Analysis</div>
    <div class="gold-rule"></div>

    <div style="display:flex;gap:20px;">
      <!-- LEFT COL -->
      <div style="flex:1.05;display:flex;flex-direction:column;gap:14px;">

        <!-- Map -->
        <div>
          <h4 style="margin-bottom:6px;">Location Context Map</h4>
          <div class="mapbox" style="height:195px;flex-direction:column;gap:8px;">
            <div class="mapbox-label">Property Location Map<br><span style="font-size:7px;opacity:0.7;">Schools &middot; Metro &middot; Police &middot; Fire &middot; Permits &middot; Radius rings</span></div>
          </div>
          <div style="font-size:7px;color:var(--slate-light);margin-top:4px;">
            &#x1F535; Regent&#8217;s Park &nbsp;|&nbsp; &#x1F3EB; Schools (name labeled) &nbsp;|&nbsp; &#x24C2; Metro (Silver Line) &nbsp;|&nbsp; &#x1F692; Fire station &nbsp;|&nbsp; &#x1F693; Police &nbsp;|&nbsp; &#8212; 1mi / 2mi radius
          </div>
        </div>

        <!-- Travel times -->
        <div>
          <h4 style="margin-bottom:7px;">Drive Times from Regent&#8217;s Park</h4>
          <div class="travel-grid">
            <div class="tc"><div><div class="tc-dest">Vienna Metro (Silver Line)</div><div class="tc-mi">1.3 miles</div></div><div class="tc-time">7 min</div></div>
            <div class="tc"><div><div class="tc-dest">Tysons Corner</div><div class="tc-mi">4.8 miles</div></div><div class="tc-time">12 min</div></div>
            <div class="tc"><div><div class="tc-dest">George Mason University</div><div class="tc-mi">0.9 miles</div></div><div class="tc-time">5 min</div></div>
            <div class="tc"><div><div class="tc-dest">Inova Fairfax Hospital</div><div class="tc-mi">3.3 miles</div></div><div class="tc-time">9 min</div></div>
            <div class="tc"><div><div class="tc-dest">Mosaic District</div><div class="tc-mi">3.1 miles</div></div><div class="tc-time">10 min</div></div>
            <div class="tc"><div><div class="tc-dest">Washington, D.C.</div><div class="tc-mi">14 miles</div></div><div class="tc-time">28 min</div></div>
          </div>
        </div>

        <!-- Traffic — v3: filled with spec data -->
        <div style="background:#f5f3ef;border:1px solid rgba(184,150,106,0.25);padding:10px 12px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:7px;">
            <h4 style="margin-bottom:0;">Traffic Volumes &#9733; (VDOT)</h4>
            <span class="score-badge badge-gold">Retail Visibility Data</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <div style="padding:7px 9px;background:white;border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:20px;font-weight:600;color:var(--navy);">42,000</div>
              <div style="font-size:7.5px;color:var(--slate-light);">Lee Hwy (Rt. 29)<br>Daily Vehicle Count</div>
            </div>
            <div style="padding:7px 9px;background:white;border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:20px;font-weight:600;color:var(--navy);">98,000</div>
              <div style="font-size:7.5px;color:var(--slate-light);">I-66 Access Corridor<br>Daily Vehicle Count</div>
            </div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);margin-top:6px;font-style:italic;">Source: VDOT Traffic Volume API &middot; Annual Daily Traffic (ADT)</div>
        </div>

        <!-- Crime section — v3: filled with spec data -->
        <div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:7px;">
            <h4 style="margin-bottom:0;">Crime Analysis &#9733;</h4>
            <div style="display:flex;align-items:center;gap:5px;"><div class="sl-dot sl-green"></div><span class="score-badge badge-green">71/100 Safety Score</span></div>
          </div>
          <div style="display:flex;gap:6px;margin-bottom:7px;">
            <div style="flex:1;padding:7px;background:var(--green-light);border:1px solid rgba(45,106,79,0.2);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--green);">71</div>
              <div style="font-size:7px;color:var(--green);">Safety Score</div>
            </div>
            <div style="flex:1;padding:7px;background:var(--red-light);border:1px solid rgba(155,28,28,0.2);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--red);">7</div>
              <div style="font-size:7px;color:var(--red);">Violent Incidents</div>
            </div>
            <div style="flex:1;padding:7px;background:var(--amber-light);border:1px solid rgba(180,83,9,0.2);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--amber);">14</div>
              <div style="font-size:7px;color:var(--amber);">Property Crimes</div>
            </div>
            <div style="flex:1;padding:7px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--slate);">71</div>
              <div style="font-size:7px;color:var(--slate-light);">Total Incidents</div>
            </div>
          </div>
          <table class="crime-table">
            <thead>
              <tr><th>Date</th><th>Type</th><th>Classification</th><th>Block Address</th><th>Distance</th></tr>
            </thead>
            <tbody>
              <tr><td>Jan 2026</td><td><span class="crime-type-violent">Assault</span></td><td>Violent</td><td>9300 Block Lee Hwy</td><td>0.4 mi</td></tr>
              <tr><td>Nov 2025</td><td><span class="crime-type-property">Vehicle Break-In</span></td><td>Property</td><td>9200 Block Clocktower</td><td>0.1 mi</td></tr>
              <tr><td>Sep 2025</td><td><span class="crime-type-property">Theft</span></td><td>Property</td><td>9400 Block Lee Hwy</td><td>0.5 mi</td></tr>
              <tr><td>Jul 2025</td><td><span class="crime-type-violent">Robbery</span></td><td>Violent</td><td>Nutley St Corridor</td><td>0.8 mi</td></tr>
              <tr><td>May 2025</td><td><span class="crime-type-property">Burglary</span></td><td>Property</td><td>Gallows Rd Area</td><td>1.1 mi</td></tr>
            </tbody>
          </table>
          <div style="font-size:7px;color:var(--slate-light);margin-top:4px;font-style:italic;">5 most notable incidents shown (violent + significant property crimes). Full incident log (71 events, 1-mi radius, trailing 12 months) available in Data Appendix. Block-level addresses used per privacy standards.</div>
        </div>

      </div>

      <!-- RIGHT COL -->
      <div style="flex:1;display:flex;flex-direction:column;gap:14px;">

        <!-- Schools — v3: filled with spec data -->
        <div>
          <h4 style="margin-bottom:7px;">School Performance &#9733; (Virginia SOL Data)</h4>
          <div style="display:flex;gap:6px;margin-bottom:6px;">
            <div class="school-card">
              <div class="sc-level">Elementary</div>
              <div class="sc-name">Mantua Elementary</div>
              <div class="sc-stats">
                <div><div class="sc-stat-label">SOL Pass</div><div class="sc-stat-val" style="color:var(--green);">84%</div></div>
                <div><div class="sc-stat-label">State Avg</div><div class="sc-stat-val" style="color:var(--slate);">74%</div></div>
                <div><div class="sc-stat-label">Rating</div><div class="sc-stat-val" style="color:var(--green);">+10%</div></div>
              </div>
            </div>
            <div class="school-card">
              <div class="sc-level">Middle School</div>
              <div class="sc-name">Frost Middle School</div>
              <div class="sc-stats">
                <div><div class="sc-stat-label">SOL Pass</div><div class="sc-stat-val" style="color:var(--green);">81%</div></div>
                <div><div class="sc-stat-label">State Avg</div><div class="sc-stat-val" style="color:var(--slate);">71%</div></div>
                <div><div class="sc-stat-label">Rating</div><div class="sc-stat-val" style="color:var(--green);">+10%</div></div>
              </div>
            </div>
            <div class="school-card">
              <div class="sc-level">High School</div>
              <div class="sc-name">Woodson High School</div>
              <div class="sc-stats">
                <div><div class="sc-stat-label">SOL Pass</div><div class="sc-stat-val" style="color:var(--green);">88%</div></div>
                <div><div class="sc-stat-label">State Avg</div><div class="sc-stat-val" style="color:var(--slate);">76%</div></div>
                <div><div class="sc-stat-label">Rating</div><div class="sc-stat-val" style="color:var(--green);">+12%</div></div>
              </div>
            </div>
          </div>
          <div style="font-size:7.5px;color:var(--slate-light);font-style:italic;">Multi-year SOL pass rate trends available in Data Appendix. School quality is the #1 stated retention driver for family renters in Fairfax County. Source: Virginia DOE.</div>
        </div>

        <!-- Healthcare -->
        <div>
          <h4 style="margin-bottom:7px;">Healthcare Access &#9733; (CMS Quality Data)</h4>
          <div style="background:var(--green-light);border:1px solid rgba(45,106,79,0.25);padding:9px 12px;margin-bottom:7px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
              <div>
                <div style="font-size:8px;font-weight:600;color:var(--green);margin-bottom:2px;">PRIMARY HOSPITAL &#8212; INOVA FAIRFAX MEDICAL CAMPUS</div>
                <div style="font-family:var(--serif);font-size:14px;font-weight:600;color:var(--navy);">Inova Fairfax Hospital &middot; 3.3 mi &middot; 9 min</div>
                <div style="font-size:8px;color:var(--slate);margin-top:3px;">CMS 5-Star Rating &middot; Leapfrog Safety Grade A &middot; Level I Trauma Center</div>
              </div>
              <div style="text-align:right;">
                <div style="font-family:var(--serif);font-size:22px;font-weight:700;color:var(--green);">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
                <div style="font-size:7px;color:var(--slate-light);">CMS 5-Star</div>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px;">
              <div style="background:white;padding:5px 7px;border-radius:2px;text-align:center;">
                <div style="font-size:9px;font-weight:600;color:var(--navy);">3,461</div>
                <div style="font-size:7px;color:var(--slate-light);">Births / Year</div>
              </div>
              <div style="background:white;padding:5px 7px;border-radius:2px;text-align:center;">
                <div style="font-size:9px;font-weight:600;color:var(--green);">23%</div>
                <div style="font-size:7px;color:var(--slate-light);">C-Section Rate &#10003;</div>
              </div>
              <div style="background:white;padding:5px 7px;border-radius:2px;text-align:center;">
                <div style="font-size:9px;font-weight:600;color:var(--navy);">26,000+</div>
                <div style="font-size:7px;color:var(--slate-light);">Inova Employees</div>
              </div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
            <div style="padding:6px 9px;background:var(--bg);border:1px solid var(--rule);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">URGENT CARE CENTERS</div>
              <div style="font-size:10px;font-weight:600;color:var(--navy);">4 within 3 miles</div>
            </div>
            <div style="padding:6px 9px;background:var(--bg);border:1px solid var(--rule);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">PHARMACIES</div>
              <div style="font-size:10px;font-weight:600;color:var(--navy);">3 within 1 mile</div>
            </div>
            <div style="padding:6px 9px;background:var(--bg);border:1px solid var(--rule);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">TOTAL RATED FACILITIES</div>
              <div style="font-size:10px;font-weight:600;color:var(--navy);">77 Fairfax County</div>
            </div>
            <div style="padding:6px 9px;background:var(--bg);border:1px solid var(--rule);">
              <div style="font-size:7px;color:var(--slate-light);margin-bottom:2px;">HEALTHCARE SCORE</div>
              <div style="font-size:10px;font-weight:600;color:var(--green);">88/100 Top Tier</div>
            </div>
          </div>
        </div>

        <!-- v3 Change 2: Tenant Utility Burden panel REMOVED per spec -->
        <!-- "Industry standard OMs do not include tenant-paid utility estimates. This is not OM information." -->

      </div>
    </div>
  </div>
  <div class="page-footer">
    <div class="pf-left">Location Analysis</div>
    <div class="pf-center">Regent&#8217;s Park &middot; Fairfax, Virginia 22031</div>
    <div style="display:flex;align-items:center;gap:10px;"><div class="wo-mark"><img src="{LOGO_B64}" alt="WO"><span class="pf-right">West Oxford Advisors</span></div><span class="pf-right">Page 6</span></div>
  </div>
</div>
'''


# ═══════════════════════════════════════════════════════════════════════════
# MAIN — Concatenate all pages and write HTML file
# ═══════════════════════════════════════════════════════════════════════════
def main():
    html = shared_styles()
    html += page1_cover()
    html += page2_exec_summary()
    html += page3_financial()
    html += page4_development()
    html += page5_market()
    html += page6_location()
    html += "\n</body>\n</html>\n"

    out_path = os.path.join(os.path.dirname(__file__), "investigation", "newco_om_v3_regents_park.html")
    with open(out_path, "w") as f:
        f.write(html)

    line_count = html.count("\n") + 1
    print(f"Generated: {out_path}")
    print(f"File size: {len(html):,} bytes")
    print(f"Line count: {line_count}")


if __name__ == "__main__":
    main()
