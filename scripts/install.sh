#!/usr/bin/env bash
# Install (or update) the SDLC Factory into a target repo.
# Usage: ./scripts/install.sh /path/to/target-repo
#
# Factory-owned files are overwritten on every run, so re-running updates them:
#   .claude/agents/<factory agents>, .claude/commands/story.md, .claude/factory/,
#   docs/stories/_templates/, docs/stories/README.md
# Repo-owned files are created only if missing, never overwritten:
#   AGENTS.md, CLAUDE.md, .github/pull_request_template.md
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/target-repo" >&2
  exit 1
fi

factory="$(cd "$(dirname "$0")/.." && pwd)"
target="$(cd "$1" && pwd)"

if [ "$target" = "$factory" ]; then
  echo "Target is the factory repo itself; pick another repo." >&2
  exit 1
fi
if [ ! -d "$target/.git" ]; then
  echo "Warning: $target is not a git repo root." >&2
fi

echo "==> Installing SDLC Factory into $target"

# Factory-owned: overwrite.
mkdir -p "$target/.claude/agents" "$target/.claude/commands" "$target/docs/stories"
cp "$factory"/.claude/agents/*.md "$target/.claude/agents/"
cp "$factory/.claude/commands/story.md" "$target/.claude/commands/story.md"
rm -rf "$target/.claude/factory"
mkdir -p "$target/.claude/factory"
cp "$factory/.claude/factory/RULES.md" "$target/.claude/factory/RULES.md"
cp -R "$factory/standards" "$target/.claude/factory/standards"
rm -rf "$target/docs/stories/_templates"
cp -R "$factory/docs/stories/_templates" "$target/docs/stories/_templates"
cp "$factory/docs/stories/README.md" "$target/docs/stories/README.md"
echo "    updated: agents, /story command, .claude/factory/, story templates"

# Record which factory version is installed.
version="$(git -C "$factory" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "$version" > "$target/.claude/factory/VERSION"

# Repo-owned: create only if missing.
if [ ! -f "$target/AGENTS.md" ]; then
  cp "$factory/templates/AGENTS.target.md" "$target/AGENTS.md"
  echo "    created: AGENTS.md (starter; fill it in)"
else
  echo "    kept:    AGENTS.md"
fi
if [ ! -f "$target/CLAUDE.md" ]; then
  echo "@AGENTS.md" > "$target/CLAUDE.md"
  echo "    created: CLAUDE.md"
else
  echo "    kept:    CLAUDE.md"
fi
if [ ! -f "$target/.github/pull_request_template.md" ]; then
  mkdir -p "$target/.github"
  cp "$factory/templates/pull_request_template.md" "$target/.github/pull_request_template.md"
  echo "    created: .github/pull_request_template.md"
else
  echo "    kept:    .github/pull_request_template.md"
fi

echo "==> Done (factory version $version). Review the changes in the target repo and commit them."
