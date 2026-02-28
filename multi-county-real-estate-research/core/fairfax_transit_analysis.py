"""
Fairfax County Transit Analysis Module

Provides transit accessibility scoring, Metro station proximity, and
bus route coverage for properties in Fairfax County.

Usage:
    from core.fairfax_transit_analysis import FairfaxTransitAnalysis

    analyzer = FairfaxTransitAnalysis()
    score = analyzer.calculate_transit_score(lat=38.8969, lon=-77.4327)
    metro = analyzer.get_nearest_metro_station(lat=38.8969, lon=-77.4327)
"""

import geopandas as gpd
import math
import os
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import Point
from shapely.ops import nearest_points

try:
    import googlemaps
    _GOOGLEMAPS_AVAILABLE = True
except ImportError:
    _GOOGLEMAPS_AVAILABLE = False


# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "transit" / "processed"


class FairfaxTransitAnalysis:
    """
    Fairfax County transit analysis for property assessment.

    Provides transit scoring, Metro access, and bus route coverage.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with transit data.

        Args:
            data_dir: Optional path to processed transit directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.bus_routes = self._load_bus_routes()
        self.metro_lines = self._load_metro_lines()
        self.metro_stations = self._load_metro_stations()

        # Spatial indices (lazy-loaded)
        self._bus_sindex = None
        self._metro_lines_sindex = None

    def _load_bus_routes(self) -> gpd.GeoDataFrame:
        """Load Fairfax Connector bus routes."""
        path = self.data_dir / "bus_routes.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Bus routes data not found at {path}")

        gdf = gpd.read_parquet(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    def _load_metro_lines(self) -> gpd.GeoDataFrame:
        """Load Metro rail lines."""
        path = self.data_dir / "metro_lines.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Metro lines data not found at {path}")

        gdf = gpd.read_parquet(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    def _load_metro_stations(self) -> gpd.GeoDataFrame:
        """Load Metro stations."""
        path = self.data_dir / "metro_stations.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Metro stations data not found at {path}")

        gdf = gpd.read_parquet(path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    @property
    def bus_sindex(self):
        """Lazy-load spatial index for bus routes."""
        if self._bus_sindex is None:
            self._bus_sindex = self.bus_routes.sindex
        return self._bus_sindex

    @property
    def metro_lines_sindex(self):
        """Lazy-load spatial index for metro lines."""
        if self._metro_lines_sindex is None:
            self._metro_lines_sindex = self.metro_lines.sindex
        return self._metro_lines_sindex

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

    def _get_driving_distance(self, origin_lat: float, origin_lon: float,
                              dest_lat: float, dest_lon: float) -> Optional[float]:
        """Get driving distance in miles via Google Distance Matrix API.

        Returns driving distance in miles, or None if unavailable.
        """
        if not _GOOGLEMAPS_AVAILABLE:
            return None

        from core.api_config import get_api_key
        api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return None

        try:
            gmaps = googlemaps.Client(key=api_key)
            result = gmaps.distance_matrix(
                origins=[f"{origin_lat},{origin_lon}"],
                destinations=[f"{dest_lat},{dest_lon}"],
                mode="driving"
            )
            element = result['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                distance_meters = element['distance']['value']
                return round(distance_meters / 1609.34, 1)
        except Exception:
            pass

        return None

    def get_nearest_metro_station(self, lat: float, lon: float) -> Dict:
        """
        Find the closest Metro station.

        Uses Haversine to identify the nearest station, then attempts to
        get actual driving distance via Google Distance Matrix API.
        Falls back to Haversine if the API is unavailable.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with nearest station information
        """
        if lat is None or lon is None:
            return {
                'station_name': None,
                'distance_miles': None,
                'latitude': None,
                'longitude': None,
                'year_opened': None,
                'walk_time_minutes': None,
                'bike_time_minutes': None,
                'message': 'Invalid coordinates provided'
            }

        # Calculate Haversine distance to all stations to find nearest
        distances = []
        for idx, row in self.metro_stations.iterrows():
            station_lat = row['latitude']
            station_lon = row['longitude']
            distance = self._haversine_distance(lat, lon, station_lat, station_lon)
            distances.append({
                'station_name': row['station_name'],
                'distance': distance,
                'latitude': station_lat,
                'longitude': station_lon,
                'year_opened': row.get('year_opened')
            })

        # Find nearest by straight-line distance
        distances.sort(key=lambda x: x['distance'])
        nearest = distances[0]

        # Try to get actual driving distance via Google Distance Matrix API
        driving_distance = self._get_driving_distance(
            lat, lon, nearest['latitude'], nearest['longitude']
        )
        final_distance = driving_distance if driving_distance is not None else nearest['distance']

        # Calculate walk/bike times based on final distance
        # Walk: 3 mph average
        # Bike: 12 mph average
        walk_time = (final_distance / 3.0) * 60  # minutes
        bike_time = (final_distance / 12.0) * 60  # minutes

        return {
            'station_name': nearest['station_name'],
            'distance_miles': round(final_distance, 2),
            'latitude': round(nearest['latitude'], 4),
            'longitude': round(nearest['longitude'], 4),
            'year_opened': nearest['year_opened'],
            'walk_time_minutes': round(walk_time),
            'bike_time_minutes': round(bike_time),
            'message': ''
        }

    def get_nearby_bus_routes(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 0.25,
        service_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find Fairfax Connector routes within radius.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 0.25 miles)
            service_types: Optional filter (Local, Express, Circulator, Feeder)
            limit: Maximum results (default: 10)

        Returns:
            List of nearby bus routes sorted by distance
        """
        if lat is None or lon is None:
            return []

        bounds = self._get_buffer_bounds(lat, lon, radius_miles)
        possible_idx = list(self.bus_sindex.intersection(bounds))

        if not possible_idx:
            return []

        candidates = self.bus_routes.iloc[possible_idx].copy()

        # Apply service type filter
        if service_types:
            types_lower = [t.lower() for t in service_types]
            candidates = candidates[candidates['service_type'].str.lower().isin(types_lower)]

        if len(candidates) == 0:
            return []

        results = []
        for idx, row in candidates.iterrows():
            distance = self._calculate_distance_to_geometry(lat, lon, row.geometry)

            if distance <= radius_miles:
                results.append({
                    'route_number': row['route_number'],
                    'route_name': row['route_name'],
                    'service_type': row['service_type'],
                    'division': row['division'],
                    'distance_miles': round(distance, 2),
                    'schedule_url': row.get('schedule_url')
                })

        results.sort(key=lambda x: x['distance_miles'])
        return results[:limit]

    def get_metro_lines_nearby(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0
    ) -> List[Dict]:
        """
        Find Metro lines within radius.

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius (default: 1.0 mile)

        Returns:
            List of nearby Metro lines with station info
        """
        if lat is None or lon is None:
            return []

        bounds = self._get_buffer_bounds(lat, lon, radius_miles)
        possible_idx = list(self.metro_lines_sindex.intersection(bounds))

        if not possible_idx:
            return []

        candidates = self.metro_lines.iloc[possible_idx]

        # Group by line name
        lines_found = {}
        for idx, row in candidates.iterrows():
            distance = self._calculate_distance_to_geometry(lat, lon, row.geometry)

            if distance <= radius_miles:
                line_name = row['line_name']
                if line_name not in lines_found or distance < lines_found[line_name]['distance']:
                    lines_found[line_name] = {
                        'line_name': line_name,
                        'line_color': row.get('line_color'),
                        'distance_miles': distance,
                        'stations': [row.get('from_station'), row.get('to_station')]
                    }

        # Get nearby stations for each line
        results = []
        for line_name, line_data in lines_found.items():
            # Find stations for this line
            line_stations = self.metro_stations[
                self.metro_stations['station_name'].str.upper().isin(
                    [s.upper() for s in line_data['stations'] if s]
                )
            ]['station_name'].tolist()

            results.append({
                'line_name': line_data['line_name'],
                'line_color': line_data['line_color'],
                'distance_miles': round(line_data['distance_miles'], 2),
                'nearest_stations': line_data['stations']
            })

        results.sort(key=lambda x: x['distance_miles'])
        return results

    def calculate_transit_score(self, lat: float, lon: float) -> Dict:
        """
        Calculate comprehensive transit accessibility score.

        Scoring (100 points total):
        - Metro access (50 pts): Distance to nearest station
        - Bus coverage (30 pts): Routes within 0.25 miles
        - Service variety (20 pts): Types of service available

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
                'nearest_metro_distance': None,
                'metro_walk_time': None,
                'bus_routes_within_quarter_mi': 0,
                'service_types_available': [],
                'breakdown': {
                    'metro_access': 0,
                    'bus_coverage': 0,
                    'service_variety': 0
                },
                'message': 'Invalid coordinates provided'
            }

        # Get Metro info
        nearest_metro = self.get_nearest_metro_station(lat, lon)

        # Get bus routes
        bus_routes = self.get_nearby_bus_routes(lat, lon, radius_miles=0.25, limit=20)

        # 1. Metro Access Score (50 pts)
        metro_distance = nearest_metro['distance_miles']
        if metro_distance is None:
            metro_score = 0
        elif metro_distance <= 0.5:
            metro_score = 50
        elif metro_distance <= 1.0:
            metro_score = 40
        elif metro_distance <= 2.0:
            metro_score = 25
        elif metro_distance <= 3.0:
            metro_score = 10
        else:
            metro_score = 0

        # 2. Bus Coverage Score (30 pts)
        num_routes = len(bus_routes)
        bus_score = min(30, num_routes * 10)

        # 3. Service Variety Score (20 pts)
        service_types = list(set(r['service_type'] for r in bus_routes))
        variety_score = 0

        if 'Express' in service_types:
            variety_score += 10
        if 'Circulator' in service_types:
            variety_score += 5
        if len(service_types) > 1:
            variety_score += 5

        # Total score
        total_score = metro_score + bus_score + variety_score

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
            'nearest_metro_distance': metro_distance,
            'metro_walk_time': nearest_metro['walk_time_minutes'],
            'bus_routes_within_quarter_mi': num_routes,
            'service_types_available': service_types,
            'breakdown': {
                'metro_access': metro_score,
                'bus_coverage': bus_score,
                'service_variety': variety_score
            },
            'message': ''
        }

    def get_commute_options(self, lat: float, lon: float) -> Dict:
        """
        Get summary of all transit options for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with Metro and bus options summary
        """
        if lat is None or lon is None:
            return {
                'metro': None,
                'bus': None,
                'overall_accessibility': 'unknown',
                'message': 'Invalid coordinates provided'
            }

        # Metro info
        nearest_metro = self.get_nearest_metro_station(lat, lon)

        # Bus info
        bus_routes = self.get_nearby_bus_routes(lat, lon, radius_miles=0.25, limit=20)

        # Determine accessibility
        metro_accessible = nearest_metro['distance_miles'] is not None and nearest_metro['distance_miles'] <= 2.0
        bus_accessible = len(bus_routes) > 0

        if metro_accessible and bus_accessible:
            accessibility = 'excellent'
        elif metro_accessible or len(bus_routes) >= 2:
            accessibility = 'good'
        elif bus_accessible:
            accessibility = 'fair'
        else:
            accessibility = 'poor'

        return {
            'metro': {
                'nearest_station': nearest_metro['station_name'],
                'distance_miles': nearest_metro['distance_miles'],
                'walk_time_minutes': nearest_metro['walk_time_minutes'],
                'accessible': metro_accessible
            },
            'bus': {
                'routes_count': len(bus_routes),
                'service_types': list(set(r['service_type'] for r in bus_routes)),
                'closest_route': {
                    'route_number': bus_routes[0]['route_number'],
                    'route_name': bus_routes[0]['route_name'],
                    'distance_miles': bus_routes[0]['distance_miles']
                } if bus_routes else None
            },
            'overall_accessibility': accessibility,
            'message': ''
        }

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the transit dataset.

        Returns:
            Dict with dataset statistics
        """
        # Bus route stats
        bus_by_type = self.bus_routes['service_type'].value_counts().to_dict()
        bus_by_division = self.bus_routes['division'].value_counts().to_dict()

        # Metro stats
        metro_lines = self.metro_lines['line_name'].unique().tolist()

        # Station stats
        station_years = self.metro_stations['year_opened'].unique().tolist()

        return {
            'bus_routes': {
                'total': len(self.bus_routes),
                'by_service_type': bus_by_type,
                'by_division': bus_by_division
            },
            'metro_lines': {
                'total_segments': len(self.metro_lines),
                'lines': metro_lines
            },
            'metro_stations': {
                'total': len(self.metro_stations),
                'oldest_year': min(station_years) if station_years else None,
                'newest_year': max(station_years) if station_years else None
            }
        }


