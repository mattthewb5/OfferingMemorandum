#!/usr/bin/env python3
"""
One-time script: convert raw HTML section extracts to Jinja2 templates.
Replaces all hardcoded data values with {{ variable }} references.
"""
import os
import re

SEC_DIR = os.path.join(os.path.dirname(__file__), 'templates', 'sections')


def read_section(name):
    with open(os.path.join(SEC_DIR, name), 'r') as f:
        return f.read()


def write_section(name, content):
    with open(os.path.join(SEC_DIR, name), 'w') as f:
        f.write(content)
    print(f"  {name}: {len(content)} chars")


# ============================================================
# COVER PAGE
# ============================================================
cover = read_section('cover.html')

# Property identity
cover = cover.replace("Regent&#8217;s Park", "{{ property_name }}", 1)  # main title
# Address line
cover = cover.replace(
    "9333 Clocktower Place &middot; Fairfax, Virginia 22031",
    "{{ property_address }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}"
)
# Submarket line
cover = cover.replace(
    "Fairfax County &middot; Merrifield&#8211;Vienna Submarket &middot; Silver Line Corridor",
    "{{ property_county }} &middot; {{ submarket_name }} Submarket &middot; {{ transit_corridor }}"
)
# Hero image placeholder
cover = cover.replace("[ Aerial / Drone Hero Image ]", "{{ hero_image_label }}")

# KPI strip
cover = cover.replace('>$232,000,000<', '>{{ asking_price_display }}<')
cover = cover.replace('>$420,289 / Unit<', '>{{ price_per_unit_display }} / Unit<')
cover = cover.replace('>552<', '>{{ total_units }}<', 1)
cover = cover.replace('>4 Stories &middot; 22 Floor Plans<', '>{{ stories }} Stories &middot; {{ floor_plan_count }} Floor Plans<')
cover = cover.replace('>5.02%<', '>{{ t12_cap_rate }}<', 1)
cover = cover.replace('>T-12 In-Place<', '>T-12 In-Place<')  # label, keep
cover = cover.replace('>$11.65M<', '>{{ t12_noi_short }}<', 1)
cover = cover.replace('>Trailing 12 Months<', '>Trailing 12 Months<')  # label, keep
cover = cover.replace('>1997<', '>{{ year_built }}<')
cover = cover.replace('>Bozzuto Managed<', '>{{ management_company_short }} Managed<')
cover = cover.replace('>$2,480<', '>{{ avg_monthly_rent }}<', 1)
cover = cover.replace('>628&#8211;1,434 SF Units<', '>{{ min_unit_sf }}&#8211;{{ max_unit_sf }} SF Units<')

# Property overview paragraph - replace the whole paragraph content
cover = re.sub(
    r'(<p>)Regent&#8217;s Park is a 552-unit.*?</p>',
    r'\1{{ property_overview_text }}</p>',
    cover, flags=re.DOTALL
)

# Badges in overview
cover = cover.replace('>Fairfax County<', '>{{ property_county }}<')
cover = cover.replace('>Vienna Metro &middot; 1.3 mi<', '>{{ metro_station_name }} &middot; {{ metro_distance }}<')
cover = cover.replace('>George Mason &middot; 0.9 mi<', '>{{ university_name_short }} &middot; {{ university_distance }}<')

# Property specs grid
cover = cover.replace('>552 Units<', '>{{ total_units }} Units<')
cover = cover.replace('>1,031 SF avg<', '>{{ avg_unit_sf }} SF avg<')
cover = cover.replace('>569,112 SF<', '>{{ total_rentable_sf }} SF<')
cover = cover.replace('>PDH &middot; PRC<', '>{{ zoning_code }}<')

# Photo strip labels
cover = cover.replace('>Aerial View<', '>{{ photo_labels[0] }}<')
cover = cover.replace('>Clubhouse<', '>{{ photo_labels[1] }}<')
cover = cover.replace('>Pool Deck<', '>{{ photo_labels[2] }}<')
cover = cover.replace('>Unit Interior<', '>{{ photo_labels[3] }}<')

# Footer
cover = cover.replace(
    "Regent&#8217;s Park &middot; 9333 Clocktower Place &middot; Fairfax, VA 22031",
    "{{ property_name }} &middot; {{ property_address }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}"
)
cover = cover.replace(">West Oxford Advisors<", ">{{ broker_name }}<")

write_section('cover.html', cover)


# ============================================================
# EXECUTIVE SUMMARY
# ============================================================
es = read_section('executive_summary.html')

# Investment thesis - replace paragraph
es = re.sub(
    r'(line-height:1\.7;color:var\(--navy\);">)Regent&#8217;s Park presents.*?</p>',
    r'\1{{ investment_thesis_text }}</p>',
    es, flags=re.DOTALL
)
es = es.replace('March 2026', '{{ report_date }}')

