# Dockerfile Migration Agent (Claude Agent SDK)

This project scaffolds a local agent that learns from your existing Dockerfile patterns and applies them consistently when migrating other Dockerfiles in this repo.

## What It Uses As References

The agent reads references from a unified knowledge base:

- `knowledge/index.yaml`: top-level index and global references.
- `knowledge/bundles/*/bundle.yaml`: bundle metadata (stack/base/php/tags/priority + globs).
- `knowledge/global/*.md`: global rules and response contracts.

Runtime selection is metadata-driven. The agent chooses bundle IDs from the index based on:
- user task intent (`worker`, `laravel`, `php83`, `php84`, etc.)
- target Dockerfile signals (`apk`/`apt-get`, `FROM`, path hints)
- bundle priority and applicability

You can still force bundle selection with `--reference-group`.

## Knowledge Base Layout

```text
knowledge/
  index.yaml
  global/
    rules.md
    response-format.md
  bundles/
    golden-alpine/bundle.yaml
    golden-debian/bundle.yaml
    worker-php83/bundle.yaml
    laravel-alpine-php85/bundle.yaml
    laravel-debian-php85/bundle.yaml
```

## Setup

1. Create a virtual environment and install dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure your API key.

```bash
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env`.
Set `KNOWLEDGE_INDEX_PATH` only if you want a non-default knowledge index path.

## Usage

Short command (recommended):

```bash
./bin/agent --target /path/to/Dockerfile --task "Migrate to PHP 8.3 multiarch format" --mode propose
```

Makefile shortcuts:

```bash
make setup
make agent TARGET=/path/to/Dockerfile TASK="Migrate to PHP 8.3 multiarch format"
make validate-knowledge
```

Command cheat sheet:

```bash
# Propose (read-only)
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose

# Write .migrated outputs (Dockerfile + related files)
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --write

# Apply edits directly
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode apply

# Interactive follow-ups
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --interactive

# Interactive with smaller follow-up context (cheaper)
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --interactive --followup-context-chars 2000

# Sync latest New Relic tarball (local reference -> target repo)
./bin/agent --target /path/to/Dockerfile --task "Update New Relic to latest local binary" --mode propose --sync-newrelic

# Disable related-file discovery
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --no-related

# Force base (skip Alpine/Debian prompt)
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --base alpine

# Debug mode (tool/event timing to stderr)
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --debug

# Wizard (interactive prompts for target/task/options)
./bin/agent --wizard

# Use custom knowledge index
./bin/agent --knowledge-index /path/to/knowledge/index.yaml --target /path/to/Dockerfile --task "Your task" --mode propose

# UI styling and spinner (auto-enabled on TTY, disable with --no-ui)
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --ui
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --no-ui

# Disable spinner
./bin/agent --target /path/to/Dockerfile --task "Your task" --mode propose --no-spinner
```

List available reference groups:

```bash
./bin/agent --list-reference-groups
```

Propose a migration (read-only):

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Align with golden image patterns and keep local New Relic install" \
  --mode propose
```

If the base image cannot be inferred, pass `--base`:

```bash
python -m agent \
  --target laravel-debian-php85/base-image/Dockerfile \
  --task "Migrate to PHP 8.3 multiarch format" \
  --base debian \
  --mode propose
```

Write migrated files to `.migrated` paths (Dockerfile + any related files returned by the agent):

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Align with golden image patterns and keep local New Relic install" \
  --mode propose \
  --write
```

Allow edits directly to the file:

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Align with golden image patterns and keep local New Relic install" \
  --mode apply
```

Sync the latest New Relic tarball from references into the target repo (if present):

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Update New Relic to latest local binary" \
  --mode propose \
  --sync-newrelic
```

`--sync-newrelic` only copies the asset; the agent still needs to update the Dockerfile `COPY` line.
The latest asset is chosen by version number and base (Alpine prefers `musl` builds).

Disable related file discovery:

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Migrate to PHP 8.3 multiarch format" \
  --mode propose \
  --no-related
```

Enable debug logging (tool/event timing to stderr):

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Migrate to PHP 8.3 multiarch format" \
  --mode propose \
  --debug
```

Enable interactive follow-ups:

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Migrate to PHP 8.3 multiarch format" \
  --mode propose \
  --interactive
```

If you want less context in follow-ups, lower the tail size:

```bash
python -m agent \
  --target worker-php83/base-image/Dockerfile \
  --task "Migrate to PHP 8.3 multiarch format" \
  --mode propose \
  --interactive \
  --followup-context-chars 2000
```

## Notes

- Default mode is `propose`, which only reads files and outputs a full Dockerfile (plus related files when requested).
- If the base image cannot be inferred, the CLI asks whether to use Alpine or Debian. You can set `--base` to skip the prompt.
- `--mode apply` allows the agent to use edit tools. Combine with `--backup` for safety.
- If your reference Dockerfiles grow, tune `MAX_REFERENCE_CHARS_TOTAL` and `MAX_REFERENCE_CHARS_PER_FILE`.
- Related files are expected to be returned in code blocks labeled like `file: path/to/file`.
- `--output` writes only the Dockerfile; use `--write` to emit related files too.
- Related file discovery is based on `COPY`/`ADD` statements in the target Dockerfile.
- If your task specifies a PHP version, the agent will honor it even if the references are on a different PHP version.
- UI mode (colors + spinner) is enabled automatically when stdout is a TTY. Disable with `--no-ui` or `NO_COLOR=1`.

## Knowledge Validation

Validate that all bundle patterns resolve to files:

```bash
make validate-knowledge
```