def example_usage():
    """Example usage of FairfaxTransitAnalysis."""

    print("=" * 70)
    print("FAIRFAX TRANSIT ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxTransitAnalysis()
    stats = analyzer.get_statistics()
    print(f"\nLoaded {stats['bus_routes']['total']} bus routes")
    print(f"Loaded {stats['metro_lines']['total_segments']} Metro line segments")
    print(f"Loaded {stats['metro_stations']['total']} Metro stations")

    # Test location near Vienna Metro
    test_lat = 38.8777
    test_lon = -77.2714

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Transit score
    print("\n--- Transit Score ---")
    score = analyzer.calculate_transit_score(test_lat, test_lon)
    print(f"  Score: {score['score']}/100 ({score['rating']})")
    print(f"  Metro distance: {score['nearest_metro_distance']} mi")
    print(f"  Walk time: {score['metro_walk_time']} min")
    print(f"  Bus routes: {score['bus_routes_within_quarter_mi']}")
    print(f"  Breakdown: {score['breakdown']}")

    # Nearest Metro
    print("\n--- Nearest Metro ---")
    metro = analyzer.get_nearest_metro_station(test_lat, test_lon)
    print(f"  Station: {metro['station_name']}")
    print(f"  Distance: {metro['distance_miles']} mi")
    print(f"  Walk time: {metro['walk_time_minutes']} min")
    print(f"  Bike time: {metro['bike_time_minutes']} min")

    # Bus routes
    print("\n--- Nearby Bus Routes ---")
    routes = analyzer.get_nearby_bus_routes(test_lat, test_lon, radius_miles=0.5, limit=5)
    for route in routes[:3]:
        print(f"  Route {route['route_number']}: {route['route_name']} ({route['service_type']})")

    # Commute options
    print("\n--- Commute Options ---")
    commute = analyzer.get_commute_options(test_lat, test_lon)
    print(f"  Metro accessible: {commute['metro']['accessible']}")
    print(f"  Bus routes: {commute['bus']['routes_count']}")
    print(f"  Overall: {commute['overall_accessibility']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