# Value-add box header
es = es.replace(
    '$19.6M Embedded Value &#8212; 9.1% Mark-to-Market Opportunity',
    '{{ embedded_value_display }} Embedded Value &#8212; {{ portfolio_rent_gap_pct }} Mark-to-Market Opportunity'
)

# Unit type rent gap cards
# 1BR
es = es.replace('1 BR / 1 BA (184 units)', '1 BR / 1 BA ({{ unit_mix[0].count }} units)')
es = es.replace('>$2,130<', '>{{ unit_mix[0].in_place_rent }}<', 1)
es = es.replace('>$2,340<', '>{{ unit_mix[0].market_rent }}<', 1)
es = es.replace('>Gap: $210 (9.0%)<', '>Gap: {{ unit_mix[0].gap_dollar }} ({{ unit_mix[0].gap_pct }})<', 1)
# 2BR
es = es.replace('2 BR / 2 BA (268 units)', '2 BR / 2 BA ({{ unit_mix[1].count }} units)')
es = es.replace('>$2,710<', '>{{ unit_mix[1].in_place_rent }}<', 1)
es = es.replace('>$2,980<', '>{{ unit_mix[1].market_rent }}<', 1)
es = es.replace('>Gap: $270 (9.1%)<', '>Gap: {{ unit_mix[1].gap_dollar }} ({{ unit_mix[1].gap_pct }})<', 1)
# 3BR
es = es.replace('3 BR / 2 BA (100 units)', '3 BR / 2 BA ({{ unit_mix[2].count }} units)')
es = es.replace('>$3,980<', '>{{ unit_mix[2].in_place_rent }}<', 1)
es = es.replace('>$4,380<', '>{{ unit_mix[2].market_rent }}<', 1)
es = es.replace('>Gap: $400 (9.1%)<', '>Gap: {{ unit_mix[2].gap_dollar }} ({{ unit_mix[2].gap_pct }})<', 1)

# Value-add footnote
es = es.replace(
    '~331 below-market units &times; $247/unit/month avg gap &times; 12 = $980,964/yr additional NOI. At 5.0% cap rate = $19.6M implied embedded value.',
    '~{{ below_market_units }} below-market units &times; {{ avg_gap_per_unit }}/unit/month avg gap &times; 12 = {{ annual_noi_potential }}/yr additional NOI. At {{ value_cap_rate }} cap rate = {{ embedded_value_display }} implied embedded value.'
)

# Investment highlight bullets - replace each one
highlight_pattern = r'(<div class="hl-bullet"><div class="hl-marker"></div><div class="hl-text">)(.*?)(</div></div>)'
highlights = list(re.finditer(highlight_pattern, es, re.DOTALL))
for idx, match in enumerate(reversed(highlights)):
    replacement = f'{match.group(1)}{{{{ investment_highlights[{len(highlights)-1-idx}] }}}}{match.group(3)}'
    es = es[:match.start()] + replacement + es[match.end():]

# KPI grid
es = es.replace('>$232M<', '>{{ asking_price_short }}<')
es = es.replace('>5.02%<', '>{{ t12_cap_rate }}<', 1)
es = es.replace('>5.26%<', '>{{ proforma_cap_rate }}<', 1)
es = es.replace('>$11.65M<', '>{{ t12_noi_short }}<', 1)
es = es.replace('>552<', '>{{ total_units }}<', 1)
es = es.replace('>$420,289<', '>{{ price_per_unit_display }}<', 1)

# Stoplight scores - replace bar widths and labels using loop-friendly approach
score_replacements = [
    ('Location Quality', 'location_quality', '78%', 'Strong', 'sl-green', 'badge-green'),
    ('Crime Safety', 'crime_safety', '71%', 'Safe', 'sl-green', 'badge-green'),
    ('Convenience', 'convenience', '82%', 'Excellent', 'sl-green', 'badge-green'),
    ('Medical Access', 'medical_access', '88%', 'Top Tier', 'sl-green', 'badge-green'),
    ('Development Pressure', 'dev_pressure', '18%', 'Low &#10003;', 'sl-green', 'badge-green'),
    ('Transit Score', 'transit_score', '64%', 'Good', 'sl-amber', 'badge-amber'),
]

# Replace score bars with Jinja for loop
scores_block = '''{% for score in stoplight_scores %}
            <div class="score-row">
              <div style="display:flex;align-items:center;gap:6px;"><div class="sl-dot {{ score.dot_class }}"></div><div class="score-label">{{ score.label }} &#8212; <strong>{{ score.badge_text }}</strong></div></div>
              <div class="score-right">
                <div class="score-bar-track"><div class="score-bar-fill bar-primary" style="width:{{ score.bar_width }};{% if score.bar_color %}background:{{ score.bar_color }};{% endif %}"></div></div>
                <span class="score-badge {{ score.badge_class }}">{{ score.badge_text }}</span>
              </div>
            </div>
{% endfor %}'''

