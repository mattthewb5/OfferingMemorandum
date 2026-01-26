"""
Fairfax County Building Permits Analysis Module

Provides development pressure scoring, construction activity analysis, and
permit trend detection based on Fairfax County's Building Records PLUS API data.

Usage:
    from core.fairfax_permits_analysis import FairfaxPermitsAnalysis

    analyzer = FairfaxPermitsAnalysis()
    pressure = analyzer.calculate_development_pressure(lat=38.8462, lon=-77.3064)
    print(f"Development Pressure: {pressure['score']}/100 ({pressure['trend']})")
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

# Data path
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "building_permits" / "processed"
PERMITS_DATA_PATH = DATA_DIR / "permits.parquet"


class FairfaxPermitsAnalysis:
    """
    Fairfax County building permits analysis for property assessment.

    Provides development pressure scoring, construction activity tracking,
    and permit trend analysis.
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize with permits data.

        Args:
            data_path: Optional path to permits parquet file
        """
        self.data_path = data_path or PERMITS_DATA_PATH
        self.permits = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Load building permits from parquet, filter to geocoded only."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Permits data not found at {self.data_path}")

        df = pd.read_parquet(self.data_path)

        # Filter to permits with coordinates
        df_geo = df.dropna(subset=['centroid_lat', 'centroid_lon']).copy()

        # Ensure datetime columns
        date_cols = ['submitted_date', 'accepted_date', 'issued_date', 'closed_date']
        for col in date_cols:
            if col in df_geo.columns:
                df_geo[col] = pd.to_datetime(df_geo[col])

        return df_geo

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance in miles.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in miles
        """
        R = 3959  # Earth's radius in miles

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def get_permits_near_point(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        months_back: Optional[int] = None,
        category_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get permits within radius of a point.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_miles: Search radius in miles (default: 1.0)
            months_back: Only include permits from last N months (None = all)
            category_filter: Filter by category ('residential_new', 'commercial_new', etc.)

        Returns:
            DataFrame of nearby permits with distance_miles column, sorted by distance
        """
        df = self.permits.copy()

        # Calculate distances
        df['distance_miles'] = df.apply(
            lambda row: self._haversine_distance(lat, lon, row['centroid_lat'], row['centroid_lon']),
            axis=1
        )

        # Filter by radius
        df = df[df['distance_miles'] <= radius_miles]

        # Filter by date if specified (use issued_date, fallback to submitted_date)
        if months_back is not None:
            cutoff_date = datetime.now() - timedelta(days=months_back * 30)
            df = df[
                (df['issued_date'] >= cutoff_date) |
                ((df['issued_date'].isna()) & (df['submitted_date'] >= cutoff_date))
            ]

        # Filter by category if specified
        if category_filter is not None:
            df = df[df['permit_category'] == category_filter]

        return df.sort_values('distance_miles')

    def calculate_development_pressure(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        months_back: int = 24
    ) -> Dict:
        """
        Calculate a development pressure score (0-100) for a location.

        Higher scores = more construction activity/development pressure.

        Scoring algorithm:
        - Residential new construction: +10 points each
        - Commercial new construction: +15 points each
        - Residential renovation: +3 points each
        - Commercial renovation: +5 points each
        - Residential demolition: +8 points each (often precedes new construction)
        - Commercial demolition: +10 points each
        - Other permits: +1 point each
        - Normalized to 0-100 scale (50 weighted points = score of 50)

        Trend classification:
        - Increasing: second_half > first_half * 1.2
        - Decreasing: second_half < first_half * 0.8
        - Stable: otherwise

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 1.0 miles)
            months_back: Time period to analyze (default: 24 months)

        Returns:
            Dict with keys:
                - score: int (0-100)
                - trend: str ('increasing', 'stable', 'decreasing', 'insufficient_data')
                - total_permits: int
                - breakdown: dict (counts by detailed category)
                - radius_miles: float
                - months_back: int
        """
        nearby = self.get_permits_near_point(lat, lon, radius_miles, months_back)

        if nearby.empty:
            return {
                'score': 0,
                'trend': 'insufficient_data',
                'total_permits': 0,
                'breakdown': {},
                'radius_miles': radius_miles,
                'months_back': months_back
            }

        # Weight by permit category
        weights = {
            'residential_new': 10,
            'commercial_new': 15,
            'residential_renovation': 3,
            'commercial_renovation': 5,
            'residential_demolition': 8,
            'commercial_demolition': 10,
            'certificate': 2,
            'elevator': 1,
            'other': 1
        }

        # Calculate weighted score
        weighted_sum = 0
        breakdown = {}

        category_counts = nearby['permit_category'].value_counts().to_dict()

        for category, count in category_counts.items():
            weight = weights.get(category, 1)
            weighted_sum += count * weight
            breakdown[category] = {
                'count': count,
                'weight': weight,
                'contribution': count * weight
            }

        # Normalize to 0-100 scale (calibrated so 50 weighted points = score of 50)
        score = min(100, int(weighted_sum * 1.0))

        # Calculate trend
        if len(nearby) < 5:
            trend = 'insufficient_data'
        else:
            cutoff_date = datetime.now() - timedelta(days=months_back * 30)
            mid_date = cutoff_date + timedelta(days=months_back * 15)

            first_half = nearby[
                (nearby['issued_date'] < mid_date) |
                ((nearby['issued_date'].isna()) & (nearby['submitted_date'] < mid_date))
            ]
            second_half = nearby[
                (nearby['issued_date'] >= mid_date) |
                ((nearby['issued_date'].isna()) & (nearby['submitted_date'] >= mid_date))
            ]

            first_count = len(first_half)
            second_count = len(second_half)

            if first_count == 0 and second_count == 0:
                trend = 'insufficient_data'
            elif first_count == 0:
                trend = 'increasing'
            elif second_count == 0:
                trend = 'decreasing'
            elif second_count > first_count * 1.2:
                trend = 'increasing'
            elif second_count < first_count * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'

        return {
            'score': score,
            'trend': trend,
            'total_permits': len(nearby),
            'breakdown': breakdown,
            'radius_miles': radius_miles,
            'months_back': months_back
        }

    def get_permit_trends(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        months_back: int = 24
    ) -> Dict:
        """
        Get permit trends by year and category.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 1.0 miles)
            months_back: Time period to analyze (default: 24 months)

        Returns:
            Dict with:
                - yearly: dict of year -> count
                - by_category: dict of year -> category breakdown
                - by_major_category: dict of year -> major category breakdown
        """
        nearby = self.get_permits_near_point(lat, lon, radius_miles, months_back)

        if nearby.empty:
            return {
                'yearly': {},
                'by_category': {},
                'by_major_category': {}
            }

        # Add year column (use issued_date, fallback to submitted_date)
        nearby = nearby.copy()
        nearby['year'] = nearby['issued_date'].dt.year
        nearby.loc[nearby['year'].isna(), 'year'] = nearby.loc[nearby['year'].isna(), 'submitted_date'].dt.year

        # Yearly counts
        yearly = nearby.groupby('year').size().to_dict()
        yearly = {int(k): v for k, v in yearly.items() if pd.notna(k)}

        # By detailed category per year
        by_category = {}
        for year in yearly.keys():
            year_data = nearby[nearby['year'] == year]
            by_category[year] = year_data['permit_category'].value_counts().to_dict()

        # By major category per year
        by_major_category = {}
        for year in yearly.keys():
            year_data = nearby[nearby['year'] == year]
            by_major_category[year] = year_data['permit_major_category'].value_counts().to_dict()

        return {
            'yearly': yearly,
            'by_category': by_category,
            'by_major_category': by_major_category
        }

    def get_permit_breakdown(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        months_back: int = 24
    ) -> Dict:
        """
        Get detailed permit breakdown by type.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 1.0 miles)
            months_back: Time period to analyze (default: 24 months)

        Returns:
            Dict with:
                - total: int
                - by_major_category: dict (residential, commercial, other)
                - by_detailed_category: dict (top 10 detailed categories)
        """
        nearby = self.get_permits_near_point(lat, lon, radius_miles, months_back)

        total = len(nearby)

        if total == 0:
            return {
                'total': 0,
                'by_major_category': {},
                'by_detailed_category': {}
            }

        # By major category
        major_counts = nearby['permit_major_category'].value_counts().to_dict()
        by_major = {}
        for cat, count in major_counts.items():
            by_major[cat] = {
                'count': count,
                'percentage': round((count / total) * 100, 1)
            }

        # By detailed category (top 10)
        detailed_counts = nearby['permit_category'].value_counts().head(10).to_dict()
        by_detailed = {}
        for cat, count in detailed_counts.items():
            by_detailed[cat] = {
                'count': count,
                'percentage': round((count / total) * 100, 1)
            }

        return {
            'total': total,
            'by_major_category': by_major,
            'by_detailed_category': by_detailed
        }


def example_usage():
    """Example usage of FairfaxPermitsAnalysis."""

    print("=" * 70)
    print("FAIRFAX BUILDING PERMITS ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxPermitsAnalysis()
    print(f"\nLoaded {len(analyzer.permits):,} geocoded building permits")

    # Example location (Fairfax County coordinates)
    test_lat = 38.8462
    test_lon = -77.3064

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")
    print(f"Radius: 1.0 miles")

    # Development pressure
    print("\n--- Development Pressure Score ---")
    pressure = analyzer.calculate_development_pressure(test_lat, test_lon, radius_miles=1.0, months_back=24)
    print(f"Score: {pressure['score']}/100")
    print(f"Trend: {pressure['trend']}")
    print(f"Total permits (24 months): {pressure['total_permits']}")
    if pressure['breakdown']:
        print("Top categories:")
        sorted_breakdown = sorted(pressure['breakdown'].items(), key=lambda x: -x[1]['contribution'])
        for cat, info in sorted_breakdown[:5]:
            print(f"  {cat}: {info['count']} permits (weight: {info['weight']}, contrib: {info['contribution']})")

    # Trends
    print("\n--- Permit Trends ---")
    trends = analyzer.get_permit_trends(test_lat, test_lon, radius_miles=1.0, months_back=24)
    print("Yearly counts:")
    for year, count in sorted(trends['yearly'].items()):
        print(f"  {year}: {count} permits")

    # Breakdown
    print("\n--- Permit Breakdown (24 months) ---")
    breakdown = analyzer.get_permit_breakdown(test_lat, test_lon, radius_miles=1.0, months_back=24)
    print(f"Total: {breakdown['total']}")
    print("By major category:")
    for cat, info in breakdown['by_major_category'].items():
        print(f"  {cat}: {info['count']} ({info['percentage']}%)")

    # Recent nearby permits
    print("\n--- Recent Permits (First 5) ---")
    nearby = analyzer.get_permits_near_point(test_lat, test_lon, radius_miles=1.0, months_back=6)
    if len(nearby) > 0:
        for idx, row in nearby.head(5).iterrows():
            date_str = row['issued_date'].strftime('%Y-%m-%d') if pd.notna(row['issued_date']) else 'N/A'
            permit_type = row['permit_type'][:35] if pd.notna(row['permit_type']) else 'N/A'
            address = row['address'][:50] if pd.notna(row['address']) else 'N/A'
            print(f"  {permit_type:35} | {date_str} | {row['distance_miles']:.2f} mi")
            print(f"    Address: {address}")
    else:
        print("  No permits found in last 6 months within 1.0 miles")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
