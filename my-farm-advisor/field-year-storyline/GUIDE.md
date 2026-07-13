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

## Selected field-year

| Property | Value |
|---|---|
| CDL field ID | `OSM_1428284928` |
| Weather field ID | `271623002471299` |
| Year | 2024 |
| CDL crop | Corn (code 1) |
| Location (weather) | 47.0643°N, 95.9458°W — NW Minnesota |
| Growing season | DOY 91–304 (Apr 1 – Oct 31) |

## Data sources

| Input | Path (relative to repo root) |
|---|---|
| Daily weather (`daily_weather.csv` schema) | `weather/nasa-power-weather/examples/sample_weather_2fields_2020_2024.csv` |
| CDL crop table | `soil/cdl-cropland/examples/sample_cdl_2_fields.csv` |
| Sentinel NDVI stats | `imagery/sentinel2-imagery/examples/sample_field_stats.csv` |

## Dashboard panels

1. **NDVI** — Sentinel-derived mean NDVI over the growing season (single sample
   anchor at 2024-06-18, NDVI=0.78; full curve generated via corn phenology
   model calibrated to the anchor)
2. **Precipitation** — Daily rainfall bars + cumulative precipitation line
3. **Temperature / extremes** — Daily T2M range fill (T2M_MIN to T2M_MAX) with
   frost lines, hot-day markers
4. **Cumulative GDD** — Growing degree days (base 10°C), accumulated from
   Apr 1

## Quick start

```bash
SKILL_DIR=my-farm-advisor/field-year-storyline
PYTHON=/home/coder/my-farm-advisor-runtime/data-pipeline/.venv/bin/python

$PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py
```

Output: `SKILL_DIR/output/field_year_storyline_OSM_1428284928_2024.png`

## Data limitations

- Sample NDVI has only one observation date (2024-06-18). The full-season curve
  is modeled from corn phenology control points, calibrated to the real anchor.
- CDL and weather sample files use different field ID conventions. In a
  production pipeline these would share a unified field_id.
- The sample weather file is named `sample_weather_2fields_2020_2024.csv` but
  uses the same schema as the pipeline's `daily_weather.csv`. Point `--weather`
  to any `daily_weather.csv` for production use.
- Weather data is from NASA POWER at 0.5° grid resolution, which smooths local
  variability.
