"""
Fairfax County Parks Analysis Module

Provides park access scoring, trail network analysis, and recreational
amenity queries for properties in Fairfax County.

Usage:
    from core.fairfax_parks_analysis import FairfaxParksAnalysis

    analyzer = FairfaxParksAnalysis()
    score = analyzer.calculate_park_access_score(lat=38.8969, lon=-77.4327)
    print(f"Park Access Score: {score['score']}/100 ({score['rating']})")
"""

import geopandas as gpd
import math
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import Point
from shapely.ops import nearest_points


# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "parks" / "processed"


class FairfaxParksAnalysis:
    """
    Fairfax County parks analysis for property assessment.

    Provides park access scoring, trail network queries, and recreational
    amenity searches.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with parks data.

        Args:
            data_dir: Optional path to processed parks directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.parks = self._load_parks()
        self.trails = self._load_trails()
        self.recreation = self._load_recreation()

        # Spatial indices (lazy-loaded)
        self._parks_sindex = None
        self._trails_sindex = None
        self._recreation_sindex = None

    def _load_parks(self) -> gpd.GeoDataFrame:
        """Load parks data."""
        path = self.data_dir / "parks.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Parks data not found at {path}")

        gdf = gpd.read_parquet(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    def _load_trails(self) -> gpd.GeoDataFrame:
        """Load trails data."""
        path = self.data_dir / "trails.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Trails data not found at {path}")

        gdf = gpd.read_parquet(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    def _load_recreation(self) -> gpd.GeoDataFrame:
        """Load recreational features data."""
        path = self.data_dir / "recreation.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Recreation data not found at {path}")

        gdf = gpd.read_parquet(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    @property
    def parks_sindex(self):
        """Lazy-load spatial index for parks."""
        if self._parks_sindex is None:
            self._parks_sindex = self.parks.sindex
        return self._parks_sindex

    @property
    def trails_sindex(self):
        """Lazy-load spatial index for trails."""
        if self._trails_sindex is None:
            self._trails_sindex = self.trails.sindex
        return self._trails_sindex

    @property
    def recreation_sindex(self):
        """Lazy-load spatial index for recreation."""
        if self._recreation_sindex is None:
            self._recreation_sindex = self.recreation.sindex
        return self._recreation_sindex

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

    def _get_buffer_bounds(self, lat: float, lon: float, radius_miles: float):
        """Get bounding box for spatial query."""
        buffer_deg = radius_miles / 69.0
        return (lon - buffer_deg, lat - buffer_deg, lon + buffer_deg, lat + buffer_deg)

    def _calculate_distance_to_geometry(self, lat: float, lon: float, geometry) -> float:
        """Calculate distance from point to nearest point on geometry."""
        point = Point(lon, lat)
        nearest_geom = nearest_points(point, geometry)[1]
        return self._haversine_distance(lat, lon, nearest_geom.y, nearest_geom.x)

    def get_nearby_parks(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        jurisdiction: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find parks within radius of a location.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 1.0 mile)
            jurisdiction: Optional filter (county, nova_parks, etc.)
            limit: Maximum results (default: 10)

        Returns:
            List of nearby parks sorted by distance
        """
        if lat is None or lon is None:
            return []

        bounds = self._get_buffer_bounds(lat, lon, radius_miles)
        possible_idx = list(self.parks_sindex.intersection(bounds))

        if not possible_idx:
            return []

        candidates = self.parks.iloc[possible_idx].copy()

        # Apply jurisdiction filter
        if jurisdiction:
            candidates = candidates[candidates['jurisdiction'].str.lower() == jurisdiction.lower()]

        if len(candidates) == 0:
            return []

        results = []
        for idx, row in candidates.iterrows():
            distance = self._calculate_distance_to_geometry(lat, lon, row.geometry)

            if distance <= radius_miles:
                results.append({
                    'park_name': row['park_name'],
                    'park_class': row.get('park_class'),
                    'jurisdiction': row['jurisdiction'],
                    'area_acres': round(row['area_acres'], 1) if row.get('area_acres') else None,
                    'distance_miles': round(distance, 2),
                    'supervisor_district': row.get('supervisor_district')
                })

        results.sort(key=lambda x: x['distance_miles'])
        return results[:limit]

    def get_trail_access(self, lat: float, lon: float, radius_miles: float = 1.0) -> Dict:
        """
        Calculate trail accessibility for a location.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 1.0 mile)

        Returns:
            Dict with trail access information
        """
        if lat is None or lon is None:
            return {
                'trails_within_radius': 0,
                'total_trail_miles': 0,
                'closest_trail_distance': None,
                'surface_types': {},
                'ada_accessible_trails': 0,
                'message': 'Invalid coordinates provided'
            }

        bounds = self._get_buffer_bounds(lat, lon, radius_miles)
        possible_idx = list(self.trails_sindex.intersection(bounds))

        if not possible_idx:
            return {
                'trails_within_radius': 0,
                'total_trail_miles': 0,
                'closest_trail_distance': None,
                'surface_types': {},
                'ada_accessible_trails': 0,
                'message': None
            }

        candidates = self.trails.iloc[possible_idx]

        # Calculate distances and filter
        trail_data = []
        for idx, row in candidates.iterrows():
            distance = self._calculate_distance_to_geometry(lat, lon, row.geometry)
            if distance <= radius_miles:
                trail_data.append({
                    'distance': distance,
                    'length_miles': row.get('length_miles', 0),
                    'surface': row.get('surface_material'),
                    'ada': row.get('ada_accessible')
                })

        if not trail_data:
            return {
                'trails_within_radius': 0,
                'total_trail_miles': 0,
                'closest_trail_distance': None,
                'surface_types': {},
                'ada_accessible_trails': 0,
                'message': None
            }

        # Aggregate results
        surface_types = {}
        ada_count = 0
        total_miles = 0
        closest_distance = None

        for trail in trail_data:
            total_miles += trail['length_miles'] or 0

            if trail['surface']:
                surface = trail['surface']
                surface_types[surface] = surface_types.get(surface, 0) + (trail['length_miles'] or 0)

            if trail['ada'] and str(trail['ada']).upper() in ['Y', 'YES', 'TRUE']:
                ada_count += 1

            if closest_distance is None or trail['distance'] < closest_distance:
                closest_distance = trail['distance']

        # Round surface type values
        surface_types = {k: round(v, 1) for k, v in surface_types.items()}

        return {
            'trails_within_radius': len(trail_data),
            'total_trail_miles': round(total_miles, 1),
            'closest_trail_distance': round(closest_distance, 2) if closest_distance else None,
            'surface_types': surface_types,
            'ada_accessible_trails': ada_count,
            'message': None
        }

    def get_recreational_amenities(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.5,
        amenity_types: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Find recreational amenities within radius.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.5 miles)
            amenity_types: Optional filter (PLAYGROUND, BASKETBALL COURT, etc.)
            limit: Maximum results (default: 20)

        Returns:
            List of nearby amenities sorted by distance
        """
        if lat is None or lon is None:
            return []

        bounds = self._get_buffer_bounds(lat, lon, radius_miles)
        possible_idx = list(self.recreation_sindex.intersection(bounds))

        if not possible_idx:
            return []

        candidates = self.recreation.iloc[possible_idx].copy()

        # Apply amenity type filter
        if amenity_types:
            types_upper = [t.upper() for t in amenity_types]
            candidates = candidates[candidates['feature_type'].str.upper().isin(types_upper)]

        if len(candidates) == 0:
            return []

        results = []
        for idx, row in candidates.iterrows():
            distance = self._calculate_distance_to_geometry(lat, lon, row.geometry)

            if distance <= radius_miles:
                results.append({
                    'feature_type': row['feature_type'],
                    'area_sqft': round(row.get('area_sqft', 0), 0) if row.get('area_sqft') else None,
                    'distance_miles': round(distance, 2),
                    'centroid_lat': round(row.get('centroid_lat', 0), 4) if row.get('centroid_lat') else None,
                    'centroid_lon': round(row.get('centroid_lon', 0), 4) if row.get('centroid_lon') else None
                })

        results.sort(key=lambda x: x['distance_miles'])
        return results[:limit]

    def calculate_park_access_score(self, lat: float, lon: float) -> Dict:
        """
        Calculate comprehensive park access score.

        Scoring (100 points total):
        - Park proximity (30 pts): Distance to nearest park
        - Trail access (25 pts): Trail miles within 1 mile
        - Amenities (20 pts): Playgrounds/courts within 0.5 mile
        - Variety (25 pts): Diversity of park sizes and types

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with score and breakdown
        """
        if lat is None or lon is None:
            return {
                'score': 0,
                'rating': 'unknown',
                'parks_within_1mi': 0,
                'parks_within_3mi': 0,
                'trail_miles_within_1mi': 0,
                'playgrounds_within_half_mi': 0,
                'closest_park_distance': None,
                'breakdown': {
                    'park_proximity': 0,
                    'trail_access': 0,
                    'amenities': 0,
                    'park_variety': 0
                },
                'message': 'Invalid coordinates provided'
            }

        # Get data for scoring
        parks_1mi = self.get_nearby_parks(lat, lon, radius_miles=1.0, limit=50)
        parks_3mi = self.get_nearby_parks(lat, lon, radius_miles=3.0, limit=100)
        trail_access = self.get_trail_access(lat, lon, radius_miles=1.0)
        playgrounds = self.get_recreational_amenities(lat, lon, radius_miles=0.5, amenity_types=['PLAYGROUND'], limit=50)
        courts = self.get_recreational_amenities(lat, lon, radius_miles=0.5, amenity_types=['BASKETBALL COURT', 'TENNIS COURT'], limit=50)

        # 1. Park Proximity Score (30 pts)
        closest_distance = parks_1mi[0]['distance_miles'] if parks_1mi else None
        if not closest_distance:
            # Check further out
            if parks_3mi:
                closest_distance = parks_3mi[0]['distance_miles']

        if closest_distance is None:
            proximity_score = 0
        elif closest_distance <= 0.5:
            proximity_score = 30
        elif closest_distance <= 1.0:
            proximity_score = 20
        elif closest_distance <= 2.0:
            proximity_score = 10
        else:
            proximity_score = 0

        # 2. Trail Access Score (25 pts)
        trail_miles = trail_access['total_trail_miles']
        if trail_miles >= 5:
            trail_score = 25
        elif trail_miles >= 3:
            trail_score = 20
        elif trail_miles >= 1:
            trail_score = 15
        elif trail_miles > 0:
            trail_score = 10
        else:
            trail_score = 0

        # 3. Amenities Score (20 pts)
        playground_count = len(playgrounds)
        court_count = len(courts)
        amenity_score = min(20, playground_count * 5 + court_count * 3)

        # 4. Variety Score (25 pts)
        variety_score = 0
        if parks_3mi:
            # Diversity of park sizes
            areas = [p['area_acres'] for p in parks_3mi if p.get('area_acres')]
            if areas:
                small = sum(1 for a in areas if a < 10)
                medium = sum(1 for a in areas if 10 <= a < 50)
                large = sum(1 for a in areas if a >= 50)

                if small > 0:
                    variety_score += 5
                if medium > 0:
                    variety_score += 8
                if large > 0:
                    variety_score += 7

            # Diversity of jurisdictions
            jurisdictions = set(p['jurisdiction'] for p in parks_3mi)
            variety_score += min(5, len(jurisdictions) * 2)

        # Calculate total score
        total_score = proximity_score + trail_score + amenity_score + variety_score

        # Determine rating
        if total_score >= 80:
            rating = 'excellent'
        elif total_score >= 60:
            rating = 'good'
        elif total_score >= 40:
            rating = 'fair'
        else:
            rating = 'poor'

        return {
            'score': round(total_score, 1),
            'rating': rating,
            'parks_within_1mi': len(parks_1mi),
            'parks_within_3mi': len(parks_3mi),
            'trail_miles_within_1mi': trail_access['total_trail_miles'],
            'playgrounds_within_half_mi': len(playgrounds),
            'closest_park_distance': closest_distance,
            'breakdown': {
                'park_proximity': proximity_score,
                'trail_access': trail_score,
                'amenities': amenity_score,
                'park_variety': variety_score
            },
            'message': None
        }

    def search_parks(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search parks by name.

        Args:
            query: Search string (case-insensitive)
            limit: Maximum results (default: 10)

        Returns:
            List of matching parks
        """
        if not query:
            return []

        mask = self.parks['park_name'].str.upper().str.contains(query.upper(), na=False)
        matches = self.parks[mask].head(limit)

        results = []
        for idx, row in matches.iterrows():
            results.append({
                'park_name': row['park_name'],
                'park_class': row.get('park_class'),
                'jurisdiction': row['jurisdiction'],
                'area_acres': round(row['area_acres'], 1) if row.get('area_acres') else None,
                'supervisor_district': row.get('supervisor_district')
            })

        return results

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the parks dataset.

        Returns:
            Dict with dataset statistics
        """
        # Parks stats
        parks_by_jurisdiction = self.parks['jurisdiction'].value_counts().to_dict()
        parks_by_class = self.parks['park_class'].value_counts().to_dict() if 'park_class' in self.parks.columns else {}

        # Trail stats
        total_trail_miles = self.trails['length_miles'].sum() if 'length_miles' in self.trails.columns else 0
        trail_surfaces = self.trails['surface_material'].value_counts().to_dict() if 'surface_material' in self.trails.columns else {}

        # Recreation stats
        recreation_types = self.recreation['feature_type'].value_counts().head(10).to_dict()

        return {
            'parks': {
                'total': len(self.parks),
                'by_jurisdiction': parks_by_jurisdiction,
                'by_class': parks_by_class
            },
            'trails': {
                'total_segments': len(self.trails),
                'total_miles': round(total_trail_miles, 1),
                'by_surface': trail_surfaces
            },
            'recreation': {
                'total_features': len(self.recreation),
                'top_types': recreation_types
            }
        }


def example_usage():
    """Example usage of FairfaxParksAnalysis."""

    print("=" * 70)
    print("FAIRFAX PARKS ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxParksAnalysis()
    stats = analyzer.get_statistics()
    print(f"\nLoaded {stats['parks']['total']} parks")
    print(f"Loaded {stats['trails']['total_segments']} trail segments ({stats['trails']['total_miles']} miles)")
    print(f"Loaded {stats['recreation']['total_features']} recreational features")

    # Test location
    test_lat = 38.8462
    test_lon = -77.3064

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Park access score
    print("\n--- Park Access Score ---")
    score = analyzer.calculate_park_access_score(test_lat, test_lon)
    print(f"  Score: {score['score']}/100 ({score['rating']})")
    print(f"  Parks within 1 mi: {score['parks_within_1mi']}")
    print(f"  Trail miles within 1 mi: {score['trail_miles_within_1mi']}")
    print(f"  Playgrounds within 0.5 mi: {score['playgrounds_within_half_mi']}")
    print(f"  Breakdown: {score['breakdown']}")

    # Nearby parks
    print("\n--- Nearby Parks ---")
    nearby = analyzer.get_nearby_parks(test_lat, test_lon, radius_miles=1.0, limit=5)
    for park in nearby[:3]:
        print(f"  {park['park_name']}: {park['distance_miles']} mi ({park['jurisdiction']})")

    # Trail access
    print("\n--- Trail Access ---")
    trails = analyzer.get_trail_access(test_lat, test_lon, radius_miles=1.0)
    print(f"  Trails within 1 mi: {trails['trails_within_radius']}")
    print(f"  Total miles: {trails['total_trail_miles']}")
    print(f"  Closest trail: {trails['closest_trail_distance']} mi")

    # Recreational amenities
    print("\n--- Playgrounds Nearby ---")
    playgrounds = analyzer.get_recreational_amenities(test_lat, test_lon, radius_miles=0.5, amenity_types=['PLAYGROUND'], limit=5)
    print(f"  Found {len(playgrounds)} playgrounds within 0.5 mi")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
