"""
Shared Presentation Components

Provides consistent UI components used by all county report generators.
Ensures uniform look and feel across counties regardless of backend data patterns.

All functions are designed to be defensive - they handle missing data gracefully
and never crash the report generation.
"""

import streamlit as st
from typing import Dict, List, Any, Optional


# Rating color mapping for consistent styling
RATING_COLORS = {
    'excellent': 'green',
    'good': 'blue',
    'fair': 'orange',
    'poor': 'red',
    'unknown': 'gray',
}


def _get_rating_color(rating: str) -> str:
    """Get color for a rating string."""
    return RATING_COLORS.get(rating.lower(), 'gray')


def _safe_get(data: dict, key: str, default: Any = 'N/A') -> Any:
    """Safely get a value from a dict with default."""
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def render_report_header(
    county_name: str,
    address: str,
    lat: float,
    lon: float
) -> None:
    """
    Render the report header with county name, address, and coordinates.

    Args:
        county_name: Display name of the county (e.g., "Loudoun County")
        address: The address being analyzed
        lat: Latitude of the property
        lon: Longitude of the property
    """
    # Main title
    st.markdown(f"## {county_name} Property Analysis")

    # Address and coordinates in columns
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"**Address:** {address}")

    with col2:
        st.markdown(f"**Lat:** {lat:.6f}")

    with col3:
        st.markdown(f"**Lon:** {lon:.6f}")

    # County badge
    county_key = county_name.lower().replace(' county', '').strip()
    badge_colors = {
        'loudoun': ':blue[LOUDOUN COUNTY]',
        'fairfax': ':green[FAIRFAX COUNTY]',
    }
    badge = badge_colors.get(county_key, f':gray[{county_name.upper()}]')
    st.markdown(f"**Region:** {badge}")

    st.divider()


def render_score_card(title: str, score_data: Dict[str, Any]) -> None:
    """
    Render a score card with score, rating, and details.

    Args:
        title: Title for the score card (e.g., "School Access")
        score_data: Dictionary with expected format:
            {
                'score': int (0-100),
                'rating': str ('Excellent', 'Good', 'Fair', 'Poor'),
                'details': dict (optional additional key/value pairs)
            }

    Example:
        render_score_card("School Access", {
            'score': 85,
            'rating': 'Good',
            'details': {'Elementary': '0.5 miles', 'Middle': '1.2 miles'}
        })
    """
    if not isinstance(score_data, dict):
        st.warning(f"No data available for {title}")
        return

    score = _safe_get(score_data, 'score', 0)
    rating = _safe_get(score_data, 'rating', 'Unknown')
    details = _safe_get(score_data, 'details', {})

    # Score and rating in columns
    col1, col2 = st.columns([1, 2])

    with col1:
        # Display score as metric
        if isinstance(score, (int, float)):
            delta_color = "normal" if score >= 50 else "inverse"
            st.metric(
                label=title,
                value=f"{score}/100" if isinstance(score, int) else f"{score:.1f}/100",
                delta=rating,
                delta_color="off"
            )
        else:
            st.metric(label=title, value=str(score))

    with col2:
        # Rating badge with color
        rating_str = str(rating).lower()
        color = _get_rating_color(rating_str)

        if color == 'green':
            st.success(f"Rating: {rating}")
        elif color == 'blue':
            st.info(f"Rating: {rating}")
        elif color == 'orange':
            st.warning(f"Rating: {rating}")
        elif color == 'red':
            st.error(f"Rating: {rating}")
        else:
            st.markdown(f"**Rating:** {rating}")

    # Expandable details section
    if details and isinstance(details, dict):
        with st.expander(f"View {title} Details"):
            for key, value in details.items():
                st.markdown(f"- **{key}:** {value}")


