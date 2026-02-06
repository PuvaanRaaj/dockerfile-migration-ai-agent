## AI Assistant Guide for `gearmanworker/base-image`

This document defines how AI assistants should work in this repository. Follow these rules whenever you edit files here.

---

### 1. Scope of This Repo

- **Purpose**: Docker base image for PHP Gearman workers in the Razer Merchant Services ecosystem.
- **Key files**:
  - `Dockerfile` – main image build definition.
  - `.gitlab-ci.yml` – GitLab CI/CD pipeline for this image.
  - `README.md` – human-facing documentation.
  - `core/` – runtime configuration (PHP, NewRelic, Supervisor, scripts, etc.).

When in doubt, **prefer small, targeted changes** over broad refactors.

---

### 2. CI/CD Pipeline Rules (`.gitlab-ci.yml`)

- **Allowed stages** (as of latest changes):
  - `build`
  - `security`
  - `production`
- **Security jobs**:
  - `grype_scan/amd64` and `grype_scan/arm64` must both:
    - `extends: .grype_scan_multiarch`
    - Keep `grype_scan/arm64` with:
      - `needs: [build, grype_scan/amd64]`
      - `variables.GRYPE_SCAN_PLATFORM: "linux/arm64"`
- **Build job**:
  - `build` **must** `extends: .build_and_push_multiarch` (do not revert to `.build` unless explicitly requested).
- **Do NOT**:
  - Reintroduce `test` or `push` stages or related jobs without explicit user instruction.
  - Add new stages without explaining the impact in `README.md`.

Whenever you change `.gitlab-ci.yml`:

1. **Keep it minimal** – change only the jobs needed for the user’s request.
2. **Validate consistency** – ensure all referenced stages exist in the `stages:` list.
3. **Mirror pipeline changes in `README.md`** (see next section).

---

### 3. README Synchronization Rules (`README.md`)

The `README` must **always reflect the current pipeline**.

When you change `.gitlab-ci.yml`:

- Update the **“Testing”** and **“CI/CD Pipeline”** sections to:
  - Describe the actual list of stages.
  - Mention multi-arch Grype scanning if `grype_scan/amd64` and `grype_scan/arm64` are present.
  - Remove references to any stages or tools that no longer exist (e.g., DeepCode, push stage).
- Keep wording concise and high-level; avoid over-explaining GitLab basics.

Before finishing:

1. Re-read the affected README section.
2. Confirm there is no mismatch between the documented stages/jobs and `.gitlab-ci.yml`.

---

### 4. Dockerfile & Image Behavior

When modifying the `Dockerfile` or `core/`:

- **Goals**:
  - Preserve compatibility for existing Gearman workers.
  - Avoid breaking PHP/NewRelic/Supervisor defaults unless explicitly requested.
- **NewRelic Agent**:
  - The NewRelic PHP agent is **bundled locally** at `core/newrelic/newrelic-php5-12.4.0.29-linux.tar.gz`.
  - It is **not downloaded** during Docker build; instead, it is copied from the local file.
  - To update: download the new version from [NewRelic releases](https://download.newrelic.com/php_agent/release/), place the tar.gz in `core/newrelic/`, and update the `COPY` command in `Dockerfile`.
- **Best practices**:
  - Favor backward-compatible changes (add, don’t remove) unless the user asks for a cleanup/breaking change.
  - Keep image size reasonable; avoid unnecessary layers or large additional tools.
  - If adding new environment variables or build args, document them in `README.md` under **Configuration**.

Do **not**:

- Introduce services or daemons unrelated to Gearman workers without clear justification.
- Change ports or entrypoint behavior silently; if changed, update `README.md`.

---

### 5. Coding & Config Style

- **YAML**:
  - Use 2-space indentation.
  - Group jobs by stage with clear comments (e.g., `# Stage: security`).
- **Shell scripts**:
  - Prefer POSIX-compatible syntax unless the file is clearly Bash-only.
  - Add comments for non-obvious logic, especially around CI-related scripts.
- **PHP / INI**:
  - Avoid introducing app-specific business logic in the base image.
  - Keep configuration generic and suitable for multiple Gearman-based services.

---

### 6. Safety, Security & Secrets

- Never add real secrets (API keys, passwords, tokens) to:
  - `Dockerfile`
  - `.gitlab-ci.yml`
  - `core/` configs
  - Any other tracked file
- Use **variables** and **secret management** (GitLab CI variables, AWS/ECS secrets, etc.) instead.
- If you see hard-coded sensitive values, **flag them in your response** and suggest moving to secrets.

---

### 7. Git & Change Management

- Do **not** run destructive git commands (reset, force push, etc.).
- Keep changes **scoped to the user’s request**.
- If a change impacts multiple files (e.g., CI and README), update all relevant files in the same task.

If the user asks for a commit:

- Use a concise, meaningful message (e.g., `chore(ci): update grype multiarch scan`).
- Do not commit unrelated formatting or opportunistic cleanups unless explicitly approved.

---

### 8. How to Respond to Users

When interacting as an AI assistant:

- Be **concise and direct**; assume the user is comfortable with engineering terminology.
- For simple edits:
  - Summarize what changed in **1–3 bullet points**.
- For CI-related changes:
  - Explicitly state:
    - Which jobs/stages were added/removed/modified.
    - Any required follow-up (e.g., “this assumes `.grype_scan_multiarch` is defined in the shared `server.base-image.yml` include”).

Avoid:

- Overly long explanations of basic tools (GitLab, Docker, etc.) unless the user asks.
- Adding new tools or dependencies without explaining why they’re needed.

---

### 9. When You Are Unsure

If requirements are ambiguous:

- Prefer **minimal, reversible changes**.
- Clearly state your assumptions in the response (e.g., “Assuming you want to keep multi-arch Grype scanning and only remove the push stage…”).
- Do **not** introduce new stages or jobs “just in case”.

Always bias toward **clarity**, **safety**, and **alignment with existing patterns** in this repo.

