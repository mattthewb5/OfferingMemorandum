"""
Fairfax County Crime Analysis Module

Provides safety scoring, crime density analysis, and trend detection
based on geocoded crime incident data from Fairfax County's public API.

Usage:
    from core.fairfax_crime_analysis import FairfaxCrimeAnalysis

    analyzer = FairfaxCrimeAnalysis()
    safety = analyzer.calculate_safety_score(lat=38.8462, lon=-77.3064)
    print(f"Safety Score: {safety['score']}/100 ({safety['rating']})")
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

# Data path
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "crime" / "processed"
CRIME_DATA_PATH = DATA_DIR / "incidents.parquet"


class FairfaxCrimeAnalysis:
    """
    Fairfax County crime data analysis for property assessment.

    Provides safety scoring, crime density analysis, and trend detection
    based on geocoded crime incident data.
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize with crime data.

        Args:
            data_path: Optional path to incidents parquet file
        """
        self.data_path = data_path or CRIME_DATA_PATH
        self.incidents = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Load crime incidents from parquet, filter to geocoded only."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Crime data not found at {self.data_path}")

        df = pd.read_parquet(self.data_path)

        # Filter to incidents with coordinates
        df_geo = df.dropna(subset=['latitude', 'longitude']).copy()

        # Ensure datetime columns
        if 'date' in df_geo.columns:
            df_geo['date'] = pd.to_datetime(df_geo['date'])

        # Normalize category values to lowercase for consistency
        if 'category' in df_geo.columns:
            df_geo['category'] = df_geo['category'].str.lower()

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

    def get_crimes_near_point(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5,
        months_back: Optional[int] = None,
        category_filter: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get crimes within radius of a point.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_miles: Search radius in miles (default: 0.5)
            months_back: Only include crimes from last N months (None = all)
            category_filter: Filter by category ('violent', 'property', 'other')

        Returns:
            DataFrame of nearby crimes with distance_miles column, sorted by distance
        """
        df = self.incidents.copy()

        # Calculate distances
        df['distance_miles'] = df.apply(
            lambda row: self._haversine_distance(lat, lon, row['latitude'], row['longitude']),
            axis=1
        )

        # Filter by radius
        df = df[df['distance_miles'] <= radius_miles]

        # Filter by date if specified
        if months_back is not None:
            cutoff_date = datetime.now() - timedelta(days=months_back * 30)
            df = df[df['date'] >= cutoff_date]

        # Filter by category if specified
        if category_filter is not None:
            df = df[df['category'] == category_filter.lower()]

        return df.sort_values('distance_miles')

    def calculate_safety_score(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5,
        months_back: int = 6
    ) -> Dict:
        """
        Calculate a safety score (0-100) for a location.

        Higher scores = safer areas.

        Scoring algorithm:
        - Start at 100
        - Violent crime: -5 points each
        - Property crime: -2 points each
        - Other incidents: -0.5 points each
        - Floor at 0, ceiling at 100

        Rating scale:
        - 85-100: Very Safe
        - 70-84: Safe
        - 50-69: Moderate
        - 30-49: Caution Advised
        - 0-29: High Crime Area

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.5 miles)
            months_back: Time period to analyze (default: 6 months)

        Returns:
            Dict with keys:
                - score: int (0-100)
                - rating: str
                - total_crimes: int
                - breakdown: dict (counts by category)
                - radius_miles: float
                - months_back: int
        """
        # Get nearby crimes in time window
        nearby = self.get_crimes_near_point(lat, lon, radius_miles, months_back)

        if nearby.empty:
            return {
                'score': 100,
                'rating': 'Very Safe',
                'total_crimes': 0,
                'breakdown': {'violent': 0, 'property': 0, 'other': 0},
                'radius_miles': radius_miles,
                'months_back': months_back
            }

        # Count by category
        breakdown = nearby['category'].value_counts().to_dict()
        violent_count = breakdown.get('violent', 0)
        property_count = breakdown.get('property', 0)
        other_count = breakdown.get('other', 0)

        # Calculate weighted score
        score = 100
        score -= violent_count * 5
        score -= property_count * 2
        score -= other_count * 0.5

        # Clamp to 0-100 range
        score = max(0, min(100, int(score)))

        # Assign rating
        if score >= 85:
            rating = 'Very Safe'
        elif score >= 70:
            rating = 'Safe'
        elif score >= 50:
            rating = 'Moderate'
        elif score >= 30:
            rating = 'Caution Advised'
        else:
            rating = 'High Crime Area'

        return {
            'score': score,
            'rating': rating,
            'total_crimes': len(nearby),
            'breakdown': {
                'violent': violent_count,
                'property': property_count,
                'other': other_count
            },
            'radius_miles': radius_miles,
            'months_back': months_back
        }

    def get_crime_trends(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5,
        months_back: int = 12
    ) -> Dict:
        """
        Analyze crime trends over time.

        Compares first half vs second half of time period to determine
        if crime is increasing, stable, or decreasing.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.5 miles)
            months_back: Total time period to analyze (default: 12 months)

        Returns:
            Dict with keys:
                - trend: str ('increasing', 'stable', 'decreasing', 'insufficient_data')
                - first_half_count: int
                - second_half_count: int
                - change_pct: float (percentage change)
                - total_crimes: int
        """
        nearby = self.get_crimes_near_point(lat, lon, radius_miles, months_back)

        if len(nearby) < 5:  # Need minimum data for trends
            return {
                'trend': 'insufficient_data',
                'first_half_count': len(nearby),
                'second_half_count': 0,
                'change_pct': 0.0,
                'total_crimes': len(nearby)
            }

        # Split into first half and second half
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        mid_date = cutoff_date + timedelta(days=months_back * 15)

        first_half = nearby[nearby['date'] < mid_date]
        second_half = nearby[nearby['date'] >= mid_date]

        first_count = len(first_half)
        second_count = len(second_half)

        # Calculate percentage change
        if first_count == 0:
            change_pct = 100.0 if second_count > 0 else 0.0
            trend = 'increasing' if second_count > 0 else 'stable'
        else:
            change_pct = ((second_count - first_count) / first_count) * 100

            # Classify trend (>20% = significant change)
            if change_pct > 20:
                trend = 'increasing'
            elif change_pct < -20:
                trend = 'decreasing'
            else:
                trend = 'stable'

        return {
            'trend': trend,
            'first_half_count': first_count,
            'second_half_count': second_count,
            'change_pct': round(change_pct, 1),
            'total_crimes': len(nearby)
        }

    def get_crime_breakdown(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5,
        months_back: int = 6
    ) -> Dict:
        """
        Get detailed crime breakdown by category.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.5 miles)
            months_back: Time period to analyze (default: 6 months)

        Returns:
            Dict with counts and percentages by category:
                - total: int
                - violent: dict (count, percentage)
                - property: dict (count, percentage)
                - other: dict (count, percentage)
        """
        nearby = self.get_crimes_near_point(lat, lon, radius_miles, months_back)

        total = len(nearby)

        if total == 0:
            return {
                'total': 0,
                'violent': {'count': 0, 'percentage': 0.0},
                'property': {'count': 0, 'percentage': 0.0},
                'other': {'count': 0, 'percentage': 0.0}
            }

        # Count by category
        breakdown = nearby['category'].value_counts().to_dict()
        violent = breakdown.get('violent', 0)
        property_crime = breakdown.get('property', 0)
        other = breakdown.get('other', 0)

        return {
            'total': total,
            'violent': {
                'count': violent,
                'percentage': round((violent / total) * 100, 1)
            },
            'property': {
                'count': property_crime,
                'percentage': round((property_crime / total) * 100, 1)
            },
            'other': {
                'count': other,
                'percentage': round((other / total) * 100, 1)
            }
        }


