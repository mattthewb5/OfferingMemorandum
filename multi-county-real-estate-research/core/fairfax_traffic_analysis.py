"""
Fairfax County Traffic Analysis Module

Provides traffic volume analysis, congestion scoring, and road traffic metrics
based on VDOT Average Daily Traffic (ADT) count data.

Usage:
    from core.fairfax_traffic_analysis import FairfaxTrafficAnalysis

    analyzer = FairfaxTrafficAnalysis()
    exposure = analyzer.calculate_traffic_exposure_score(lat=38.8462, lon=-77.3064)
    print(f"Traffic Exposure: {exposure['score']}/100 ({exposure['rating']})")
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional
import math
from rapidfuzz import fuzz, process

# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "traffic" / "processed"
# Statewide VDOT parquet replaces the legacy bbox-clipped traffic_volumes.parquet.
# Loaded lazily and spatially filtered to Fairfax County at load time.
STATEWIDE_TRAFFIC_PATH = SCRIPT_DIR.parent / "data" / "shared" / "traffic" / "vdot_statewide_traffic.parquet"
TRAFFIC_DATA_PATH = STATEWIDE_TRAFFIC_PATH

# Fairfax County bounding box for fast prefilter (lat, lon)
_FAIRFAX_BBOX = (38.58, 39.08, -77.55, -76.85)


class FairfaxTrafficAnalysis:
    """
    Fairfax County traffic analysis for property assessment.

    Provides traffic exposure scoring, road traffic lookups, and congestion analysis
    based on VDOT ADT (Average Daily Traffic) count data.
    """

    # Traffic level thresholds
    TRAFFIC_LEVELS = {
        'Very Low': (0, 1000),
        'Low': (1000, 5000),
        'Moderate': (5000, 15000),
        'High': (15000, 30000),
        'Very High': (30000, float('inf'))
    }

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize with traffic volume data.

        Args:
            data_path: Optional path to traffic volumes parquet file
        """
        self.data_path = data_path or TRAFFIC_DATA_PATH
        self._traffic = None

    @property
    def traffic(self) -> gpd.GeoDataFrame:
        """Lazy load traffic data."""
        if self._traffic is None:
            self._traffic = self._load_data()
        return self._traffic

    def _load_data(self) -> gpd.GeoDataFrame:
        """Load statewide VDOT traffic volume data, filtered to Fairfax County."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Traffic data not found at {self.data_path}")

        gdf = gpd.read_parquet(self.data_path)

        # Precise filter: segments whose county_fips includes Fairfax (51059 -> '059')
        gdf = gdf[gdf.geometry.notna()].copy()
        if 'county_fips' in gdf.columns:
            gdf = gdf[gdf['county_fips'].fillna('').str.contains(r'\b059\b', regex=True)].copy()
        else:
            # Fallback bbox (less precise)
            lat_min, lat_max, lon_min, lon_max = _FAIRFAX_BBOX
            bounds = gdf.geometry.bounds
            mask = (
                (bounds['maxy'] >= lat_min) & (bounds['miny'] <= lat_max) &
                (bounds['maxx'] >= lon_min) & (bounds['minx'] <= lon_max)
            )
            gdf = gdf.loc[mask].copy()

        # Derive centroid lat/lon for legacy distance calculations
        centroids = gdf.geometry.centroid
        gdf['latitude'] = centroids.y
        gdf['longitude'] = centroids.x

        # Normalize column names to legacy schema expected by this module
        rename = {
            'ADT': 'adt',
            'ADT_QUALITY': 'data_quality',
            'ROUTE_COMMON_NAME': 'road_name',
            'ROUTE_NAME': 'route_name',
            'DATA_DATE': 'data_date',
        }
        gdf = gdf.rename(columns={k: v for k, v in rename.items() if k in gdf.columns})
        # Provide street_name alias for downstream code
        if 'street_name' not in gdf.columns and 'road_name' in gdf.columns:
            gdf['street_name'] = gdf['road_name']
        return gdf

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

    def get_nearby_traffic(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5
    ) -> List[Dict]:
        """
        Get road segments with traffic data within radius of a point.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_miles: Search radius in miles (default: 0.5)

        Returns:
            List of road dictionaries with distance_miles, sorted by distance
        """
        df = self.traffic.copy()

        # Calculate distances using centroid
        df['distance_miles'] = df.apply(
            lambda row: self._haversine_distance(lat, lon, row['latitude'], row['longitude']),
            axis=1
        )

        # Filter by radius
        nearby = df[df['distance_miles'] <= radius_miles].copy()

        if nearby.empty:
            return []

        # Deduplicate: for each road name, pick the best representative ADT.
        # When a road has multiple segments, outlier ADT values (e.g. SC-7812's
        # 18K on a 2K subdivision road) get filtered by taking the median.
        # Prefer newer data and quality "G" (measured) over "R" (estimated).
        deduped_rows = []
        for road_name, group in nearby.groupby('road_name'):
            if len(group) >= 3:
                # Multiple segments: use median ADT to filter outliers
                representative_adt = int(group['adt'].median())
            else:
                # Few segments: prefer quality "G" and newer data
                g_quality = group[group['data_quality'] == 'G']
                if len(g_quality) > 0:
                    representative_adt = int(g_quality['adt'].median())
                else:
                    representative_adt = int(group['adt'].median())

            # Use the closest segment for location/distance
            closest = group.sort_values('distance_miles').iloc[0]
            deduped_rows.append({
                'road_name': road_name,
                'route_name': closest.get('route_name', ''),
                'adt': representative_adt,
                'traffic_level': self._categorize_adt(representative_adt),
                'peak_hour_estimate': int(representative_adt * 0.1),
                'distance_miles': round(closest['distance_miles'], 3),
                'latitude': closest['latitude'],
                'longitude': closest['longitude']
            })

        # Sort by distance
        deduped_rows.sort(key=lambda x: x['distance_miles'])

        return deduped_rows

    def calculate_traffic_exposure_score(self, lat: float, lon: float) -> Dict:
        """
        Calculate traffic exposure score for a location.

        Score is INVERTED: LOWER traffic exposure = HIGHER score (better for residential).

        Scoring system (0-100, higher is better):
        - Distance to nearest high-traffic road (0-40 pts): farther = better
        - Nearest road ADT level (0-40 pts): lower ADT = better score
        - Count of high-traffic roads nearby (0-20 pts): fewer = better

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with score (0-100), rating, and analysis details
        """
        # Get roads within 1 mile
        nearby = self.get_nearby_traffic(lat, lon, radius_miles=1.0)

        if len(nearby) == 0:
            return {
                'score': 95,
                'rating': 'Excellent',
                'nearest_road': None,
                'nearest_distance_miles': None,
                'high_traffic_roads_nearby': 0,
                'analysis': 'No traffic data available nearby. Likely a quiet residential area.',
                'factors': {
                    'distance_score': 40,
                    'adt_score': 40,
                    'density_score': 15
                }
            }

        # Find nearest road
        nearest = nearby[0]
        nearest_distance = nearest['distance_miles']
        nearest_adt = nearest['adt']

        # Count high-traffic roads (>30,000 ADT) within 0.5 miles
        high_traffic = [r for r in nearby if r['adt'] >= 30000 and r['distance_miles'] <= 0.5]
        high_traffic_count = len(high_traffic)

        # 1. Distance score (0-40 points) - farther from traffic = better
        # Excellent: >0.5mi from any road = 40, Close: <0.1mi = 5
        if nearest_distance >= 0.5:
            distance_score = 40
        elif nearest_distance >= 0.3:
            distance_score = 30
        elif nearest_distance >= 0.2:
            distance_score = 20
        elif nearest_distance >= 0.1:
            distance_score = 15
        else:
            distance_score = 5

        # 2. ADT score (0-40 points) - lower traffic = better
        if nearest_adt < 5000:
            adt_score = 40
        elif nearest_adt < 15000:
            adt_score = 30
        elif nearest_adt < 30000:
            adt_score = 20
        elif nearest_adt < 50000:
            adt_score = 10
        else:
            adt_score = 5

        # 3. Density score (0-20 points) - fewer high-traffic roads = better
        if high_traffic_count == 0:
            density_score = 20
        elif high_traffic_count == 1:
            density_score = 15
        elif high_traffic_count <= 3:
            density_score = 10
        else:
            density_score = 5

        # Calculate total score
        total_score = distance_score + adt_score + density_score

        # Determine rating
        if total_score >= 85:
            rating = 'Excellent'
            analysis = 'Minimal traffic exposure. Quiet location ideal for residential use.'
        elif total_score >= 70:
            rating = 'Good'
            analysis = 'Low traffic exposure. Generally quiet with manageable traffic levels.'
        elif total_score >= 55:
            rating = 'Fair'
            analysis = 'Moderate traffic exposure. Some noise and traffic concerns possible.'
        else:
            rating = 'Poor'
            analysis = 'High traffic exposure. Significant noise and safety considerations.'

        return {
            'score': total_score,
            'rating': rating,
            'nearest_road': nearest['road_name'],
            'nearest_adt': nearest_adt,
            'nearest_distance_miles': round(nearest_distance, 3),
            'high_traffic_roads_nearby': high_traffic_count,
            'analysis': analysis,
            'factors': {
                'distance_score': distance_score,
                'adt_score': adt_score,
                'density_score': density_score
            }
        }

    def get_road_traffic(self, road_name: str, limit: int = 50) -> List[Dict]:
        """
        Look up traffic data for a specific road by name.

        Args:
            road_name: Road name to search (supports fuzzy matching)
            limit: Maximum number of segments to return

        Returns:
            List of road segments with their ADT values
        """
        df = self.traffic

        # Try exact match first
        exact = df[df['road_name'].str.upper() == road_name.upper()]

        if len(exact) == 0:
            # Try fuzzy match
            road_names = df['road_name'].dropna().unique().tolist()
            match = process.extractOne(road_name, road_names, scorer=fuzz.token_sort_ratio)

            if match and match[1] >= 60:
                exact = df[df['road_name'] == match[0]]
            else:
                return []

        # Sort by ADT descending
        exact = exact.nlargest(limit, 'adt')

        results = []
        for _, row in exact.iterrows():
            results.append({
                'road_name': row['road_name'],
                'route_name': row.get('route_name', ''),
                'adt': int(row['adt']),
                'traffic_level': row['traffic_level'],
                'latitude': row['latitude'],
                'longitude': row['longitude']
            })

        return results

    def get_congested_roads(self, min_adt: int = 30000, limit: int = 50) -> pd.DataFrame:
        """
        Get highest-traffic roads in the county.

        Args:
            min_adt: Minimum ADT threshold (default: 30,000)
            limit: Maximum number of roads to return

        Returns:
            DataFrame of congested roads
        """
        df = self.traffic[self.traffic['adt'] >= min_adt].copy()

        # Group by road name and get max ADT
        grouped = df.groupby('road_name').agg({
            'adt': 'max',
            'route_name': 'first',
            'traffic_level': 'first',
            'latitude': 'first',
            'longitude': 'first'
        }).reset_index()

        # Sort by ADT descending
        grouped = grouped.nlargest(limit, 'adt')

        return grouped[['road_name', 'route_name', 'adt', 'traffic_level']]

    def analyze_commute_corridor(
        self,
        lat: float,
        lon: float,
        direction: str = "east"
    ) -> Dict:
        """
        Analyze major commute corridors from a location.

        Args:
            lat: Latitude of starting point
            lon: Longitude of starting point
            direction: Direction of commute ('east', 'west', 'north', 'south')

        Returns:
            Dict with major corridors and their traffic levels
        """
        # Define major corridors by direction
        corridors = {
            'east': ['I-66', 'US-50', 'VA-7', 'VA-236'],
            'west': ['I-66', 'US-50', 'VA-7', 'VA-267'],
            'north': ['VA-28', 'VA-123', 'VA-286'],
            'south': ['I-95', 'VA-123', 'US-1', 'VA-286']
        }

        direction = direction.lower()
        if direction not in corridors:
            direction = 'east'

        target_corridors = corridors[direction]

        # Get traffic data for corridors
        df = self.traffic
        corridor_data = []

        for corridor in target_corridors:
            corridor_roads = df[df['route_name'].str.contains(corridor, na=False, case=False)]
            if len(corridor_roads) > 0:
                max_adt = corridor_roads['adt'].max()
                avg_adt = corridor_roads['adt'].mean()
                corridor_data.append({
                    'corridor': corridor,
                    'max_adt': int(max_adt),
                    'avg_adt': int(avg_adt),
                    'traffic_level': self._categorize_adt(max_adt),
                    'segments': len(corridor_roads)
                })

        # Sort by max ADT
        corridor_data.sort(key=lambda x: x['max_adt'], reverse=True)

        return {
            'location': {'lat': lat, 'lon': lon},
            'direction': direction,
            'corridors': corridor_data,
            'summary': f"Found {len(corridor_data)} major corridors for {direction}bound commute"
        }

    def _categorize_adt(self, adt: float) -> str:
        """Categorize ADT into traffic level."""
        for level, (low, high) in self.TRAFFIC_LEVELS.items():
            if low <= adt < high:
                return level
        return 'Very High'

    def search_roads(self, query: str, limit: int = 20) -> pd.DataFrame:
        """
        Search roads by name.

        Args:
            query: Search string (case-insensitive)
            limit: Maximum number of results

        Returns:
            DataFrame of matching roads
        """
        df = self.traffic
        matches = df[
            (df['road_name'].str.upper().str.contains(query.upper(), na=False)) |
            (df['route_name'].str.upper().str.contains(query.upper(), na=False))
        ].copy()

        # Group by road name and get max ADT
        if len(matches) > 0:
            grouped = matches.groupby('road_name').agg({
                'adt': 'max',
                'route_name': 'first',
                'traffic_level': 'first'
            }).reset_index()
            return grouped.nlargest(limit, 'adt')

        return pd.DataFrame()

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about traffic data.

        Returns:
            Dict with dataset statistics
        """
        df = self.traffic

        # Traffic level distribution
        level_counts = df['traffic_level'].value_counts().to_dict()

        # ADT statistics
        adt_stats = {
            'min': int(df['adt'].min()),
            'max': int(df['adt'].max()),
            'mean': int(df['adt'].mean()),
            'median': int(df['adt'].median())
        }

        # Top roads by ADT
        top_roads = df.groupby('road_name')['adt'].max().nlargest(10).to_dict()

        # Data quality distribution
        quality_counts = df['data_quality'].value_counts().to_dict()

        # Geographic bounds
        bounds = {
            'min_latitude': round(df['latitude'].min(), 4),
            'max_latitude': round(df['latitude'].max(), 4),
            'min_longitude': round(df['longitude'].min(), 4),
            'max_longitude': round(df['longitude'].max(), 4)
        }

        return {
            'total_road_segments': len(df),
            'unique_roads': df['road_name'].nunique(),
            'traffic_levels': level_counts,
            'adt_statistics': adt_stats,
            'top_roads': top_roads,
            'data_quality': quality_counts,
            'geographic_bounds': bounds,
            'data_source': 'Virginia Department of Transportation (VDOT) Traffic Counts',
            'county': 'Fairfax County, VA'
        }


