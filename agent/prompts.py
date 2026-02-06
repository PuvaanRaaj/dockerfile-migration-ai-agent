from pathlib import Path
from typing import List

from agent.context.reference_loader import ReferenceBundle
from agent.reference_assets import ReferenceAsset
from agent.reference_selection import SelectionResult


def _code_fence_lang(path: Path) -> str:
    name = path.name
    suffix = path.suffix.lower()

    if name == "Dockerfile" or suffix == ".dockerfile":
        return "dockerfile"
    if suffix in {".sh"}:
        return "bash"
    if suffix in {".yml", ".yaml"}:
        return "yaml"
    if suffix in {".md"}:
        return "markdown"
    if suffix in {".ini", ".conf", ".cf", ".template"}:
        return "ini"
    return "text"


def build_system_prompt(
    bundle: ReferenceBundle,
    selection: SelectionResult,
    assets: List[ReferenceAsset],
) -> str:
    parts: List[str] = []
    parts.append("You are a Dockerfile migration agent for this repository.")
    parts.append("Follow the established patterns in the reference files below.")
    parts.append("If two references conflict, prefer the selected stack bundle over golden bundles.")
    parts.append("Do not invent new tools or practices without clear evidence in references.")
    parts.append("Do not include binary file contents in responses.")
    parts.append("")
    parts.append(
        f"Selected base: {selection.base or 'unknown'} | "
        f"stack: {selection.stack or 'unknown'} | "
        f"php tag: {selection.php_tag or 'unknown'}"
    )
    if selection.selected:
        parts.append("Selected references: " + ", ".join(item.id for item in selection.selected))
    else:
        parts.append("Selected references: none")

    if assets:
        parts.append("Reference assets (binary files not in prompt):")
        for asset in assets:
            suffix = "musl" if asset.is_musl else "glibc"
            version = ".".join(str(p) for p in asset.version) if asset.version else "unknown"
            parts.append(f"- {asset.path.as_posix()} (version {version}, {suffix})")
    parts.append("")

    if not bundle.entries:
        parts.append("No reference files were loaded. Be conservative and ask for clarification.")
        parts.append("")

    for entry in bundle.entries:
        parts.append(f"### Reference: {entry.path.as_posix()}")
        parts.append(f"```{_code_fence_lang(entry.path)}")
        parts.append(entry.content)
        parts.append("```")
        if entry.truncated:
            parts.append("(reference truncated)")
        parts.append("")

    parts.append("Migration rules:")
    parts.append("- Preserve multi-stage structure and base image conventions.")
    parts.append("- Keep version pinning and local New Relic tarball usage if present.")
    parts.append("- If the user specifies a PHP version, follow it even if references differ.")
    parts.append("- If no PHP version is specified, preserve the target Dockerfile's PHP version.")
    parts.append("- Update Dockerfile-related files (entrypoint/supervisor/php configs) when they are part of the migration.")
    parts.append("- Prefer minimal, targeted changes aligned with the references.")
    parts.append("- If you cannot find a pattern, ask for guidance rather than guessing.")
    parts.append("")
    parts.append("When responding:")
    parts.append("- Explain what will change and why.")
    parts.append("- Provide each changed file in a full code block.")
    parts.append("- Use `file: <relative/path>` fence info for non-Dockerfile files.")
    parts.append("- Call out risks and required follow-up actions only when necessary.")

    return "\n".join(parts)
