"""
Fairfax County Healthcare Analysis Module

Provides healthcare access scoring, facility quality analysis, and spatial queries
for hospitals and urgent care facilities.

Usage:
    from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis

    analyzer = FairfaxHealthcareAnalysis()
    access = analyzer.calculate_healthcare_access_score(lat=38.8462, lon=-77.3064)
    print(f"Healthcare Access: {access['score']}/100")
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math

# Data path
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "healthcare" / "processed"
FACILITIES_DATA_PATH = DATA_DIR / "facilities.parquet"


class FairfaxHealthcareAnalysis:
    """
    Fairfax County healthcare facility analysis for property assessment.

    Provides healthcare access scoring, quality metrics, and facility comparisons.
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize with healthcare facilities data.

        Args:
            data_path: Optional path to facilities parquet file
        """
        self.data_path = data_path or FACILITIES_DATA_PATH
        self.facilities = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Load healthcare facilities from parquet."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Healthcare data not found at {self.data_path}")

        df = pd.read_parquet(self.data_path)

        # Filter to facilities with coordinates
        df_geo = df.dropna(subset=['latitude', 'longitude']).copy()

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

    def get_facilities_near_point(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 10.0,
        facility_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get healthcare facilities within radius of a point.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_miles: Search radius in miles (default: 10.0)
            facility_type: Filter by type ('hospital', 'urgent_care', None for all)

        Returns:
            DataFrame of nearby facilities with distance_miles column, sorted by distance
        """
        df = self.facilities.copy()

        # Calculate distances
        df['distance_miles'] = df.apply(
            lambda row: self._haversine_distance(lat, lon, row['latitude'], row['longitude']),
            axis=1
        )

        # Filter by radius
        df = df[df['distance_miles'] <= radius_miles]

        # Filter by type if specified
        if facility_type is not None:
            df = df[df['facility_type'] == facility_type]

        return df.sort_values('distance_miles')

    def calculate_healthcare_access_score(
        self,
        lat: float,
        lon: float
    ) -> Dict:
        """
        Calculate a healthcare access score (0-100) for a location.

        Higher scores = better healthcare access.

        Scoring algorithm:
        - Base: 50 points
        - Hospital within 5 miles: +20 points
        - Hospital within 3 miles: +10 additional points
        - 5-star hospital within 10 miles: +15 points
        - Urgent care within 3 miles: +10 points
        - Multiple urgent care nearby: +5 points (up to 2)
        - Emergency services: +5 points
        - Capped at 100

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with score, rating, and breakdown
        """
        score = 50  # Base score
        breakdown = {}

        # Find nearest hospital
        hospitals = self.get_facilities_near_point(lat, lon, radius_miles=10, facility_type='hospital')

        if len(hospitals) > 0:
            nearest_hospital = hospitals.iloc[0]
            dist = nearest_hospital['distance_miles']

            breakdown['nearest_hospital'] = {
                'name': nearest_hospital['name'],
                'distance_miles': round(dist, 2),
                'cms_rating': nearest_hospital.get('cms_rating'),
                'leapfrog_grade': nearest_hospital.get('leapfrog_grade')
            }

            # Distance scoring
            if dist <= 5:
                score += 20
                if dist <= 3:
                    score += 10

            # Quality scoring - check for any 5-star hospital within 10 miles
            five_star_hospitals = hospitals[hospitals['cms_rating'] == 5]
            if len(five_star_hospitals) > 0:
                score += 15

            # Emergency services from nearest hospital
            if nearest_hospital.get('emergency_services') == 'Yes':
                score += 5
        else:
            breakdown['nearest_hospital'] = None

        # Find urgent care facilities
        urgent_care = self.get_facilities_near_point(lat, lon, radius_miles=3, facility_type='urgent_care')

        if len(urgent_care) > 0:
            score += 10
            # Bonus for multiple options
            if len(urgent_care) >= 2:
                score += 5
            if len(urgent_care) >= 3:
                score += 5

            breakdown['urgent_care_nearby'] = {
                'count_within_3mi': len(urgent_care),
                'nearest_distance': round(urgent_care.iloc[0]['distance_miles'], 2)
            }
        else:
            breakdown['urgent_care_nearby'] = {'count_within_3mi': 0}

        # Cap at 100
        score = min(100, int(score))

        # Assign rating
        if score >= 85:
            rating = 'Excellent Access'
        elif score >= 70:
            rating = 'Good Access'
        elif score >= 55:
            rating = 'Moderate Access'
        elif score >= 40:
            rating = 'Limited Access'
        else:
            rating = 'Poor Access'

        return {
            'score': score,
            'rating': rating,
            'breakdown': breakdown,
            'hospitals_within_10mi': len(hospitals),
            'urgent_care_within_3mi': len(urgent_care)
        }

    def get_quality_metrics(
        self,
        facility_name: str
    ) -> Optional[Dict]:
        """
        Get quality metrics for a specific facility.

        Args:
            facility_name: Name of facility (partial match supported)

        Returns:
            Dict with quality metrics or None if not found
        """
        # Case-insensitive partial match
        matches = self.facilities[
            self.facilities['name'].str.upper().str.contains(facility_name.upper(), na=False)
        ]

        if len(matches) == 0:
            return None

        facility = matches.iloc[0]

        return {
            'name': facility['name'],
            'facility_type': facility['facility_type'],
            'cms_facility_id': facility.get('cms_facility_id'),
            'cms_rating': facility.get('cms_rating'),
            'leapfrog_grade': facility.get('leapfrog_grade'),
            'leapfrog_date': facility.get('leapfrog_date'),
            'leapfrog_notes': facility.get('leapfrog_notes'),
            'emergency_services': facility.get('emergency_services'),
            'hospital_type': facility.get('hospital_type'),
            'address': facility['address'],
            'city': facility['city'],
            'phone': facility['phone'],
            'website': facility['website']
        }

    def compare_facilities(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 10.0,
        facility_type: str = 'hospital',
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        Compare nearby facilities ranked by quality and distance.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 10 miles)
            facility_type: 'hospital' or 'urgent_care' (default: 'hospital')
            top_n: Number of facilities to return (default: 5)

        Returns:
            DataFrame with ranked facilities
        """
        facilities = self.get_facilities_near_point(lat, lon, radius_miles, facility_type)

        if len(facilities) == 0:
            return pd.DataFrame()

        # Calculate composite score
        # Distance score: 0-50 points (closer = better)
        # Quality score: 0-50 points (higher rating = better)

        facilities = facilities.copy()

        # Distance score (inverse - closer is better)
        max_dist = facilities['distance_miles'].max()
        if max_dist > 0:
            facilities['distance_score'] = 50 * (1 - facilities['distance_miles'] / max_dist)
        else:
            facilities['distance_score'] = 50

        # Quality score
        facilities['quality_score'] = 0.0

        # CMS rating contribution
        for idx, row in facilities.iterrows():
            quality_points = 0.0

            if pd.notna(row.get('cms_rating')):
                quality_points += (row['cms_rating'] / 5) * 30  # Up to 30 points

            if pd.notna(row.get('leapfrog_grade')):
                grade_points = {'A': 20, 'B': 15, 'C': 10, 'D': 5, 'F': 0}
                quality_points += grade_points.get(row['leapfrog_grade'], 0)

            facilities.at[idx, 'quality_score'] = quality_points

        # Composite score
        facilities['composite_score'] = facilities['distance_score'] + facilities['quality_score']

        # Sort by composite score
        facilities = facilities.sort_values('composite_score', ascending=False)

        # Select columns for output
        output_cols = [
            'name', 'distance_miles', 'cms_rating', 'leapfrog_grade',
            'emergency_services', 'city', 'phone', 'composite_score'
        ]
        available_cols = [c for c in output_cols if c in facilities.columns]

        return facilities[available_cols].head(top_n)


def example_usage():
    """Example usage of FairfaxHealthcareAnalysis."""

    print("=" * 70)
    print("FAIRFAX HEALTHCARE ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxHealthcareAnalysis()
    print(f"\nLoaded {len(analyzer.facilities)} healthcare facilities")
    print(f"  Hospitals: {len(analyzer.facilities[analyzer.facilities['facility_type'] == 'hospital'])}")
    print(f"  Urgent Care: {len(analyzer.facilities[analyzer.facilities['facility_type'] == 'urgent_care'])}")

    # Example location (Fairfax County)
    test_lat = 38.8462
    test_lon = -77.3064

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Healthcare access score
    print("\n--- Healthcare Access Score ---")
    access = analyzer.calculate_healthcare_access_score(test_lat, test_lon)
    print(f"Score: {access['score']}/100")
    print(f"Rating: {access['rating']}")
    print(f"Hospitals within 10 miles: {access['hospitals_within_10mi']}")
    print(f"Urgent care within 3 miles: {access['urgent_care_within_3mi']}")

    if access['breakdown'].get('nearest_hospital'):
        hosp = access['breakdown']['nearest_hospital']
        print(f"\nNearest Hospital: {hosp['name']}")
        print(f"  Distance: {hosp['distance_miles']} miles")
        cms = hosp.get('cms_rating')
        cms_str = f"{int(cms)} stars" if pd.notna(cms) and cms else "N/A"
        print(f"  CMS Rating: {cms_str}")
        print(f"  Leapfrog Grade: {hosp.get('leapfrog_grade') or 'N/A'}")

    # Quality metrics for specific hospital
    print("\n--- Quality Metrics: Inova Fairfax ---")
    metrics = analyzer.get_quality_metrics("INOVA FAIRFAX HOSPITAL")
    if metrics:
        print(f"Name: {metrics['name']}")
        cms = metrics.get('cms_rating')
        cms_str = f"{int(cms)} stars" if pd.notna(cms) and cms else "N/A"
        print(f"CMS Rating: {cms_str}")
        print(f"Leapfrog Grade: {metrics.get('leapfrog_grade') or 'N/A'}")
        print(f"Leapfrog Notes: {metrics.get('leapfrog_notes') or 'N/A'}")
        print(f"Emergency Services: {metrics.get('emergency_services') or 'N/A'}")

    # Compare hospitals
    print("\n--- Top 5 Hospitals (by quality & distance) ---")
    comparison = analyzer.compare_facilities(test_lat, test_lon, radius_miles=15, top_n=5)
    if len(comparison) > 0:
        for idx, row in comparison.iterrows():
            print(f"\n{row['name']}")
            print(f"  Distance: {row['distance_miles']:.1f} mi")
            cms = row.get('cms_rating')
            cms_str = f"{int(cms)} stars" if pd.notna(cms) and cms else "N/A"
            print(f"  CMS Rating: {cms_str}")
            print(f"  Leapfrog: {row.get('leapfrog_grade') or 'N/A'}")
            print(f"  Score: {row['composite_score']:.1f}/100")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
