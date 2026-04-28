#!/usr/bin/env bash

set -u -o pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  printf 'PASS: %s\n' "$1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

warn() {
  printf 'WARN: %s\n' "$1"
  WARN_COUNT=$((WARN_COUNT + 1))
}

fail() {
  printf 'FAIL: %s\n' "$1"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/.." && pwd)

cd "${REPO_ROOT}" || {
  printf 'FAIL: could not enter repo root %s\n' "${REPO_ROOT}"
  exit 1
}

REPO_NAME=$(basename -- "${REPO_ROOT}")

EXPECTED_SKILLS=()
case "${REPO_NAME}" in
  my-farm-advisor-skills)
    EXPECTED_SKILLS=(
      my-farm-advisor
      my-farm-breeding-trial-management
      my-farm-qtl-analysis
    )
    ;;
  superior-byte-works-skills)
    EXPECTED_SKILLS=(
      wrighter
      timesfm-forecasting
    )
    ;;
  *)
    warn "No repository profile configured for ${REPO_NAME}; skill checks limited"
    ;;
esac

HAS_GIT=0
TRACKED_FILES=()
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  HAS_GIT=1
  mapfile -t TRACKED_FILES < <(git ls-files)
  pass "Git worktree metadata available"
else
  warn 'Git metadata unavailable; tracked-file checks will be skipped'
fi

tracked_prefix() {
  local prefix=$1
  local path
  for path in "${TRACKED_FILES[@]}"; do
    if [[ "${path}" == "${prefix}" || "${path}" == "${prefix}"/* ]]; then
      return 0
    fi
  done
  return 1
}

tracked_basename() {
  local name=$1
  local path
  for path in "${TRACKED_FILES[@]}"; do
    case "${path}" in
      "${name}"|*/"${name}")
        return 0
        ;;
    esac
  done
  return 1
}

bootstrap_sensitive_file() {
  local path=$1
  local label=$2
  local strict_on_existing=${3:-0}
  local context_present=${4:-0}

  if [[ -s "${path}" ]]; then
    pass "${label} present (${path})"
    return
  fi

  if (( strict_on_existing )) && (( context_present )); then
    fail "${label} missing or empty (${path})"
    return
  fi

  if [[ -e "${path}" ]]; then
    warn "${label} exists but is empty (${path})"
  else
    warn "${label} missing (${path})"
  fi
}

printf '== Validation profile: %s ==\n' "${REPO_NAME}"

bootstrap_started=0
for skill_dir in "${EXPECTED_SKILLS[@]}"; do
  if [[ -d "${skill_dir}" ]]; then
    bootstrap_started=1
    pass "Skill directory present (${skill_dir})"
    bootstrap_sensitive_file "${skill_dir}/SKILL.md" "Skill manifest for ${skill_dir}" 1 1
    bootstrap_sensitive_file "${skill_dir}/README.md" "Skill README for ${skill_dir}" 1 1
  else
    warn "Skill directory missing (${skill_dir}) [bootstrap tolerated]"
  fi
done

bootstrap_sensitive_file 'README.md' 'Root README'
bootstrap_sensitive_file 'PROVENANCE.md' 'Root provenance file' 1 "${bootstrap_started}"
bootstrap_sensitive_file 'IMPORT_MANIFEST.md' 'Root import manifest' 1 "${bootstrap_started}"

for forbidden_path in superior-byte-works-wrighter superior-byte-works-google-timesfm-forecasting; do
  if [[ -e "${forbidden_path}" ]]; then
    fail "Forbidden path present (${forbidden_path})"
  else
    pass "Forbidden path absent (${forbidden_path})"
  fi
done

for tracked_forbidden in node_modules .cache data .sisyphus; do
  if (( HAS_GIT == 0 )); then
    warn "Skipped tracked-path check for ${tracked_forbidden}/ because git metadata is unavailable"
  elif tracked_prefix "${tracked_forbidden}"; then
    fail "Forbidden tracked path detected (${tracked_forbidden}/)"
  else
    pass "Forbidden tracked path absent (${tracked_forbidden}/)"
  fi
done

for asset_name in countries.geojson states_usa.geojson; do
  if (( HAS_GIT == 0 )); then
    warn "Skipped tracked asset check for ${asset_name} because git metadata is unavailable"
  elif tracked_basename "${asset_name}"; then
    fail "Large asset is tracked (${asset_name})"
  else
    pass "Large asset not tracked (${asset_name})"
  fi
done

geoadmin_root=''
if [[ -d 'my-farm-advisor/shared/geoadmin' ]]; then
  geoadmin_root='my-farm-advisor/shared/geoadmin'
elif [[ -d 'my-farm-advisor/r2-seed-pipeline/src/data/geoadmin' ]]; then
  geoadmin_root='my-farm-advisor/r2-seed-pipeline/src/data/geoadmin'
elif [[ -d 'shared/geoadmin' ]]; then
  geoadmin_root='shared/geoadmin'
elif [[ -d 'geoadmin' ]]; then
  geoadmin_root='geoadmin'
fi

if [[ -n "${geoadmin_root}" ]]; then
  pass "Geoadmin root detected (${geoadmin_root})"
  for level in l0 l1 l2; do
    bootstrap_sensitive_file "${geoadmin_root}/${level}/metadata.json" "Geoadmin metadata ${level}" 1 1
  done
else
  warn 'Geoadmin metadata root missing [bootstrap tolerated until import]'
fi

printf '\nSummary: %d pass, %d warn, %d fail\n' "${PASS_COUNT}" "${WARN_COUNT}" "${FAIL_COUNT}"

if (( FAIL_COUNT > 0 )); then
  printf 'RESULT: FAIL\n'
  exit 1
fi

printf 'RESULT: PASS\n'
exit 0
