#!/usr/bin/env bash
# Requires manual approval before each PyPI publish.
#
# Run this AFTER making the repo public: required-reviewer protection is not
# available for private repos on the Free plan (the API answers 422,
# "billing plan supports"). The environment itself already exists either way.
set -euo pipefail

REPO="${1:-artapo/fusion360-mcp}"
USER_ID="$(gh api user --jq .id)"

gh api --method PUT "repos/$REPO/environments/pypi" --input - <<JSON
{"wait_timer":0,"prevent_self_review":false,
 "reviewers":[{"type":"User","id":$USER_ID}],
 "deployment_branch_policy":null}
JSON

echo "Protection applied. Current rules:"
gh api "repos/$REPO/environments/pypi" \
  --jq '.protection_rules[] | .type'
