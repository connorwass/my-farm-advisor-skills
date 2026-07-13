# Field-Year Storyline Dashboard

Assignment 3 skill for generating multi-panel storyline dashboards that align
Sentinel NDVI, daily weather, and CDL crop data on a shared growing-season
timeline.

## Selected Field-Year

| Property | Value |
|---|---|
| CDL field ID | OSM_1428284928 |
| Weather field ID | 271623002471299 |
| Years | 2020–2024 |
| Primary year | 2024 |
| CDL crop (2024) | Corn |

## Input Files

All inputs from `data-pipeline` and its children:

| File | Location |
|---|---|
| Daily weather (`daily_weather.csv`) | `weather/nasa-power-weather/examples/sample_weather_2fields_2020_2024.csv` (same schema) |
| CDL crop table | `soil/cdl-cropland/examples/sample_cdl_2_fields.csv` |
| Sentinel NDVI | `imagery/sentinel2-imagery/examples/sample_field_stats.csv` |

## Weather Metrics Calculated

- Daily precipitation (PRECTOTCORR, mm)
- Cumulative precipitation (running sum)
- Daily temperature range (T2M_MIN to T2M_MAX)
- Growing Degree Days (GDD, base 10°C)
- Cumulative GDD
- Event detection: heavy rain (>20mm/day), heat (>35°C max), frost (Tmin ≤0°C)

## Dashboard Image

`my-farm-advisor/field-year-storyline/output/field_year_storyline_OSM_1428284928_2024.png`

Four panels with shared date axis (Apr–Oct):
1. **NDVI** — modeled full-season curve anchored on Sentinel-2 sample (0.78 on Jun 18)
2. **Precipitation** — daily bars + cumulative line
3. **Temperature / Extremes** — min-max fill range with frost and heat markers
4. **Cumulative GDD** — season accumulation with milestone annotations

## How to Rerun

```bash
SKILL_DIR=my-farm-advisor/field-year-storyline
PYTHON=/home/coder/my-farm-advisor-runtime/data-pipeline/.venv/bin/python

$PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py \
    --field OSM_1428284928 \
    --weather-field 271623002471299 \
    --year 2024
```

To generate all years:
```bash
for year in 2020 2021 2022 2023 2024; do
    $PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py --year $year
done
```

## Data Limitations

- **NDVI:** Only one real Sentinel-2 sample date (2024-06-18, NDVI=0.78). The
  full-season curve is generated via a corn phenology model calibrated to that
  anchor. Multi-date NDVI would improve accuracy in production.
- **Field ID mismatch:** CDL uses `OSM_*` IDs, weather uses numeric IDs. No
  cross-mapping exists in the sample data. Selection is manual.
- **Weather filename:** The sample is named `sample_weather_2fields_2020_2024.csv`
  but uses the same schema as the pipeline's `daily_weather.csv`. Use `--weather`
  to point to any `daily_weather.csv` in production.
- **Geography:** Weather field (47.06°N, 95.95°W, NW Minnesota) and CDL/NDVI
  origin (Iowa corn belt) differ. In a full pipeline run, all data shares a
  unified field_id.
- **Resolution:** NASA POWER weather is gridded at ~0.5°, smoothing local
  variability.
