"""
Fairfax County Utilities Analysis Module

Provides utility line proximity queries for power lines, gas lines, and
telephone infrastructure in Fairfax County.

Usage:
    from core.fairfax_utilities_analysis import FairfaxUtilitiesAnalysis

    analyzer = FairfaxUtilitiesAnalysis()
    nearby = analyzer.get_nearby_utilities(lat=38.8969, lon=-77.4327)
    proximity = analyzer.check_proximity(lat=38.8969, lon=-77.4327, distance_threshold_miles=0.1)
"""

import geopandas as gpd
import math
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import Point
from shapely.ops import nearest_points


# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "utilities" / "processed"
UTILITY_LINES_PATH = DATA_DIR / "utility_lines.parquet"


class FairfaxUtilitiesAnalysis:
    """
    Fairfax County utilities analysis for property assessment.

    Provides utility line proximity queries for disclosure requirements
    and infrastructure awareness.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with utility data.

        Args:
            data_dir: Optional path to processed utilities directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.utility_lines = self._load_utility_lines()
        self._sindex = None

    def _load_utility_lines(self) -> gpd.GeoDataFrame:
        """Load utility lines from parquet."""
        path = self.data_dir / "utility_lines.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Utility lines data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    @property
    def sindex(self):
        """Lazy-load spatial index."""
        if self._sindex is None:
            self._sindex = self.utility_lines.sindex
        return self._sindex

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance in miles."""
        R = 3959  # Earth's radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _calculate_distance_to_line(self, lat: float, lon: float, line_geometry) -> float:
        """
        Calculate distance from point to nearest point on a line.

        Args:
            lat: Latitude
            lon: Longitude
            line_geometry: Shapely LineString or MultiLineString

        Returns:
            Distance in miles
        """
        point = Point(lon, lat)

        # Find nearest point on line
        nearest_geom = nearest_points(point, line_geometry)[1]

        # Calculate haversine distance
        return self._haversine_distance(lat, lon, nearest_geom.y, nearest_geom.x)

    def get_nearby_utilities(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5,
        utility_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Find utility lines within radius of a location.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.5 miles)
            utility_types: Optional filter by type (electric, gas, telephone)
            limit: Maximum number of results (default: 20)

        Returns:
            List of nearby utility lines sorted by distance
        """
        if lat is None or lon is None:
            return []

        point = Point(lon, lat)

        # Convert radius to approximate degrees for bounding box query
        # 1 degree latitude ≈ 69 miles
        buffer_deg = radius_miles / 69.0

        # Create bounding box
        minx, miny, maxx, maxy = (
            lon - buffer_deg,
            lat - buffer_deg,
            lon + buffer_deg,
            lat + buffer_deg
        )

        # Get candidates using spatial index
        possible_idx = list(self.sindex.intersection((minx, miny, maxx, maxy)))
        if not possible_idx:
            return []

        candidates = self.utility_lines.iloc[possible_idx].copy()

        # Apply utility type filter if specified
        if utility_types:
            utility_types_lower = [t.lower() for t in utility_types]
            candidates = candidates[candidates['utility_type'].str.lower().isin(utility_types_lower)]

        if len(candidates) == 0:
            return []

        # Calculate distances
        results = []
        for idx, row in candidates.iterrows():
            distance = self._calculate_distance_to_line(lat, lon, row.geometry)

            if distance <= radius_miles:
                results.append({
                    'utility_type': row['utility_type'],
                    'operator': row['operator'],
                    'length_miles': round(row['length_miles'], 2),
                    'distance_miles': round(distance, 2),
                    'object_id': row['object_id']
                })

        # Sort by distance and limit
        results.sort(key=lambda x: x['distance_miles'])
        return results[:limit]

    def check_proximity(
        self,
        lat: float,
        lon: float,
        distance_threshold_miles: float = 0.1
    ) -> Dict:
        """
        Check if property is within threshold of any utility line.

        Useful for disclosure requirements and property assessments.

        Args:
            lat: Latitude
            lon: Longitude
            distance_threshold_miles: Distance threshold (default: 0.1 miles / 528 ft)

        Returns:
            Dict with proximity information
        """
        if lat is None or lon is None:
            return {
                'within_threshold': False,
                'threshold_miles': distance_threshold_miles,
                'closest_utility': None,
                'utilities_within_threshold': [],
                'message': 'Invalid coordinates provided'
            }

        # Get utilities within threshold
        nearby = self.get_nearby_utilities(
            lat, lon,
            radius_miles=distance_threshold_miles,
            limit=50
        )

        if not nearby:
            return {
                'within_threshold': False,
                'threshold_miles': distance_threshold_miles,
                'closest_utility': None,
                'utilities_within_threshold': [],
                'message': None
            }

        # Get closest utility
        closest = nearby[0]

        # Get all utilities within threshold
        within_threshold = [
            {
                'utility_type': u['utility_type'],
                'operator': u['operator'],
                'distance_miles': u['distance_miles']
            }
            for u in nearby
        ]

        return {
            'within_threshold': True,
            'threshold_miles': distance_threshold_miles,
            'closest_utility': {
                'utility_type': closest['utility_type'],
                'operator': closest['operator'],
                'distance_miles': closest['distance_miles']
            },
            'utilities_within_threshold': within_threshold,
            'message': None
        }

    def get_utility_types_nearby(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5
    ) -> Dict:
        """
        Get summary of utility types within radius.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.5 miles)

        Returns:
            Dict with summary by utility type
        """
        if lat is None or lon is None:
            return {
                'electric': {'count': 0, 'operators': [], 'total_miles': 0, 'closest_distance': None},
                'gas': {'count': 0, 'operators': [], 'total_miles': 0, 'closest_distance': None},
                'telephone': {'count': 0, 'operators': [], 'total_miles': 0, 'closest_distance': None}
            }

        nearby = self.get_nearby_utilities(lat, lon, radius_miles=radius_miles, limit=100)

        result = {
            'electric': {'count': 0, 'operators': [], 'total_miles': 0.0, 'closest_distance': None},
            'gas': {'count': 0, 'operators': [], 'total_miles': 0.0, 'closest_distance': None},
            'telephone': {'count': 0, 'operators': [], 'total_miles': 0.0, 'closest_distance': None}
        }

        for utility in nearby:
            utype = utility['utility_type'].lower()
            if utype in result:
                result[utype]['count'] += 1
                result[utype]['total_miles'] += utility['length_miles']

                if utility['operator'] not in result[utype]['operators']:
                    result[utype]['operators'].append(utility['operator'])

                if result[utype]['closest_distance'] is None or utility['distance_miles'] < result[utype]['closest_distance']:
                    result[utype]['closest_distance'] = utility['distance_miles']

        # Round totals
        for utype in result:
            result[utype]['total_miles'] = round(result[utype]['total_miles'], 1)

        return result

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the utility dataset.

        Returns:
            Dict with dataset statistics
        """
        # Counts by type
        type_counts = self.utility_lines['utility_type'].value_counts().to_dict()

        # Operators by type
        operators_by_type = {}
        for utype in ['electric', 'gas', 'telephone']:
            subset = self.utility_lines[self.utility_lines['utility_type'] == utype]
            operators_by_type[utype] = subset['operator'].unique().tolist()

        # Total miles by type
        miles_by_type = self.utility_lines.groupby('utility_type')['length_miles'].sum().to_dict()
        miles_by_type = {k: round(v, 1) for k, v in miles_by_type.items()}

        # Geographic bounds
        bounds = self.utility_lines.total_bounds

        return {
            'total_lines': len(self.utility_lines),
            'by_type': type_counts,
            'miles_by_type': miles_by_type,
            'operators_by_type': operators_by_type,
            'total_miles': round(self.utility_lines['length_miles'].sum(), 1),
            'geographic_bounds': {
                'min_longitude': round(bounds[0], 4),
                'min_latitude': round(bounds[1], 4),
                'max_longitude': round(bounds[2], 4),
                'max_latitude': round(bounds[3], 4)
            }
        }


