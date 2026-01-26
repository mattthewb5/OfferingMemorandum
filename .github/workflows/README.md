# GitHub Actions Workflows

Automated data updates for Fairfax County datasets.

## Active Workflows

### 1. Crime Data (Daily)

| Attribute | Value |
|-----------|-------|
| **File** | `fairfax_crime_etl.yml` |
| **Schedule** | Daily at 6 AM UTC (1 AM ET / 2 AM EDT) |
| **Runtime** | ~2-5 minutes |

**What it does:**
- Fetches latest crime data from Fairfax County public API
- Geocodes up to 100 new addresses per run
- Deduplicates and appends to existing dataset
- Commits updated data back to repository

**Manual trigger:**
1. Go to GitHub Actions tab
2. Select "Fairfax Crime Data - Daily Update"
3. Click "Run workflow"
4. Optionally set `max_geocode` parameter

### 2. Building Permits (Weekly)

| Attribute | Value |
|-----------|-------|
| **File** | `fairfax_permits_etl.yml` |
| **Schedule** | Weekly on Monday at 3 AM UTC (10 PM Sunday ET) |
| **Runtime** | ~2-3 minutes (incremental) |

**What it does:**
- Fetches permits issued in last 30 days
- Updates existing dataset (appends new, updates existing)
- Commits updated data back to repository

**Manual trigger:**
1. Go to GitHub Actions tab
2. Select "Fairfax Building Permits - Weekly Update"
3. Click "Run workflow"
4. Optionally check "full_refresh" for complete re-download

## How to View Runs

1. Go to GitHub repository
2. Click **"Actions"** tab
3. Select workflow from left sidebar
4. View run history and logs

## How to Manually Trigger

1. Go to **Actions** tab
2. Select workflow from left sidebar
3. Click **"Run workflow"** dropdown button (right side)
4. Set optional parameters (if any)
5. Click green **"Run workflow"** button

## Monitoring

| Status | Meaning |
|--------|---------|
| ✅ Green checkmark | Success |
| ❌ Red X | Failure (check logs) |
| 🟡 Yellow dot | Running |

**Email Notifications:**
- Go to GitHub Settings → Notifications
- Enable "Actions" notifications
- Optionally configure for failures only

## Troubleshooting

### If a workflow fails:

1. **Check the logs:**
   - Click on the failed run
   - Expand the failed step
   - Read error messages

2. **Common issues:**

   | Issue | Solution |
   |-------|----------|
   | API timeout | Wait and retry manually |
   | Geocoding service down | Run with `--no-geocode` or wait |
   | Rate limiting | Wait 15-30 minutes, retry |
   | Git conflicts | Rare - may need manual merge |
   | Package install failure | Check pip dependencies |

3. **Re-run a failed job:**
   - Click on the failed run
   - Click "Re-run all jobs" button

### To disable a workflow temporarily:

1. Open the `.yml` file
2. Comment out the `schedule:` section:
   ```yaml
   # schedule:
   #   - cron: '0 6 * * *'
   ```
3. Commit changes
4. Manual triggers still work

### To change the schedule:

Edit the cron expression in the workflow file:

```yaml
schedule:
  - cron: '0 6 * * *'  # minute hour day month day-of-week
```

**Common schedules:**
| Cron | Description |
|------|-------------|
| `'0 0 * * *'` | Daily at midnight UTC |
| `'0 6 * * *'` | Daily at 6 AM UTC |
| `'0 */6 * * *'` | Every 6 hours |
| `'0 0 * * 0'` | Weekly on Sunday |
| `'0 3 * * 1'` | Weekly on Monday at 3 AM UTC |
| `'0 0 1 * *'` | Monthly on 1st |

**Tip:** Use [crontab.guru](https://crontab.guru/) to build cron expressions.

## Resource Usage

GitHub Actions provides:
- **2,000 minutes/month** on free tier
- **3,000 minutes/month** on Pro tier

Estimated usage:
- Crime ETL: ~5 min/day × 30 days = **150 min/month**
- Permits ETL: ~3 min/week × 4 weeks = **12 min/month**
- **Total: ~162 min/month** (well within free tier)

## Data Committed

Workflows commit to these paths:

```
multi-county-real-estate-research/data/fairfax/
├── crime/processed/
│   ├── incidents.parquet
│   └── metadata.json
└── building_permits/processed/
    ├── permits.parquet
    └── metadata.json
```

Commits appear as:
- **Author:** GitHub Actions Bot
- **Message:** "Auto-update: Fairfax [crime/building permits] YYYY-MM-DD"

## Security Notes

- Workflows use `GITHUB_TOKEN` (automatic, no setup needed)
- No external secrets required
- Data sources are public APIs (no authentication)
- Write permission limited to repository only
