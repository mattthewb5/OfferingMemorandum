"""
Fairfax County Schools Analysis Module

Provides school assignment lookups, facility searches, and attendance zone queries
for properties in Fairfax County.

Usage:
    from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis

    analyzer = FairfaxSchoolsAnalysis()
    schools = analyzer.get_assigned_schools(lat=38.8969, lon=-77.4327)
    print(f"Elementary: {schools['elementary']['school_name']}")
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import Point
import math

# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "schools" / "processed"
ELEMENTARY_ZONES_PATH = DATA_DIR / "elementary_zones.parquet"
MIDDLE_ZONES_PATH = DATA_DIR / "middle_zones.parquet"
HIGH_ZONES_PATH = DATA_DIR / "high_zones.parquet"
FACILITIES_PATH = DATA_DIR / "facilities.parquet"


class FairfaxSchoolsAnalysis:
    """
    Fairfax County school analysis for property assessment.

    Provides school assignment lookups, facility searches, and zone analysis.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with school data.

        Args:
            data_dir: Optional path to processed schools directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.elementary_zones = self._load_zones('elementary')
        self.middle_zones = self._load_zones('middle')
        self.high_zones = self._load_zones('high')
        self.facilities = self._load_facilities()

        # Spatial indices for efficient lookups
        self._elem_sindex = None
        self._middle_sindex = None
        self._high_sindex = None

    def _load_zones(self, level: str) -> gpd.GeoDataFrame:
        """Load school attendance zones for a level."""
        path_map = {
            'elementary': self.data_dir / "elementary_zones.parquet",
            'middle': self.data_dir / "middle_zones.parquet",
            'high': self.data_dir / "high_zones.parquet",
        }

        path = path_map.get(level)
        if path is None or not path.exists():
            raise FileNotFoundError(f"School zones data not found for {level} at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    def _load_facilities(self) -> gpd.GeoDataFrame:
        """Load school facility point locations."""
        path = self.data_dir / "facilities.parquet"
        if not path.exists():
            raise FileNotFoundError(f"School facilities data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    @property
    def elem_sindex(self):
        """Lazy-load spatial index for elementary zones."""
        if self._elem_sindex is None:
            self._elem_sindex = self.elementary_zones.sindex
        return self._elem_sindex

    @property
    def middle_sindex(self):
        """Lazy-load spatial index for middle zones."""
        if self._middle_sindex is None:
            self._middle_sindex = self.middle_zones.sindex
        return self._middle_sindex

    @property
    def high_sindex(self):
        """Lazy-load spatial index for high zones."""
        if self._high_sindex is None:
            self._high_sindex = self.high_zones.sindex
        return self._high_sindex

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

    def _find_zone_match(self, lat: float, lon: float, zones: gpd.GeoDataFrame,
                         sindex) -> Optional[gpd.GeoSeries]:
        """Find the zone containing a point using spatial index."""
        point = Point(lon, lat)

        # Use spatial index for efficient lookup
        possible_matches_idx = list(sindex.intersection(point.bounds))

        if not possible_matches_idx:
            return None

        # Check actual containment
        possible_matches = zones.iloc[possible_matches_idx]
        matches = possible_matches[possible_matches.geometry.contains(point)]

        if len(matches) == 0:
            return None

        return matches.iloc[0]

    def _get_facility_for_school(self, school_name: str, school_type: str) -> Optional[Dict]:
        """Find facility details for a school."""
        # Match by name and type
        matches = self.facilities[
            (self.facilities['school_name'].str.upper() == school_name.upper()) &
            (self.facilities['school_type'] == school_type)
        ]

        if len(matches) == 0:
            # Try matching just by name
            matches = self.facilities[
                self.facilities['school_name'].str.upper() == school_name.upper()
            ]

        if len(matches) == 0:
            return None

        facility = matches.iloc[0]
        return {
            'latitude': facility.get('latitude'),
            'longitude': facility.get('longitude'),
            'address': facility.get('address'),
            'city': facility.get('city'),
            'zip_code': facility.get('zip_code'),
            'phone': facility.get('phone'),
            'website': facility.get('website'),
        }

    def get_assigned_schools(self, lat: float, lon: float) -> Dict:
        """
        Find elementary, middle, and high school assignments for coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with school assignments for each level
        """
        if lat is None or lon is None:
            return {
                'elementary': None,
                'middle': None,
                'high': None,
                'all_assigned': False,
                'message': 'Invalid coordinates provided'
            }

        result = {
            'elementary': None,
            'middle': None,
            'high': None,
            'all_assigned': False,
            'message': None
        }

        # Find elementary school
        elem_match = self._find_zone_match(lat, lon, self.elementary_zones, self.elem_sindex)
        if elem_match is not None:
            facility = self._get_facility_for_school(elem_match['school_name'], 'ES')
            distance = None
            if facility and facility.get('latitude') and facility.get('longitude'):
                distance = round(self._haversine_distance(
                    lat, lon, facility['latitude'], facility['longitude']
                ), 2)

            result['elementary'] = {
                'school_name': elem_match['school_name'],
                'grades': elem_match.get('grades'),
                'address': f"{elem_match.get('street_number', '')} {elem_match.get('street_name', '')}".strip() if elem_match.get('street_number') else (facility.get('address') if facility else None),
                'city': elem_match.get('city'),
                'phone': str(int(elem_match['phone'])) if pd.notna(elem_match.get('phone')) else None,
                'website': elem_match.get('website'),
                'region': elem_match.get('region'),
                'distance_miles': distance
            }

        # Find middle school
        middle_match = self._find_zone_match(lat, lon, self.middle_zones, self.middle_sindex)
        if middle_match is not None:
            facility = self._get_facility_for_school(middle_match['school_name'], 'MS')
            distance = None
            if facility and facility.get('latitude') and facility.get('longitude'):
                distance = round(self._haversine_distance(
                    lat, lon, facility['latitude'], facility['longitude']
                ), 2)

            result['middle'] = {
                'school_name': middle_match['school_name'],
                'grades': middle_match.get('grades'),
                'address': f"{middle_match.get('street_number', '')} {middle_match.get('street_name', '')}".strip() if middle_match.get('street_number') else (facility.get('address') if facility else None),
                'city': middle_match.get('city'),
                'phone': None,  # Middle zones don't have phone in data
                'website': middle_match.get('website'),
                'region': middle_match.get('region'),
                'distance_miles': distance
            }

        # Find high school
        high_match = self._find_zone_match(lat, lon, self.high_zones, self.high_sindex)
        if high_match is not None:
            facility = self._get_facility_for_school(high_match['school_name'], 'HS')
            distance = None
            if facility and facility.get('latitude') and facility.get('longitude'):
                distance = round(self._haversine_distance(
                    lat, lon, facility['latitude'], facility['longitude']
                ), 2)

            result['high'] = {
                'school_name': high_match['school_name'],
                'grades': high_match.get('grades'),
                'address': f"{high_match.get('street_number', '')} {high_match.get('street_name', '')}".strip() if high_match.get('street_number') else (facility.get('address') if facility else None),
                'city': high_match.get('city'),
                'phone': None,  # High zones don't have phone in data
                'website': high_match.get('website'),
                'region': high_match.get('region'),
                'distance_miles': distance
            }

        # Check if all levels assigned
        result['all_assigned'] = all([
            result['elementary'] is not None,
            result['middle'] is not None,
            result['high'] is not None
        ])

        if not result['all_assigned']:
            missing = []
            if result['elementary'] is None:
                missing.append('elementary')
            if result['middle'] is None:
                missing.append('middle')
            if result['high'] is None:
                missing.append('high')
            result['message'] = f"Location not in attendance zone for: {', '.join(missing)}"

        return result

    def get_school_facilities(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 5.0,
        school_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find nearby school facilities.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius in miles (default: 5.0)
            school_types: Optional filter by type codes (ES, MS, HS, etc.)
            limit: Maximum number of results (default: 10)

        Returns:
            List of facilities with distance, sorted by distance
        """
        if lat is None or lon is None:
            return []

        gdf = self.facilities.copy()

        # Filter by school types if specified
        if school_types:
            gdf = gdf[gdf['school_type'].isin(school_types)]

        # Calculate distances
        gdf['distance_miles'] = gdf.apply(
            lambda row: self._haversine_distance(
                lat, lon, row['latitude'], row['longitude']
            ) if pd.notna(row['latitude']) and pd.notna(row['longitude']) else None,
            axis=1
        )

        # Filter by radius
        gdf = gdf[gdf['distance_miles'] <= radius_miles].copy()

        if len(gdf) == 0:
            return []

        # Sort by distance and limit
        gdf = gdf.sort_values('distance_miles').head(limit)

        results = []
        for _, row in gdf.iterrows():
            results.append({
                'school_name': row['school_name'],
                'school_type': row['school_type'],
                'type_description': row.get('type_description'),
                'grades': row.get('grades'),
                'address': row.get('address'),
                'city': row.get('city'),
                'zip_code': row.get('zip_code'),
                'phone': row.get('phone'),
                'website': row.get('website'),
                'region': row.get('region'),
                'latitude': row.get('latitude'),
                'longitude': row.get('longitude'),
                'distance_miles': round(row['distance_miles'], 2)
            })

        return results

    def search_schools(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search schools by name.

        Args:
            query: Search string (case-insensitive partial match)
            limit: Maximum number of results (default: 10)

        Returns:
            List of matching schools with details
        """
        if not query:
            return []

        # Case-insensitive search
        matches = self.facilities[
            self.facilities['school_name'].str.upper().str.contains(query.upper(), na=False)
        ]

        if len(matches) == 0:
            return []

        matches = matches.head(limit)

        results = []
        for _, row in matches.iterrows():
            results.append({
                'school_name': row['school_name'],
                'school_type': row['school_type'],
                'type_description': row.get('type_description'),
                'grades': row.get('grades'),
                'address': row.get('address'),
                'city': row.get('city'),
                'zip_code': row.get('zip_code'),
                'website': row.get('website'),
                'region': row.get('region'),
                'latitude': row.get('latitude'),
                'longitude': row.get('longitude'),
            })

        return results

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the school dataset.

        Returns:
            Dict with dataset statistics
        """
        # Zone counts
        elem_count = len(self.elementary_zones)
        middle_count = len(self.middle_zones)
        high_count = len(self.high_zones)

        # Facility counts by type
        facility_counts = self.facilities['school_type'].value_counts().to_dict()

        # Geographic bounds
        all_zones = pd.concat([
            self.elementary_zones[['geometry']],
            self.middle_zones[['geometry']],
            self.high_zones[['geometry']]
        ])
        bounds = all_zones.total_bounds

        return {
            'attendance_zones': {
                'elementary': elem_count,
                'middle': middle_count,
                'high': high_count,
                'total': elem_count + middle_count + high_count
            },
            'facilities': {
                'total': len(self.facilities),
                'by_type': facility_counts
            },
            'geographic_bounds': {
                'min_longitude': round(bounds[0], 4),
                'min_latitude': round(bounds[1], 4),
                'max_longitude': round(bounds[2], 4),
                'max_latitude': round(bounds[3], 4)
            }
        }


def example_usage():
    """Example usage of FairfaxSchoolsAnalysis."""

    print("=" * 70)
    print("FAIRFAX SCHOOLS ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxSchoolsAnalysis()
    stats = analyzer.get_statistics()
    print(f"\nLoaded {stats['attendance_zones']['total']} attendance zones")
    print(f"  Elementary: {stats['attendance_zones']['elementary']}")
    print(f"  Middle: {stats['attendance_zones']['middle']}")
    print(f"  High: {stats['attendance_zones']['high']}")
    print(f"\nLoaded {stats['facilities']['total']} school facilities")

    # Example location
    test_lat = 38.8969
    test_lon = -77.4327

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Get assigned schools
    print("\n--- Assigned Schools ---")
    assigned = analyzer.get_assigned_schools(test_lat, test_lon)

    for level in ['elementary', 'middle', 'high']:
        school = assigned.get(level)
        if school:
            print(f"\n{level.title()}: {school['school_name']}")
            print(f"  Grades: {school['grades']}")
            print(f"  Distance: {school['distance_miles']} miles")
        else:
            print(f"\n{level.title()}: Not assigned")

    # Nearby facilities
    print("\n--- Nearby Elementary Schools (5 miles) ---")
    nearby = analyzer.get_school_facilities(test_lat, test_lon, radius_miles=5.0, school_types=['ES'], limit=5)
    for school in nearby:
        print(f"  {school['school_name']}: {school['distance_miles']} mi")

    # Search
    print("\n--- Search: 'Fairfax' ---")
    results = analyzer.search_schools("Fairfax", limit=5)
    for school in results:
        print(f"  {school['school_name']} ({school['school_type']})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
