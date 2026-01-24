# Configuration Files

Small configuration and lookup files that ARE committed to GitHub.

## Files

- `data_sources.json` - Catalog of data sources with URLs and dates
- `road_classifications.json` - Highway/collector pattern matching
- `zoning_codes.csv` - Zoning code descriptions
- `school_boundaries.json` - School attendance zone mappings

## Size Limit

Files in this directory must be < 10 MB to ensure GitHub compatibility.

## Usage

These files provide reference data and configuration for processing scripts:

```python
import json

with open('data_sources.json') as f:
    sources = json.load(f)

print(sources['sales_data']['url'])
```
