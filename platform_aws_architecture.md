# [PLATFORM_NAME] — AWS Architecture Handoff

**Prepared for Solutions Architect Review · April 2026**

> **Name placeholder:** `[PLATFORM_NAME]` is used throughout pending trademark review. Find-and-replace when final name is confirmed.

This document defines the application-level architecture requirements for [PLATFORM_NAME], an AI-powered commercial real estate Offering Memorandum platform. It distinguishes between decisions made at the application level (which affect code) and decisions reserved for the SA (pure infrastructure).

---

## 1. Product Overview

[PLATFORM_NAME] is an AI-powered Offering Memorandum (OM) generation platform for commercial real estate brokers. It produces institutional-quality OMs by pulling from primary government data sources — deed records, permits, school performance, traffic volumes, zoning data — that no competing OM tool provides.

**Target users:** Commercial real estate brokers and brokerage firms. Output delivered to institutional investors.

**Current tech stack:**
- Python backend — context builders, data pipelines, document generation
- Streamlit front-end — 6-step wizard (interim; see Section 9 for migration path)
- WeasyPrint — HTML-to-PDF generation (planned)
- Claude API — narrative generation
- Google Maps, RentCast, ATTOM, Census, BLS — data enrichment APIs

**Deployment model:** Multi-tenant SaaS. Brokerage firms are tenants. Individual brokers are users within a firm. Billing is per generated OM at launch, with a future path to firm-wide seat licensing.

---

## 2. Architecture Requirements

| Layer | Requirement / Owner |
|---|---|
| Entry / CDN | CloudFront + custom domain. SA owns configuration. |
| Load Balancer | ALB routing to ECS Fargate. SA owns configuration. |
| Compute | ECS Fargate — containerized Streamlit app. SA owns task sizing and scaling. |
| Auth | Cognito user pool. App-level interface defined in Section 5. SA owns pool config. |
| Storage | S3 + `storage.py` abstraction. Fully defined in Section 4. Claude Code builds. |
| Database | RDS PostgreSQL. Schema defined in Section 6. SA owns instance config. |
| Secrets + Observability | Secrets Manager + CloudWatch. Interfaces defined in Section 7. SA owns wiring. |

---

## 3. Data Flow

**Broker login → OM generation → download**

1. Broker authenticates via Cognito. JWT token issued. Streamlit session state populated with `user_id`, `firm_id`, `role`.
2. Broker completes 6-step wizard. Draft state auto-saved to S3 on every field change (`draft.json` keyed by `session_id`).
3. File uploads (photos, CSVs, rent roll, T-12) written to S3 under `sessions/{firm_id}/{user_id}/{session_id}/uploads/`.
4. Broker clicks Generate. Application calls context builders sequentially, each reading from S3 and data APIs.
5. Claude API called for narrative generation. Output assembled into HTML document.
6. Generated HTML written to S3 under `sessions/{firm_id}/{user_id}/{session_id}/outputs/`.
7. Row written to `generated_oms` table in RDS. `billed` flag set to `false`.
8. Presigned S3 URL returned to broker. Browser opens HTML in new tab. Download button triggers `st.download_button`.

---

## 4. Storage Layer

### 4.1 S3 Bucket Structure

- **Environments:** Two buckets — `[platform]-prod` and `[platform]-dev`
- **Per-tenant buckets:** Not used. Per-environment buckets with firm-keyed prefixes.

**Key naming convention:**
```
tenants/{firm_id}/logos/{filename}
sessions/{firm_id}/{user_id}/{session_id}/uploads/{filename}
sessions/{firm_id}/{user_id}/{session_id}/outputs/{om_filename}
sessions/{firm_id}/{user_id}/{session_id}/draft.json
assets/templates/{filename}
```

> `firm_id` and `user_id` are stable UUIDs from Cognito. `session_id` is generated at session creation — UUID or address-slug at SA discretion.

### 4.2 `storage.py` Interface

The application never calls `open()`, `os.path`, or `boto3` directly. All file I/O goes through `storage.py`.

**Interface contract:**
```python
storage.write(key, data)           # bytes or string → None
storage.read(key)                  # key → bytes
storage.exists(key)                # key → bool
storage.delete(key)                # key → None
storage.list(prefix)               # prefix → list[str]
storage.get_url(key, expires=3600) # key → presigned URL string
```

