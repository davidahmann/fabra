#!/usr/bin/env bash
set -euo pipefail

# Deploy the Supabase Edge Function used by the docs-site search modal.
#
# Requirements:
# - `supabase` CLI installed
# - authenticated (`supabase login`) OR `SUPABASE_ACCESS_TOKEN` set
# - `OPENAI_API_KEY` set in Supabase secrets for the project
#
# Usage:
#   bash scripts/deploy_supabase_search.sh
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/docs-site/.env.local"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: missing ${ENV_FILE} (needs NEXT_PUBLIC_SUPABASE_URL)" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

if [[ -z "${NEXT_PUBLIC_SUPABASE_URL:-}" ]]; then
  echo "ERROR: NEXT_PUBLIC_SUPABASE_URL not set in ${ENV_FILE}" >&2
  exit 1
fi

PROJECT_REF="$(echo "$NEXT_PUBLIC_SUPABASE_URL" | sed -E 's#^https?://([^./]+)\..*$#\1#')"
if [[ -z "$PROJECT_REF" ]]; then
  echo "ERROR: failed to derive project ref from NEXT_PUBLIC_SUPABASE_URL" >&2
  exit 1
fi

echo "Deploying function: search"
echo "Project ref: ${PROJECT_REF}"

# Keep the docs-site search endpoint public (no JWT required).
supabase functions deploy search --project-ref "$PROJECT_REF" --no-verify-jwt

echo "Done."
