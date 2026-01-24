# Sales Data - Processed Files

**These files ARE committed to GitHub**

## Contents

- `combined_sales.parquet` - Filtered and optimized sales data

## File Format

Parquet format provides:
- ~100x compression vs CSV/Excel
- Columnar storage for fast queries
- Schema preservation

## Expected Size

Target: < 50 MB per file (GitHub warning threshold)

## Loading Data

```python
import pandas as pd

# Load sales data
sales = pd.read_parquet('combined_sales.parquet')
print(f"Loaded {len(sales):,} sales records")
```
