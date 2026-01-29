"""
Fairfax County Cell Towers Analysis Module

Provides cell tower proximity analysis, coverage scoring, and infrastructure queries
for telecommunications infrastructure assessment.

Usage:
    from core.fairfax_cell_towers_analysis import FairfaxCellTowersAnalysis

    analyzer = FairfaxCellTowersAnalysis()
    coverage = analyzer.calculate_coverage_score(lat=38.8462, lon=-77.3064)
    print(f"Cell Coverage Score: {coverage['score']}/100")
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional
import math

# Data path
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "cell_towers" / "processed"
TOWERS_DATA_PATH = DATA_DIR / "towers.parquet"


class FairfaxCellTowersAnalysis:
    """
    Fairfax County cell tower analysis for property assessment.

    Provides cell coverage scoring, tower proximity analysis, and infrastructure queries.
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize with cell tower data.

        Args:
            data_path: Optional path to towers parquet file
        """
        self.data_path = data_path or TOWERS_DATA_PATH
        self.towers = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Load cell towers from parquet."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Cell tower data not found at {self.data_path}")

        gdf = gpd.read_parquet(self.data_path)

        # Convert to DataFrame, keeping lat/lon columns
        df = pd.DataFrame(gdf.drop(columns='geometry'))

        return df

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

    def get_towers_near_point(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 5.0,
        structure_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get cell towers within radius of a point.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_miles: Search radius in miles (default: 5.0)
            structure_type: Filter by structure type (e.g., 'TOWER', 'POLE', None for all)

        Returns:
            DataFrame of nearby towers with distance_miles column, sorted by distance
        """
        df = self.towers.copy()

        # Filter by structure type if specified
        if structure_type:
            df = df[df['structure_type'] == structure_type]

        # Calculate distances
        df['distance_miles'] = df.apply(
            lambda row: self._haversine_distance(lat, lon, row['latitude'], row['longitude']),
            axis=1
        )

        # Filter by radius and sort
        df = df[df['distance_miles'] <= radius_miles].sort_values('distance_miles')

        return df

    def calculate_coverage_score(self, lat: float, lon: float) -> Dict:
        """
        Calculate cell coverage score for a location.

        Score is based on:
        - Proximity to nearest tower (primary factor)
        - Number of towers within 2 miles (redundancy)
        - Height of nearby towers (coverage potential)
        - Diversity of tower types (network variety)

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with coverage score (0-100), rating, and analysis details
        """
        # Get towers within 5 miles
        nearby_towers = self.get_towers_near_point(lat, lon, radius_miles=5.0)

        if len(nearby_towers) == 0:
            return {
                'score': 25,
                'rating': 'Limited',
                'nearest_tower_miles': None,
                'towers_within_2mi': 0,
                'towers_within_5mi': 0,
                'coverage_analysis': 'No cell towers found within 5 miles. Coverage may be limited.',
                'factors': {
                    'proximity_score': 0,
                    'redundancy_score': 0,
                    'height_score': 0,
                    'diversity_score': 0
                }
            }

        # Calculate factors
        nearest_distance = nearby_towers['distance_miles'].min()
        towers_within_2mi = len(nearby_towers[nearby_towers['distance_miles'] <= 2.0])
        towers_within_5mi = len(nearby_towers)

        # 1. Proximity score (0-40 points)
        # Excellent: <0.5mi = 40, Good: 0.5-1mi = 30, Moderate: 1-2mi = 20, Limited: >2mi = 10
        if nearest_distance <= 0.5:
            proximity_score = 40
        elif nearest_distance <= 1.0:
            proximity_score = 35 - (nearest_distance - 0.5) * 10
        elif nearest_distance <= 2.0:
            proximity_score = 25 - (nearest_distance - 1.0) * 5
        else:
            proximity_score = max(5, 20 - (nearest_distance - 2.0) * 5)

        # 2. Redundancy score (0-25 points) - multiple towers = better reliability
        if towers_within_2mi >= 5:
            redundancy_score = 25
        elif towers_within_2mi >= 3:
            redundancy_score = 20
        elif towers_within_2mi >= 2:
            redundancy_score = 15
        elif towers_within_2mi >= 1:
            redundancy_score = 10
        else:
            redundancy_score = 5

        # 3. Height score (0-20 points) - taller towers = better coverage
        avg_height = nearby_towers[nearby_towers['distance_miles'] <= 2.0]['height_feet'].mean()
        if pd.isna(avg_height):
            avg_height = nearby_towers['height_feet'].mean()

        if avg_height >= 150:
            height_score = 20
        elif avg_height >= 100:
            height_score = 15
        elif avg_height >= 75:
            height_score = 10
        else:
            height_score = 5

        # 4. Diversity score (0-15 points) - multiple structure types = carrier variety
        unique_types = nearby_towers[nearby_towers['distance_miles'] <= 2.0]['structure_type'].nunique()
        if unique_types >= 4:
            diversity_score = 15
        elif unique_types >= 3:
            diversity_score = 12
        elif unique_types >= 2:
            diversity_score = 8
        else:
            diversity_score = 5

        # Calculate total score
        total_score = min(100, proximity_score + redundancy_score + height_score + diversity_score)

        # Determine rating
        if total_score >= 80:
            rating = 'Excellent'
            analysis = 'Strong cell coverage with multiple nearby towers and redundant infrastructure.'
        elif total_score >= 65:
            rating = 'Good'
            analysis = 'Good cell coverage with adequate tower infrastructure.'
        elif total_score >= 50:
            rating = 'Moderate'
            analysis = 'Moderate cell coverage. Signal strength may vary in some areas.'
        elif total_score >= 35:
            rating = 'Fair'
            analysis = 'Fair cell coverage. Indoor reception may be limited.'
        else:
            rating = 'Limited'
            analysis = 'Limited cell coverage. Consider signal boosters for indoor use.'

        return {
            'score': round(total_score),
            'rating': rating,
            'nearest_tower_miles': round(nearest_distance, 2),
            'towers_within_2mi': towers_within_2mi,
            'towers_within_5mi': towers_within_5mi,
            'coverage_analysis': analysis,
            'factors': {
                'proximity_score': round(proximity_score),
                'redundancy_score': round(redundancy_score),
                'height_score': round(height_score),
                'diversity_score': round(diversity_score)
            }
        }

    def get_nearest_towers(
        self,
        lat: float,
        lon: float,
        limit: int = 5
    ) -> List[Dict]:
        """
        Get the nearest cell towers to a location.

        Args:
            lat: Latitude
            lon: Longitude
            limit: Maximum number of towers to return (default: 5)

        Returns:
            List of tower dictionaries with distance and details
        """
        nearby = self.get_towers_near_point(lat, lon, radius_miles=10.0)

        if len(nearby) == 0:
            return []

        results = []
        for _, row in nearby.head(limit).iterrows():
            results.append({
                'tower_id': int(row['tower_id']),
                'fcc_registration': row['fcc_registration'],
                'owner': row['owner'],
                'carrier_category': row['carrier_category'],
                'structure_type': row['structure_type'],
                'structure_type_desc': row['structure_type_desc'],
                'height_feet': round(row['height_feet'], 1),
                'city': row['city'],
                'distance_miles': round(row['distance_miles'], 2),
                'latitude': row['latitude'],
                'longitude': row['longitude']
            })

        return results

    def get_towers_by_city(self, city: str) -> pd.DataFrame:
        """
        Get all towers in a specific city.

        Args:
            city: City name (case-insensitive)

        Returns:
            DataFrame of towers in the specified city
        """
        return self.towers[
            self.towers['city'].str.upper() == city.upper()
        ].copy()

    def get_towers_by_structure_type(self, structure_type: str) -> pd.DataFrame:
        """
        Get all towers of a specific structure type.

        Args:
            structure_type: Structure type code (e.g., 'TOWER', 'POLE', 'MTOWER')

        Returns:
            DataFrame of towers of the specified type
        """
        return self.towers[
            self.towers['structure_type'] == structure_type.upper()
        ].copy()

    def search_towers(self, query: str, limit: int = 20) -> pd.DataFrame:
        """
        Search towers by owner name or city.

        Args:
            query: Search string (case-insensitive partial match)
            limit: Maximum number of results

        Returns:
            DataFrame of matching towers
        """
        query_upper = query.upper()

        matches = self.towers[
            (self.towers['owner'].str.upper().str.contains(query_upper, na=False)) |
            (self.towers['city'].str.upper().str.contains(query_upper, na=False))
        ].copy()

        return matches.head(limit)

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the cell tower dataset.

        Returns:
            Dict with dataset statistics
        """
        df = self.towers

        # Structure type distribution
        structure_counts = df['structure_type_desc'].value_counts().to_dict()

        # Status distribution
        status_counts = df['status_desc'].value_counts().to_dict()

        # City distribution
        city_counts = df['city'].value_counts().head(10).to_dict()

        # Height statistics
        height_stats = {
            'min_feet': round(df['height_feet'].min(), 1),
            'max_feet': round(df['height_feet'].max(), 1),
            'mean_feet': round(df['height_feet'].mean(), 1),
            'median_feet': round(df['height_feet'].median(), 1)
        }

        # Geographic bounds
        bounds = {
            'min_latitude': round(df['latitude'].min(), 4),
            'max_latitude': round(df['latitude'].max(), 4),
            'min_longitude': round(df['longitude'].min(), 4),
            'max_longitude': round(df['longitude'].max(), 4)
        }

        return {
            'total_towers': len(df),
            'structure_types': structure_counts,
            'status': status_counts,
            'top_cities': city_counts,
            'height_statistics': height_stats,
            'geographic_bounds': bounds,
            'data_source': 'FCC Antenna Structure Registration (ASR)',
            'county': 'Fairfax County, VA',
            'county_fips': '51059'
        }


def example_usage():
    """Example usage of FairfaxCellTowersAnalysis."""

    print("=" * 70)
    print("FAIRFAX CELL TOWERS ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxCellTowersAnalysis()
    stats = analyzer.get_statistics()

    print(f"\nLoaded {stats['total_towers']} cell towers")
    print(f"\nStructure types: {stats['structure_types']}")
    print(f"\nTop cities: {stats['top_cities']}")
    print(f"\nHeight range: {stats['height_statistics']['min_feet']} - {stats['height_statistics']['max_feet']} feet")

    # Example location (Fairfax City)
    test_lat = 38.8462
    test_lon = -77.3064

    print(f"\nAnalyzing location: {test_lat}, {test_lon} (Fairfax City)")

    # Calculate coverage score
    print("\n--- Coverage Score ---")
    coverage = analyzer.calculate_coverage_score(test_lat, test_lon)
    print(f"Score: {coverage['score']}/100 ({coverage['rating']})")
    print(f"Nearest tower: {coverage['nearest_tower_miles']} miles")
    print(f"Towers within 2 mi: {coverage['towers_within_2mi']}")
    print(f"Towers within 5 mi: {coverage['towers_within_5mi']}")
    print(f"Analysis: {coverage['coverage_analysis']}")

    # Get nearest towers
    print("\n--- Nearest Towers ---")
    nearest = analyzer.get_nearest_towers(test_lat, test_lon, limit=3)
    for tower in nearest:
        print(f"  {tower['structure_type_desc']}: {tower['distance_miles']} mi, {tower['height_feet']} ft")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
