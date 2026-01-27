"""
Fairfax County Zoning Analysis Module

Provides zoning district lookups, overlay identification, and land use analysis
for properties in Fairfax County.

Usage:
    from core.fairfax_zoning_analysis import FairfaxZoningAnalysis

    analyzer = FairfaxZoningAnalysis()
    zoning = analyzer.get_zoning(lat=38.8969, lon=-77.4327)
    print(f"Zone: {zoning['zone_code']} ({zoning['zone_type']})")
"""

import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import Point


# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "zoning" / "processed"
DISTRICTS_PATH = DATA_DIR / "districts.parquet"
OVERLAYS_PATH = DATA_DIR / "overlays.parquet"


# Zone type descriptions
ZONE_TYPE_DESCRIPTIONS = {
    'residential': 'Residential - Single or multi-family housing',
    'commercial': 'Commercial - Retail, office, and business uses',
    'industrial': 'Industrial - Manufacturing and warehousing',
    'planned_units': 'Planned Development - Mixed-use or special development',
    'tyson': 'Tysons Corner Special District',
    'other': 'Other/Special Use'
}

# Common zone code descriptions
ZONE_CODE_DESCRIPTIONS = {
    # Residential
    'R-1': 'Residential, 1 dwelling unit per acre',
    'R-2': 'Residential, 2 dwelling units per acre',
    'R-3': 'Residential, 3 dwelling units per acre',
    'R-4': 'Residential, 4 dwelling units per acre',
    'R-5': 'Residential, 5 dwelling units per acre',
    'R-8': 'Residential, 8 dwelling units per acre',
    'R-12': 'Residential, 12 dwelling units per acre',
    'R-16': 'Residential, 16 dwelling units per acre',
    'R-20': 'Residential, 20 dwelling units per acre',
    'R-30': 'Residential, 30 dwelling units per acre',
    'R-C': 'Residential Conservation',
    'R-E': 'Residential Estate',
    'R-MHP': 'Residential Mobile Home Park',
    # Commercial
    'C-1': 'Commercial, Low-intensity retail',
    'C-2': 'Commercial, Convenience center',
    'C-3': 'Commercial, Office',
    'C-4': 'Commercial, General',
    'C-5': 'Commercial, High-intensity office',
    'C-6': 'Commercial, Community retail',
    'C-7': 'Commercial, Regional retail',
    'C-8': 'Commercial, Highway',
    # Industrial
    'I-1': 'Industrial, Light',
    'I-2': 'Industrial, Limited',
    'I-3': 'Industrial, Light-general',
    'I-4': 'Industrial, Medium',
    'I-5': 'Industrial, General',
    'I-6': 'Industrial, Heavy',
    # Planned Development
    'PDH': 'Planned Development Housing',
    'PDC': 'Planned Development Commercial',
    'PRM': 'Planned Residential Mixed-use',
    'PTC': 'Planned Tysons Corner',
}


