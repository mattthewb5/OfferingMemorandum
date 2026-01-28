"""
Fairfax County Emergency Services Analysis Module

Provides emergency services proximity analysis with fire protection assessment
based on Insurance Services Office (ISO) Fire Protection Class standards.

Fire Protection Assessment:
    Based on ISO Public Protection Classification (PPC) standards used by
    approximately 75% of U.S. insurance companies to determine homeowners
    insurance rates.

    Key ISO Standard: Properties located more than 5 road miles from a fire
    station automatically receive ISO Class 10 rating (highest risk, highest
    insurance premiums).

    ISO Classes range from 1 (superior fire protection) to 10 (inadequate
    fire protection). Distance to nearest fire station is a primary factor
    in determining classification.

References:
    - Insurance Services Office (ISO) Public Protection Classification
    - Fire Suppression Rating Schedule (FSRS)
    - ISO Mitigation (Verisk Analytics)

Data:
    - Fire Stations: 47 stations (Fairfax County, Fort Belvoir, City of Fairfax)
    - Police Stations: 23 stations/facilities

Usage:
    from core.fairfax_emergency_services_analysis import FairfaxEmergencyServicesAnalysis

    analyzer = FairfaxEmergencyServicesAnalysis()

    # Get fire protection assessment (ISO-based)
    fire_assessment = analyzer.assess_fire_protection_iso(lat=38.9188, lon=-77.2311)
    print(f"Fire Protection: {fire_assessment['rating']}")
    print(f"ISO Status: {fire_assessment['iso_threshold_status']}")
    print(f"Insurance Impact: {fire_assessment['insurance_impact']}")

    # Get nearest stations
    fire = analyzer.get_nearest_fire_station(38.9188, -77.2311)
    police = analyzer.get_nearest_police_station(38.9188, -77.2311)
"""

import geopandas as gpd
import math
from pathlib import Path
from typing import Dict, List, Optional


# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "emergency_services" / "processed"


