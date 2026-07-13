---
name: eda-cdl-weather-boundary
description: >
  Field-boundary, weather, and CDL EDA subskill. Compares field boundaries, weather
  patterns, and cropland data layer crop composition within a field, across fields
  within a grower, and across IA, IL, and NE growers. Generates static statistical
  visualizations, comparison tables, and a geospatial overview map.
version: 1.0.0
author: Boreal Bytes
tags: [eda, boundaries, weather, cdl, cropland, comparison, visualization]
---

# Workflow: eda-cdl-weather-boundary

## Description

Analyze field boundaries, weather time series, and CDL crop composition across
IA, IL, and NE growers. The workflow uses pre-computed farm-level tables and
boundary GeoJSONs already present in the runtime data tree. It produces static
PNG figures, CSV comparison tables, and a geospatial overview map — no
interactive dashboard.

**No soil analysis is included.**

## Comparisons Produced

| Level | What is compared |
|---|---|
| Within a field | Weather time series across years (same field, different seasons) |
| Across fields within a grower | Field size, shape compactness, weather variability, crop rotation patterns |
| Across growers (IA vs IL vs NE) | Field size distributions, temperature/precipitation gradients, CDL crop diversity, rotation frequency |

## Data Sources

All data is read from the canonical runtime tree under
`${DATA_PIPELINE_DATA_ROOT}/data-pipeline/growers/`.

| Category | Source file | Path pattern |
|---|---|---|
| Boundaries | `boundary/field_boundaries.geojson` | `growers/{grower}/farms/{farm}/boundary/` |
| Weather | `{grower}_{farm}_weather_2021_2025.csv` | `growers/{grower}/farms/{farm}/derived/tables/` |
| CDL full composition | `{grower}_{farm}_cdl_2021_2025_full_composition.csv` | `growers/{grower}/farms/{farm}/derived/tables/` |
| Crop rotation | `{grower}_{farm}_crop_rotation.csv` | `growers/{grower}/farms/{farm}/derived/tables/` |

## Requirements

```bash
pip install pandas numpy matplotlib seaborn scipy geopandas shapely
```

All dependencies are pre-installed in the runtime venv at
`${DATA_PIPELINE_DATA_ROOT}/data-pipeline/.venv/`.

## Scripts

### `scripts/run_all.py`

Single orchestrator that generates all analysis outputs in one invocation.

**Outputs** (all written to `${DATA_PIPELINE_DATA_ROOT}/data-pipeline/eda/eda-cdl-weather-boundary/output/`):

| File | Description |
|---|---|
| `field_boundary_viz.png` | Field size histogram + compactness violin |
| `field_boundary_comparison.csv` | ANOVA table and per-grower summary stats |
| `weather_viz.png` | Monthly T2M trends + monthly precipitation violins |
| `weather_correlation.csv` | Pearson r (T2M vs precip) per grower |
| `cdl_viz.png` | Crop composition stacked bars + rotation frequency bars |
| `cdl_diversity_comparison.csv` | Shannon diversity by grower × year |
| `geospatial_overview.png` | All 30 field boundaries colored by grower |

### Quick Start

```bash
export DATA_PIPELINE_DATA_ROOT=/home/coder/my-farm-advisor-runtime
PYTHON=${DATA_PIPELINE_DATA_ROOT}/data-pipeline/.venv/bin/python
SKILL_DIR=/home/coder/my-farm-advisor-skills/my-farm-advisor/eda/eda-cdl-weather-boundary

mkdir -p ${DATA_PIPELINE_DATA_ROOT}/data-pipeline/eda/eda-cdl-weather-boundary/output

$PYTHON ${SKILL_DIR}/scripts/run_all.py
```

## Output Interpretation

### Field Boundaries

- **Size histogram:** IA fields are expected to be largest (prairie region, regular
  land surveys), IL fields smallest (fragmented ownership), NE intermediate.
- **Compactness violin:** Values near 1 are near-circular (e.g., center-pivot
  circles in NE). Higher values indicate irregular shapes (e.g., IL fields along
  rivers or section lines).

### Weather

- **Monthly T2M trend:** NE is coldest, IA moderate, IL warmest — a latitudinal
  gradient of ~1°C per degree of latitude across the growing season.
- **Precip violins:** IL tends to receive more summer precipitation. Field-to-field
  variability within a grower indicates microclimate or drainage differences.
- **T2M vs precip correlation:** Tests whether warmer fields are also drier.

### CDL / Cropland

- **Composition bars:** All growers should be overwhelmingly corn-soy. "Other"
  categories suggest conservation set-aside or specialty crops.
- **Rotation frequency:** Classic 2-year corn-soy rotation is expected. Continuous
  corn signals high-intensity management.
- **Diversity trend:** Shannon index is expected to be low (<1.0) and stable across
  years. A dip indicates a grower concentrated acres into a single crop.

## Story Summary

The three growers span a north-south transect of the US corn belt:

- **Nebraska** — northern edge, cooler/drier, potential for center-pivot irrigation
- **Iowa** — central corn belt, large fields, classic corn-soy rotation
- **Illinois** — southern corn belt, warmer/wetter, potentially smaller more
  fragmented fields

Together they illustrate how field characteristics, climate, and management
decisions vary across the region while maintaining the corn-soy production system
that defines the midwestern agricultural landscape.
