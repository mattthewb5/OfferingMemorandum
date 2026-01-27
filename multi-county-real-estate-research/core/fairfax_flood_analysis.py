"""
Fairfax County Flood Analysis Module

Provides FEMA flood zone lookups, dam inundation risk assessment, and
floodplain easement queries for properties in Fairfax County.

Usage:
    from core.fairfax_flood_analysis import FairfaxFloodAnalysis

    analyzer = FairfaxFloodAnalysis()
    flood = analyzer.get_flood_risk(lat=38.8969, lon=-77.4327)
    print(f"Flood Zone: {flood['fema_zone']['zone_code']} ({flood['fema_zone']['risk_level']})")
"""

import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional
from shapely.geometry import Point


# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "flood" / "processed"
FEMA_ZONES_PATH = DATA_DIR / "fema_zones.parquet"
DAM_INUNDATION_PATH = DATA_DIR / "dam_inundation.parquet"
EASEMENTS_PATH = DATA_DIR / "easements.parquet"


# Risk level descriptions
RISK_DESCRIPTIONS = {
    'high': 'High flood risk - Properties require flood insurance if federally-backed mortgage',
    'moderate': 'Moderate flood risk - Lower premiums due to federal protection, but insurance recommended',
    'minimal': 'Minimal flood risk - Flood insurance not required but recommended'
}

# Zone code descriptions
ZONE_DESCRIPTIONS = {
    'A': '1% annual chance flood zone, no Base Flood Elevation determined',
    'AE': '1% annual chance flood zone with Base Flood Elevation',
    'AH': '1% annual chance shallow flooding (1-3 ft ponding)',
    'AO': '1% annual chance shallow flooding with sheet flow',
    'A99': 'Protected by federal flood protection system under construction',
    'X': 'Area outside 0.2% annual chance flood (minimal risk)',
    'X SHADED': 'Area between 1% and 0.2% annual chance flood (moderate risk)',
    'D': 'Undetermined risk - possible but not mapped',
    'V': 'High-risk coastal flood zone',
    'VE': 'High-risk coastal flood zone with Base Flood Elevation'
}