**Backend selection:**
```
STORAGE_BACKEND=local   # reads/writes /tmp/[platform]-local/ on disk
STORAGE_BACKEND=s3      # reads/writes S3 bucket defined by S3_BUCKET env var
```

The application code never checks which backend is active. Backend selection is fully encapsulated within `storage.py`. Same key structure is mirrored on local disk for local dev.

- **Local dev:** Set `STORAGE_BACKEND=local`. No AWS account required.
- **Production:** Set `STORAGE_BACKEND=s3` and `S3_BUCKET=[bucket-name]`. SA injects via ECS task definition environment.

---

## 5. Auth Layer (Cognito)

### 5.1 Session State Contract

After successful Cognito authentication, three values are populated into Streamlit session state:
```python
current_user.user_id    # UUID — individual broker identity
current_user.firm_id    # UUID — brokerage firm identity
current_user.role       # enum: 'admin' | 'broker'
```

The application never trusts user-submitted IDs. All S3 writes and RDS rows use `firm_id` and `user_id` from session state only.

### 5.2 Roles

| Role | Permissions |
|---|---|
| broker | Create sessions, generate OMs, download outputs |
| admin | All broker permissions + manage firm users + view billing history |

Platform-level access (NewCo operations) is handled directly in AWS console, not through the application.

### 5.3 Local Dev Auth Bypass

In local mode, Cognito is bypassed entirely. A hardcoded dev user is injected into session state at startup:
```python
DEV_USER = {"user_id": "dev-user-001", "firm_id": "dev-firm-001", "role": "admin"}
```

No login screen, no token exchange. SA wires up the real Cognito integration at deployment time without any application code changes.

**SA owns:** User pool configuration, hosted UI or custom login page, JWT token validation middleware, password policy and MFA settings.

---

## 6. Database Schema (RDS PostgreSQL)

**Rule:** S3 holds files. RDS holds facts. Draft state, uploads, and generated HTML live in S3. Account data, session metadata, and billing records live in RDS.

### 6.1 firms
| Column | Type | Notes |
|---|---|---|
| firm_id | UUID PK | Stable identifier, assigned at onboarding |
| firm_name | text | Brokerage display name |
| billing_model | enum | `per_report` \| `license` |
| seat_count | int nullable | Populated for license model only |
| created_at | timestamp | |

### 6.2 users
| Column | Type | Notes |
|---|---|---|
| user_id | UUID PK | Matches Cognito identity |
| firm_id | UUID FK | → firms |
| name | text | |
| email | text | |
| role | enum | `admin` \| `broker` |
| created_at | timestamp | |

### 6.3 sessions
| Column | Type | Notes |
|---|---|---|
| session_id | UUID PK | |
| user_id | UUID FK | → users |
| firm_id | UUID FK | → firms (denormalized for query efficiency) |
| property_address | text | |
| status | enum | `draft` \| `generated` \| `archived` |
| s3_prefix | text | Pointer to session folder in S3 |
| created_at | timestamp | |
| updated_at | timestamp | |

### 6.4 generated_oms *(billing ledger)*
| Column | Type | Notes |
|---|---|---|
| om_id | UUID PK | |
| session_id | UUID FK | → sessions |
| user_id | UUID FK | → users |
| firm_id | UUID FK | → firms |
| property_address | text | |
| generated_at | timestamp | |
| billed | boolean | false until invoiced |
| s3_key | text | Pointer to output HTML in S3 |

Per-report billing: invoice on rows where `billed = false`. License billing: same table, per-row flag ignored for revenue calculation. Schema supports both models without migration.

---

## 7. Secrets + Observability

### 7.1 Secrets Management

Nothing sensitive in environment variables in production. All secrets injected via AWS Secrets Manager at runtime. The application calls `get_secret(name)` — in local dev it reads from `.env`, in production it reads from Secrets Manager. Same interface, no code changes between environments.

**Secrets inventory:**

