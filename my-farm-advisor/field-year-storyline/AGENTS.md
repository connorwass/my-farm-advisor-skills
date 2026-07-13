# Local Instructions

## Purpose

This folder owns the field-year-storyline subskill: generating a multi-panel
dashboard that aligns Sentinel NDVI, daily weather, and CDL crop data on a
shared growing-season timeline for one field-year.

## Safe edit scope

Edits should stay in this folder and its children unless the user explicitly
asks for a broader skill change. Do not change parent `SKILL.md`, sibling
workflows, or root policy from a subskill task unless explicitly requested.

## Read nearby docs first

Read `GUIDE.md` first, then `README.md`. If routing context is needed, read
`../../INDEX.md` and `../../SKILL.md`.

## Local validation

Run the dashboard script and verify the output image is generated:

```bash
SKILL_DIR=my-farm-advisor/field-year-storyline
PYTHON=/home/coder/my-farm-advisor-runtime/data-pipeline/.venv/bin/python
$PYTHON $SKILL_DIR/scripts/generate_storyline_dashboard.py
ls -lh $SKILL_DIR/output/
```

Expected: one or more PNG files produced without errors.

## Local-delta-only reminder

This nested AGENTS.md only records instructions that differ from the parent or
root files. Do not duplicate root-wide asset, vendor, or validation policy here
except this pointer to `../../../AGENTS.md`.
