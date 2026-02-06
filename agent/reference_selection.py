import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from agent.knowledge_base import KnowledgeBundle


@dataclass
class SelectionResult:
    selected: List[KnowledgeBundle]
    base: Optional[str]
    stack: Optional[str]
    php_tag: Optional[str]
    warnings: List[str]


def detect_base(task: str, target_text: str) -> Optional[str]:
    task_lower = task.lower()
    if "alpine" in task_lower:
        return "alpine"
    if "debian" in task_lower:
        return "debian"

    text = target_text.lower()
    alpine = bool(re.search(r"^from\s+.*alpine", text, re.MULTILINE)) or "apk add" in text
    debian = bool(re.search(r"^from\s+.*debian", text, re.MULTILINE)) or "apt-get" in text

    if alpine and not debian:
        return "alpine"
    if debian and not alpine:
        return "debian"

    return None


def detect_stack(task: str, target_path: Path, target_text: str) -> Optional[str]:
    task_lower = task.lower()
    path_lower = target_path.as_posix().lower()
    text_lower = target_text.lower()

    if "laravel" in task_lower or "laravel" in path_lower or "laravel" in text_lower:
        return "laravel"
    if (
        "worker" in task_lower
        or "worker" in path_lower
        or "gearman" in task_lower
        or "gearman" in path_lower
        or "gearman" in text_lower
    ):
        return "worker"

    return None


def detect_php_tag(task: str, target_text: str) -> Optional[str]:
    text = f"{task}\n{target_text}".lower()
    match = re.search(r"php\s*([0-9]+\.[0-9]+)", text)
    if match:
        return _normalize_php_tag(match.group(1))

    match = re.search(r"php\s*([0-9]{2})\b", text)
    if match:
        return _normalize_php_tag(match.group(1))

    match = re.search(r"php([0-9]{2})\b", text)
    if match:
        return _normalize_php_tag(match.group(1))

    return None


def _normalize_php_tag(version: str) -> Optional[str]:
    if version in {"8.3", "83"}:
        return "php83"
    if version in {"8.4", "84"}:
        return "php84"
    if version in {"8.5", "85"}:
        return "php85"
    if version:
        return f"php{version.replace('.', '')}"
    return None


def _matches_target(bundle: KnowledgeBundle, target_rel_path: str) -> bool:
    if not bundle.applies_to_path_patterns:
        return True
    for pattern in bundle.applies_to_path_patterns:
        if fnmatch.fnmatch(target_rel_path, pattern):
            return True
    return False


def _score_bundle(
    bundle: KnowledgeBundle,
    target_rel_path: str,
    stack: Optional[str],
    base: Optional[str],
    php_tag: Optional[str],
) -> int:
    score = bundle.priority

    if _matches_target(bundle, target_rel_path):
        score += 20

    if stack and bundle.stack == stack:
        score += 120
    elif stack and bundle.stack and bundle.stack != "golden":
        score -= 40

    if base and bundle.base_os == base:
        score += 80
    elif base and bundle.base_os and bundle.base_os != base:
        score -= 60

    if php_tag and bundle.php_tag == php_tag:
        score += 70
    elif php_tag and bundle.php_tag and bundle.php_tag != php_tag:
        score -= 25

    return score


def _is_golden(bundle: KnowledgeBundle) -> bool:
    return bundle.stack == "golden" or "golden" in bundle.tags


def select_references(
    task: str,
    target_path: Path,
    target_text: str,
    bundles: List[KnowledgeBundle],
    base_override: Optional[str] = None,
    forced_groups: Optional[List[str]] = None,
) -> SelectionResult:
    warnings: List[str] = []
    base = base_override or detect_base(task, target_text)
    stack = detect_stack(task, target_path, target_text)
    php_tag = detect_php_tag(task, target_text)

    selected: List[KnowledgeBundle] = []
    bundle_map = {bundle.id: bundle for bundle in bundles}

    forced_groups = forced_groups or []
    for bundle_id in forced_groups:
        bundle = bundle_map.get(bundle_id)
        if bundle:
            selected.append(bundle)
        else:
            warnings.append(f"Unknown reference group: {bundle_id}")

    target_rel = target_path.as_posix()

    if base:
        golden_candidates = [
            bundle for bundle in bundles if _is_golden(bundle) and bundle.base_os == base
        ]
        if golden_candidates:
            golden = sorted(golden_candidates, key=lambda item: item.priority, reverse=True)[0]
            if golden not in selected:
                selected.append(golden)

    non_golden = [bundle for bundle in bundles if not _is_golden(bundle)]
    ranked = sorted(
        non_golden,
        key=lambda item: _score_bundle(item, target_rel, stack, base, php_tag),
        reverse=True,
    )

    primary = ranked[0] if ranked else None
    if primary and _score_bundle(primary, target_rel, stack, base, php_tag) > 0:
        if primary not in selected:
            selected.append(primary)

        if php_tag and primary.php_tag and primary.php_tag != php_tag:
            warnings.append(
                f"No exact {php_tag} bundle found. Using {primary.id} ({primary.php_tag}) as closest reference."
            )

    if not selected:
        warnings.append("No reference groups selected. Using only global rules.")

    return SelectionResult(
        selected=selected,
        base=base,
        stack=stack,
        php_tag=php_tag,
        warnings=warnings,
    )
