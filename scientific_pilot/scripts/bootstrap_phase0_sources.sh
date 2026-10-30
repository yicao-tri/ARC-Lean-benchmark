#!/usr/bin/env bash
# Create only the missing Phase 0 source clones at the exact locked commits.
# Usage: bash scientific_pilot/scripts/bootstrap_phase0_sources.sh "$ARC_RESOURCE_ROOT"
set -euo pipefail

RESOURCE_ROOT=${1:?"pass the absolute ARC resources directory"}

clone_locked() {
  local repo_url=$1
  local directory=$2
  local commit=$3
  local destination="${RESOURCE_ROOT}/${directory}"
  if [ -e "${destination}" ]; then
    echo "refusing to overwrite existing path: ${destination}" >&2
    return 1
  fi
  git clone "${repo_url}" "${destination}"
  git -C "${destination}" checkout --detach "${commit}"
  if [ "$(git -C "${destination}" rev-parse HEAD)" != "${commit}" ]; then
    echo "commit verification failed for ${destination}" >&2
    return 1
  fi
}

clone_locked "https://github.com/google-deepmind/miniF2F.git" "miniF2F" "f0a20e14c1eeccd859d51bb4c2b3ee487889c303"
clone_locked "https://github.com/jmeadows17/formal-science.git" "formal-science" "89b1e0ee60a346039107279dd109d00dfe8e8252"

echo "Clones are pinned. FormalScience remains unavailable for Phase 1 until its licence/permission and Lean environment gates are resolved."
