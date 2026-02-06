# Global Migration Rules

1. Keep base OS and package manager conventions consistent (`apk` for Alpine, `apt-get` for Debian).
2. If the user asks for a specific PHP version, that version overrides reference PHP versions.
3. If the user does not ask for a PHP version, preserve the target repo PHP version.
4. Update related files referenced by Dockerfile `COPY` and `ADD` instructions.
5. Keep New Relic installation local-first (repo tarball + template) when pattern exists.
6. Never include binary file contents in responses.
7. Prefer minimal diffs and backward-compatible changes unless user requests cleanup.
8. Keep multi-arch logic explicit and deterministic.
9. If `.gitlab-ci.yml` exists, enforce multi-arch pipeline shape from `gitlab-ci-multiarch-reference.yml`.
10. For GitLab CI migration, keep these required jobs:
   - `build` extends `.build_and_push_multiarch`
   - `grype_scan/amd64` extends `.grype_scan_multiarch`
   - `grype_scan/arm64` extends `.grype_scan_multiarch` with `GRYPE_SCAN_PLATFORM: linux/arm64`
   - `create_image_tag_issue_notification` with `SCRIPT_NAME: core/scripts/create-issue-notification.sh`
11. For GitLab CI migration, stages must include `build`, `security`, `production`.
