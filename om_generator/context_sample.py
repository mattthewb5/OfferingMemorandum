"""
Sample context dictionary for the OM Jinja2 template.
All values match the v3 prototype dummy data exactly.
This file serves as the wiring checklist &#8212; every variable here
must eventually be populated from real data sources.
"""


def get_sample_context():
    """Return the full context dict with v3 dummy values."""
    return {
        # ============================================================
        # GLOBAL / IDENTITY
        # ============================================================
        "property_name": "Regent&#8217;s Park",
        "property_address": "9333 Clocktower Place",
        "property_address_short": "9333 Clocktower Pl.",
        "property_city": "Fairfax",
        "property_state": "Virginia",
        "property_state_abbr": "VA",
        "property_zip": "22031",
        "property_county": "Fairfax County",
        "submarket_name": "Merrifield&#8211;Vienna",
        "transit_corridor": "Silver Line Corridor",
        "metro_station_name": "Vienna/Fairfax-GMU",
        "metro_badge_text": "Vienna Metro",
        "metro_distance": "1.3 mi",
        "hero_image_label": "[ Aerial / Drone Hero Image ]",
        "broker_name": "West Oxford Advisors",
        "report_date": "March 2026",

        # West Oxford logo (base64) &#8212; loaded at runtime by generate_om.py
        "wo_logo_base64": "",  # populated by generate_om.py

        # ============================================================
        # PROPERTY SPECS
        # ============================================================
        "total_units": "552",
        "stories": "4",
        "floor_plan_count": "22",
        "year_built": "1997",
        "management_company_short": "Bozzuto",
        "avg_unit_sf": "1,031",
        "total_rentable_sf": "569,112",
        "min_unit_sf": "628",
        "max_unit_sf": "1,434",
        "zoning_code": "PDH \u00b7 PRC",
        "zoning_code_slash": "PDH / PRC",
        "zoning_display": "PDH \u00b7 Planned Dev. Housing",
        "utility_structure_short": "Tenant: Elec+Gas | LL: Water",

        # Photo strip placeholders
        "photo_labels": ["Aerial View", "Clubhouse", "Pool Deck", "Unit Interior"],

        # ============================================================
        # PRICING / VALUATION
        # ============================================================
        "asking_price_display": "$232,000,000",
        "asking_price_full": "$232,000,000",
        "asking_price_short": "$232M",
        "price_per_unit_display": "$420,289",
        "t12_cap_rate": "5.02%",
        "proforma_cap_rate": "5.26%",
        "t12_noi_short": "$11.65M",
        "avg_monthly_rent": "$2,480",
        "opex_ratio": "25.4%",

        # ============================================================
        # PROPERTY OVERVIEW TEXT
        # ============================================================
        "property_overview_text": (
            "Regent\u2019s Park is a 552-unit, institutionally managed multifamily community "
            "positioned at the convergence of Fairfax County\u2019s most coveted location attributes: "
            "walking distance to Vienna Metro (Silver Line), one mile from George Mason University, "
            "and immediate access to the I-495/I-66 corridor. Built in 1997 and continuously managed "
            "by Bozzuto Management Company, the property comprises four residential buildings with 22 "
            "distinct floor plans ranging from 628 to 1,434 square feet across one, two, and "
            "three-bedroom configurations. In-place rents averaging 9.1% below current submarket "
            "rates present a systematic mark-to-market opportunity across the portfolio through a "
            "structured lease renewal program."
        ),

        # ============================================================
        # INVESTMENT THESIS
        # ============================================================
        "investment_thesis_text": (
            "Regent&#8217;s Park presents a rare combination of scale, transit access, and "
            "embedded rent upside in one of the most supply-constrained multifamily submarkets "
            "in the Mid-Atlantic region. As a 552-unit, institutionally operated community within "
            "walking distance of the Vienna Metro Station and one mile from George Mason University, "
            "the property draws from three durable demand cohorts: federal government employees, "
            "technology sector professionals, and graduate students \u2014 all insulated from "
            "cyclical employment volatility. With in-place rents tracking 9.1% below current "
            "RentCast submarket averages and zero new competitive multifamily supply planned within "
            "the 2-mile radius, the asset offers a clear, low-execution-risk path to value creation "
            "through systematic mark-to-market lease renewals."
        ),

        # ============================================================
        # VALUE-ADD / RENT GAP
        # ============================================================
        "embedded_value_display": "$19.6M",
        "portfolio_rent_gap_pct": "9.1%",
        "below_market_units": "331",
        "avg_gap_per_unit": "$247",
        "annual_noi_potential": "$980,964",
        "value_cap_rate": "5.0%",
        "portfolio_avg_market_rent": "$2,727",
        "portfolio_avg_gap": "$247",
        "university_name_short": "George Mason",
        "university_distance": "0.9 mi",

        # ============================================================
        # UNIT MIX (list of dicts)
        # ============================================================
        "unit_mix": [
            {
                "type": "1 BR / 1 BA",
                "count": "184",
                "pct": "33%",
                "avg_sf": "728",
                "in_place_rent": "$2,130",
                "market_rent": "$2,340",
                "gap_dollar": "$210",
                "gap_pct": "9.0%",
            },
            {
                "type": "2 BR / 2 BA",
                "count": "268",
                "pct": "49%",
                "avg_sf": "1,064",
                "in_place_rent": "$2,710",
                "market_rent": "$2,980",
                "gap_dollar": "$270",
                "gap_pct": "9.1%",
            },
            {
                "type": "3 BR / 2 BA",
                "count": "100",
                "pct": "18%",
                "avg_sf": "1,434",
                "in_place_rent": "$3,980",
                "market_rent": "$4,380",
                "gap_dollar": "$400",
                "gap_pct": "9.1%",
            },
        ],

        # ============================================================
        # INVESTMENT HIGHLIGHTS (raw HTML)
        # ============================================================
        "investment_highlights": [
            '<strong>Vienna Metro Access \u2014 Institutional Rent Premium:</strong> Vienna/Fairfax-GMU Metro station 1.3 miles from property. Silver Line access to Tysons Corner, Reston, Arlington, and Union Station. NoVA research consistently documents 10\u201320% rent premium for walkable Metro proximity, directly supporting above-market rent capture on unit turnover.',
            '<strong>George Mason University Demand Engine:</strong> GMU at 0.9 miles enrolls 39,000+ students with 7,500+ employees. Graduate student and faculty housing demand provides recession-resistant occupancy floor. University enrollment has grown consistently regardless of broader economic cycles.',
            '<strong>Supply-Constrained Location \u2014 Zero Competing Pipeline:</strong> Development Pressure Score of 18/100 (Low). PDH/PRC zoning with Comprehensive Plan designation unchanged. No new multifamily permits within 2-mile radius in trailing 24 months. Fairfax County\u2019s development review process makes competitive supply additions a 5\u20137 year horizon at minimum.',
            '<strong>Top-Tier School District \u2014 Family Tenant Retention:</strong> Served by Woodson High School (88% SOL), Frost Middle (81%), and Mantua Elementary (84%) \u2014 all consistently above Virginia SOL state averages. School quality is the #1 stated retention driver for family renters in Fairfax County surveys.',
            '<strong>Inova Fairfax Hospital \u2014 Healthcare Anchor (3.3 mi):</strong> One of the region\u2019s premier healthcare facilities drives consistent demand from medical professionals and health system employees. Inova Health System employment has grown +206% since 2009 (to 26,000+ employees), creating sustained multifamily demand within the care radius.',
            '<strong>Deep, Diversified Employment \u2014 Recession-Resistant Demand:</strong> 3-mile median household income of $159,400 (2.1\u00d7 national median). Federal government (28,126 county employees), FCPS, George Mason University, and the Tysons/Merrifield technology corridor provide multi-sector employment insulation unavailable in single-industry markets.',
        ],

        # ============================================================
        # STOPLIGHT SCORES
        # ============================================================
        "stoplight_scores": [
            {"label": "Location Quality", "badge_text": "Strong", "label_detail": "Strong", "bar_width": "78%", "bar_color": "", "dot_class": "sl-green", "badge_class": "badge-green"},
            {"label": "Crime Safety", "badge_text": "Safe", "label_detail": "Safe", "bar_width": "71%", "bar_color": "var(--green)", "dot_class": "sl-green", "badge_class": "badge-green"},
            {"label": "Convenience", "badge_text": "Excellent", "label_detail": "Excellent", "bar_width": "82%", "bar_color": "", "dot_class": "sl-green", "badge_class": "badge-green"},
            {"label": "Medical Access", "badge_text": "Top Tier", "label_detail": "Top Tier", "bar_width": "88%", "bar_color": "var(--green)", "dot_class": "sl-green", "badge_class": "badge-green"},
            {"label": "Development Pressure", "badge_text": "Low \u2713", "label_detail": "Low \u00b7 Supply Constrained", "bar_width": "18%", "bar_color": "var(--green)", "dot_class": "sl-green", "badge_class": "badge-green"},
            {"label": "Transit Score", "badge_text": "Good", "label_detail": "Good / Car Needed", "bar_width": "64%", "bar_color": "var(--amber)", "dot_class": "sl-amber", "badge_class": "badge-amber"},
        ],

        # ============================================================
        # T-12 ACTUAL P&L
        # ============================================================
        "t12": {
            "gpr": "$16,428,000",
            "vacancy_pct": "4.5%",
            "vacancy_loss": "$739,000",
            "credit_loss_pct": "0.5%",
            "credit_loss": "$82,000",
            "egi": "$15,607,000",
            "real_estate_taxes": "$1,385,000",
            "insurance": "$345,000",
            "repairs": "$580,000",
            "mgmt_pct": "5%",
            "management": "$780,000",
            "utilities": "$485,000",
            "admin": "$245,000",
            "reserves": "$138,000",
            "noi": "$11,649,000",
        },

        # ============================================================
        # PRO FORMA YR1
        # ============================================================
        "pf": {
            "gpr": "$16,940,000",
            "vacancy_pct": "5.0%",
            "vacancy_loss": "$847,000",
            "credit_loss_pct": "0.5%",
            "credit_loss": "$85,000",
            "egi": "$15,890,000",
            "real_estate_taxes": "$1,415,000",
            "insurance": "$355,000",
            "repairs": "$590,000",
            "mgmt_pct": "5%",
            "management": "$795,000",
            "utilities": "$495,000",
            "admin": "$250,000",
            "reserves": "$138,000",
            "noi": "$12,200,000",
        },

        "reserves_per_unit": "$250",
        "rent_growth_assumption": "3.5%",

        # ============================================================
        # UTILITY BENCHMARK
        # ============================================================
        "utility_per_unit": "$879",
        "utility_benchmark_low": "$820",
        "utility_benchmark_high": "$960",
        "utility_assessment": "Within Normal Range",

        # ============================================================
        # CASH FLOW PROJECTION
        # ============================================================
        "cashflow": {
            "yr1_egi": "$15.89M",
            "yr3_egi": "$16.51M",
            "yr5_egi": "$17.16M",
            "yr1_noi": "$12.20M",
            "yr3_noi": "$12.73M",
            "yr5_noi": "$13.29M",
            "yr1_debt_svc": "$5.99M",
            "yr3_debt_svc": "$5.99M",
            "yr5_debt_svc": "$5.99M",
            "yr1_cashflow": "$6.22M",
            "yr3_cashflow": "$6.75M",
            "yr5_cashflow": "$7.30M",
        },

        # ============================================================
        # FINANCING
        # ============================================================
        "financing": {
            "ltv": "65%",
            "interest_rate": "6.25%",
            "amortization": "30",
            "dscr": "1.38",
        },

        # ============================================================
        # COMPARABLE SALES
        # ============================================================
        "comps_submarket_display": "Vienna/Merrifield",
        "comps_methodology_text": (
            "Multifamily building sales comparables sourced from Virginia RETR deed transfer "
            "records via Fairfax County GIS parcel layer cross-reference. RETR integration in "
            "development \u2014 comps will auto-populate on platform activation. For "
            "institutional-quality comps in the interim, broker has sourced the following from "
            "Fairfax County land records and CREXi transaction database."
        ),
        "comps": [
            {"name": "Halstead Square, 2729 Merrilee Dr", "units": "438", "sale_price": "$178,500,000", "price_per_unit": "$407,534", "cap_rate": "5.1%", "sale_date": "Jun 2024", "source": "Virginia RETR"},
            {"name": "Avalon Mosaic, 2987 District Ave", "units": "317", "sale_price": "$134,200,000", "price_per_unit": "$423,344", "cap_rate": "4.9%", "sale_date": "Feb 2024", "source": "Virginia RETR"},
            {"name": "Prosperity Flats, 2700 Dorr Ave", "units": "186", "sale_price": "$74,800,000", "price_per_unit": "$402,151", "cap_rate": "5.3%", "sale_date": "Oct 2023", "source": "Virginia RETR"},
        ],

        # ============================================================
        # DEVELOPMENT INTELLIGENCE
        # ============================================================
        "dev_pressure_score": "18",
        "dev_pressure_label": "Low Development Pressure",
        "dev_pressure_narrative": (
            "Minimal competing development activity within the 2-mile radius. No new multifamily "
            "permits filed in the trailing 24 months. Existing PDH/PRC zoning and Fairfax "
            "County\u2019s lengthy entitlement process create a substantial barrier to competitive "
            "supply additions \u2014 protecting in-place NOI and supporting rent growth."
        ),
        "dev_formula_components": [
            {"name": "Permit Volume (# near property vs. county baseline)", "weight": "30%", "bar_width": "20%", "bar_color": "var(--green)", "score_label": "Low"},
            {"name": "Permit Recency (last 12 mo. vs. 24 mo. total)", "weight": "20%", "bar_width": "15%", "bar_color": "var(--green)", "score_label": "Low"},
            {"name": "Permit Type (residential/new vs. commercial alt.)", "weight": "20%", "bar_width": "25%", "bar_color": "var(--amber)", "score_label": "Low-Med"},
            {"name": "Proximity (distance from nearest permit activity)", "weight": "15%", "bar_width": "12%", "bar_color": "var(--green)", "score_label": "Low"},
            {"name": "Planning Zone (Comp Plan growth center distance)", "weight": "15%", "bar_width": "18%", "bar_color": "var(--green)", "score_label": "Low"},
        ],

        "total_county_permits": "41,504",
        "permits_2mi_count": "13",
        "new_mf_permits_count": "0",
        "commercial_permits_count": "9",
        "nearest_permit_distance": "1.8 mi",
        "permits_context_footnote": (
            "13 permits within 2-mile radius vs. Fairfax County permit database of 41,504 "
            "total permits for similarly-zoned parcels. Zero new multifamily permits filed "
            "within 2 miles in the trailing 24 months."
        ),
        "permit_activity_bars": [
            {"label": "New Residential", "width": "0%", "count": "0", "fill_class": "bar-primary"},
            {"label": "Commercial Alteration", "width": "69%", "count": "9", "fill_class": "bar-primary"},
            {"label": "Residential Renovation", "width": "31%", "count": "4", "fill_class": "bar-light"},
        ],
        "permit_chart_footnote": (
            "Commercial alteration permits indicate area economic activity without introducing "
            "residential competition. Total: 13 permits within 2-mi radius, 24-month period."
        ),

        # Zoning
        "comp_plan_designation": "Medium Res / Suburban",
        "growth_center_distance": "1.8 mi \u2014 Outside",
        "upzoning_risk": "Low \u2014 Stable Designation",
        "zoning_narrative": (
            "Fairfax County\u2019s PDH designation requires Planned Development approval for "
            "any density increases \u2014 a multi-year entitlement process that serves as an "
            "effective barrier to rapid competing development. The Comp Plan\u2019s suburban "
            "residential designation for this area has not changed in the most recent General "
            "Plan update cycle."
        ),

        # ============================================================
        # DEMOGRAPHICS
        # ============================================================
        "demo": {
            "median_income": "$159,400",
            "income_multiplier": "2.1",
            "population": "128,400",
            "population_growth": "+4.2% 5-yr growth",
            "bachelors_pct": "62%",
            "state_bachelors_pct": "41%",
            "median_age": "38 yrs",
            "income_distribution": [
                {"label": "$200,000+", "pct": "28%", "fill_class": "bar-primary"},
                {"label": "$150,000\u2013$200,000", "pct": "19%", "fill_class": "bar-primary"},
                {"label": "$100,000\u2013$150,000", "pct": "24%", "fill_class": "bar-primary"},
                {"label": "$75,000\u2013$100,000", "pct": "14%", "fill_class": "bar-light"},
                {"label": "&lt;$75,000", "pct": "15%", "fill_class": "bar-light"},
            ],
            "income_source_footnote": (
                "Source: U.S. Census ACS 5-Year Estimates. 71% of households earn $100K+, "
                "supporting premium multifamily rents."
            ),
        },

        # ============================================================
        # MARKET CONTEXT
        # ============================================================
        "market": {
            "avg_cap_rate": "5.1% T-12",
            "avg_price_per_unit": "$411K",
            "county_vacancy_rate": "4.5%",
            "rent_growth_12mo": "+3.8%",
            "narrative_text": (
                "Fairfax County\u2019s multifamily market benefits from federal government "
                "employment stability, technology sector growth anchored by the Amazon HQ2 "
                "spillover effect, and structural supply constraints from the county\u2019s "
                "development approval process. The Merrifield&#8211;Vienna submarket consistently "
                "outperforms the broader county averages due to Metro proximity and George Mason "
                "University demand."
            ),
            "source_attribution": (
                "Source: Serafin Real Estate NoVA Market Reports Q1 2023\u2013Q3 2025; "
                "Fairfax County DTA 2025 Assessments"
            ),
        },

        # ============================================================
        # EMPLOYERS
        # ============================================================
        "employers": [
            {"rank": "1", "name": "Fairfax County Gov\u2019t", "sector": "Public Administration", "employees": "28,126"},
            {"rank": "2", "name": "Fairfax County Public Schools", "sector": "Education", "employees": "25,000+"},
            {"rank": "3", "name": "Inova Health System", "sector": "Healthcare", "employees": "26,000+"},
            {"rank": "4", "name": "George Mason University", "sector": "Higher Education", "employees": "7,500+"},
            {"rank": "5", "name": "Booz Allen Hamilton", "sector": "Defense / Consulting", "employees": "~13,000"},
            {"rank": "6", "name": "Leidos Holdings", "sector": "Defense Technology", "employees": "~8,500"},
            {"rank": "7", "name": "DXC Technology", "sector": "IT Services", "employees": "~6,000"},
            {"rank": "8", "name": "Capital One Financial", "sector": "Financial Services", "employees": "~5,500"},
        ],
        "employer_footnote": (
            "\u2605 NewCo employer database covers 18 years of Fairfax County employment data. "
            "Recession-resistant government, healthcare, and defense employers account for "
            "majority of regional employment base."
        ),

        # ============================================================
        # AMENITIES
        # ============================================================
        "amenities": [
            {"count": "34", "label": "Restaurants"},
            {"count": "6", "label": "Grocery / Market"},
            {"count": "8", "label": "Fitness / Gym"},
            {"count": "5", "label": "Parks / Trails"},
            {"count": "11", "label": "Coffee Shops"},
            {"count": "22", "label": "Retail Shops"},
        ],

        # ============================================================
        # DATA SOURCES
        # ============================================================
        "data_sources": [
            {"icon": "\u2713", "name": "Census ACS 5-Year API", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "VDOT Traffic Volume API", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "Virginia DOE SOL Data", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "CMS Hospital Ratings", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "Fairfax Co. Permit DB (41K+)", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "Google Places API", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "Fairfax Co. GIS / Zoning", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "Fairfax Co. Crime Database", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "EIA Forms 861 + 176 (Utilities)", "color": "var(--slate-light)"},
            {"icon": "\u2713", "name": "Fairfax Water Authority", "color": "var(--slate-light)"},
            {"icon": "\u2299", "name": "RentCast (mkt rents \u00b7 on activation)", "color": "var(--wo-blue)"},
            {"icon": "\u2299", "name": "Virginia RETR (CRE comps \u00b7 pending)", "color": "var(--wo-blue)"},
        ],

        # ============================================================
        # DRIVE TIMES
        # ============================================================
        "drive_times": [
            {"destination": "Vienna Metro (Silver Line)", "distance": "1.3 miles", "time": "7 min"},
            {"destination": "Tysons Corner", "distance": "4.8 miles", "time": "12 min"},
            {"destination": "George Mason University", "distance": "0.9 miles", "time": "5 min"},
            {"destination": "Inova Fairfax Hospital", "distance": "3.3 miles", "time": "9 min"},
            {"destination": "Mosaic District", "distance": "3.1 miles", "time": "10 min"},
            {"destination": "Washington, D.C.", "distance": "14 miles", "time": "28 min"},
        ],

        # ============================================================
        # TRAFFIC
        # ============================================================
        "traffic": {
            "primary_road_name": "Lee Hwy (Rt. 29)",
            "primary_road_count": "42,000",
            "secondary_road_name": "I-66 Access Corridor",
            "secondary_road_count": "98,000",
        },

        # ============================================================
        # CRIME
        # ============================================================
        "crime": {
            "safety_score": "71",
            "violent_count": "7",
            "property_count": "14",
            "total_incidents": "71",
            "incidents": [
                {"date": "Jan 2026", "type": "Assault", "type_class": "violent", "classification": "Violent", "address": "9300 Block Lee Hwy", "distance": "0.4 mi"},
                {"date": "Nov 2025", "type": "Vehicle Break-In", "type_class": "property", "classification": "Property", "address": "9200 Block Clocktower", "distance": "0.1 mi"},
                {"date": "Sep 2025", "type": "Theft", "type_class": "property", "classification": "Property", "address": "9400 Block Lee Hwy", "distance": "0.5 mi"},
                {"date": "Jul 2025", "type": "Robbery", "type_class": "violent", "classification": "Violent", "address": "Nutley St Corridor", "distance": "0.8 mi"},
                {"date": "May 2025", "type": "Burglary", "type_class": "property", "classification": "Property", "address": "Gallows Rd Area", "distance": "1.1 mi"},
            ],
            "footnote": (
                "5 most notable incidents shown (violent + significant property crimes). Full "
                "incident log (71 events, 1-mi radius, trailing 12 months) available in Data "
                "Appendix. Block-level addresses used per privacy standards."
            ),
        },

        # ============================================================
        # SCHOOLS
        # ============================================================
        "schools": [
            {"level": "Elementary", "name": "Mantua Elementary", "sol_pass": "84%", "state_avg": "74%", "delta": "+10%"},
            {"level": "Middle School", "name": "Frost Middle School", "sol_pass": "81%", "state_avg": "71%", "delta": "+10%"},
            {"level": "High School", "name": "Woodson High School", "sol_pass": "88%", "state_avg": "76%", "delta": "+12%"},
        ],
        "school_footnote": (
            "Multi-year SOL pass rate trends available in Data Appendix. School quality is "
            "the #1 stated retention driver for family renters in Fairfax County. Source: Virginia DOE."
        ),

        # ============================================================
        # HEALTHCARE
        # ============================================================
        "healthcare": {
            "primary_label": "PRIMARY HOSPITAL \u2014 INOVA FAIRFAX MEDICAL CAMPUS",
            "name": "Inova Fairfax Hospital",
            "distance": "3.3 mi",
            "drive_time": "9 min",
            "certifications": "CMS 5-Star Rating \u00b7 Leapfrog Safety Grade A \u00b7 Level I Trauma Center",
            "births_per_year": "3,461",
            "csection_rate": "23%",
            "employee_count": "26,000+",
            "urgent_care_count": "4 within 3 miles",
            "pharmacy_count": "3 within 1 mile",
            "total_facilities": "77 Fairfax County",
            "score": "88/100 Top Tier",
        },

        # ============================================================
        # PAGE INFRASTRUCTURE
        # ============================================================
        "footer_section_names": [
            "",  # index 0 unused (cover has custom footer)
            "Executive Summary",
            "Financial Analysis",
            "Development Intelligence",
            "Market Overview",
            "Location Analysis",
        ],
        "page_numbers": [
            "",  # index 0 unused
            "2",
            "3",
            "4",
            "5",
            "6",
        ],
    }