# Find and replace the score rows block
score_start = es.find('<div class="score-row">')
score_end = es.find('</div>\n          </div>\n          <div style="font-size:7px;color:var(--slate-light);margin-top:5px')
if score_start > 0 and score_end > 0:
    es = es[:score_start] + scores_block + '\n          ' + es[score_end:]

# Property details
es = es.replace('>9333 Clocktower Pl.<', '>{{ property_address_short }}<')
es = es.replace('>Merrifield&#8211;Vienna<', '>{{ submarket_name }}<')
es = es.replace('>PDH &middot; Planned Dev. Housing<', '>{{ zoning_display }}<')
es = es.replace('>1997 / Bozzuto Mgmt<', '>{{ year_built }} / {{ management_company_short }} Mgmt<')
es = es.replace('>Tenant: Elec+Gas | LL: Water<', '>{{ utility_structure_short }}<')

# Footer
es = es.replace('>Executive Summary<', '>{{ footer_section_names[1] }}<')
es = es.replace("Regent&#8217;s Park &middot; Fairfax, Virginia 22031",
                "{{ property_name }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}")
es = es.replace('>Page 2<', '>Page {{ page_numbers[1] }}<')

write_section('executive_summary.html', es)


# ============================================================
# FINANCIALS
# ============================================================
fin = read_section('financials.html')

# Unit mix table rows - use Jinja for loop
unit_mix_rows = '''{% for unit in unit_mix %}
        <tr><td class="strong">{{ unit.type }}</td><td class="r">{{ unit.count }}</td><td class="r">{{ unit.pct }}</td><td class="r">{{ unit.avg_sf }}</td><td class="r">{{ unit.in_place_rent }}</td><td class="r" style="color:var(--green);">{{ unit.market_rent }}</td><td class="r" style="color:var(--wo-blue);">{{ unit.gap_dollar }} ({{ unit.gap_pct }})</td></tr>
{% endfor %}'''

# Replace the 3 unit rows
unit_start = fin.find('<tr><td class="strong">1 BR')
unit_end = fin.find('</tbody>', unit_start)
if unit_start > 0 and unit_end > 0:
    fin = fin[:unit_start] + unit_mix_rows + '\n      ' + fin[unit_end:]

# Portfolio footer row
fin = fin.replace(
    '<tr><td><strong>Portfolio</strong></td><td class="r"><strong>552</strong></td><td class="r"></td><td class="r"><strong>1,031 avg</strong></td><td class="r"><strong>$2,480 avg</strong></td><td class="r"><strong style="color:var(--green);">$2,727 avg</strong></td><td class="r"><strong style="color:var(--wo-blue);">$247 (9.1%)</strong></td></tr>',
    '<tr><td><strong>Portfolio</strong></td><td class="r"><strong>{{ total_units }}</strong></td><td class="r"></td><td class="r"><strong>{{ avg_unit_sf }} avg</strong></td><td class="r"><strong>{{ avg_monthly_rent }} avg</strong></td><td class="r"><strong style="color:var(--green);">{{ portfolio_avg_market_rent }} avg</strong></td><td class="r"><strong style="color:var(--wo-blue);">{{ portfolio_avg_gap }} ({{ portfolio_rent_gap_pct }})</strong></td></tr>'
)

# Rent roll footnote
fin = fin.replace('Full 552-unit', 'Full {{ total_units }}-unit')
fin = fin.replace('ZIP 22031', 'ZIP {{ property_zip }}')

# T-12 Actual P&L
fin = fin.replace('>$16,428,000<', '>{{ t12.gpr }}<')
fin = fin.replace('Vacancy Loss (4.5%)', 'Vacancy Loss ({{ t12.vacancy_pct }})')
fin = fin.replace('>($739,000)<', '>({{ t12.vacancy_loss }})<')
fin = fin.replace('Credit / Bad Debt (0.5%)', 'Credit / Bad Debt ({{ t12.credit_loss_pct }})')
fin = fin.replace('>($82,000)<', '>({{ t12.credit_loss }})<', 1)
fin = fin.replace('>$15,607,000<', '>{{ t12.egi }}<')
fin = fin.replace('>($1,385,000)<', '>({{ t12.real_estate_taxes }})<', 1)
fin = fin.replace('>($345,000)<', '>({{ t12.insurance }})<', 1)
fin = fin.replace('>($580,000)<', '>({{ t12.repairs }})<', 1)
fin = fin.replace('Property Management (5%)', 'Property Management ({{ t12.mgmt_pct }})')
fin = fin.replace('>($780,000)<', '>({{ t12.management }})<', 1)
fin = fin.replace('>($485,000)<', '>({{ t12.utilities }})<', 1)
fin = fin.replace('>($245,000)<', '>({{ t12.admin }})<', 1)
fin = fin.replace('Reserves ($250/unit)', 'Reserves ({{ reserves_per_unit }}/unit)')
fin = fin.replace('>($138,000)<', '>({{ t12.reserves }})<', 1)
fin = fin.replace('>$11,649,000<', '>{{ t12.noi }}<')

