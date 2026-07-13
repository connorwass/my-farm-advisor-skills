---
name: field-year-storyline
description: >
  Field-year storyline dashboard generator. Selects a field and year from CDL
  tables, reads daily weather and Sentinel NDVI records, aligns them on a shared
  growing-season timeline, and produces a 4-panel mini-dashboard with NDVI
  (polynomial fit), precipitation, temperature/extremes, and cumulative GDD.
version: 1.1.0
author: Connor Wass
tags: [storyline, dashboard, ndvi, weather, gdd, cdl, sentinel, polynomial]
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

## NDVI curve fitting

The NDVI panel uses a degree-4 polynomial regression (`numpy.polynomial.Polynomial.fit`)
fitted to a merged set of:
- A corn phenology reference curve (`CORN_NDVI_PHENOLOGY` — 14 anchor points from
  DOY 91–304 covering green-up, peak, and senescence)
- Any observed Sentinel-2 NDVI records for the field

This produces a smooth best-fit curve rather than interpolating through every
point, giving a more realistic vegetation trajectory when observations are sparse
(~1–5 dates per year due to cloud cover and revisit frequency).

## Required inputs

**Production** (runtime data-pipeline):
- `growers/{grower}/.../fields/{field}/weather/daily_weather.csv`
- `growers/{grower}/.../derived/tables/{farm}_cdl_*_full_composition.csv`
- Landsat NDVI rasters from `.../satellite/landsat/<year>/` (extracted via `scripts/extract_production_ndvi.py`)

## Output

`/home/coder/my-farm-advisor-runtime/field-year-storyline/field_year_storyline_{field_id}_{year}.png`