def example_usage():
    """Example usage of FairfaxCrimeAnalysis."""

    print("=" * 70)
    print("FAIRFAX CRIME ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxCrimeAnalysis()
    print(f"\nLoaded {len(analyzer.incidents):,} geocoded crime incidents")

    # Example location (Fairfax County coordinates)
    test_lat = 38.8462
    test_lon = -77.3064

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")
    print(f"Radius: 0.5 miles")

    # Safety score
    print("\n--- Safety Score ---")
    safety = analyzer.calculate_safety_score(test_lat, test_lon, radius_miles=0.5, months_back=6)
    print(f"Score: {safety['score']}/100")
    print(f"Rating: {safety['rating']}")
    print(f"Total crimes (6 months): {safety['total_crimes']}")
    print(f"Breakdown: Violent={safety['breakdown']['violent']}, "
          f"Property={safety['breakdown']['property']}, "
          f"Other={safety['breakdown']['other']}")

    # Trends
    print("\n--- Crime Trends (12 months) ---")
    trends = analyzer.get_crime_trends(test_lat, test_lon, radius_miles=0.5, months_back=12)
    print(f"Trend: {trends['trend']}")
    print(f"First 6 months: {trends['first_half_count']} crimes")
    print(f"Last 6 months: {trends['second_half_count']} crimes")
    print(f"Change: {trends['change_pct']:+.1f}%")

    # Detailed breakdown
    print("\n--- Crime Breakdown ---")
    breakdown = analyzer.get_crime_breakdown(test_lat, test_lon, radius_miles=0.5, months_back=6)
    print(f"Total: {breakdown['total']}")
    print(f"Violent: {breakdown['violent']['count']} ({breakdown['violent']['percentage']}%)")
    print(f"Property: {breakdown['property']['count']} ({breakdown['property']['percentage']}%)")
    print(f"Other: {breakdown['other']['count']} ({breakdown['other']['percentage']}%)")

    # Nearby crimes
    print("\n--- Recent Nearby Crimes (First 5) ---")
    nearby = analyzer.get_crimes_near_point(test_lat, test_lon, radius_miles=0.5, months_back=1)
    if len(nearby) > 0:
        for idx, row in nearby.head(5).iterrows():
            date_str = row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'N/A'
            desc = row['description'][:40] if pd.notna(row['description']) else 'N/A'
            print(f"  {desc:40} | {date_str} | {row['distance_miles']:.2f} mi | {row['category']}")
    else:
        print("  No crimes found in last month within 0.5 miles")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