| Secret Name | Purpose |
|---|---|
| GOOGLE_MAPS_API_KEY | Geocoding, Places, Static Maps, Street View |
| CENSUS_API_KEY | Census geocoder and demographic data |
| RENTCAST_API_KEY | Rental market data |
| ATTOM_API_KEY | Property deed and sales data |
| ANTHROPIC_API_KEY | Narrative generation via Claude API |
| BLS_API_KEY | Bureau of Labor Statistics economic data |
| DB_CONNECTION_STRING | RDS PostgreSQL connection string |
| S3_BUCKET | Active S3 bucket name for current environment |

> Adding a new secret: one entry in Secrets Manager (SA) + one line in `get_secret()` (Claude Code). No architecture changes required.

### 7.2 Metrics

**Must have — business critical:**
- OM generation count — core usage and billing signal
- Generation success / failure rate
- Generation duration

**Good to have — operational health:**
- Active session count
- API error rate by upstream service
- Fargate CPU and memory utilization

**Defer until production traffic:**
- Per-firm usage
- Wizard step abandonment rate

### 7.3 Day-One Alarms

| Condition | Action |
|---|---|
| Generation failure rate > 5% | Page immediately |
| Any Fargate task crash | Page immediately |
| Fargate CPU > 80% sustained | Warning — not page |

---

## 8. AWS Service Map

| Service | Purpose |
|---|---|
| CloudFront | CDN + custom domain. Static asset delivery. |
| ALB | Routes traffic to ECS Fargate tasks. Health checks. |
| ECS Fargate | Containerized Streamlit app. Stateless tasks. SA owns sizing and scaling. |
| Cognito | Broker authentication. User pool per environment. |
| S3 | All file I/O. Two buckets: prod and dev. |
| RDS (PostgreSQL) | Broker accounts, sessions, billing ledger. |
| Secrets Manager | All API keys and connection strings. |
| CloudWatch | Logs, metrics, alarms. |

---

## 9. Future Considerations

### 9.1 Streamlit → FastAPI + React Migration

Streamlit is correct for initial development but has known limitations at scale (per-session process model, constrained UI flexibility, limited mobile support).

The architecture is designed to make this migration low-risk:
- All business logic lives in Python context builders — not in `provenance_app.py`
- `storage.py`, `get_secret()`, and the auth session state contract are framework-agnostic
- **Migration path:** wrap Python backend with FastAPI, rewrite `provenance_app.py` in React
- S3, RDS, Cognito, Secrets Manager, CloudWatch — all untouched by the migration

**Recommended successor stack:**
- **FastAPI** — wraps Python backend as REST API. Minimal rewrite.
- **React** — wizard UI, maps (Mapbox GL JS or Google Maps JS API), data tables (AG Grid), file uploads, progress indicators.

The SA should avoid coupling infrastructure tightly to Streamlit-specific patterns.

### 9.2 Billing Model Evolution

Current: per-report billing. Future: firm-wide seat license.

The `firms` table has `billing_model` (enum) and `seat_count` (nullable int) from day one. Switching a firm from per-report to license requires one row update, not a schema change.

### 9.3 Geographic Expansion

Current coverage: Fairfax County and Loudoun County, VA. Expansion targets: Austin, Raleigh-Durham, Denver, SF Bay Area. New counties require only new data pipeline runs — no AWS architecture changes.

---

## 10. Open Questions for the SA

The following decisions are intentionally left to the SA — pure infrastructure, no effect on application code.

| Decision | Guidance |
|---|---|
| VPC / subnet design | Public/private subnet split, NAT gateway, availability zones |
| Fargate task sizing | vCPU and memory per task. Recommend profiling under load. |
| Fargate scaling policy | Target tracking vs. step scaling. Min/max task count. |
| RDS configuration | Instance class, Multi-AZ, backup retention, parameter group |
| ALB health check | Path, interval, thresholds |
| CloudFront configuration | Cache behavior, TTLs, origin shield |
| Cognito hosted UI | Hosted UI vs. custom login page. MFA policy. |
| S3 lifecycle rules | Transition to Glacier for old session outputs. Retention period. |
| CloudWatch alarm routing | SNS topics, PagerDuty or similar integration |
| Session ID format | UUID vs. address-slug for `session_id` in S3 key structure |
| Staging environment | Whether to add staging between dev and prod |

---

*Document prepared April 2026. For questions contact the NewCo development team.*
