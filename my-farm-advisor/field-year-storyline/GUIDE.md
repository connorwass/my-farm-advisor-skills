---
name: field-year-storyline
description: >
  Generates a 4-panel storyline dashboard for a selected field-year using CDL,
  daily weather, and Sentinel NDVI from the data-pipeline sample data.
version: 1.0.0
author: Connor Wass
tags: [storyline, dashboard, ndvi, weather, gdd, cdl]
---

# Workflow: field-year-storyline

## Description

Select one field and one year, identify the crop from CDL tables, read daily
weather records and Sentinel NDVI, align them on a shared growing-season
timeline, and produce a mini-dashboard with plot annotations and event
captions.

## Selected field-year (production)

| Property | Value |
|---|---|
| Field ID | `osm-1360394834` |
| Grower / Farm | ia-grower / ia-grower-iowa |
| Years | 2021–2025 |
| Location | Iowa corn belt |
| Growing season | DOY 91–304 (Apr 1 – Oct 31) |

## Data sources

| Input | Path |
|---|---|
| Daily weather | Runtime: `growers/ia-grower/.../fields/osm-1360394834/weather/daily_weather.csv` |
| CDL crop table | Runtime: `growers/ia-grower/.../derived/tables/ia_grower_iowa_cdl_2021_2025_full_composition.csv` |
| NDVI (Landsat) | Runtime: `.../satellite/landsat/<year>/landsat_<date>_ndvi.tif` (extracted via `scripts/extract_production_ndvi.py`) |
| Sample inputs | Also usable from `weather/.../examples/`, `soil/.../examples/`, `imagery/.../examples/` |

## Dashboard panels

1. **NDVI** — Landsat-derived mean NDVI with observed points (4–9 dates/year)
   and PCHIP interpolation between them
2. **Precipitation** — Daily rainfall bars + cumulative precipitation line
3. **Temperature / extremes** — Daily T2M range fill (T2M_MIN to T2M_MAX) with
   frost lines, hot-day markers
4. **Cumulative GDD** — Growing degree days (base 10°C), accumulated from Apr 1

## Quick start (production run)

```bash
SKILL_DIR=my-farm-advisor/field-year-storyline
PYTHON=/home/coder/my-farm-advisor-runtime/data-pipeline/.venv/bin/python

# 1. Extract NDVI from Landsat rasters
$PYTHON $SKILL_DIR/scripts/extract_production_ndvi.py \
    --field-dir /path/to/fields/osm-1360394834 \
    --year 2024 \
    --output /tmp/ndvi_2024.csv

# 2. Generate dashboard
$PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py \
    --field osm-1360394834 \
    --weather-field osm-1360394834 \
    --year 2024 \
    --weather /path/to/fields/osm-1360394834/weather/daily_weather.csv \
    --cdl /path/to/ia_grower_iowa_cdl_2021_2025_full_composition.csv \
    --ndvi-stats /tmp/ndvi_2024.csv
```

Output: `field_year_storyline_osm-1360394834_2024.png`

## Data limitations

- Weather and CDL data is real pipeline output. NDVI is extracted from Landsat
  30m scene rasters — fewer dates than Sentinel-2 would provide but real
  per-field measurements.
- Late-season NDVI (Nov) can include senescent crop or residue after harvest.
- NASA POWER weather at 0.5° grid resolution smooths local variability.