# Pro Forma P&L
fin = fin.replace('>$16,940,000<', '>{{ pf.gpr }}<')
fin = fin.replace('Vacancy Loss (5.0%)', 'Vacancy Loss ({{ pf.vacancy_pct }})')
fin = fin.replace('>($847,000)<', '>({{ pf.vacancy_loss }})<')
fin = fin.replace('>($85,000)<', '>({{ pf.credit_loss }})<')
fin = fin.replace('>$15,890,000<', '>{{ pf.egi }}<')
fin = fin.replace('>($1,415,000)<', '>({{ pf.real_estate_taxes }})<')
fin = fin.replace('>($355,000)<', '>({{ pf.insurance }})<')
fin = fin.replace('>($590,000)<', '>({{ pf.repairs }})<')
fin = fin.replace('>($795,000)<', '>({{ pf.management }})<')
fin = fin.replace('>($495,000)<', '>({{ pf.utilities }})<')
fin = fin.replace('>($250,000)<', '>({{ pf.admin }})<')
fin = fin.replace('>($138,000)<', '>({{ pf.reserves }})<')
fin = fin.replace('>$12,200,000<', '>{{ pf.noi }}<')

# Methodology footnote
fin = fin.replace('3.5% rent growth', '{{ rent_growth_assumption }} rent growth')

# Utility benchmark
fin = fin.replace('$485,000 / 552 units', '{{ t12.utilities }} / {{ total_units }} units')
fin = fin.replace('>$879/unit/yr<', '>{{ utility_per_unit }}/unit/yr<', 1)
fin = fin.replace('>$820/unit/yr<', '>{{ utility_benchmark_low }}/unit/yr<')
fin = fin.replace('>$960/unit/yr<', '>{{ utility_benchmark_high }}/unit/yr<')
fin = fin.replace(
    '$879 within $820&#8211;$960 range',
    '{{ utility_per_unit }} within {{ utility_benchmark_low }}&#8211;{{ utility_benchmark_high }} range'
)
fin = fin.replace('>Within Normal Range<', '>{{ utility_assessment }}<')
fin = fin.replace(
    'Utility expense ($485,000 T-12 Actual) reflects landlord-paid water, sewer, and common area electric only &#8212; approximately $879/unit/year.',
    'Utility expense ({{ t12.utilities }} T-12 Actual) reflects landlord-paid water, sewer, and common area electric only &#8212; approximately {{ utility_per_unit }}/unit/year.'
)

# Cash flow projection
fin = fin.replace('>$15.89M<', '>{{ cashflow.yr1_egi }}<')
fin = fin.replace('>$16.51M<', '>{{ cashflow.yr3_egi }}<')
fin = fin.replace('>$17.16M<', '>{{ cashflow.yr5_egi }}<')
fin = fin.replace('>$12.20M<', '>{{ cashflow.yr1_noi }}<')
fin = fin.replace('>$12.73M<', '>{{ cashflow.yr3_noi }}<')
fin = fin.replace('>$13.29M<', '>{{ cashflow.yr5_noi }}<')
fin = fin.replace('>($5.99M)<', '>({{ cashflow.yr1_debt_svc }})<')
# The other two debt svc are identical but we need them too
fin = fin.replace('>($5.99M)<', '>({{ cashflow.yr3_debt_svc }})<', 1)
fin = fin.replace('>($5.99M)<', '>({{ cashflow.yr5_debt_svc }})<', 1)
fin = fin.replace('>$6.22M<', '>{{ cashflow.yr1_cashflow }}<')
fin = fin.replace('>$6.75M<', '>{{ cashflow.yr3_cashflow }}<')
fin = fin.replace('>$7.30M<', '>{{ cashflow.yr5_cashflow }}<')

# Financing assumptions footnote
fin = fin.replace(
    'Assumes 65% LTV financing at 6.25% interest, 30-yr amortization. DSCR: 1.38&times;.',
    'Assumes {{ financing.ltv }} LTV financing at {{ financing.interest_rate }} interest, {{ financing.amortization }}-yr amortization. DSCR: {{ financing.dscr }}&times;.'
)