def example_usage():
    """Example usage of FairfaxUtilitiesAnalysis."""

    print("=" * 70)
    print("FAIRFAX UTILITIES ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxUtilitiesAnalysis()
    stats = analyzer.get_statistics()
    print(f"\nLoaded {stats['total_lines']} utility lines ({stats['total_miles']} miles)")
    print(f"  By type:")
    for utype, count in stats['by_type'].items():
        miles = stats['miles_by_type'].get(utype, 0)
        print(f"    {utype}: {count} lines, {miles} miles")

    # Test location
    test_lat = 38.8969
    test_lon = -77.4327

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Get nearby utilities
    print("\n--- Nearby Utilities (0.5 mi) ---")
    nearby = analyzer.get_nearby_utilities(test_lat, test_lon, radius_miles=0.5)
    for utility in nearby[:5]:
        print(f"  {utility['utility_type']}: {utility['operator']} ({utility['distance_miles']} mi)")

    # Check proximity
    print("\n--- Proximity Check (0.1 mi threshold) ---")
    proximity = analyzer.check_proximity(test_lat, test_lon, 0.1)
    print(f"  Within threshold: {proximity['within_threshold']}")
    if proximity['closest_utility']:
        print(f"  Closest: {proximity['closest_utility']['utility_type']} at {proximity['closest_utility']['distance_miles']} mi")

    # Summary by type
    print("\n--- Utilities by Type (0.5 mi) ---")
    by_type = analyzer.get_utility_types_nearby(test_lat, test_lon, 0.5)
    for utype, info in by_type.items():
        if info['count'] > 0:
            print(f"  {utype}: {info['count']} lines, closest at {info['closest_distance']} mi")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
