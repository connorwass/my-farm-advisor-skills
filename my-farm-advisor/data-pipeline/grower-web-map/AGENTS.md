# Grower Web Map — Local Instructions

## Purpose

Generates a lightweight, self-contained interactive HTML web map for each grower, showing all farm field polygon boundaries on a Leaflet/OSM base map. The map supports zoom, pan, click-to-inspect popups (grower, farm, field, area, county, crop), and a sidebar with a field list and zoom-to-field control.

## Runtime contract

- `DATA_PIPELINE_DATA_ROOT` is required and must point to the runtime root (e.g., `~/my-farm-advisor-runtime`).
- Source lives under the subskill `src/` directory; runtime copy lives under `${DATA_PIPELINE_DATA_ROOT}/data-pipeline/grower-web-map/src/`.
- Output is written to `growers/<grower_slug>/derived/reports/grower_web_map.html`.
- No Python dependencies beyond the parent data-pipeline venv (leaflet and OSM tiles load from CDN).

## Runbook

Install into runtime:
```bash
export DATA_PIPELINE_DATA_ROOT=~/my-farm-advisor-runtime
cd my-farm-advisor/data-pipeline/grower-web-map
bash scripts/install.sh
```

Run for a grower:
```bash
export DATA_PIPELINE_DATA_ROOT=~/my-farm-advisor-runtime
"${DATA_PIPELINE_DATA_ROOT}/data-pipeline/.venv/bin/python" \
  "${DATA_PIPELINE_DATA_ROOT}/data-pipeline/grower-web-map/src/generate_grower_web_map.py" \
  --grower-slug ia-grower
```

Open the output at:
```
${DATA_PIPELINE_DATA_ROOT}/data-pipeline/growers/ia-grower/derived/reports/grower_web_map.html
```
