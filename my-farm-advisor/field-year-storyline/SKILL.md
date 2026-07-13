---
name: field-year-storyline
description: >
  Field-year storyline dashboard generator. Selects a field and year from CDL
  tables, reads daily weather and Sentinel NDVI records, aligns them on a shared
  growing-season timeline, and produces a 4-panel mini-dashboard with NDVI,
  precipitation, temperature/extremes, and cumulative GDD.
version: 1.0.0
author: Connor Wass
tags: [storyline, dashboard, ndvi, weather, gdd, cdl, sentinel]
---

# field-year-storyline

Generates a field-year storyline dashboard image from pipeline sample data.

## When to use

Use this skill when you need a compact visual summary of one field's growing
season — NDVI trajectory, rainfall, temperature extremes, and GDD accumulation
on a shared date axis.

## Start here

Read `GUIDE.md` for the workflow walkthrough, then run:

```bash
python scripts/generate_storyline_dashboard.py
```

## Required inputs

**Production** (runtime data-pipeline):
- `growers/{grower}/.../fields/{field}/weather/daily_weather.csv`
- `growers/{grower}/.../derived/tables/{farm}_cdl_*_full_composition.csv`
- Landsat NDVI rasters from `.../satellite/landsat/<year>/` (extracted via `scripts/extract_production_ndvi.py`)

**Sample fallback** (committed):
- `weather/nasa-power-weather/examples/sample_weather_2fields_2020_2024.csv`
- `soil/cdl-cropland/examples/sample_cdl_2_fields.csv`
- `imagery/sentinel2-imagery/examples/sample_field_stats.csv`

## Output

`output/field_year_storyline_{field_id}_{year}.png`
