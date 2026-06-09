# maturity-by-fips

_Repo-native skill scaffold for annual county/FIPS maturity products._

---

## 📋 Purpose

This workflow owns annual maturity-by-FIPS logic for the repository, including heuristic corn RM and soybean MG outputs that reuse canonical shared data assets.

## 📦 Scope

- Annual maturity configuration and output indexing
- Shared integration points for county weather, GDD, corn RM, and soybean MG artifacts
- Future orchestration support for the annual maturity pipeline

## 🔗 Integration

- Code lives under `my-farm-advisor/strategy/maturity-by-fips/src/`
- Shared outputs live under `${DATA_PIPELINE_DATA_ROOT}/data-pipeline/shared/corn_maturity/` and `${DATA_PIPELINE_DATA_ROOT}/data-pipeline/shared/soybean_maturity/`
- Annual entrypoints live under `${DATA_PIPELINE_DATA_ROOT}/data-pipeline/src/scripts/`
