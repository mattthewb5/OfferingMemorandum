"""
Loudoun County School Zone Analysis for OM Generator

Point-in-polygon zone lookup → school name resolution → SOL score retrieval.
Returns the same dict shape as the Fairfax path so schools_context.py can
dispatch transparently.
"""

import json
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "loudoun"

_PERF_CSV = _DATA_DIR / "school_performance_trends_with_state_avg.csv"


def _load_performance_data() -> pd.DataFrame:
    """Load VDOE performance CSV with whitespace-stripped school names."""
    df = pd.read_csv(_PERF_CSV)
    if "School_Name" in df.columns:
        df["School_Name"] = df["School_Name"].str.strip()
    return df


def _normalize_school_name(name) -> str:
    """Strip suffixes/initials for fuzzy comparison (mirrors loudoun_school_performance.py)."""
    if pd.isna(name) or name is None:
        return ""
    name = str(name).upper().strip().replace(".", "").replace(",", "")
    for suffix in [
        " ELEMENTARY SCHOOL", " MIDDLE SCHOOL", " HIGH SCHOOL",
        " ELEMENTARY", " MIDDLE", " HIGH", " ES", " MS", " HS",
    ]:
        if name.endswith(suffix):
            name = name[: -len(suffix)].strip()
            break
    # Remove single-letter words (middle initials)
    words = [w for w in name.split() if len(w) > 1]
    return " ".join(words)


def _match_school_in_performance_data(
    school_name: str, perf_df: pd.DataFrame, division_name: str = "Loudoun County"
) -> str | None:
    """Priority match: literal exact → normalized exact → normalized partial."""
    loudoun = perf_df[perf_df["Division_Name"] == division_name]["School_Name"].unique()
    target_lower = school_name.strip().lower()
    for pn in loudoun:
        if pn.strip().lower() == target_lower:
            return pn
    norm_target = _normalize_school_name(school_name)
    for pn in loudoun:
        norm_pn = _normalize_school_name(pn)
        if norm_target == norm_pn:
            return pn
        if norm_target in norm_pn or norm_pn in norm_target:
            return pn
    return None

# Zone GeoJSON property keys per level
_ZONE_CONFIG = {
    "elementary": {
        "file": "schools/elementary_zones.geojson",
        "code_col": "ES_SCH_CODE",
        "label": "Elementary",
        "school_type": "Elem",
    },
    "middle": {
        "file": "schools/middle_zones.geojson",
        "code_col": "MS_SCH_CODE",
        "label": "Middle School",
        "school_type": "Middle",
    },
    "high": {
        "file": "schools/high_zones.geojson",
        "code_col": "HS_SCH_CODE",
        "label": "High School",
        "school_type": "High",
    },
}

# Suffix expansion for GIS name → performance CSV name
_SUFFIX_MAP = {
    " ES": " Elementary",
    " MS": " Middle",
    " HS": " High",
}


