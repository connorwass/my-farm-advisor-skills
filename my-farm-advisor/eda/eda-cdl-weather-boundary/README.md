# eda-cdl-weather-boundary

**Location:** `eda/eda-cdl-weather-boundary/` within `my-farm-advisor`.

Cross-grower EDA skill comparing field boundaries, weather, and CDL crop composition across IA, IL, and NE growers. Produces 8 static output files (PNG visualizations + CSV comparisons) and two HTML reports:

| File | Description |
|---|---|
| `eda_report.html` | Full EDA report with tables, PNG charts, and three interactive Leaflet field-boundary maps (one per grower) |
| `field_boundary_maps.html` | Standalone Leaflet page with three interactive maps, no surrounding report |

All outputs are written to:
```
${DATA_PIPELINE_DATA_ROOT}/data-pipeline/eda/eda-cdl-weather-boundary/output/
```
