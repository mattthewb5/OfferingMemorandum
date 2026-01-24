# Metro Transit Data

Metrorail station locations and service information.

## Data Source

WMATA Open Data:
https://developer.wmata.com/

## Contents

- Station locations (lat/lon)
- Station names and codes
- Line assignments (Silver, Orange, Blue, etc.)
- Parking availability

## Stations in Fairfax County Area

Silver Line:
- Tysons Corner
- Spring Hill
- Greensboro
- McLean
- Wiehle-Reston East
- Reston Town Center
- Herndon
- Innovation Center
- Washington Dulles International Airport
- Loudoun Gateway
- Ashburn

Orange Line:
- Vienna/Fairfax-GMU
- Dunn Loring-Merrifield
- West Falls Church

## Loading Data

```python
import pandas as pd

stations = pd.read_csv('metro_stations.csv')
fairfax_stations = stations[stations.COUNTY == 'Fairfax']
```

## Use Cases

- Transit proximity analysis
- Commute time estimation
- Property value premium calculation