class FairfaxEmergencyServicesAnalysis:
    """
    Fairfax County emergency services analysis for property assessment.

    Provides fire and police station proximity analysis with fire protection
    assessment based on ISO (Insurance Services Office) standards.

    ISO Fire Protection Class Background:
        The Insurance Services Office (ISO) evaluates fire protection for
        communities nationwide. Approximately 75% of U.S. insurance companies
        use ISO's Public Protection Classification (PPC) system to determine
        homeowners insurance rates.

        Key ISO Standard: Properties located MORE THAN 5 ROAD MILES from a
        fire station automatically receive ISO Class 10 rating (worst rating,
        highest insurance premiums).
    """

    # ISO threshold constant - properties beyond this distance get Class 10
    ISO_DISTANCE_THRESHOLD_MILES = 5.0

    # Average emergency vehicle speed for response time estimates (mph)
    EMERGENCY_VEHICLE_SPEED_MPH = 20.0

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with emergency services data.

        Args:
            data_dir: Optional path to processed emergency services directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.fire_stations = self._load_fire_stations()
        self.police_stations = self._load_police_stations()

    def _load_fire_stations(self) -> gpd.GeoDataFrame:
        """Load fire stations from parquet."""
        fire_path = self.data_dir / "fire_stations.parquet"
        if not fire_path.exists():
            raise FileNotFoundError(f"Fire stations data not found: {fire_path}")

        gdf = gpd.read_parquet(fire_path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    def _load_police_stations(self) -> gpd.GeoDataFrame:
        """Load police stations from parquet."""
        police_path = self.data_dir / "police_stations.parquet"
        if not police_path.exists():
            raise FileNotFoundError(f"Police stations data not found: {police_path}")

        gdf = gpd.read_parquet(police_path)
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)
        return gdf

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance between two points in miles.

        Uses Haversine formula for accurate distance calculation on Earth's surface.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in miles
        """
        R = 3959  # Earth radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def _calculate_drive_time(self, distance_miles: float) -> int:
        """
        Calculate estimated drive time for emergency vehicles.

        Args:
            distance_miles: Distance in miles

        Returns:
            Estimated drive time in minutes (rounded up)
        """
        if distance_miles <= 0:
            return 1  # Minimum 1 minute
        time_hours = distance_miles / self.EMERGENCY_VEHICLE_SPEED_MPH
        time_minutes = math.ceil(time_hours * 60)
        return max(1, time_minutes)  # Minimum 1 minute

    def get_nearest_fire_station(self, lat: float, lon: float) -> Dict:
        """
        Find nearest fire station to given coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with nearest fire station details and distance
        """
        # Validate coordinates
        if lat is None or lon is None:
            return {
                'station_name': None,
                'station_full_name': None,
                'station_code': None,
                'address': None,
                'distance_miles': None,
                'drive_time_minutes': None,
                'latitude': None,
                'longitude': None,
                'jurisdiction': None,
                'error': 'Invalid coordinates provided'
            }

        try:
            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return {
                    'station_name': None,
                    'station_full_name': None,
                    'station_code': None,
                    'address': None,
                    'distance_miles': None,
                    'drive_time_minutes': None,
                    'latitude': None,
                    'longitude': None,
                    'jurisdiction': None,
                    'error': 'Coordinates out of valid range'
                }

            # Calculate distances to all fire stations
            min_distance = float('inf')
            nearest_station = None

            for idx, station in self.fire_stations.iterrows():
                distance = self._haversine_distance(
                    lat, lon,
                    station['latitude'], station['longitude']
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = station

            if nearest_station is None:
                return {
                    'station_name': None,
                    'station_full_name': None,
                    'station_code': None,
                    'address': None,
                    'distance_miles': None,
                    'drive_time_minutes': None,
                    'latitude': None,
                    'longitude': None,
                    'jurisdiction': None,
                    'error': 'No fire stations found'
                }

            return {
                'station_name': nearest_station['station_name'],
                'station_full_name': nearest_station['station_full_name'],
                'station_code': nearest_station['station_code'],
                'address': nearest_station['address'],
                'distance_miles': round(min_distance, 2),
                'drive_time_minutes': self._calculate_drive_time(min_distance),
                'latitude': nearest_station['latitude'],
                'longitude': nearest_station['longitude'],
                'jurisdiction': nearest_station['jurisdiction']
            }

        except Exception as e:
            return {
                'station_name': None,
                'station_full_name': None,
                'station_code': None,
                'address': None,
                'distance_miles': None,
                'drive_time_minutes': None,
                'latitude': None,
                'longitude': None,
                'jurisdiction': None,
                'error': f'Error finding nearest fire station: {str(e)}'
            }

    def get_nearest_police_station(self, lat: float, lon: float) -> Dict:
        """
        Find nearest police station to given coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with nearest police station details and distance
        """
        # Validate coordinates
        if lat is None or lon is None:
            return {
                'station_name': None,
                'address': None,
                'phone': None,
                'distance_miles': None,
                'drive_time_minutes': None,
                'latitude': None,
                'longitude': None,
                'station_type': None,
                'error': 'Invalid coordinates provided'
            }

        try:
            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                return {
                    'station_name': None,
                    'address': None,
                    'phone': None,
                    'distance_miles': None,
                    'drive_time_minutes': None,
                    'latitude': None,
                    'longitude': None,
                    'station_type': None,
                    'error': 'Coordinates out of valid range'
                }

            # Calculate distances to all police stations
            min_distance = float('inf')
            nearest_station = None

            for idx, station in self.police_stations.iterrows():
                distance = self._haversine_distance(
                    lat, lon,
                    station['latitude'], station['longitude']
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = station

            if nearest_station is None:
                return {
                    'station_name': None,
                    'address': None,
                    'phone': None,
                    'distance_miles': None,
                    'drive_time_minutes': None,
                    'latitude': None,
                    'longitude': None,
                    'station_type': None,
                    'error': 'No police stations found'
                }

            return {
                'station_name': nearest_station['station_name'],
                'address': nearest_station['address'],
                'phone': nearest_station['phone'],
                'distance_miles': round(min_distance, 2),
                'drive_time_minutes': self._calculate_drive_time(min_distance),
                'latitude': nearest_station['latitude'],
                'longitude': nearest_station['longitude'],
                'station_type': nearest_station['station_type']
            }

        except Exception as e:
            return {
                'station_name': None,
                'address': None,
                'phone': None,
                'distance_miles': None,
                'drive_time_minutes': None,
                'latitude': None,
                'longitude': None,
                'station_type': None,
                'error': f'Error finding nearest police station: {str(e)}'
            }

    def assess_fire_protection_iso(self, lat: float, lon: float) -> Dict:
        """
        Assess fire protection using ISO-aligned methodology.

        Based on Insurance Services Office (ISO) Fire Protection Class standards
        used by approximately 75% of U.S. insurance companies.

        Key ISO Standard: Properties >5 road miles from fire station automatically
        receive ISO Class 10 rating (highest insurance premiums).

        Rating Tiers:
            - Excellent (<=1 mi): ISO Class 1-3 range, lowest premiums
            - Very Good (1-3 mi): ISO Class 3-5 range, low premiums
            - Good (3-5 mi): ISO Class 5-8 range, within ISO threshold
            - Limited (>5 mi): ISO Class 10, beyond ISO threshold, high premiums

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with ISO-aligned fire protection assessment
        """
        # Validate coordinates
        if lat is None or lon is None:
            return {
                'fire_distance_miles': None,
                'rating': None,
                'iso_class_range': None,
                'iso_threshold_status': None,
                'insurance_impact': None,
                'nearest_station_name': None,
                'nearest_station_address': None,
                'methodology': 'Based on ISO Fire Protection Class standards',
                'error': 'Invalid coordinates provided'
            }

        # Get nearest fire station
        nearest_fire = self.get_nearest_fire_station(lat, lon)

        if nearest_fire.get('error'):
            return {
                'fire_distance_miles': None,
                'rating': None,
                'iso_class_range': None,
                'iso_threshold_status': None,
                'insurance_impact': None,
                'nearest_station_name': None,
                'nearest_station_address': None,
                'methodology': 'Based on ISO Fire Protection Class standards',
                'error': nearest_fire['error']
            }

        fire_distance = nearest_fire['distance_miles']

        # Apply ISO-aligned rating tiers
        if fire_distance <= 1.0:
            rating = 'Excellent'
            iso_class_range = '1-3'
            insurance_impact = 'Lowest premiums - optimal fire protection'
        elif fire_distance <= 3.0:
            rating = 'Very Good'
            iso_class_range = '3-5'
            insurance_impact = 'Low premiums - good fire protection'
        elif fire_distance <= 5.0:
            rating = 'Good'
            iso_class_range = '5-8'
            insurance_impact = 'Moderate premiums - within ISO threshold'
        else:  # > 5.0 miles (CRITICAL ISO THRESHOLD)
            rating = 'Limited'
            iso_class_range = '10'
            insurance_impact = 'High premiums - beyond ISO 5-mile threshold'

        # Determine ISO threshold status
        iso_threshold_status = 'within' if fire_distance <= self.ISO_DISTANCE_THRESHOLD_MILES else 'beyond'

        return {
            'fire_distance_miles': fire_distance,
            'rating': rating,
            'iso_class_range': iso_class_range,
            'iso_threshold_status': iso_threshold_status,
            'insurance_impact': insurance_impact,
            'nearest_station_name': nearest_fire['station_name'],
            'nearest_station_address': nearest_fire['address'],
            'methodology': 'Based on ISO Fire Protection Class standards'
        }

    def get_emergency_services_coverage(
        self,
        lat: float,
        lon: float,
        fire_radius_miles: float = 5.0,
        police_radius_miles: float = 5.0
    ) -> Dict:
        """
        Get emergency services coverage within specified radius.

        Default fire radius is 5.0 miles (ISO standard threshold).

        Args:
            lat: Latitude
            lon: Longitude
            fire_radius_miles: Radius for fire stations (default: 5.0 miles)
            police_radius_miles: Radius for police stations (default: 5.0 miles)

        Returns:
            Dictionary with all stations within radius
        """
        # Validate coordinates
        if lat is None or lon is None:
            return {
                'fire_stations': [],
                'police_stations': [],
                'fire_count': 0,
                'police_count': 0,
                'nearest_fire_distance': None,
                'nearest_police_distance': None,
                'within_iso_threshold': False,
                'error': 'Invalid coordinates provided'
            }

        try:
            # Find fire stations within radius
            fire_stations_nearby = []
            for idx, station in self.fire_stations.iterrows():
                distance = self._haversine_distance(
                    lat, lon,
                    station['latitude'], station['longitude']
                )
                if distance <= fire_radius_miles:
                    fire_stations_nearby.append({
                        'station_name': station['station_name'],
                        'distance_miles': round(distance, 2),
                        'address': station['address']
                    })

            # Sort by distance
            fire_stations_nearby.sort(key=lambda x: x['distance_miles'])

            # Find police stations within radius
            police_stations_nearby = []
            for idx, station in self.police_stations.iterrows():
                distance = self._haversine_distance(
                    lat, lon,
                    station['latitude'], station['longitude']
                )
                if distance <= police_radius_miles:
                    police_stations_nearby.append({
                        'station_name': station['station_name'],
                        'distance_miles': round(distance, 2),
                        'address': station['address']
                    })

            # Sort by distance
            police_stations_nearby.sort(key=lambda x: x['distance_miles'])

            # Get nearest distances
            nearest_fire_distance = fire_stations_nearby[0]['distance_miles'] if fire_stations_nearby else None
            nearest_police_distance = police_stations_nearby[0]['distance_miles'] if police_stations_nearby else None

            # Determine ISO threshold status (based on nearest fire station)
            # Need to check all fire stations, not just those within radius
            nearest_fire = self.get_nearest_fire_station(lat, lon)
            within_iso_threshold = (
                nearest_fire.get('distance_miles') is not None and
                nearest_fire['distance_miles'] <= self.ISO_DISTANCE_THRESHOLD_MILES
            )

            return {
                'fire_stations': fire_stations_nearby,
                'police_stations': police_stations_nearby,
                'fire_count': len(fire_stations_nearby),
                'police_count': len(police_stations_nearby),
                'nearest_fire_distance': nearest_fire_distance,
                'nearest_police_distance': nearest_police_distance,
                'within_iso_threshold': within_iso_threshold
            }

        except Exception as e:
            return {
                'fire_stations': [],
                'police_stations': [],
                'fire_count': 0,
                'police_count': 0,
                'nearest_fire_distance': None,
                'nearest_police_distance': None,
                'within_iso_threshold': False,
                'error': f'Error getting coverage: {str(e)}'
            }

    def get_response_time_estimates(self, lat: float, lon: float) -> Dict:
        """
        Calculate estimated emergency response times.

        Assumes 20 mph average speed for emergency vehicles.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with response time estimates for fire and police
        """
        # Validate coordinates
        if lat is None or lon is None:
            return {
                'fire_response': {
                    'distance_miles': None,
                    'estimated_minutes': None,
                    'station_name': None
                },
                'police_response': {
                    'distance_miles': None,
                    'estimated_minutes': None,
                    'station_name': None
                },
                'note': 'Estimates assume 20 mph average speed for emergency vehicles',
                'error': 'Invalid coordinates provided'
            }

        # Get nearest stations
        nearest_fire = self.get_nearest_fire_station(lat, lon)
        nearest_police = self.get_nearest_police_station(lat, lon)

        fire_response = {
            'distance_miles': nearest_fire.get('distance_miles'),
            'estimated_minutes': nearest_fire.get('drive_time_minutes'),
            'station_name': nearest_fire.get('station_name')
        }

        police_response = {
            'distance_miles': nearest_police.get('distance_miles'),
            'estimated_minutes': nearest_police.get('drive_time_minutes'),
            'station_name': nearest_police.get('station_name')
        }

        return {
            'fire_response': fire_response,
            'police_response': police_response,
            'note': 'Estimates assume 20 mph average speed for emergency vehicles'
        }

    def get_statistics(self) -> Dict:
        """
        Get statistics about emergency services data.

        Returns:
            Dictionary with counts and geographic info
        """
        # Fire station statistics
        fire_total = len(self.fire_stations)
        fire_by_jurisdiction = self.fire_stations['jurisdiction'].value_counts().to_dict()
        fire_by_type = self.fire_stations['station_type'].value_counts().to_dict()

        # Police station statistics
        police_total = len(self.police_stations)
        police_by_type = self.police_stations['station_type'].value_counts().to_dict()

        # Geographic bounds (combine both datasets)
        all_lats = list(self.fire_stations['latitude']) + list(self.police_stations['latitude'])
        all_lons = list(self.fire_stations['longitude']) + list(self.police_stations['longitude'])

        return {
            'fire_stations': {
                'total': fire_total,
                'by_jurisdiction': fire_by_jurisdiction,
                'by_type': fire_by_type
            },
            'police_stations': {
                'total': police_total,
                'by_type': police_by_type
            },
            'coverage': {
                'total_emergency_facilities': fire_total + police_total
            },
            'geographic_bounds': {
                'min_latitude': round(min(all_lats), 4),
                'max_latitude': round(max(all_lats), 4),
                'min_longitude': round(min(all_lons), 4),
                'max_longitude': round(max(all_lons), 4)
            }
        }