# Key Metrics sidebar
fin = fin.replace('>$232,000,000<', '>{{ asking_price_full }}<')
fin = fin.replace('>$420,289<', '>{{ price_per_unit_display }}<')
fin = fin.replace('>5.02%<', '>{{ t12_cap_rate }}<')
fin = fin.replace('>5.26%<', '>{{ proforma_cap_rate }}<')
fin = fin.replace('>25.4%<', '>{{ opex_ratio }}<')

# Comparable sales - use for loop
comps_rows = '''{% for comp in comps %}
          <tr><td class="strong">{{ comp.name }}</td><td class="r">{{ comp.units }}</td><td class="r">{{ comp.sale_price }}</td><td class="r">{{ comp.price_per_unit }}</td><td class="r">{{ comp.cap_rate }}</td><td>{{ comp.sale_date }}</td><td><span class="score-badge badge-navy">{{ comp.source }}</span></td></tr>
{% endfor %}'''

comp_start = fin.find('<tr><td class="strong">Halstead')
comp_end = fin.find('</tbody>', comp_start)
if comp_start > 0 and comp_end > 0:
    fin = fin[:comp_start] + comps_rows + '\n        ' + fin[comp_end:]

# Comps intro text
fin = fin.replace(
    'Vienna/Merrifield Submarket',
    '{{ submarket_name }} Submarket'
)
fin = re.sub(
    r'Multifamily building sales comparables sourced.*?CREXi transaction database\.',
    '{{ comps_methodology_text }}',
    fin, flags=re.DOTALL
)

# Footer
fin = fin.replace('>Financial Analysis<', '>{{ footer_section_names[2] }}<')
fin = fin.replace("Regent&#8217;s Park &middot; Fairfax, Virginia 22031",
                  "{{ property_name }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}")
fin = fin.replace('>Page 3<', '>Page {{ page_numbers[2] }}<')

write_section('financials.html', fin)


# ============================================================
# DEVELOPMENT INTELLIGENCE
# ============================================================
dev = read_section('development_intelligence.html')

# Dev pressure score
dev = dev.replace('<div class="pressure-num">18</div>', '<div class="pressure-num">{{ dev_pressure_score }}</div>')
dev = dev.replace('>out of 100<', '>out of 100<')  # keep label
dev = dev.replace('>Low Development Pressure<', '>{{ dev_pressure_label }}<')

# Dev pressure narrative
dev = re.sub(
    r'(line-height:1\.6;color:var\(--slate\);">)Minimal competing.*?rent growth\.',
    r'\1{{ dev_pressure_narrative }}',
    dev, flags=re.DOTALL
)

# Formula components - use for loop
formula_rows = '''{% for comp in dev_formula_components %}
          <div class="formula-row">
            <div class="formula-name">{{ comp.name }}</div>
            <div class="formula-weight">{{ comp.weight }}</div>
            <div class="formula-bar-track"><div class="formula-bar-fill" style="width:{{ comp.bar_width }};background:{{ comp.bar_color }};"></div></div>
            <div class="formula-score">{{ comp.score_label }}</div>
          </div>
{% endfor %}'''

formula_start = dev.find('<div class="formula-row">')
formula_end = dev.rfind('</div>\n          <div style="font-size:7.5px;color:var(--slate-light);margin-top:7px;font-style:italic;">Score:')
if formula_start > 0 and formula_end > 0:
    dev = dev[:formula_start] + formula_rows + '\n          ' + dev[formula_end:]

# County context
dev = dev.replace(
    'Fairfax County Context &#8212; 41,504 Total Permits in Database',
    '{{ property_county }} Context &#8212; {{ total_county_permits }} Total Permits in Database'
)
dev = dev.replace('>13<', '>{{ permits_2mi_count }}<', 1)
dev = dev.replace('>0<', '>{{ new_mf_permits_count }}<', 1)
dev = dev.replace('>9<', '>{{ commercial_permits_count }}<', 1)
dev = dev.replace('>1.8 mi<', '>{{ nearest_permit_distance }}<')

# County context footnote
dev = dev.replace(
    '13 permits within 2-mile radius vs. Fairfax County permit database of 41,504 total permits for similarly-zoned parcels. Zero new multifamily permits filed within 2 miles in the trailing 24 months.',
    '{{ permits_context_footnote }}'
)

# Permit activity chart - use for loop
permit_chart = '''{% for bar in permit_activity_bars %}
            <div class="bar-row">
              <div class="bar-rl">{{ bar.label }}</div>
              <div class="bar-track"><div class="bar-fill {{ bar.fill_class }}" style="width:{{ bar.width }};"></div></div>
              <div class="bar-pct">{{ bar.count }}</div>
            </div>
{% endfor %}'''

