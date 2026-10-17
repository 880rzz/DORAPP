#!/usr/bin/env bash
set -euo pipefail

kind="$1"
title="$2"
shift 2
for path in "$@"; do
  if [ -e "$path" ] || git ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    git add -- "$path"
  fi
done
if git diff --cached --quiet; then
  echo "No material changes for $kind"
  exit 0
fi

git config user.name "dorapp-${kind}[bot]"
git config user.email "actions@users.noreply.github.com"
git commit -m "chore(${kind}): refresh generated data"
branch="automation/${kind}/${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
git push origin "HEAD:refs/heads/${branch}"
gh pr create --base main --head "$branch" --title "$title" \
  --body "Automated, source-based update from run ${GITHUB_RUN_ID}. Review the generated diff and required CI before merging. Discovery candidates remain in review queues."
# PRs created with GITHUB_TOKEN do not emit pull_request workflow events.
gh workflow run validate.yml --ref "$branch"
