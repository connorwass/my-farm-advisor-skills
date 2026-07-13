# Field-Year Storyline Dashboard

Assignment 3 skill for generating multi-panel storyline dashboards that align
Sentinel NDVI, daily weather, and CDL crop data on a shared growing-season
timeline.

## Selected Field-Year (Production)

| Property | Value |
|---|---|
| Field ID | `osm-1360394834` |
| Grower / Farm | ia-grower / ia-grower-iowa |
| Years | 2021–2025 |
| Location | Iowa corn belt |

## Input Files

**Production run** (runtime data-pipeline):

| File | Location |
|---|---|
| Daily weather | `growers/ia-grower/farms/ia-grower-iowa/fields/osm-1360394834/weather/daily_weather.csv` |
| CDL crop table | `growers/ia-grower/farms/ia-grower-iowa/derived/tables/ia_grower_iowa_cdl_2021_2025_full_composition.csv` |
| NDVI (Landsat) | Extracted from `.../satellite/landsat/<year>/` rasters via `scripts/extract_production_ndvi.py` |

**Sample fallback** (committed in repo):

| File | Location |
|---|---|
| Daily weather | `weather/nasa-power-weather/examples/sample_weather_2fields_2020_2024.csv` |
| CDL crop table | `soil/cdl-cropland/examples/sample_cdl_2_fields.csv` |
| Sentinel NDVI | `imagery/sentinel2-imagery/examples/sample_field_stats.csv` |

## Weather Metrics Calculated

- Daily precipitation (PRECTOTCORR, mm)
- Cumulative precipitation (running sum)
- Daily temperature range (T2M_MIN to T2M_MAX)
- Growing Degree Days (GDD, base 10°C)
- Cumulative GDD
- Event detection: heavy rain (>20mm/day), heat (>35°C max), frost (Tmin ≤0°C)

## Dashboard Image (Production)

`my-farm-advisor/field-year-storyline/output/field_year_storyline_osm-1360394834_2024.png`

Four panels with shared date axis (Apr–Oct):
1. **NDVI** — observed Landsat points (7 dates for 2024) with PCHIP interpolation
2. **Precipitation** — daily bars + cumulative line
3. **Temperature / Extremes** — min-max fill range with frost and heat markers
4. **Cumulative GDD** — season accumulation with milestone annotations

## How to Rerun (Production)

```bash
FIELD_DIR=/home/coder/my-farm-advisor-runtime/data-pipeline/growers/ia-grower/farms/ia-grower-iowa/fields/osm-1360394834
SKILL_DIR=/home/coder/my-farm-advisor-skills/my-farm-advisor/field-year-storyline
PYTHON=/home/coder/my-farm-advisor-runtime/data-pipeline/.venv/bin/python

# Extract NDVI
$PYTHON $SKILL_DIR/scripts/extract_production_ndvi.py \
    --field-dir $FIELD_DIR --year 2024 --output /tmp/ndvi_2024.csv

# Generate dashboard
$PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py \
    --field osm-1360394834 \
    --weather-field osm-1360394834 \
    --year 2024 \
    --weather $FIELD_DIR/weather/daily_weather.csv \
    --cdl $FIELD_DIR/../../derived/tables/ia_grower_iowa_cdl_2021_2025_full_composition.csv \
    --ndvi-stats /tmp/ndvi_2024.csv \
    --output-dir $SKILL_DIR/output
```

## Data Limitations

- **NDVI source:** Landsat 30m (4–9 dates/year). Fewer dates than Sentinel-2
  but real per-field measurements extracted from scene rasters.
- **Late-season NDVI:** Nov scenes include senescent crop or residue after
  harvest.
- **Weather resolution:** NASA POWER at 0.5° grid, smoothing local variability.
