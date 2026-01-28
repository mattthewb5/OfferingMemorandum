"""
Fairfax County School Performance Analysis Module

Provides school performance scoring, trend analysis, and quality metrics
based on Virginia VDOE Standards of Learning (SOL) test data.

Usage:
    from core.fairfax_school_performance_analysis import FairfaxSchoolPerformanceAnalysis

    analyzer = FairfaxSchoolPerformanceAnalysis()
    performance = analyzer.get_school_performance("Terraset Elementary")
    print(f"Overall Pass Rate: {performance['recent_overall_pass_rate']}%")
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process

# Data paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "schools" / "performance" / "processed"
SUMMARY_DATA_PATH = DATA_DIR / "performance_summary.parquet"
TRENDS_DATA_PATH = DATA_DIR / "performance_trends.parquet"


class FairfaxSchoolPerformanceAnalysis:
    """
    Fairfax County school performance analysis for property assessment.

    Provides performance scoring, trend analysis, and quality metrics
    based on VDOE SOL test data.
    """

    def __init__(
        self,
        summary_path: Optional[Path] = None,
        trends_path: Optional[Path] = None
    ):
        """
        Initialize with school performance data.

        Args:
            summary_path: Optional path to performance summary parquet file
            trends_path: Optional path to performance trends parquet file
        """
        self.summary_path = summary_path or SUMMARY_DATA_PATH
        self.trends_path = trends_path or TRENDS_DATA_PATH
        self._summary = None
        self._trends = None

    @property
    def summary(self) -> pd.DataFrame:
        """Lazy load school summary data."""
        if self._summary is None:
            self._summary = self._load_summary()
        return self._summary

    @property
    def trends(self) -> pd.DataFrame:
        """Lazy load school trend data."""
        if self._trends is None:
            self._trends = self._load_trends()
        return self._trends

    def _load_summary(self) -> pd.DataFrame:
        """Load school performance summary from parquet."""
        if not self.summary_path.exists():
            raise FileNotFoundError(f"Performance summary not found at {self.summary_path}")
        return pd.read_parquet(self.summary_path)

    def _load_trends(self) -> pd.DataFrame:
        """Load school performance trends from parquet."""
        if not self.trends_path.exists():
            raise FileNotFoundError(f"Performance trends not found at {self.trends_path}")
        return pd.read_parquet(self.trends_path)

    def _fuzzy_match_school(self, school_name: str, threshold: int = 70) -> Optional[str]:
        """
        Find best fuzzy match for a school name.

        Args:
            school_name: School name to match
            threshold: Minimum match score (0-100)

        Returns:
            Matched school name or None if no good match
        """
        school_names = self.summary['school_name'].tolist()
        result = process.extractOne(
            school_name,
            school_names,
            scorer=fuzz.token_sort_ratio
        )

        if result and result[1] >= threshold:
            return result[0]
        return None

    def get_school_performance(self, school_name: str) -> Dict:
        """
        Get performance metrics for a specific school.

        Args:
            school_name: School name (supports fuzzy matching)

        Returns:
            Dict with performance metrics, trends, and analysis
        """
        # Try exact match first
        df = self.summary
        match = df[df['school_name'].str.upper() == school_name.upper()]

        if len(match) == 0:
            # Try fuzzy match
            matched_name = self._fuzzy_match_school(school_name)
            if matched_name:
                match = df[df['school_name'] == matched_name]
            else:
                return {
                    'found': False,
                    'school_name': school_name,
                    'error': f'School not found: {school_name}',
                    'suggestion': self._fuzzy_match_school(school_name, threshold=50)
                }

        school = match.iloc[0]

        return {
            'found': True,
            'school_id': int(school['school_id']),
            'school_name': school['school_name'],
            'school_type': school['school_type'],

            # Most recent year data
            'most_recent_year': school['most_recent_year'],
            'recent_reading_pass_rate': self._safe_float(school['recent_reading_pass_rate']),
            'recent_math_pass_rate': self._safe_float(school['recent_math_pass_rate']),
            'recent_science_pass_rate': self._safe_float(school['recent_science_pass_rate']),
            'recent_history_pass_rate': self._safe_float(school['recent_history_pass_rate']),
            'recent_overall_pass_rate': self._safe_float(school['recent_overall_pass_rate']),

            # 5-year averages
            'avg_reading_pass_rate': self._safe_float(school['avg_reading_pass_rate']),
            'avg_math_pass_rate': self._safe_float(school['avg_math_pass_rate']),
            'avg_science_pass_rate': self._safe_float(school['avg_science_pass_rate']),
            'avg_history_pass_rate': self._safe_float(school['avg_history_pass_rate']),
            'avg_overall_pass_rate': self._safe_float(school['avg_overall_pass_rate']),

            # Trends
            'reading_trend': school['reading_trend'],
            'math_trend': school['math_trend'],
            'science_trend': school['science_trend'],
            'overall_trend': school['overall_trend'],
            'overall_trend_slope': self._safe_float(school['overall_trend_slope']),

            # Performance category
            'performance_category': school['performance_category'],

            # Data info
            'years_of_data': int(school['years_of_data']),
            'data_years': school['data_years']
        }

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float, returning None for NaN."""
        if pd.isna(value):
            return None
        return float(value)

    def match_school_to_facilities(self, school_name: str) -> Dict:
        """
        Match performance data to school facilities from FairfaxSchoolsAnalysis.

        Args:
            school_name: School name to match

        Returns:
            Dict with performance data and facility match info
        """
        performance = self.get_school_performance(school_name)

        if not performance['found']:
            return performance

        # Try to import and match with facilities module
        try:
            from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
            facilities_analyzer = FairfaxSchoolsAnalysis()

            # Try fuzzy matching against facility names
            facility_names = facilities_analyzer.schools['school_name'].tolist()
            facility_match = process.extractOne(
                performance['school_name'],
                facility_names,
                scorer=fuzz.token_sort_ratio
            )

            if facility_match and facility_match[1] >= 70:
                facility = facilities_analyzer.schools[
                    facilities_analyzer.schools['school_name'] == facility_match[0]
                ].iloc[0]

                performance['facility_match'] = {
                    'matched': True,
                    'facility_name': facility_match[0],
                    'match_score': facility_match[1],
                    'latitude': float(facility['latitude']) if pd.notna(facility['latitude']) else None,
                    'longitude': float(facility['longitude']) if pd.notna(facility['longitude']) else None,
                    'address': facility.get('address', None),
                    'school_level': facility.get('school_level', None)
                }
            else:
                performance['facility_match'] = {
                    'matched': False,
                    'reason': 'No matching facility found'
                }

        except ImportError:
            performance['facility_match'] = {
                'matched': False,
                'reason': 'FairfaxSchoolsAnalysis module not available'
            }
        except Exception as e:
            performance['facility_match'] = {
                'matched': False,
                'reason': f'Error matching facility: {str(e)}'
            }

        return performance

    def calculate_school_quality_score(self, school_name: str) -> Dict:
        """
        Calculate school quality score on 0-100 scale.

        Scoring system:
        - Recent performance: 0-50 points (average pass rate * 0.5)
        - 5-year trend: 0-30 points (improving=30, stable=15, declining=0)
        - Performance consistency: 0-20 points (based on variance)

        Args:
            school_name: School name to score

        Returns:
            Dict with score (0-100), rating, and breakdown
        """
        performance = self.get_school_performance(school_name)

        if not performance['found']:
            return {
                'found': False,
                'school_name': school_name,
                'error': performance.get('error', 'School not found')
            }

        # 1. Recent performance score (0-50 points)
        recent_overall = performance['recent_overall_pass_rate']
        if recent_overall is not None:
            performance_score = min(50, recent_overall * 0.5)
        else:
            performance_score = 25  # Default for missing data

        # 2. Trend score (0-30 points) - with ceiling recognition
        overall_trend = performance['overall_trend']

        # Schools at ≥95% pass rate are at the "ceiling" - can't improve further
        # Give them full credit for maintaining excellence
        if recent_overall is not None and recent_overall >= 95.0:
            # Schools at ceiling - already at excellence
            if overall_trend in ['improving', 'stable']:
                trend_score = 30  # Full credit for sustaining excellence
                trend_note = "Maintaining excellence at ceiling"
            else:
                trend_score = 0  # Only penalize if declining from excellence
                trend_note = "Declining from excellence"
        else:
            # Schools below ceiling - normal trend scoring
            if overall_trend == 'improving':
                trend_score = 30
                trend_note = "Improving performance"
            elif overall_trend == 'stable':
                trend_score = 15
                trend_note = "Stable performance"
            elif overall_trend == 'declining':
                trend_score = 0
                trend_note = "Declining performance"
            else:
                trend_score = 10  # insufficient_data
                trend_note = "Insufficient trend data"

        # 3. Consistency score (0-20 points)
        # Based on subject pass rate balance
        subjects = [
            performance['recent_reading_pass_rate'],
            performance['recent_math_pass_rate'],
            performance['recent_science_pass_rate']
        ]
        subjects = [s for s in subjects if s is not None]

        if len(subjects) >= 2:
            variance = np.var(subjects)
            # Lower variance = higher consistency
            if variance < 25:  # Very consistent
                consistency_score = 20
            elif variance < 50:  # Moderately consistent
                consistency_score = 15
            elif variance < 100:  # Some variation
                consistency_score = 10
            else:  # High variation
                consistency_score = 5
        else:
            consistency_score = 10  # Default for missing data

        # Calculate total score
        total_score = min(100, performance_score + trend_score + consistency_score)

        # Determine rating
        if total_score >= 85:
            rating = 'Excellent'
            analysis = 'Top-performing school with strong academics and positive trends.'
        elif total_score >= 70:
            rating = 'Good'
            analysis = 'Solid academic performance with generally positive outcomes.'
        elif total_score >= 55:
            rating = 'Fair'
            analysis = 'Average performance. Some areas may need attention.'
        else:
            rating = 'Needs Improvement'
            analysis = 'Below-average performance. Consider supplementary education options.'

        return {
            'found': True,
            'school_name': performance['school_name'],
            'school_type': performance['school_type'],
            'score': round(total_score),
            'rating': rating,
            'analysis': analysis,
            'factors': {
                'performance_score': round(performance_score, 1),
                'trend_score': round(trend_score, 1),
                'trend_note': trend_note,
                'consistency_score': round(consistency_score, 1)
            },
            'recent_pass_rate': performance['recent_overall_pass_rate'],
            'trend': overall_trend,
            'performance_category': performance['performance_category']
        }

    def get_school_trends(self, school_name: str, years: int = 5) -> Dict:
        """
        Get year-by-year performance trends for a school.

        Args:
            school_name: School name
            years: Number of years to include (default: 5)

        Returns:
            Dict with yearly performance data for charts
        """
        # Find the school
        df = self.summary
        match = df[df['school_name'].str.upper() == school_name.upper()]

        if len(match) == 0:
            matched_name = self._fuzzy_match_school(school_name)
            if matched_name:
                match = df[df['school_name'] == matched_name]
            else:
                return {
                    'found': False,
                    'school_name': school_name,
                    'error': 'School not found'
                }

        school = match.iloc[0]
        school_id = school['school_id']

        # Get trend data
        trends_df = self.trends
        school_trends = trends_df[trends_df['School_ID'] == school_id].sort_values('Year_Start')

        # Limit to requested years
        if len(school_trends) > years:
            school_trends = school_trends.tail(years)

        yearly_data = []
        for _, row in school_trends.iterrows():
            yearly_data.append({
                'year': row['Year'],
                'reading_pass_rate': self._safe_float(row['Reading_Pass_Rate']),
                'math_pass_rate': self._safe_float(row['Math_Pass_Rate']),
                'science_pass_rate': self._safe_float(row['Science_Pass_Rate']),
                'history_pass_rate': self._safe_float(row['History_Pass_Rate']),
                'overall_pass_rate': self._safe_float(row['Overall_Pass_Rate'])
            })

        return {
            'found': True,
            'school_name': school['school_name'],
            'school_type': school['school_type'],
            'years_included': len(yearly_data),
            'yearly_data': yearly_data,
            'trends': {
                'reading': school['reading_trend'],
                'math': school['math_trend'],
                'science': school['science_trend'],
                'overall': school['overall_trend']
            },
            'trend_slopes': {
                'reading': self._safe_float(school['reading_trend_slope']),
                'math': self._safe_float(school['math_trend_slope']),
                'overall': self._safe_float(school['overall_trend_slope'])
            }
        }

    def compare_schools(self, school_names: List[str]) -> pd.DataFrame:
        """
        Compare multiple schools side-by-side.

        Args:
            school_names: List of school names to compare

        Returns:
            DataFrame with comparison data
        """
        comparisons = []

        for name in school_names:
            perf = self.get_school_performance(name)
            if perf['found']:
                score = self.calculate_school_quality_score(name)
                comparisons.append({
                    'school_name': perf['school_name'],
                    'school_type': perf['school_type'],
                    'quality_score': score['score'],
                    'rating': score['rating'],
                    'recent_overall': perf['recent_overall_pass_rate'],
                    'recent_reading': perf['recent_reading_pass_rate'],
                    'recent_math': perf['recent_math_pass_rate'],
                    'recent_science': perf['recent_science_pass_rate'],
                    'avg_overall': perf['avg_overall_pass_rate'],
                    'trend': perf['overall_trend'],
                    'performance_category': perf['performance_category']
                })

        return pd.DataFrame(comparisons)

    def search_schools(self, query: str, limit: int = 20) -> pd.DataFrame:
        """
        Search schools by name.

        Args:
            query: Search string (case-insensitive)
            limit: Maximum number of results

        Returns:
            DataFrame of matching schools
        """
        df = self.summary
        matches = df[df['school_name'].str.upper().str.contains(query.upper(), na=False)]
        return matches[['school_name', 'school_type', 'performance_category',
                       'recent_overall_pass_rate', 'overall_trend']].head(limit)

    def get_schools_by_type(self, school_type: str) -> pd.DataFrame:
        """
        Get all schools of a specific type.

        Args:
            school_type: Type ('Elem', 'Middle', 'High', 'Combined', 'Other')

        Returns:
            DataFrame of schools
        """
        df = self.summary
        return df[df['school_type'].str.upper() == school_type.upper()].copy()

    def get_schools_by_performance(self, category: str) -> pd.DataFrame:
        """
        Get schools by performance category.

        Args:
            category: 'Excellent', 'Good', 'Fair', 'Needs Improvement'

        Returns:
            DataFrame of schools in that category
        """
        df = self.summary
        return df[df['performance_category'] == category].copy()

    def get_top_schools(self, n: int = 10, school_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get top performing schools.

        Args:
            n: Number of schools to return
            school_type: Optional filter by type

        Returns:
            DataFrame of top schools
        """
        df = self.summary
        if school_type:
            df = df[df['school_type'].str.upper() == school_type.upper()]

        return df.nlargest(n, 'recent_overall_pass_rate')[
            ['school_name', 'school_type', 'recent_overall_pass_rate',
             'avg_overall_pass_rate', 'overall_trend', 'performance_category']
        ]

    def get_statistics(self) -> Dict:
        """
        Get summary statistics about school performance.

        Returns:
            Dict with dataset statistics
        """
        df = self.summary

        # Performance category distribution
        category_counts = df['performance_category'].value_counts().to_dict()

        # School type distribution
        type_counts = df['school_type'].value_counts().to_dict()

        # Trend distribution
        trend_counts = df['overall_trend'].value_counts().to_dict()

        # Pass rate statistics
        pass_rate_stats = {
            'reading': {
                'mean': round(df['avg_reading_pass_rate'].mean(), 1),
                'median': round(df['avg_reading_pass_rate'].median(), 1),
                'min': round(df['avg_reading_pass_rate'].min(), 1),
                'max': round(df['avg_reading_pass_rate'].max(), 1)
            },
            'math': {
                'mean': round(df['avg_math_pass_rate'].mean(), 1),
                'median': round(df['avg_math_pass_rate'].median(), 1),
                'min': round(df['avg_math_pass_rate'].min(), 1),
                'max': round(df['avg_math_pass_rate'].max(), 1)
            },
            'science': {
                'mean': round(df['avg_science_pass_rate'].mean(), 1),
                'median': round(df['avg_science_pass_rate'].median(), 1),
                'min': round(df['avg_science_pass_rate'].min(), 1),
                'max': round(df['avg_science_pass_rate'].max(), 1)
            },
            'overall': {
                'mean': round(df['avg_overall_pass_rate'].mean(), 1),
                'median': round(df['avg_overall_pass_rate'].median(), 1),
                'min': round(df['avg_overall_pass_rate'].min(), 1),
                'max': round(df['avg_overall_pass_rate'].max(), 1)
            }
        }

        # Top/bottom schools
        top_schools = df.nlargest(5, 'recent_overall_pass_rate')[
            ['school_name', 'recent_overall_pass_rate']
        ].to_dict('records')

        bottom_schools = df.nsmallest(5, 'recent_overall_pass_rate')[
            ['school_name', 'recent_overall_pass_rate']
        ].to_dict('records')

        return {
            'total_schools': len(df),
            'school_types': type_counts,
            'performance_categories': category_counts,
            'trends': trend_counts,
            'pass_rate_statistics': pass_rate_stats,
            'top_schools': top_schools,
            'bottom_schools': bottom_schools,
            'data_source': 'Virginia Department of Education (VDOE) SOL Results',
            'data_years': '2020-2021 to 2024-2025',
            'county': 'Fairfax County, VA'
        }


def example_usage():
    """Example usage of FairfaxSchoolPerformanceAnalysis."""

    print("=" * 70)
    print("FAIRFAX SCHOOL PERFORMANCE ANALYSIS - Example Usage")
    print("=" * 70)

    analyzer = FairfaxSchoolPerformanceAnalysis()
    stats = analyzer.get_statistics()

    print(f"\nLoaded {stats['total_schools']} schools")
    print(f"School types: {stats['school_types']}")
    print(f"Performance categories: {stats['performance_categories']}")

    # Example 1: Get school performance
    print("\n--- Example 1: Get School Performance ---")
    perf = analyzer.get_school_performance("Terraset Elementary")
    if perf['found']:
        print(f"School: {perf['school_name']} ({perf['school_type']})")
        print(f"Recent Overall: {perf['recent_overall_pass_rate']}%")
        print(f"5-Year Average: {perf['avg_overall_pass_rate']}%")
        print(f"Trend: {perf['overall_trend']}")
        print(f"Category: {perf['performance_category']}")

    # Example 2: Calculate quality score
    print("\n--- Example 2: Quality Score ---")
    score = analyzer.calculate_school_quality_score("Terraset Elementary")
    print(f"Quality Score: {score['score']}/100 ({score['rating']})")
    print(f"Analysis: {score['analysis']}")

    # Example 3: Compare schools
    print("\n--- Example 3: Compare Schools ---")
    comparison = analyzer.compare_schools([
        "Thomas Jefferson High for Science and Technology",
        "Longfellow Middle",
        "Terraset Elementary"
    ])
    print(comparison.to_string(index=False))

    print("\n" + "=" * 70)


if __name__ == "__main__":
    example_usage()
