"""
Loudoun County Crime Analysis Module

Provides safety scoring, crime density analysis, and trend detection
based on geocoded crime incident data from Loudoun County Sheriff's Office.

Mirrors the structure of fairfax_crime_analysis.py with Loudoun-specific
data sources, column mappings, and percentile-based scoring thresholds.

Usage:
    from core.loudoun_crime_analysis import LoudounCrimeAnalysis

    analyzer = LoudounCrimeAnalysis()
    safety = analyzer.calculate_safety_score(lat=39.0437, lon=-77.4875)
    print(f"Safety Score: {safety['score']}/100 ({safety['rating']})")
"""

import json
import math
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "loudoun" / "crime"
CRIME_DATA_PATH = DATA_DIR / "processed" / "incidents (3).parquet"
COUNTY_AVERAGES_PATH = DATA_DIR / "county_averages.json"


class LoudounCrimeAnalysis:
    """
    Loudoun County crime data analysis for property assessment.

    Provides safety scoring, crime density analysis, YoY trend indicators,
    and percentile ranking based on geocoded crime incident data.
    """

    def __init__(
        self,
        data_path: Optional[Path] = None,
        averages_path: Optional[Path] = None,
    ):
        self.data_path = data_path or CRIME_DATA_PATH
        self.averages_path = averages_path or COUNTY_AVERAGES_PATH
        self.county_averages = self._load_county_averages()
        self.incidents = self._load_data()

    def _load_county_averages(self) -> dict:
        """Load county-wide averages and thresholds from JSON."""
        with open(self.averages_path, "r") as f:
            return json.load(f)

    def _load_data(self) -> pd.DataFrame:
        """Load crime incidents from parquet, filter to geocoded only."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Crime data not found at {self.data_path}")

        df = pd.read_parquet(self.data_path)

        # Filter to incidents with coordinates
        df = df.dropna(subset=["latitude", "longitude"]).copy()

        # Parse string dates to datetime (Clarification 2)
        df["occurred_datetime"] = pd.to_datetime(df["occurred_datetime"])
        df["date"] = pd.to_datetime(df["date"])

        # Normalize category to lowercase (Clarification 3)
        if "category" in df.columns:
            df["category"] = df["category"].str.lower()

        return df

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance in miles."""
        R = 3959  # Earth's radius in miles
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def get_crimes_near_point(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        months_back: Optional[int] = None,
        category_filter: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get crimes within radius of a point.

        Returns DataFrame with distance_miles column, sorted by distance.
        """
        df = self.incidents.copy()

        df["distance_miles"] = df.apply(
            lambda row: self._haversine_distance(lat, lon, row["latitude"], row["longitude"]),
            axis=1,
        )

        df = df[df["distance_miles"] <= radius_miles]

        if months_back is not None:
            cutoff_date = datetime.now() - timedelta(days=months_back * 30)
            df = df[df["date"] >= cutoff_date]

        if category_filter is not None:
            df = df[df["category"] == category_filter.lower()]

        return df.sort_values("distance_miles")

    def calculate_safety_score(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        months_back: int = 6,
    ) -> Dict:
        """
        Calculate a safety score (0-100) for a location using Loudoun
        percentile thresholds from county_averages.json.

        Scoring (Clarification 1 — score_10 * 10):
          count < p25 → 8-10 on 1-10 scale → 80-100
          p25 <= count < p50 → 5-7 → 50-70
          p50 <= count < p75 → 3-4 → 30-40
          count >= p75 → 1-2 → 10-20

        Returns dict matching FairfaxCrimeAnalysis shape.
        """
        nearby = self.get_crimes_near_point(lat, lon, radius_miles, months_back)

        if nearby.empty:
            return {
                "score": 100,
                "rating": "Very Safe",
                "total_crimes": 0,
                "breakdown": {"violent": 0, "property": 0, "other": 0},
                "radius_miles": radius_miles,
                "months_back": months_back,
            }

        breakdown = nearby["category"].value_counts().to_dict()
        violent_count = breakdown.get("violent", 0)
        property_count = breakdown.get("property", 0)
        other_count = breakdown.get("other", 0)

        # Weighted crime count (violent 3x, property 1x, other excluded)
        weighted_crimes = violent_count * 3 + property_count

        # Percentile-based scoring using Loudoun thresholds
        thresholds = self.county_averages["safety_score_thresholds"]
        p25 = thresholds["p25"]
        p50 = thresholds["p50"]
        p75 = thresholds["p75"]

        if weighted_crimes < p25:
            # 8-10 band: linearly map [0, p25) → [100, 80]
            ratio = weighted_crimes / p25 if p25 > 0 else 0
            score_10 = 10 - ratio * 2  # 10 down to 8
        elif weighted_crimes < p50:
            # 5-7 band: linearly map [p25, p50) → [70, 50]
            ratio = (weighted_crimes - p25) / (p50 - p25) if (p50 - p25) > 0 else 0
            score_10 = 7 - ratio * 2  # 7 down to 5
        elif weighted_crimes < p75:
            # 3-4 band: linearly map [p50, p75) → [40, 30]
            ratio = (weighted_crimes - p50) / (p75 - p50) if (p75 - p50) > 0 else 0
            score_10 = 4 - ratio * 1  # 4 down to 3
        else:
            # 1-2 band: map [p75, inf) → [20, 10]
            p90 = thresholds["p90"]
            if p90 > p75:
                ratio = min(1.0, (weighted_crimes - p75) / (p90 - p75))
            else:
                ratio = 1.0
            score_10 = 2 - ratio * 1  # 2 down to 1

        # Clarification 1: simple multiplication to 0-100 scale
        score = max(0, min(100, int(score_10 * 10)))

        if score >= 80:
            rating = "Very Safe"
        elif score >= 60:
            rating = "Safe"
        elif score >= 40:
            rating = "Moderate"
        elif score >= 20:
            rating = "Caution Advised"
        else:
            rating = "High Crime Area"

        return {
            "score": score,
            "rating": rating,
            "total_crimes": len(nearby),
            "breakdown": {
                "violent": violent_count,
                "property": property_count,
                "other": other_count,
            },
            "radius_miles": radius_miles,
            "months_back": months_back,
        }

    def calculate_yoy_trend(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
    ) -> Dict:
        """
        Calculate year-over-year crime trend for a location.

        Uses local 1-mile radius data if both years have >= 30 incidents,
        otherwise falls back to county-wide YoY from county_averages.json.

        Returns dict with yoy_trend_pct, yoy_trend_direction, yoy_trend_source.
        """
        now = datetime.now()
        current_year = now.year
        prior_year = current_year - 1

        # Get all incidents within radius (no time filter)
        nearby = self.get_crimes_near_point(lat, lon, radius_miles, months_back=None)

        current_year_count = len(nearby[nearby["date"].dt.year == current_year])
        prior_year_count = len(nearby[nearby["date"].dt.year == prior_year])

        # Fallback rule: if either year has fewer than 30 incidents, use county-wide
        if current_year_count >= 30 and prior_year_count >= 30:
            yoy_pct = ((current_year_count - prior_year_count) / prior_year_count) * 100
            source = "local"
        else:
            # Use the most recent complete YoY from county_averages.json
            yoy_data = self.county_averages["yoy_trend"]
            yoy_pct = yoy_data["2024_to_2025_pct"]
            source = "county"

        # Direction classification (flat = within ±2%)
        if yoy_pct <= -2:
            direction = "down"
        elif yoy_pct >= 2:
            direction = "up"
        else:
            direction = "flat"

        return {
            "yoy_trend_pct": str(round(yoy_pct, 1)),
            "yoy_trend_direction": direction,
            "yoy_trend_source": source,
        }

    def calculate_percentile_rank(
        self,
        incident_count: int,
    ) -> int:
        """
        Calculate percentile rank (1-100) for an incident count using
        the p25/p50/p75/p90 distribution from county_averages.json.

        Uses linear interpolation between known percentile anchors.
        """
        dist = self.county_averages["radius_1mi_6mo"]
        p25 = dist["p25"]
        p50 = dist["p50"]
        p75 = dist["p75"]
        p90 = dist["p90"]

        if incident_count <= 0:
            return 1
        elif incident_count <= p25:
            # 1st to 25th percentile
            rank = 1 + (incident_count / p25) * 24
        elif incident_count <= p50:
            # 25th to 50th
            rank = 25 + ((incident_count - p25) / (p50 - p25)) * 25
        elif incident_count <= p75:
            # 50th to 75th
            rank = 50 + ((incident_count - p50) / (p75 - p50)) * 25
        elif incident_count <= p90:
            # 75th to 90th
            rank = 75 + ((incident_count - p75) / (p90 - p75)) * 15
        else:
            # Above 90th
            rank = 90 + min(10, ((incident_count - p90) / p90) * 10)

        return max(1, min(100, int(round(rank))))

    def build_trend_narrative(self) -> str:
        """
        Build a one-sentence trend narrative from county_averages.json YoY values.
        """
        yoy = self.county_averages["yoy_trend"]
        pct_2024 = abs(yoy["2023_to_2024_pct"])
        pct_2025 = abs(yoy["2024_to_2025_pct"])

        direction_2024 = "declined" if yoy["2023_to_2024_pct"] < 0 else "increased"
        direction_2025 = "and" if (yoy["2023_to_2024_pct"] < 0) == (yoy["2024_to_2025_pct"] < 0) else "but"

        if yoy["2023_to_2024_pct"] < 0 and yoy["2024_to_2025_pct"] < 0:
            return (
                f"Loudoun County crime {direction_2024} {pct_2024}% in 2024 "
                f"{direction_2025} {pct_2025}% in 2025, with property crime "
                f"leading the reduction."
            )
        else:
            return (
                f"Loudoun County crime changed {yoy['2023_to_2024_pct']}% in 2024 "
                f"and {yoy['2024_to_2025_pct']}% in 2025."
            )