bar_start = dev.find('<div class="bar-row">')
bar_end = dev.rfind('</div>\n          </div>\n          <div style="font-size:7.5px;color:var(--slate-light);font-style:italic;margin-top:5px;">Commercial')
if bar_start > 0 and bar_end > 0:
    dev = dev[:bar_start] + permit_chart + '\n          ' + dev[bar_end:]

# Permit chart footnote
dev = dev.replace(
    'Commercial alteration permits indicate area economic activity without introducing residential competition. Total: 13 permits within 2-mi radius, 24-month period.',
    '{{ permit_chart_footnote }}'
)

# Zoning intel
dev = dev.replace('>PDH / PRC<', '>{{ zoning_code }}<')
dev = dev.replace('>Medium Res / Suburban<', '>{{ comp_plan_designation }}<')
dev = dev.replace('>1.8 mi &#8212; Outside<', '>{{ growth_center_distance }}<')
dev = dev.replace('>Low &#8212; Stable Designation<', '>{{ upzoning_risk }}<')

# Zoning narrative
dev = re.sub(
    r"Fairfax County&#8217;s PDH designation requires.*?update cycle\.",
    '{{ zoning_narrative }}',
    dev, flags=re.DOTALL
)

# Footer
dev = dev.replace('>Development Intelligence<', '>{{ footer_section_names[3] }}<')
dev = dev.replace("Regent&#8217;s Park &middot; Fairfax, Virginia 22031",
                  "{{ property_name }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}")
dev = dev.replace('>Page 4<', '>Page {{ page_numbers[3] }}<')

write_section('development_intelligence.html', dev)


# ============================================================
# MARKET OVERVIEW
# ============================================================
mkt = read_section('market_overview.html')

# Demographics
mkt = mkt.replace('>$159,400<', '>{{ demo.median_income }}<')
mkt = mkt.replace('>2.1&times; National Median<', '>{{ demo.income_multiplier }}&times; National Median<')
mkt = mkt.replace('>128,400<', '>{{ demo.population }}<')
mkt = mkt.replace('>+4.2% 5-yr growth<', '>{{ demo.population_growth }}<')
mkt = mkt.replace('>62%<', '>{{ demo.bachelors_pct }}<')
mkt = mkt.replace('>vs. 41% VA statewide<', '>vs. {{ demo.state_bachelors_pct }} VA statewide<')
mkt = mkt.replace('>38 yrs<', '>{{ demo.median_age }}<')

# Income distribution - use for loop
income_bars = '''{% for bar in demo.income_distribution %}
            <div class="bar-row"><div class="bar-rl">{{ bar.label }}</div><div class="bar-track"><div class="bar-fill {{ bar.fill_class }}" style="width:{{ bar.pct }};"></div></div><div class="bar-pct">{{ bar.pct }}</div></div>
{% endfor %}'''

inc_start = mkt.find('<div class="bar-row"><div class="bar-rl">$200,000')
inc_end = mkt.find('</div>\n          </div>\n          <div style="font-size:7.5px;color:var(--slate-light);margin-top:4px;font-style:italic;">Source: U.S. Census')
if inc_start > 0 and inc_end > 0:
    mkt = mkt[:inc_start] + income_bars + '\n          ' + mkt[inc_end:]

mkt = mkt.replace(
    'Source: U.S. Census ACS 5-Year Estimates. 71% of households earn $100K+, supporting premium multifamily rents.',
    '{{ demo.income_source_footnote }}'
)

# Market context
mkt = mkt.replace(
    'Fairfax County Multifamily Market Context',
    '{{ property_county }} Multifamily Market Context'
)
mkt = mkt.replace('>5.1% T-12<', '>{{ market.avg_cap_rate }}<')
mkt = mkt.replace('>$411K<', '>{{ market.avg_price_per_unit }}<')
mkt = mkt.replace('>4.5%<', '>{{ market.county_vacancy_rate }}<', 1)
mkt = mkt.replace('>+3.8%<', '>{{ market.rent_growth_12mo }}<')

# Market narrative
mkt = re.sub(
    r"Fairfax County&#8217;s multifamily market benefits.*?demand\.",
    '{{ market.narrative_text }}',
    mkt, flags=re.DOTALL
)
mkt = mkt.replace(
    'Source: Serafin Real Estate NoVA Market Reports Q1 2023&#8211;Q3 2025; Fairfax County DTA 2025 Assessments',
    '{{ market.source_attribution }}'
)

# Employers - use for loop
emp_rows = '''{% for emp in employers %}
            <div class="emp-row"><div class="emp-rank">{{ emp.rank }}</div><div class="emp-name">{{ emp.name }}</div><div class="emp-sector">{{ emp.sector }}</div><div class="emp-count">{{ emp.employees }}</div></div>
{% endfor %}'''