def example_usage():
    """Example usage of FairfaxTrafficAnalysis."""

    print("=" * 70)
    print("FAIRFAX TRAFFIC ANALYSIS - Example Usage")
    print("=" * 70)

    analyzer = FairfaxTrafficAnalysis()
    stats = analyzer.get_statistics()

    print(f"\nLoaded {stats['total_road_segments']} road segments with traffic data")
    print(f"ADT range: {stats['adt_statistics']['min']:,} - {stats['adt_statistics']['max']:,}")
    print(f"\nTraffic level distribution: {stats['traffic_levels']}")

    # Example location (Fairfax City)
    test_lat = 38.8462
    test_lon = -77.3064

    print(f"\nAnalyzing location: {test_lat}, {test_lon} (Fairfax City)")

    # Traffic exposure score
    print("\n--- Traffic Exposure Score ---")
    exposure = analyzer.calculate_traffic_exposure_score(test_lat, test_lon)
    print(f"Score: {exposure['score']}/100 ({exposure['rating']})")
    print(f"Nearest road: {exposure['nearest_road']} ({exposure['nearest_adt']:,} ADT)")
    print(f"Distance: {exposure['nearest_distance_miles']} mi")
    print(f"Analysis: {exposure['analysis']}")

    # Nearby traffic
    print("\n--- Nearby Traffic ---")
    nearby = analyzer.get_nearby_traffic(test_lat, test_lon, radius_miles=0.5)
    for road in nearby[:5]:
        print(f"  {road['road_name']}: {road['adt']:,} ADT ({road['distance_miles']} mi)")

    # Commute analysis
    print("\n--- Commute Corridor Analysis (East) ---")
    commute = analyzer.analyze_commute_corridor(test_lat, test_lon, "east")
    for corridor in commute['corridors'][:3]:
        print(f"  {corridor['corridor']}: max {corridor['max_adt']:,} ADT")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
