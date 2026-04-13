"""
RentCast API Client
Fetches rental estimates and property data from RentCast API.

API Documentation: https://developers.rentcast.io/reference

Caching:
- Property records (/v1/properties) are cached for 7 days
- Includes subdivision and HOA data
- Cache location: cache/rentcast/
"""

import re
import requests
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib

# Cache configuration
CACHE_DIR = Path(__file__).parent.parent / 'cache' / 'rentcast'
CACHE_TTL_DAYS = 7  # Property records don't change often


@dataclass
class RentEstimate:
    """Rental estimate information from RentCast."""
    address: str
    city: str
    state: str
    zipcode: str
    rent_estimate: Optional[int] = None
    rent_range_low: Optional[int] = None
    rent_range_high: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    sqft: Optional[int] = None
    lot_size: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    price_estimate: Optional[int] = None
    price_range_low: Optional[int] = None
    price_range_high: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ============================================================================
# CACHE UTILITIES
# ============================================================================

def _get_cache_key(address: str) -> str:
    """Generate cache key from address."""
    normalized = address.lower().strip().replace(' ', '_').replace(',', '').replace('.', '')
    # Use hash for very long addresses
    if len(normalized) > 100:
        return hashlib.md5(normalized.encode()).hexdigest()
    return normalized


def _get_cached_property_records(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached property records if exists and not expired.

    Returns:
        Cached data dict or None if not found/expired
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)

        # Check TTL
        cached_at = datetime.fromisoformat(cached.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_at > timedelta(days=CACHE_TTL_DAYS):
            return None  # Expired

        return cached.get('data')

    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def _save_property_records_to_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """Save property records to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"

    cache_data = {
        'cached_at': datetime.now().isoformat(),
        'data': data
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, default=str)


# ============================================================================
# RENTCAST CLIENT
# ============================================================================

class RentCastClient:
    """Client for RentCast API."""

    BASE_URL = "https://api.rentcast.io/v1"

    def __init__(self, api_key: str):
        """
        Initialize RentCast client.

        Args:
            api_key: RentCast API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Api-Key': api_key,
            'Accept': 'application/json'
        })

    def get_property_records(self, address: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Get property records for an address.

        Includes subdivision name, HOA fees, and other property details.
        Results are cached for 7 days to minimize API calls.

        Args:
            address: Full address (e.g., "43500 Tuckaway Pl, Leesburg, VA 20176")
            use_cache: Whether to use cached results (default True)

        Returns:
            Property records dictionary or None if not found.
            Key fields include:
            - subdivision: str (e.g., "RIVER CREEK SECTION 1")
            - hoa: dict with 'fee' key (monthly HOA amount)
        """
        cache_key = _get_cache_key(address)

        # Check cache first
        if use_cache:
            cached = _get_cached_property_records(cache_key)
            if cached:
                # Handle both list and dict formats in cache
                if isinstance(cached, list):
                    if cached:
                        cached = cached[0]
                    else:
                        cached = None
                if cached:
                    cached['_from_cache'] = True
                    return cached

        try:
            url = f"{self.BASE_URL}/properties"
            params = {'address': address}

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # API returns a list of properties - take the first match
            if isinstance(data, list):
                if not data:
                    return None
                data = data[0]

            # Cache the result
            if use_cache and data:
                _save_property_records_to_cache(cache_key, data)

            data['_from_cache'] = False
            return data

        except requests.exceptions.RequestException as e:
            print(f"Error fetching property records: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_rent_estimate(self, address: str) -> Optional[RentEstimate]:
        """
        Get rental estimate for a property.

        Args:
            address: Full address (e.g., "43500 Tuckaway Pl, Leesburg, VA 20176")

        Returns:
            RentEstimate object or None if not found
        """
        try:
            url = f"{self.BASE_URL}/avm/rent/long-term"
            params = {'address': address}

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract property details and rent estimate
            # Handle both nested dict and direct value formats
            rent_data = data.get('rent', {})
            if isinstance(rent_data, dict):
                rent_estimate = rent_data.get('estimate')
                rent_range_low = rent_data.get('rangeMin')
                rent_range_high = rent_data.get('rangeMax')
            else:
                # Rent is a direct value
                rent_estimate = rent_data if rent_data else None
                rent_range_low = data.get('rentRangeMin')
                rent_range_high = data.get('rentRangeMax')

            return RentEstimate(
                address=data.get('address', address),
                city=data.get('city', ''),
                state=data.get('state', ''),
                zipcode=data.get('zipCode', ''),
                rent_estimate=rent_estimate,
                rent_range_low=rent_range_low,
                rent_range_high=rent_range_high,
                bedrooms=data.get('bedrooms'),
                bathrooms=data.get('bathrooms'),
                sqft=data.get('squareFootage'),
                lot_size=data.get('lotSize'),
                year_built=data.get('yearBuilt'),
                property_type=data.get('propertyType'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )

        except requests.exceptions.RequestException as e:
            print(f"Error fetching rent estimate: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_value_estimate(self, address: str) -> Optional[RentEstimate]:
        """
        Get property value estimate.

        Args:
            address: Full address (e.g., "43500 Tuckaway Pl, Leesburg, VA 20176")

        Returns:
            RentEstimate object with value estimates or None if not found
        """
        try:
            url = f"{self.BASE_URL}/avm/value"
            params = {'address': address}

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Extract property details and value estimate
            # Handle both nested dict and direct value formats
            price_data = data.get('price', {})
            if isinstance(price_data, dict):
                price_estimate = price_data.get('estimate')
                price_range_low = price_data.get('rangeMin')
                price_range_high = price_data.get('rangeMax')
            else:
                # Price is a direct value
                price_estimate = price_data if price_data else None
                price_range_low = data.get('priceRangeMin')
                price_range_high = data.get('priceRangeMax')

            return RentEstimate(
                address=data.get('address', address),
                city=data.get('city', ''),
                state=data.get('state', ''),
                zipcode=data.get('zipCode', ''),
                price_estimate=price_estimate,
                price_range_low=price_range_low,
                price_range_high=price_range_high,
                bedrooms=data.get('bedrooms'),
                bathrooms=data.get('bathrooms'),
                sqft=data.get('squareFootage'),
                lot_size=data.get('lotSize'),
                year_built=data.get('yearBuilt'),
                property_type=data.get('propertyType'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude')
            )

        except requests.exceptions.RequestException as e:
            print(f"Error fetching value estimate: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_complete_estimate(self, address: str) -> Optional[RentEstimate]:
        """
        Get both rental and value estimates for a property.

        Args:
            address: Full address

        Returns:
            RentEstimate object with both rent and value estimates
        """
        # Get value estimate first (usually more complete)
        value_data = self.get_value_estimate(address)

        if not value_data:
            print("Could not get value estimate, trying rent estimate...")
            return self.get_rent_estimate(address)

        # Try to add rent estimate to the value data
        rent_data = self.get_rent_estimate(address)
        if rent_data:
            value_data.rent_estimate = rent_data.rent_estimate
            value_data.rent_range_low = rent_data.rent_range_low
            value_data.rent_range_high = rent_data.rent_range_high

        return value_data

    def get_market_rent_statistics(self, zipcode: str, bedrooms: int,
                                       property_type: str = "Apartment") -> Optional[Dict]:
        """
        Get aggregate market rent statistics by zip code and bedroom count.

        Args:
            zipcode: ZIP code (e.g., "22031")
            bedrooms: Number of bedrooms (0 for Studio)
            property_type: Property type (default "Apartment")

        Returns:
            Dict with avg_rent, median_rent, min_rent, max_rent, sample_size
            or None on error/empty response.
        """
        cache_key = f"market_rent_{zipcode}_{bedrooms}_{property_type.lower()}"

        # Check cache first
        cached = _get_cached_property_records(cache_key)
        if cached:
            return cached

        try:
            url = f"{self.BASE_URL}/market/rent/long-term"
            params = {
                'zipCode': zipcode,
                'bedrooms': bedrooms,
                'propertyType': property_type,
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            if not data:
                return None

            # RentCast market endpoint returns a list of listings —
            # compute aggregate statistics from the results
            if isinstance(data, list):
                rents = [item.get('rent') for item in data if item.get('rent')]
                if not rents:
                    return None
                result = {
                    'avg_rent': int(sum(rents) / len(rents)),
                    'median_rent': int(sorted(rents)[len(rents) // 2]),
                    'min_rent': int(min(rents)),
                    'max_rent': int(max(rents)),
                    'sample_size': len(rents),
                }
            elif isinstance(data, dict):
                # Single aggregate response format
                result = {
                    'avg_rent': int(data.get('averageRent') or data.get('rent') or 0),
                    'median_rent': int(data.get('medianRent') or data.get('rent') or 0),
                    'min_rent': int(data.get('minRent') or 0),
                    'max_rent': int(data.get('maxRent') or 0),
                    'sample_size': int(data.get('sampleSize') or data.get('count') or 1),
                }
            else:
                return None

            if result['avg_rent'] == 0:
                return None

            # Cache the result
            _save_property_records_to_cache(cache_key, result)
            return result

        except requests.exceptions.RequestException as e:
            print(f"Error fetching market rent statistics: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def get_market_rent_for_unit_mix(self, zipcode: str,
                                      unit_mix_inputs: list) -> Dict[int, int]:
        """
        Convenience wrapper: fetch market rent for each unique bedroom count
        in a unit mix list.

        Args:
            zipcode: ZIP code (e.g., "22031")
            unit_mix_inputs: List of unit dicts, each with a 'type' label
                             like "1 BR / 1 BA", "Studio", etc.

        Returns:
            Dict keyed by bedroom count (int): {1: 2340, 2: 2950, 3: 3800}
            Returns empty dict on any failure.
        """
        try:
            # Extract unique bedroom counts from unit type labels
            bedroom_counts = set()
            for unit in unit_mix_inputs:
                unit_type = unit.get('type', '')
                if unit_type.lower().startswith('studio'):
                    bedroom_counts.add(0)
                else:
                    match = re.search(r'(\d+)\s*BR', unit_type, re.IGNORECASE)
                    if match:
                        bedroom_counts.add(int(match.group(1)))

            result = {}
            for br in bedroom_counts:
                stats = self.get_market_rent_statistics(zipcode, br)
                if stats and stats.get('avg_rent'):
                    result[br] = stats['avg_rent']

            return result
        except Exception as e:
            print(f"Error fetching market rents for unit mix: {e}")
            return {}

    def format_estimate_report(self, estimate: RentEstimate) -> str:
        """Format an estimate report for display."""
        lines = [
            "=" * 70,
            "RENTCAST PROPERTY ESTIMATE",
            "=" * 70,
            f"Address: {estimate.address}",
            f"City: {estimate.city}, {estimate.state} {estimate.zipcode}",
        ]

        if estimate.latitude and estimate.longitude:
            lines.append(f"Location: ({estimate.latitude}, {estimate.longitude})")

        lines.extend([
            "",
            "Property Details:",
            f"  Bedrooms: {estimate.bedrooms or 'N/A'}",
            f"  Bathrooms: {estimate.bathrooms or 'N/A'}",
            f"  Living Area: {estimate.sqft or 'N/A'} sqft",
            f"  Lot Size: {estimate.lot_size or 'N/A'} sqft",
            f"  Year Built: {estimate.year_built or 'N/A'}",
            f"  Property Type: {estimate.property_type or 'N/A'}",
            ""
        ])

        # Value estimate section
        if estimate.price_estimate:
            lines.extend([
                "Value Estimate:",
                f"  Estimated Value: ${estimate.price_estimate:,}",
                f"  Value Range: ${estimate.price_range_low:,} - ${estimate.price_range_high:,}" if estimate.price_range_low and estimate.price_range_high else "  Value Range: N/A",
            ])
            if estimate.sqft and estimate.sqft > 0:
                price_per_sqft = estimate.price_estimate / estimate.sqft
                lines.append(f"  Price per sqft: ${price_per_sqft:,.2f}")
            lines.append("")

        # Rent estimate section
        if estimate.rent_estimate:
            lines.extend([
                "Rental Estimate:",
                f"  Estimated Monthly Rent: ${estimate.rent_estimate:,}",
                f"  Rent Range: ${estimate.rent_range_low:,} - ${estimate.rent_range_high:,}" if estimate.rent_range_low and estimate.rent_range_high else "  Rent Range: N/A",
            ])
            if estimate.price_estimate and estimate.rent_estimate:
                gross_yield = (estimate.rent_estimate * 12 / estimate.price_estimate) * 100
                lines.append(f"  Gross Rental Yield: {gross_yield:.2f}%")
            lines.append("")

        lines.append("=" * 70)
        return "\n".join(lines)


if __name__ == '__main__':
    # Test the client
    from api_config import get_api_key

    api_key = get_api_key('RENTCAST_API_KEY')
    if not api_key:
        print("Error: RENTCAST_API_KEY not found in config")
        exit(1)

    client = RentCastClient(api_key)

    # Test with the provided address
    test_address = "43500 Tuckaway Pl, Leesburg, VA 20176"

    print(f"Testing RentCast API with: {test_address}\n")

    # Get complete estimate (both rent and value)
    estimate = client.get_complete_estimate(test_address)
    if estimate:
        print(client.format_estimate_report(estimate))
    else:
        print("Failed to retrieve property estimate")