emp_start = mkt.find('<div class="emp-row"><div class="emp-rank">1</div>')
emp_end = mkt.find('</div>\n          </div>\n          <div style="font-size:7.5px;color:var(--slate-light);margin-top:4px;font-style:italic;">&#9733; NewCo')
if emp_start > 0 and emp_end > 0:
    mkt = mkt[:emp_start] + emp_rows + '\n          ' + mkt[emp_end:]

mkt = mkt.replace(
    '&#9733; NewCo employer database covers 18 years of Fairfax County employment data. Recession-resistant government, healthcare, and defense employers account for majority of regional employment base.',
    '{{ employer_footnote }}'
)

# Amenities - use for loop
amenity_items = '''{% for amenity in amenities %}
            <div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">
              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">{{ amenity.count }}</div>
              <div style="font-size:7.5px;color:var(--slate-light);">{{ amenity.label }}</div>
            </div>
{% endfor %}'''

am_start = mkt.find('<div style="padding:8px 10px;background:var(--bg);border:1px solid var(--rule);text-align:center;">\n              <div style="font-family:var(--serif);font-size:18px;font-weight:600;color:var(--navy);">34')
am_end = mkt.find('</div>\n          </div>\n        </div>\n\n        <!-- Data attribution')
if am_start > 0 and am_end > 0:
    mkt = mkt[:am_start] + amenity_items + '\n          ' + mkt[am_end:]

# Data sources - use for loop
source_items = '''{% for source in data_sources %}
            <div style="font-size:7.5px;color:{{ source.color }};">{{ source.icon }} {{ source.name }}</div>
{% endfor %}'''

src_start = mkt.find('<div style="font-size:7.5px;color:var(--slate-light);">&#10003; Census')
src_end = mkt.find('</div>\n          </div>\n          <div style="margin-top:8px;padding-top:7px;border-top:1px solid')
if src_start > 0 and src_end > 0:
    mkt = mkt[:src_start] + source_items + '\n          ' + mkt[src_end:]

# Footer
mkt = mkt.replace('>Market Overview<', '>{{ footer_section_names[4] }}<')
mkt = mkt.replace("Regent&#8217;s Park &middot; Fairfax, Virginia 22031",
                  "{{ property_name }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}")
mkt = mkt.replace('>Page 5<', '>Page {{ page_numbers[4] }}<')

write_section('market_overview.html', mkt)


# ============================================================
# LOCATION ANALYSIS
# ============================================================
loc = read_section('location_analysis.html')

# Map legend
loc = loc.replace(
    '&#x1F535; Regent&#8217;s Park',
    '&#x1F535; {{ property_name }}'
)

# Drive times - use for loop
drive_rows = '''{% for dt in drive_times %}
            <div class="tc"><div><div class="tc-dest">{{ dt.destination }}</div><div class="tc-mi">{{ dt.distance }}</div></div><div class="tc-time">{{ dt.time }}</div></div>
{% endfor %}'''

dt_start = loc.find('<div class="tc"><div><div class="tc-dest">Vienna Metro')
dt_end = loc.find('</div>\n          </div>\n        </div>\n\n        <!-- Traffic')
if dt_start > 0 and dt_end > 0:
    loc = loc[:dt_start] + drive_rows + '\n          ' + loc[dt_end:]

# Drive times header
loc = loc.replace("Drive Times from Regent&#8217;s Park", "Drive Times from {{ property_name }}")

# Traffic volumes
loc = loc.replace('>42,000<', '>{{ traffic.primary_road_count }}<')
loc = loc.replace(
    'Lee Hwy (Rt. 29)<br>Daily Vehicle Count',
    '{{ traffic.primary_road_name }}<br>Daily Vehicle Count'
)
loc = loc.replace('>98,000<', '>{{ traffic.secondary_road_count }}<')
loc = loc.replace(
    'I-66 Access Corridor<br>Daily Vehicle Count',
    '{{ traffic.secondary_road_name }}<br>Daily Vehicle Count'
)

# Crime
loc = loc.replace('>71/100 Safety Score<', '>{{ crime.safety_score }}/100 Safety Score<')
loc = loc.replace(
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--green);">71</div>\n              <div style="font-size:7px;color:var(--green);">Safety Score</div>',
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--green);">{{ crime.safety_score }}</div>\n              <div style="font-size:7px;color:var(--green);">Safety Score</div>'
)
loc = loc.replace(
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--red);">7</div>\n              <div style="font-size:7px;color:var(--red);">Violent Incidents</div>',
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--red);">{{ crime.violent_count }}</div>\n              <div style="font-size:7px;color:var(--red);">Violent Incidents</div>'
)
loc = loc.replace(
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--amber);">14</div>\n              <div style="font-size:7px;color:var(--amber);">Property Crimes</div>',
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--amber);">{{ crime.property_count }}</div>\n              <div style="font-size:7px;color:var(--amber);">Property Crimes</div>'
)
loc = loc.replace(
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--slate);">71</div>\n              <div style="font-size:7px;color:var(--slate-light);">Total Incidents</div>',
    '<div style="font-family:var(--serif);font-size:18px;font-weight:700;color:var(--slate);">{{ crime.total_incidents }}</div>\n              <div style="font-size:7px;color:var(--slate-light);">Total Incidents</div>'
)

