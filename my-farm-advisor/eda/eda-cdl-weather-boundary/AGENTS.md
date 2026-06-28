# Local Instructions

## Purpose

This folder owns the eda-cdl-weather-boundary EDA subskill for field-boundary, weather, and CDL/cropland data layer exploratory analysis. It compares within a field (weather time series), across fields within a grower (boundaries, CDL, weather), and across IA, IL, and NE growers.

## Safe edit scope

Edits should stay in this folder and its children unless the user explicitly asks for a broader skill change. Do not change parent `SKILL.md`, sibling EDA workflows, or root policy from a subskill task unless explicitly requested.

## Read nearby docs first

Read `GUIDE.md` first. If routing context is needed, read `../INDEX.md` and `../../SKILL.md`.

## Local validation

Run the analysis script and verify outputs are generated:

```bash
export DATA_PIPELINE_DATA_ROOT=/home/coder/my-farm-advisor-runtime
PYTHON=${DATA_PIPELINE_DATA_ROOT}/data-pipeline/.venv/bin/python
SKILL_DIR=/home/coder/my-farm-advisor-skills/my-farm-advisor/eda/eda-cdl-weather-boundary
mkdir -p ${DATA_PIPELINE_DATA_ROOT}/data-pipeline/eda/eda-cdl-weather-boundary/output
$PYTHON ${SKILL_DIR}/scripts/run_all.py
ls -lh ${DATA_PIPELINE_DATA_ROOT}/data-pipeline/eda/eda-cdl-weather-boundary/output/
```

Expected: 7 PNGs/CSVs produced without errors.

## Local-delta-only reminder

This nested AGENTS.md only records instructions that differ from the parent or root files. Do not duplicate root-wide asset, vendor, or validation policy here except this pointer to `../../../AGENTS.md`.
