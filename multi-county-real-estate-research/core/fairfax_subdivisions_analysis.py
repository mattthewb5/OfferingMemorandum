"""
Fairfax County Subdivisions Analysis Module

Provides subdivision boundary lookups, point-in-polygon queries, and
neighborhood identification for properties.

Usage:
    from core.fairfax_subdivisions_analysis import FairfaxSubdivisionsAnalysis

    analyzer = FairfaxSubdivisionsAnalysis()
    subdivision = analyzer.get_subdivision(lat=38.8969, lon=-77.4327)
    print(f"Property is in: {subdivision['subdivision_name']}")
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from shapely.geometry import Point
import math

# Data path
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "subdivisions" / "processed"
SUBDIVISIONS_DATA_PATH = DATA_DIR / "subdivisions.parquet"


class FairfaxSubdivisionsAnalysis:
    """
    Fairfax County subdivision analysis for property assessment.

    Provides subdivision identification, boundary lookups, and neighborhood context.
    """

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize with subdivisions data.

        Args:
            data_path: Optional path to subdivisions parquet file
        """
        self.data_path = data_path or SUBDIVISIONS_DATA_PATH
        self.subdivisions = self._load_data()
        self._spatial_index = None

    def _load_data(self) -> gpd.GeoDataFrame:
        """Load subdivisions from parquet with geometry."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Subdivisions data not found at {self.data_path}")

        gdf = gpd.read_parquet(self.data_path)

        # Ensure CRS is WGS84
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.set_crs(epsg=4326)

        return gdf

    @property
    def spatial_index(self):
        """Lazy-load spatial index for efficient queries."""
        if self._spatial_index is None:
            self._spatial_index = self.subdivisions.sindex
        return self._spatial_index

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

    def get_subdivision(self, lat: float, lon: float) -> Dict:
        """
        Get the subdivision containing a point.

        Uses spatial indexing for efficient point-in-polygon lookup.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dict with subdivision info or None fields if not in any subdivision
        """
        if lat is None or lon is None:
            return {
                'found': False,
                'subdivision_name': None,
                'section': None,
                'phase': None,
                'block': None,
                'record_date': None,
                'deed_book': None,
                'deed_page': None,
                'message': 'Invalid coordinates provided'
            }

        point = Point(lon, lat)  # Note: Point takes (x, y) = (lon, lat)

        # Use spatial index for efficient lookup
        possible_matches_idx = list(self.spatial_index.intersection(point.bounds))

        if not possible_matches_idx:
            return {
                'found': False,
                'subdivision_name': None,
                'section': None,
                'phase': None,
                'block': None,
                'record_date': None,
                'deed_book': None,
                'deed_page': None,
                'message': 'Location not within any recorded subdivision'
            }

        # Check actual containment
        possible_matches = self.subdivisions.iloc[possible_matches_idx]
        matches = possible_matches[possible_matches.geometry.contains(point)]

        if len(matches) == 0:
            return {
                'found': False,
                'subdivision_name': None,
                'section': None,
                'phase': None,
                'block': None,
                'record_date': None,
                'deed_book': None,
                'deed_page': None,
                'message': 'Location not within any recorded subdivision'
            }

        # Return first match (if multiple, they likely share the same name)
        match = matches.iloc[0]

        # Handle record_date formatting
        record_date = match.get('record_date')
        if pd.notna(record_date):
            try:
                record_date = pd.Timestamp(record_date).strftime('%Y-%m-%d')
            except Exception:
                record_date = str(record_date)
        else:
            record_date = None

        return {
            'found': True,
            'subdivision_name': match.get('subdivision_name'),
            'section': match.get('section') if pd.notna(match.get('section')) else None,
            'phase': match.get('phase') if pd.notna(match.get('phase')) else None,
            'block': match.get('block') if pd.notna(match.get('block')) else None,
            'record_date': record_date,
            'deed_book': match.get('deed_book') if pd.notna(match.get('deed_book')) else None,
            'deed_page': match.get('deed_page') if pd.notna(match.get('deed_page')) else None,
            'message': None
        }

    def get_nearby_subdivisions(
        self,
        lat: float,
        lon: float,
        radius_miles: float = 1.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get subdivisions near a point (by centroid distance).

        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius in miles (default: 1.0)
            limit: Maximum number of results (default: 10)

        Returns:
            List of dicts with subdivision info and distance, sorted by distance
        """
        if lat is None or lon is None:
            return []

        point = Point(lon, lat)

        # Calculate centroid of each subdivision using projected CRS for accuracy
        gdf = self.subdivisions.copy()
        # Project to UTM zone 18N (appropriate for Fairfax County) for accurate centroids
        gdf_projected = gdf.to_crs(epsg=32618)
        centroids_projected = gdf_projected.geometry.centroid
        # Convert centroids back to WGS84
        centroids_gdf = gpd.GeoDataFrame(geometry=centroids_projected, crs='EPSG:32618')
        centroids_wgs84 = centroids_gdf.to_crs(epsg=4326)
        gdf['centroid'] = centroids_wgs84.geometry

        # Calculate distances to centroids
        gdf['distance_miles'] = gdf['centroid'].apply(
            lambda c: self._haversine_distance(lat, lon, c.y, c.x)
        )

        # Filter by radius
        nearby = gdf[gdf['distance_miles'] <= radius_miles].copy()

        if len(nearby) == 0:
            return []

        # Get unique subdivision names with minimum distance
        nearby_unique = nearby.groupby('subdivision_name').agg({
            'distance_miles': 'min',
            'section': 'first',
            'phase': 'first',
            'block': 'first',
            'record_date': 'first'
        }).reset_index()

        # Sort by distance
        nearby_unique = nearby_unique.sort_values('distance_miles').head(limit)

        results = []
        for _, row in nearby_unique.iterrows():
            record_date = row.get('record_date')
            if pd.notna(record_date):
                try:
                    record_date = pd.Timestamp(record_date).strftime('%Y-%m-%d')
                except Exception:
                    record_date = str(record_date)
            else:
                record_date = None

            results.append({
                'subdivision_name': row['subdivision_name'],
                'distance_miles': round(row['distance_miles'], 2),
                'section': row.get('section') if pd.notna(row.get('section')) else None,
                'phase': row.get('phase') if pd.notna(row.get('phase')) else None,
                'record_date': record_date
            })

        return results

    def get_subdivision_stats(self) -> Dict:
        """
        Get summary statistics about the subdivision dataset.

        Returns:
            Dict with dataset statistics
        """
        gdf = self.subdivisions

        # Count unique subdivisions
        unique_names = gdf['subdivision_name'].nunique()

        # Top subdivisions by polygon count (sections/phases)
        top_subdivisions = gdf['subdivision_name'].value_counts().head(10).to_dict()

        # Geographic bounds
        bounds = gdf.total_bounds

        # Date range
        valid_dates = gdf['record_date'].dropna()
        if len(valid_dates) > 0:
            # Filter out invalid dates (pre-1800)
            valid_dates = pd.to_datetime(valid_dates, errors='coerce')
            valid_dates = valid_dates[valid_dates > '1800-01-01']
            date_min = valid_dates.min().strftime('%Y-%m-%d') if len(valid_dates) > 0 else None
            date_max = valid_dates.max().strftime('%Y-%m-%d') if len(valid_dates) > 0 else None
        else:
            date_min = None
            date_max = None

        # Sections breakdown
        with_section = gdf['section'].notna().sum()
        with_phase = gdf['phase'].notna().sum()

        return {
            'total_features': len(gdf),
            'unique_subdivision_names': unique_names,
            'top_subdivisions_by_sections': top_subdivisions,
            'geographic_bounds': {
                'min_longitude': round(bounds[0], 4),
                'min_latitude': round(bounds[1], 4),
                'max_longitude': round(bounds[2], 4),
                'max_latitude': round(bounds[3], 4)
            },
            'date_range': {
                'earliest': date_min,
                'latest': date_max
            },
            'features_with_section': with_section,
            'features_with_phase': with_phase
        }

    def search_subdivisions(
        self,
        name_pattern: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search for subdivisions by name (case-insensitive partial match).

        Args:
            name_pattern: Search pattern (case-insensitive)
            limit: Maximum results to return (default: 20)

        Returns:
            List of matching subdivision names with counts
        """
        if not name_pattern:
            return []

        gdf = self.subdivisions

        # Case-insensitive search
        matches = gdf[
            gdf['subdivision_name'].str.upper().str.contains(name_pattern.upper(), na=False)
        ]

        if len(matches) == 0:
            return []

        # Group and count
        results = matches.groupby('subdivision_name').size().reset_index(name='section_count')
        results = results.sort_values('section_count', ascending=False).head(limit)

        return [
            {
                'subdivision_name': row['subdivision_name'],
                'section_count': int(row['section_count'])
            }
            for _, row in results.iterrows()
        ]


def example_usage():
    """Example usage of FairfaxSubdivisionsAnalysis."""

    print("=" * 70)
    print("FAIRFAX SUBDIVISIONS ANALYSIS - Example Usage")
    print("=" * 70)

    # Initialize
    analyzer = FairfaxSubdivisionsAnalysis()
    stats = analyzer.get_subdivision_stats()
    print(f"\nLoaded {stats['total_features']:,} subdivision features")
    print(f"Unique subdivision names: {stats['unique_subdivision_names']:,}")

    # Example location - Reston area
    test_lat = 38.9688
    test_lon = -77.3411

    print(f"\nAnalyzing location: {test_lat}, {test_lon}")

    # Get subdivision
    print("\n--- Subdivision Lookup ---")
    subdivision = analyzer.get_subdivision(test_lat, test_lon)
    if subdivision['found']:
        print(f"Subdivision: {subdivision['subdivision_name']}")
        print(f"Section: {subdivision['section'] or 'N/A'}")
        print(f"Phase: {subdivision['phase'] or 'N/A'}")
        print(f"Record Date: {subdivision['record_date'] or 'N/A'}")
    else:
        print(f"Not in subdivision: {subdivision['message']}")

    # Nearby subdivisions
    print("\n--- Nearby Subdivisions (within 1 mile) ---")
    nearby = analyzer.get_nearby_subdivisions(test_lat, test_lon, radius_miles=1.0)
    for sub in nearby[:5]:
        print(f"  {sub['subdivision_name']}: {sub['distance_miles']} mi")

    # Search
    print("\n--- Search: 'RESTON' ---")
    results = analyzer.search_subdivisions("RESTON", limit=5)
    for result in results:
        print(f"  {result['subdivision_name']}: {result['section_count']} sections")

    # Stats
    print("\n--- Top Subdivisions (by section count) ---")
    for name, count in list(stats['top_subdivisions_by_sections'].items())[:5]:
        print(f"  {name}: {count} sections")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