class LoudounSchoolsAnalysis:
    """Loudoun school zone lookup and SOL score retrieval."""

    def __init__(self):
        self._zones = {}       # level → GeoDataFrame
        self._code_to_name = None  # SCH_CODE → GIS name from school_sites
        self._code_to_coords = None  # SCH_CODE → {"lat": float, "lon": float}
        self._perf_df = None

    # ── lazy loaders ───────────────────────────────────────────────

    def _load_zone(self, level: str) -> gpd.GeoDataFrame:
        if level not in self._zones:
            cfg = _ZONE_CONFIG[level]
            path = _DATA_DIR / cfg["file"]
            gdf = gpd.read_file(path)
            if gdf.crs is None or gdf.crs.to_epsg() != 4326:
                gdf = gdf.set_crs(epsg=4326, allow_override=True)
            self._zones[level] = gdf
        return self._zones[level]

    def _load_code_map(self) -> dict:
        if self._code_to_name is None:
            path = _DATA_DIR / "schools" / "school_sites.geojson"
            with open(path) as f:
                gj = json.load(f)
            self._code_to_name = {
                feat["properties"]["SCH_CODE"]: feat["properties"]["NAME"]
                for feat in gj["features"]
            }
            self._code_to_coords = {
                feat["properties"]["SCH_CODE"]: {
                    "lat": feat["geometry"]["coordinates"][1],
                    "lon": feat["geometry"]["coordinates"][0],
                }
                for feat in gj["features"]
                if feat.get("geometry") and feat["geometry"].get("coordinates")
            }
        return self._code_to_name

    def _load_perf(self) -> pd.DataFrame:
        if self._perf_df is None:
            self._perf_df = _load_performance_data()
        return self._perf_df

    # ── point-in-polygon ───────────────────────────────────────────

    def _zone_lookup(self, lat: float, lon: float, level: str) -> str | None:
        """Return the 3-letter school code for the zone containing (lat, lon)."""
        gdf = self._load_zone(level)
        cfg = _ZONE_CONFIG[level]
        pt = Point(lon, lat)
        hits = gdf[gdf.geometry.contains(pt)]
        if hits.empty:
            return None
        return hits.iloc[0][cfg["code_col"]]

    # ── name resolution ────────────────────────────────────────────

    def _gis_name_to_perf_name(self, gis_name: str) -> str:
        """Convert GIS abbreviation ('ALDIE ES') to performance CSV name ('Aldie Elementary').

        Strategy:
        1. Check for known suffix and expand it.
        2. Title-case the result.
        3. Fall back to _match_school_in_performance_data (handles edge cases
           like 'ACADEMIES OF LOUDOUN' via normalized / partial matching).
        """
        upper = gis_name.strip().upper()

        # Try suffix expansion first
        for abbrev, full in _SUFFIX_MAP.items():
            if upper.endswith(abbrev):
                base = upper[: -len(abbrev)].strip()
                return base.title() + full

        # No standard suffix — title-case the whole thing
        return upper.title()

    # ── public API ─────────────────────────────────────────────────

    def get_schools(self, lat: float, lon: float) -> dict:
        """
        Look up assigned schools and their SOL scores for a Loudoun property.

        Returns the dict shape expected by schools_context.py / the OM template:
        {
            "schools": [ {level, name, sol_pass, state_avg, delta}, ... ],
            "school_footnote": str,
        }
        """
        code_map = self._load_code_map()
        perf_df = self._load_perf()

        # State averages (School_ID 999999)
        state_rows = perf_df[perf_df["School_ID"] == 999999]

        schools = []
        years_used = set()

        for level, cfg in _ZONE_CONFIG.items():
            code = self._zone_lookup(lat, lon, level)
            if code is None:
                continue

            # Code → GIS name
            gis_name = code_map.get(code)
            if gis_name is None:
                continue

            # GIS name → performance CSV name
            candidate = self._gis_name_to_perf_name(gis_name)
            perf_name = _match_school_in_performance_data(candidate, perf_df)

            # If suffix-expansion didn't work, try the raw GIS name
            if perf_name is None:
                perf_name = _match_school_in_performance_data(gis_name, perf_df)

            # ── SOL score for this school ──────────────────────────
            sol_pass_str = "N/A"
            year = None
            if perf_name is not None:
                school_rows = perf_df[
                    (perf_df["School_Name"] == perf_name)
                    & (perf_df["Division_Name"] == "Loudoun County")
                ].sort_values("Year", ascending=False)

                if not school_rows.empty:
                    top = school_rows.iloc[0]
                    if pd.notna(top["Overall_Pass_Rate"]):
                        sol_pass_str = f"{round(top['Overall_Pass_Rate'])}%"
                        year = top["Year"]
                        years_used.add(year)

            # ── state average for this school type ─────────────────
            state_avg_str = "N/A"
            delta_str = "N/A"

            st_type = cfg["school_type"]
            st_rows = state_rows[state_rows["School_Type"] == st_type].sort_values(
                "Year", ascending=False
            )
            if not st_rows.empty:
                # Prefer same year; fall back to most recent
                if year is not None:
                    exact = st_rows[st_rows["Year"] == year]
                    st_row = exact.iloc[0] if not exact.empty else st_rows.iloc[0]
                else:
                    st_row = st_rows.iloc[0]

                if pd.notna(st_row["Overall_Pass_Rate"]):
                    state_avg_rounded = round(st_row["Overall_Pass_Rate"])
                    state_avg_str = f"{state_avg_rounded}%"

                    if sol_pass_str != "N/A":
                        sol_val = int(sol_pass_str.replace("%", ""))
                        delta = sol_val - state_avg_rounded
                        delta_str = f"+{delta}%" if delta >= 0 else f"{delta}%"

            display_name = perf_name if perf_name else gis_name.title()

            coords = (self._code_to_coords or {}).get(code, {})
            schools.append(
                {
                    "level": cfg["label"],
                    "name": display_name,
                    "sol_pass": sol_pass_str,
                    "state_avg": state_avg_str,
                    "delta": delta_str,
                    "lat": coords.get("lat"),
                    "lon": coords.get("lon"),
                }
            )

        # Footnote
        year_display = ", ".join(sorted(years_used)) if years_used else "N/A"
        school_footnote = (
            f"Multi-year SOL pass rate trends available in Data Appendix. "
            f"School quality is the #1 stated retention driver for family renters "
            f"in Loudoun County. Source: Virginia DOE ({year_display})."
        )

        return {
            "schools": schools,
            "school_footnote": school_footnote,
        }
