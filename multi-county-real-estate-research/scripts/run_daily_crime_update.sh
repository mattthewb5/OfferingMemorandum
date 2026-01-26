#!/bin/bash
# Fairfax County Crime Data Daily Update
#
# Run this script daily (e.g., via cron at 6 AM)
#
# Cron example:
#   0 6 * * * /path/to/scripts/run_daily_crime_update.sh >> /path/to/logs/crime_etl.log 2>&1
#
# What it does:
#   1. Fetches weekly crime data from Fairfax County API
#   2. Geocodes new addresses (up to 100 per run)
#   3. Deduplicates against existing data
#   4. Appends new incidents to processed/incidents.parquet
#   5. Updates metadata.json

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Log start
echo ""
echo "=================================================="
echo "FAIRFAX CRIME ETL - $(date)"
echo "=================================================="

# Change to project directory
cd "$PROJECT_DIR"

# Run ETL
python3 scripts/fairfax_crime_etl.py --fetch-weekly --max-geocode 100

# Log completion
echo ""
echo "ETL completed at $(date)"
echo "=================================================="