class FairfaxFloodAnalysis:
    """
    Fairfax County flood risk analysis for property assessment.

    Provides FEMA flood zone lookups, dam inundation risk, and easement queries.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize with flood data.

        Args:
            data_dir: Optional path to processed flood directory
        """
        self.data_dir = data_dir or DATA_DIR
        self.fema_zones = self._load_fema_zones()
        self.dam_inundation = self._load_dam_inundation()
        self.easements = self._load_easements()

        # Spatial indices for efficient lookups
        self._fema_sindex = None
        self._dam_sindex = None
        self._easements_sindex = None

    def _load_fema_zones(self) -> gpd.GeoDataFrame:
        """Load FEMA flood zone boundaries."""
        path = self.data_dir / "fema_zones.parquet"
        if not path.exists():
            raise FileNotFoundError(f"FEMA flood zones data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    def _load_dam_inundation(self) -> gpd.GeoDataFrame:
        """Load dam break inundation zones."""
        path = self.data_dir / "dam_inundation.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Dam inundation data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    def _load_easements(self) -> gpd.GeoDataFrame:
        """Load floodplain easement boundaries."""
        path = self.data_dir / "easements.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Floodplain easements data not found at {path}")

        gdf = gpd.read_parquet(path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    @property
    def fema_sindex(self):
        """Lazy-load spatial index for FEMA zones."""
        if self._fema_sindex is None:
            self._fema_sindex = self.fema_zones.sindex
        return self._fema_sindex

    @property
    def dam_sindex(self):
        """Lazy-load spatial index for dam inundation zones."""
        if self._dam_sindex is None:
            self._dam_sindex = self.dam_inundation.sindex
        return self._dam_sindex

    @property
    def easements_sindex(self):
        """Lazy-load spatial index for easements."""
        if self._easements_sindex is None:
            self._easements_sindex = self.easements.sindex
        return self._easements_sindex

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

    def get_fema_zone(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get FEMA flood zone for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with FEMA zone information or None
        """
        if lat is None or lon is None:
            return None

        matches = self._find_containing_features(
            lat, lon, self.fema_zones, self.fema_sindex
        )

        if len(matches) == 0:
            return None

        zone = matches.iloc[0]
        zone_code = zone['zone_code']

        return {
            'zone_code': zone_code,
            'zone_subtype': zone.get('zone_subtype'),
            'risk_level': zone.get('risk_level', 'unknown'),
            'risk_description': RISK_DESCRIPTIONS.get(
                zone.get('risk_level'), 'Unknown risk level'
            ),
            'zone_description': zone.get('description') or ZONE_DESCRIPTIONS.get(
                zone_code, f'FEMA Zone {zone_code}'
            ),
            'previous_zone': zone.get('previous_zone'),
            'sfha_change': zone.get('sfha_change'),
            'insurance_required': zone.get('risk_level') == 'high'
        }

    def get_dam_inundation_risk(self, lat: float, lon: float) -> List[Dict]:
        """
        Check if location is in any dam break inundation zones.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            List of dam inundation risks (empty if none)
        """
        if lat is None or lon is None:
            return []

        matches = self._find_containing_features(
            lat, lon, self.dam_inundation, self.dam_sindex
        )

        risks = []
        for _, dam in matches.iterrows():
            risks.append({
                'dam_name': dam['dam_name'],
                'dam_owner': dam.get('dam_owner'),
                'break_type': dam.get('break_type'),
            })

        return risks

    def check_floodplain_easement(self, lat: float, lon: float) -> Dict:
        """
        Check if location is within a recorded floodplain easement.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with easement information
        """
        if lat is None or lon is None:
            return {'in_easement': False, 'easement_count': 0, 'easements': []}

        matches = self._find_containing_features(
            lat, lon, self.easements, self.easements_sindex
        )

        easements = []
        for _, easement in matches.iterrows():
            easements.append({
                'easement_id': easement.get('easement_id'),
                'easement_type': easement.get('easement_type', 'floodplain')
            })

        return {
            'in_easement': len(easements) > 0,
            'easement_count': len(easements),
            'easements': easements
        }

    def get_flood_risk(self, lat: float, lon: float) -> Dict:
        """
        Get comprehensive flood risk assessment for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with all flood risk information
        """
        if lat is None or lon is None:
            return {
                'fema_zone': None,
                'dam_inundation_risks': [],
                'floodplain_easement': {'in_easement': False, 'easement_count': 0},
                'overall_risk': 'unknown',
                'insurance_required': False,
                'message': 'Invalid coordinates provided'
            }

        # Get all flood data
        fema = self.get_fema_zone(lat, lon)
        dams = self.get_dam_inundation_risk(lat, lon)
        easement = self.check_floodplain_easement(lat, lon)

        # Determine overall risk
        overall_risk = 'minimal'
        insurance_required = False

        if fema:
            if fema['risk_level'] == 'high':
                overall_risk = 'high'
                insurance_required = True
            elif fema['risk_level'] == 'moderate':
                overall_risk = 'moderate'

        # Dam risk elevates overall risk
        if dams:
            if overall_risk == 'minimal':
                overall_risk = 'moderate'

        # Easement presence indicates flood history
        if easement['in_easement']:
            if overall_risk == 'minimal':
                overall_risk = 'moderate'

        return {
            'fema_zone': fema,
            'dam_inundation_risks': dams,
            'floodplain_easement': easement,
            'overall_risk': overall_risk,
            'overall_risk_description': RISK_DESCRIPTIONS.get(overall_risk, 'Unknown'),
            'insurance_required': insurance_required,
            'message': None
        }

    def get_zones_by_risk(self, risk_level: str) -> gpd.GeoDataFrame:
        """
        Get all FEMA zones with a specific risk level.

        Args:
            risk_level: 'high', 'moderate', or 'minimal'

        Returns:
            GeoDataFrame of matching zones
        """
        return self.fema_zones[self.fema_zones['risk_level'] == risk_level]

    def get_dams(self) -> List[str]:
        """
        Get list of all dams with inundation data.

        Returns:
            List of dam names
        """
        return sorted(self.dam_inundation['dam_name'].unique().tolist())

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about the flood dataset.

        Returns:
            Dict with dataset statistics
        """
        # FEMA zone counts by risk
        risk_counts = self.fema_zones['risk_level'].value_counts().to_dict()
        zone_counts = self.fema_zones['zone_code'].value_counts().to_dict()

        # Dam statistics
        dam_names = self.dam_inundation['dam_name'].unique()

        # Geographic bounds
        bounds = self.fema_zones.total_bounds

        return {
            'fema_zones': {
                'total': len(self.fema_zones),
                'by_risk_level': risk_counts,
                'by_zone_code': zone_counts
            },
            'dam_inundation': {
                'total_zones': len(self.dam_inundation),
                'unique_dams': len(dam_names),
                'dam_names': sorted(dam_names.tolist())
            },
            'easements': {
                'total': len(self.easements)
            },
            'geographic_bounds': {
                'min_longitude': round(bounds[0], 4),
                'min_latitude': round(bounds[1], 4),
                'max_longitude': round(bounds[2], 4),
                'max_latitude': round(bounds[3], 4)
            }
        }


def example_usage():
    """Example usage of FairfaxFloodAnalysis."""

    print("=" * 70)
    print("FAIRFAX FLOOD ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxFloodAnalysis()
    stats = analyzer.get_statistics()
    print(f"\nLoaded {stats['fema_zones']['total']} FEMA flood zones")
    print(f"  By risk level:")
    for risk, count in stats['fema_zones']['by_risk_level'].items():
        print(f"    {risk}: {count}")
    print(f"\nLoaded {stats['dam_inundation']['total_zones']} dam inundation zones")
    print(f"  Unique dams: {stats['dam_inundation']['unique_dams']}")
    print(f"\nLoaded {stats['easements']['total']} floodplain easements")

    # Example location (Fairfax area)
    test_lat = 38.8969
    test_lon = -77.4327

    print(f"\n{'='*70}")
    print(f"Analyzing location: {test_lat}, {test_lon}")
    print(f"{'='*70}")

    # Get comprehensive flood risk
    flood = analyzer.get_flood_risk(test_lat, test_lon)

    print("\n--- FEMA Flood Zone ---")
    if flood['fema_zone']:
        fema = flood['fema_zone']
        print(f"Zone Code: {fema['zone_code']}")
        print(f"Risk Level: {fema['risk_level']}")
        print(f"Description: {fema['zone_description']}")
        print(f"Insurance Required: {'Yes' if fema['insurance_required'] else 'No'}")
        if fema.get('previous_zone'):
            print(f"Previous Zone: {fema['previous_zone']}")
    else:
        print("Location not within mapped FEMA flood zone")

    print("\n--- Dam Inundation Risk ---")
    if flood['dam_inundation_risks']:
        for dam in flood['dam_inundation_risks']:
            print(f"  Dam: {dam['dam_name']}")
            print(f"    Owner: {dam['dam_owner']}")
            print(f"    Scenario: {dam['break_type']}")
    else:
        print("No dam inundation risk at this location")

    print("\n--- Floodplain Easement ---")
    easement = flood['floodplain_easement']
    if easement['in_easement']:
        print(f"Location is within {easement['easement_count']} floodplain easement(s)")
    else:
        print("Not within a recorded floodplain easement")

    print("\n--- Overall Assessment ---")
    print(f"Overall Risk: {flood['overall_risk'].upper()}")
    print(f"  {flood['overall_risk_description']}")
    print(f"Flood Insurance Required: {'Yes' if flood['insurance_required'] else 'No'}")

    # List dams
    print("\n--- Dams with Inundation Data ---")
    dams = analyzer.get_dams()
    for dam in dams[:5]:
        print(f"  {dam}")
    if len(dams) > 5:
        print(f"  ... and {len(dams) - 5} more")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