def render_nearby_items(
    section_title: str,
    items: List[Dict[str, Any]],
    item_type: str,
    default_show: int = 5
) -> None:
    """
    Render a list of nearby items (schools, hospitals, etc.).

    Args:
        section_title: Title for the section (e.g., "Nearby Schools")
        items: List of items with expected format:
            [
                {
                    'name': str,
                    'distance_miles': float,
                    'latitude': float (optional),
                    'longitude': float (optional),
                    ...additional fields...
                }
            ]
        item_type: Type of item for display (e.g., "school", "hospital")
        default_show: Number of items to show by default (rest in expander)

    Example:
        render_nearby_items("Nearby Schools", [
            {'name': 'Jefferson Elementary', 'distance_miles': 0.5},
            {'name': 'Lincoln Middle', 'distance_miles': 1.2},
        ], "school")
    """
    st.markdown(f"**{section_title}**")

    if not items or not isinstance(items, list):
        st.info(f"No {item_type}s found nearby")
        return

    # Sort by distance (should already be sorted, but verify)
    try:
        sorted_items = sorted(
            items,
            key=lambda x: x.get('distance_miles', float('inf'))
        )
    except (TypeError, KeyError):
        sorted_items = items

    # Display top items
    top_items = sorted_items[:default_show]
    remaining_items = sorted_items[default_show:]

    for i, item in enumerate(top_items, 1):
        name = _safe_get(item, 'name', f'Unknown {item_type}')
        distance = _safe_get(item, 'distance_miles', None)

        if distance is not None and isinstance(distance, (int, float)):
            st.markdown(f"{i}. **{name}** - {distance:.1f} miles")
        else:
            st.markdown(f"{i}. **{name}**")

    # Show remaining in expander
    if remaining_items:
        with st.expander(f"Show {len(remaining_items)} more {item_type}s"):
            for i, item in enumerate(remaining_items, len(top_items) + 1):
                name = _safe_get(item, 'name', f'Unknown {item_type}')
                distance = _safe_get(item, 'distance_miles', None)

                if distance is not None and isinstance(distance, (int, float)):
                    st.markdown(f"{i}. **{name}** - {distance:.1f} miles")
                else:
                    st.markdown(f"{i}. **{name}**")


def render_statistics_summary(stats: Dict[str, Any]) -> None:
    """
    Render a summary of statistics in a formatted layout.

    Args:
        stats: Dictionary of statistics to display. Handles nested dicts.
            {
                'Total Count': 150,
                'Average Price': '$500,000',
                'Nested': {'Sub1': 'value1', 'Sub2': 'value2'}
            }

    Example:
        render_statistics_summary({
            'Total Permits': 45,
            'Average Value': '$250,000',
            'Time Period': '2024'
        })
    """
    if not stats or not isinstance(stats, dict):
        st.info("No statistics available")
        return

    # Separate flat values from nested dicts
    flat_stats = {}
    nested_stats = {}

    for key, value in stats.items():
        if isinstance(value, dict):
            nested_stats[key] = value
        else:
            flat_stats[key] = value

    # Display flat stats in columns
    if flat_stats:
        # Create columns (up to 4)
        num_cols = min(len(flat_stats), 4)
        cols = st.columns(num_cols)

        for i, (key, value) in enumerate(flat_stats.items()):
            col_idx = i % num_cols
            with cols[col_idx]:
                # Use metric for numeric values
                if isinstance(value, (int, float)):
                    st.metric(label=key, value=value)
                else:
                    st.metric(label=key, value=str(value))

    # Display nested stats in expanders
    if nested_stats:
        for section_name, section_data in nested_stats.items():
            with st.expander(f"{section_name} Details"):
                if isinstance(section_data, dict):
                    for k, v in section_data.items():
                        st.markdown(f"- **{k}:** {v}")
                else:
                    st.write(section_data)


def render_section_header(
    icon: str,
    title: str,
    subtitle: Optional[str] = None
) -> None:
    """
    Render a consistent section header with icon and title.

    Args:
        icon: Emoji icon for the section (e.g., "📚", "🏗️")
        title: Section title
        subtitle: Optional subtitle or description

    Example:
        render_section_header("📚", "Schools Analysis", "Public and private schools within 3 miles")
    """
    st.markdown(f"### {icon} {title}")

    if subtitle:
        st.caption(subtitle)


def render_data_table(
    title: str,
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None
) -> None:
    """
    Render data as a formatted table.

    Args:
        title: Title for the table section
        data: List of dictionaries to display
        columns: Optional list of column names to include (default: all)
    """
    st.markdown(f"**{title}**")

    if not data:
        st.info("No data available")
        return

    try:
        import pandas as pd
        df = pd.DataFrame(data)
        if columns:
            df = df[[c for c in columns if c in df.columns]]
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        # Fallback to simple display
        for item in data[:10]:
            st.write(item)
        if len(data) > 10:
            st.info(f"... and {len(data) - 10} more items")


def render_map_placeholder(
    lat: float,
    lon: float,
    title: str = "Location Map"
) -> None:
    """
    Render a placeholder for a map (POC - actual map integration would go here).

    Args:
        lat: Center latitude
        lon: Center longitude
        title: Map title
    """
    st.markdown(f"**{title}**")

    try:
        import pandas as pd
        # Simple map with single point
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data)
    except Exception:
        st.info(f"Map centered at ({lat:.4f}, {lon:.4f})")


def render_error_section(
    section_name: str,
    error_message: str
) -> None:
    """
    Render an error message for a failed section (graceful degradation).

    Args:
        section_name: Name of the section that failed
        error_message: Error message to display
    """
    st.warning(f"**{section_name}** - Data unavailable")
    with st.expander("Error Details"):
        st.code(error_message)
