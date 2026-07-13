# Field-Year Storyline Dashboard

Generates multi-panel storyline dashboards that align Sentinel-2 NDVI, daily
weather, and CDL crop data on a shared growing-season timeline.

## Selected Field-Year (Production)

| Property | Value |
|---|---|
| Field ID | `osm-1360326432` |
| Grower / Farm | ia-grower / ia-grower-iowa |
| Years | 2021–2025 |
| Location | Iowa corn belt |

## Input Files

| File | Location |
|---|---|
| Daily weather | `growers/ia-grower/farms/ia-grower-iowa/fields/osm-1360326432/weather/daily_weather.csv` |
| CDL crop table | `growers/ia-grower/farms/ia-grower-iowa/derived/tables/ia_grower_iowa_cdl_2021_2025_full_composition.csv` |
| NDVI (Sentinel-2) | Extracted from `.../satellite/sentinel/<year>/` rasters via `scripts/extract_production_ndvi.py` |

## Weather Metrics Calculated

- Daily precipitation (PRECTOTCORR, mm)
- Cumulative precipitation (running sum)
- Daily temperature range (T2M_MIN to T2M_MAX)
- Growing Degree Days (GDD, base 10°C)
- Cumulative GDD
- Event detection: heavy rain (>20mm/day), heat (>35°C max, wave peaks only), frost (Tmin ≤0°C, spring last / fall first)

## NDVI Curve Fitting

NDVI uses a **degree-4 polynomial regression** (`numpy.polynomial.Polynomial.fit`)
fitted to merged phenology reference points and Sentinel-2 observations, producing
a smooth best-fit curve rather than interpolating through every point.

## Dashboard Image (Production)

`output/field_year_storyline_osm-1360326432_{year}.png`

Four panels with shared date axis (Apr–Oct):
1. **NDVI** — observed Sentinel-2 points (4–8 dates/year) with polynomial fit
2. **Precipitation** — daily bars + cumulative line
3. **Temperature / Extremes** — min-max fill range with frost and heat markers (heat wave peaks only)
4. **Cumulative GDD** — season accumulation with milestone annotations

Each panel includes a summary info box (peak values, totals). A season overview
bar at the top shows crop, precip, GDD, and peak NDVI.

## How to Rerun (All Years)

```bash
FIELD_DIR=/home/coder/my-farm-advisor-runtime/data-pipeline/growers/ia-grower/farms/ia-grower-iowa/fields/osm-1360326432
SKILL_DIR=/home/coder/.config/opencode/skills/my-farm-advisor/field-year-storyline
PYTHON=/home/coder/my-farm-advisor-runtime/data-pipeline/.venv/bin/python
CDL=/home/coder/my-farm-advisor-runtime/data-pipeline/growers/ia-grower/farms/ia-grower-iowa/derived/tables/ia_grower_iowa_cdl_2021_2025_full_composition.csv

for year in 2021 2022 2023 2024 2025; do
  # Extract NDVI
  $PYTHON $SKILL_DIR/scripts/extract_production_ndvi.py \
    --field-dir $FIELD_DIR --year $year --source Sentinel-2 \
    --output /tmp/ndvi_osm-1360326432_${year}.csv

  # Generate dashboard
  $PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py \
    --field osm-1360326432 \
    --weather-field osm-1360326432 \
    --year $year \
    --weather $FIELD_DIR/weather/daily_weather.csv \
    --cdl $CDL \
    --ndvi-stats /tmp/ndvi_osm-1360326432_${year}.csv \
    --output-dir $SKILL_DIR/output
done
```

## Data Limitations

- **NDVI source:** Sentinel-2 10m (4–8 dates/year). Cloud cover and revisit
  schedule limit clear-sky observations during the growing season.
- **Late-season NDVI:** Late-season scenes include senescent crop or residue
  after harvest.
- **Weather resolution:** NASA POWER at 0.5° grid, smoothing local variability.
