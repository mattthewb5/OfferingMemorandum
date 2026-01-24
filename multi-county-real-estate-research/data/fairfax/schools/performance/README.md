# School Performance Data

**These files ARE committed to GitHub** (small CSV files)

## Contents

School performance metrics from Virginia DOE:
- `sol_scores.csv` - SOL test pass rates by school
- `accreditation.csv` - School accreditation status
- `enrollment.csv` - Student enrollment by school

## Data Source

Virginia School Quality Profiles:
https://schoolquality.virginia.gov/

## Loading Data

```python
import pandas as pd

sol_scores = pd.read_csv('sol_scores.csv')
accreditation = pd.read_csv('accreditation.csv')
```

## Key Metrics

- **SOL Pass Rate**: % of students passing Standards of Learning tests
- **Accreditation**: State accreditation status
- **Enrollment**: Total student count

## Update Frequency

School performance data is typically updated annually after the school year ends.