# Crime incident table - use for loop
crime_rows = '''{% for inc in crime.incidents %}
              <tr><td>{{ inc.date }}</td><td><span class="crime-type-{{ inc.type_class }}">{{ inc.type }}</span></td><td>{{ inc.classification }}</td><td>{{ inc.address }}</td><td>{{ inc.distance }}</td></tr>
{% endfor %}'''

crime_start = loc.find('<tr><td>Jan 2026')
crime_end = loc.find('</tbody>\n          </table>')
if crime_start > 0 and crime_end > 0:
    loc = loc[:crime_start] + crime_rows + '\n            ' + loc[crime_end:]

# Crime footnote
loc = loc.replace(
    '5 most notable incidents shown (violent + significant property crimes). Full incident log (71 events, 1-mi radius, trailing 12 months) available in Data Appendix. Block-level addresses used per privacy standards.',
    '{{ crime.footnote }}'
)

# Schools - use for loop
school_cards = '''{% for school in schools %}
            <div class="school-card">
              <div class="sc-level">{{ school.level }}</div>
              <div class="sc-name">{{ school.name }}</div>
              <div class="sc-stats">
                <div><div class="sc-stat-label">SOL Pass</div><div class="sc-stat-val" style="color:var(--green);">{{ school.sol_pass }}</div></div>
                <div><div class="sc-stat-label">State Avg</div><div class="sc-stat-val" style="color:var(--slate);">{{ school.state_avg }}</div></div>
                <div><div class="sc-stat-label">Rating</div><div class="sc-stat-val" style="color:var(--green);">{{ school.delta }}</div></div>
              </div>
            </div>
{% endfor %}'''

sch_start = loc.find('<div class="school-card">')
sch_end = loc.find('</div>\n          </div>\n          <div style="font-size:7.5px;color:var(--slate-light);font-style:italic;">Multi-year SOL')
if sch_start > 0 and sch_end > 0:
    loc = loc[:sch_start] + school_cards + '\n          ' + loc[sch_end:]

# School footnote
loc = loc.replace(
    'Multi-year SOL pass rate trends available in Data Appendix. School quality is the #1 stated retention driver for family renters in Fairfax County. Source: Virginia DOE.',
    '{{ school_footnote }}'
)

# Healthcare
loc = loc.replace(
    'PRIMARY HOSPITAL &#8212; INOVA FAIRFAX MEDICAL CAMPUS',
    '{{ healthcare.primary_label }}'
)
loc = loc.replace(
    'Inova Fairfax Hospital &middot; 3.3 mi &middot; 9 min',
    '{{ healthcare.name }} &middot; {{ healthcare.distance }} &middot; {{ healthcare.drive_time }}'
)
loc = loc.replace(
    'CMS 5-Star Rating &middot; Leapfrog Safety Grade A &middot; Level I Trauma Center',
    '{{ healthcare.certifications }}'
)
loc = loc.replace('>3,461<', '>{{ healthcare.births_per_year }}<')
loc = loc.replace('>23%<', '>{{ healthcare.csection_rate }}<')
loc = loc.replace('>26,000+<', '>{{ healthcare.employee_count }}<')
loc = loc.replace('>4 within 3 miles<', '>{{ healthcare.urgent_care_count }}<')
loc = loc.replace('>3 within 1 mile<', '>{{ healthcare.pharmacy_count }}<')
loc = loc.replace('>77 Fairfax County<', '>{{ healthcare.total_facilities }}<')
loc = loc.replace('>88/100 Top Tier<', '>{{ healthcare.score }}<')

# Footer
loc = loc.replace('>Location Analysis<', '>{{ footer_section_names[5] }}<')
loc = loc.replace("Regent&#8217;s Park &middot; Fairfax, Virginia 22031",
                  "{{ property_name }} &middot; {{ property_city }}, {{ property_state }} {{ property_zip }}")
loc = loc.replace('>Page 6<', '>Page {{ page_numbers[5] }}<')

write_section('location_analysis.html', loc)


# Also handle metro station reference in exec summary property details
# This was in the truncated line 444 — let me fix it separately
es = read_section('executive_summary.html')
es = es.replace('Vienna/Fairfax-GMU', '{{ metro_station_name }}')
write_section('executive_summary.html', es)

print("\nAll sections templatized successfully!")
