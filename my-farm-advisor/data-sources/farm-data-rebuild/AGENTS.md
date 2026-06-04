# Local Instructions

## Purpose

This folder owns deterministic rebuilds of `data/my-farm-advisor/` from a field-boundary GeoJSON input into the canonical grower, farm, field, and shared data tree.

## Safe edit scope

Edits should stay in this folder and its children unless the user explicitly asks for a broader skill change. Do not change parent `SKILL.md`, sibling workflows, or root policy from a subskill task unless explicitly requested.

## Read nearby docs first

Read `README.md` first, then `../INDEX.md` and `../../SKILL.md` for routing context. The rebuild entrypoint is `python scripts/rebuild_data_folder.py --boundaries path/to/fields.geojson` from the runtime script tree.

## Local workflow notes

- Required input: `--boundaries` pointing to field-boundary GeoJSON.
- Optional inputs: `--grower-slug`, `--farm-slug`, `--farm-name`, `--skip-downloads`, and `--keep-legacy-workdirs`.
- Use `data/my-farm-advisor/scripts/ingest/bootstrap_farm_from_county.py` before rebuilds when a county bootstrap should create or append field boundaries and inventory mappings.
- The rebuild coordinates `field-boundaries`, `ssurgo-soil`, `nasa-power-weather`, `cdl-cropland`, `farm-intelligence-reporting`, and `ssurgo-poster-cards`.

## Local validation

When runtime scripts are available, run the documented rebuild command against a small boundary fixture. Otherwise run `./scripts/validate.sh` from the repository root after structural changes.

## Local-delta-only reminder

This nested AGENTS.md only records instructions that differ from the parent or root files. Do not duplicate root-wide asset, vendor, or validation policy here except this pointer to `../../../AGENTS.md`.