class FairfaxZoningAnalysis:
    """
    Fairfax County zoning analysis for property assessment.

    Provides zoning district lookups, overlay identification, and development analysis.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with zoning data.

        Args:
            data_dir: Optional path to processed zoning directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.districts = self._load_districts()
        self.overlays = self._load_overlays()

        # Spatial indices for efficient lookups
        self._districts_sindex = None
        self._overlays_sindex = None

    def _load_districts(self) -> gpd.GeoDataFrame:
        """Load zoning district boundaries."""
        path = self.data_dir / "districts.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Zoning districts data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    def _load_overlays(self) -> gpd.GeoDataFrame:
        """Load zoning overlay district boundaries."""
        path = self.data_dir / "overlays.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Zoning overlays data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    @property
    def districts_sindex(self):
        """Lazy-load spatial index for districts."""
        if self._districts_sindex is None:
            self._districts_sindex = self.districts.sindex
        return self._districts_sindex

    @property
    def overlays_sindex(self):
        """Lazy-load spatial index for overlays."""
        if self._overlays_sindex is None:
            self._overlays_sindex = self.overlays.sindex
        return self._overlays_sindex

    def _find_containing_features(
        self,
        lat: float,
        lon: float,
        gdf: gpd.GeoDataFrame,
        sindex
    ) -> gpd.GeoDataFrame:
        """Find all features containing a point using spatial index."""
        point = Point(lon, lat)

        # Use spatial index for efficient lookup
        possible_matches_idx = list(sindex.intersection(point.bounds))

        if not possible_matches_idx:
            return gpd.GeoDataFrame()

        # Check actual containment
        possible_matches = gdf.iloc[possible_matches_idx]
        matches = possible_matches[possible_matches.geometry.contains(point)]

        return matches

    def get_zoning(self, lat: float, lon: float) -> Dict:
        """
        Get zoning district for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with zoning information
        """
        if lat is None or lon is None:
            return {
                'zone_code': None,
                'zone_type': None,
                'zone_description': None,
                'has_proffer': None,
                'public_land': None,
                'cluster': None,
                'overlays': [],
                'message': 'Invalid coordinates provided'
            }

        # Find district
        matches = self._find_containing_features(
            lat, lon, self.districts, self.districts_sindex
        )

        if len(matches) == 0:
            return {
                'zone_code': None,
                'zone_type': None,
                'zone_description': None,
                'has_proffer': None,
                'public_land': None,
                'cluster': None,
                'overlays': [],
                'message': 'Location not within any zoning district'
            }

        district = matches.iloc[0]
        zone_code = district['zone_code']

        # Get description for zone code
        zone_description = self._get_zone_description(zone_code)

        # Find overlays
        overlay_matches = self._find_containing_features(
            lat, lon, self.overlays, self.overlays_sindex
        )

        overlays = []
        for _, overlay in overlay_matches.iterrows():
            overlay_info = {
                'overlay_type': overlay['overlay_type'],
            }
            if overlay.get('decibel_level') and overlay['decibel_level'] > 0:
                overlay_info['decibel_level'] = overlay['decibel_level']
            overlays.append(overlay_info)

        return {
            'zone_code': zone_code,
            'zone_type': district['zone_type'],
            'zone_type_description': ZONE_TYPE_DESCRIPTIONS.get(
                district['zone_type'], district['zone_type']
            ),
            'zone_description': zone_description,
            'has_proffer': bool(district.get('has_proffer')),
            'public_land': bool(district.get('public_land')),
            'cluster': district.get('cluster'),
            'overlays': overlays,
            'message': None
        }

    def _get_zone_description(self, zone_code: str) -> str:
        """Get human-readable description for a zone code."""
        if not zone_code:
            return None

        # Check exact match first
        if zone_code in ZONE_CODE_DESCRIPTIONS:
            return ZONE_CODE_DESCRIPTIONS[zone_code]

        # Check for PDH-x patterns (Planned Development Housing with density)
        if zone_code.startswith('PDH-'):
            density = zone_code.replace('PDH-', '')
            return f'Planned Development Housing, {density} units per acre'

        # Check for base code (e.g., R-1 from R-1(C))
        base_code = zone_code.split('(')[0].strip()
        if base_code in ZONE_CODE_DESCRIPTIONS:
            return ZONE_CODE_DESCRIPTIONS[base_code]

        return None

    def get_overlays(self, lat: float, lon: float) -> List[Dict]:
        """
        Get all overlay districts for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            List of overlay districts with details
        """
        if lat is None or lon is None:
            return []

        matches = self._find_containing_features(
            lat, lon, self.overlays, self.overlays_sindex
        )

        overlays = []
        for _, overlay in matches.iterrows():
            overlay_info = {
                'overlay_type': overlay['overlay_type'],
            }
            if overlay.get('decibel_level') and overlay['decibel_level'] > 0:
                overlay_info['decibel_level'] = overlay['decibel_level']
                overlay_info['noise_description'] = self._get_noise_description(
                    overlay['decibel_level']
                )
            overlays.append(overlay_info)

        return overlays

    def _get_noise_description(self, decibel_level: float) -> str:
        """Get description for airport noise level."""
        if decibel_level >= 75:
            return "Very high aircraft noise - Significant impact on outdoor activities"
        elif decibel_level >= 70:
            return "High aircraft noise - Noticeable during conversations"
        elif decibel_level >= 65:
            return "Moderate aircraft noise - May affect sleep"
        elif decibel_level >= 60:
            return "Low-moderate aircraft noise - Background noise level"
        else:
            return "Low aircraft noise"

    def check_airport_noise(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Check if location is within airport noise impact zone.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with noise information or None if not in noise zone
        """
        overlays = self.get_overlays(lat, lon)

        for overlay in overlays:
            if overlay['overlay_type'] == 'airport_noise_impact':
                return {
                    'in_noise_zone': True,
                    'decibel_level': overlay.get('decibel_level'),
                    'description': overlay.get('noise_description'),
                }

        return None

    def get_zone_types(self) -> Dict[str, int]:
        """
        Get count of districts by zone type.

        Returns:
            Dict with zone type counts
        """
        return self.districts['zone_type'].value_counts().to_dict()

    def get_overlay_types(self) -> Dict[str, int]:
        """
        Get count of overlay districts by type.

        Returns:
            Dict with overlay type counts
        """
        return self.overlays['overlay_type'].value_counts().to_dict()

    def search_zones(self, zone_code_pattern: str, limit: int = 20) -> List[Dict]:
        """
        Search for zoning districts by code pattern.

        Args:
            zone_code_pattern: Pattern to match (case-insensitive)
            limit: Maximum results

        Returns:
            List of matching zone codes with counts
        """
        if not zone_code_pattern:
            return []

        # Find matching zone codes
        mask = self.districts['zone_code'].str.upper().str.contains(
            zone_code_pattern.upper(), na=False
        )
        matches = self.districts[mask]

        # Group by zone code and count
        zone_counts = matches.groupby('zone_code').size().sort_values(ascending=False)

        results = []
        for zone_code, count in zone_counts.head(limit).items():
            # Get zone type for this code
            zone_type = matches[matches['zone_code'] == zone_code].iloc[0]['zone_type']
            results.append({
                'zone_code': zone_code,
                'zone_type': zone_type,
                'description': self._get_zone_description(zone_code),
                'district_count': int(count)
            })

        return results

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the zoning dataset.

        Returns:
            Dict with dataset statistics
        """
        # District counts by type
        type_counts = self.districts['zone_type'].value_counts().to_dict()

        # Unique zone codes
        unique_codes = self.districts['zone_code'].nunique()

        # Overlay counts by type
        overlay_counts = self.overlays['overlay_type'].value_counts().to_dict()

        # Proffer/public land stats
        proffer_count = self.districts['has_proffer'].sum() if 'has_proffer' in self.districts.columns else 0
        public_land_count = self.districts['public_land'].sum() if 'public_land' in self.districts.columns else 0

        # Geographic bounds
        bounds = self.districts.total_bounds

        return {
            'districts': {
                'total': len(self.districts),
                'unique_zone_codes': unique_codes,
                'by_type': type_counts,
                'with_proffer': int(proffer_count),
                'public_land': int(public_land_count)
            },
            'overlays': {
                'total': len(self.overlays),
                'by_type': overlay_counts
            },
            'geographic_bounds': {
                'min_longitude': round(bounds[0], 4),
                'min_latitude': round(bounds[1], 4),
                'max_longitude': round(bounds[2], 4),
                'max_latitude': round(bounds[3], 4)
            }
        }


def example_usage():
    """Example usage of FairfaxZoningAnalysis."""

    print("=" * 70)
    print("FAIRFAX ZONING ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxZoningAnalysis()
    stats = analyzer.get_statistics()
    print(f"\nLoaded {stats['districts']['total']} zoning districts")
    print(f"  Unique zone codes: {stats['districts']['unique_zone_codes']}")
    print(f"  By type:")
    for ztype, count in stats['districts']['by_type'].items():
        print(f"    {ztype}: {count}")
    print(f"\nLoaded {stats['overlays']['total']} overlay districts")
    for otype, count in stats['overlays']['by_type'].items():
        print(f"  {otype}: {count}")

    # Example location (Fairfax City area)
    test_lat = 38.8969
    test_lon = -77.4327

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Get zoning
    print("\n--- Zoning District ---")
    zoning = analyzer.get_zoning(test_lat, test_lon)
    if zoning['zone_code']:
        print(f"Zone Code: {zoning['zone_code']}")
        print(f"Zone Type: {zoning['zone_type']} ({zoning['zone_type_description']})")
        if zoning['zone_description']:
            print(f"Description: {zoning['zone_description']}")
        print(f"Has Proffer: {zoning['has_proffer']}")
        print(f"Public Land: {zoning['public_land']}")
        if zoning['cluster']:
            print(f"Cluster: {zoning['cluster']}")
    else:
        print(f"No zoning found: {zoning['message']}")

    # Check overlays
    print("\n--- Overlay Districts ---")
    if zoning['overlays']:
        for overlay in zoning['overlays']:
            print(f"  {overlay['overlay_type']}")
            if 'decibel_level' in overlay:
                print(f"    Noise Level: {overlay['decibel_level']} dB")
    else:
        print("  No overlays apply to this location")

    # Airport noise check
    print("\n--- Airport Noise Check ---")
    noise = analyzer.check_airport_noise(test_lat, test_lon)
    if noise:
        print(f"In Noise Zone: Yes")
        print(f"Decibel Level: {noise['decibel_level']} dB")
        print(f"Description: {noise['description']}")
    else:
        print("Not in airport noise impact zone")

    # Search example
    print("\n--- Search: 'PDH' ---")
    results = analyzer.search_zones("PDH", limit=5)
    for zone in results:
        print(f"  {zone['zone_code']}: {zone['district_count']} districts")
        if zone['description']:
            print(f"    {zone['description']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
