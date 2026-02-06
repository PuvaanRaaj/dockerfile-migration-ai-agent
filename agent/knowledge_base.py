import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


@dataclass(frozen=True)
class KnowledgeBundle:
    id: str
    name: str
    description: str
    priority: int
    stack: Optional[str]
    base_os: Optional[str]
    php_tag: Optional[str]
    tags: List[str]
    reference_globs: List[str]
    asset_globs: List[str]
    applies_to_path_patterns: List[str]


@dataclass(frozen=True)
class KnowledgeBase:
    index_path: Path
    global_reference_globs: List[str]
    bundles: List[KnowledgeBundle]

    @property
    def bundle_ids(self) -> List[str]:
        return [bundle.id for bundle in self.bundles]

    def bundle_map(self) -> Dict[str, KnowledgeBundle]:
        return {bundle.id: bundle for bundle in self.bundles}


def _as_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _load_document(path: Path):
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        return json.loads(text)

    if suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise ModuleNotFoundError(
                f"PyYAML is required to parse {path}. Install it or switch to JSON manifests."
            )
        return yaml.safe_load(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if yaml is None:
            raise ValueError(f"Unsupported knowledge format for {path}")
        return yaml.safe_load(text)


def _load_bundle(manifest_path: Path) -> KnowledgeBundle:
    data = _load_document(manifest_path) or {}

    applies_to = data.get("applies_to") or {}
    return KnowledgeBundle(
        id=str(data.get("id") or manifest_path.stem),
        name=str(data.get("name") or manifest_path.stem),
        description=str(data.get("description") or ""),
        priority=int(data.get("priority") or 0),
        stack=str(data.get("stack")) if data.get("stack") is not None else None,
        base_os=str(data.get("base_os")) if data.get("base_os") is not None else None,
        php_tag=str(data.get("php_tag")) if data.get("php_tag") is not None else None,
        tags=_as_list(data.get("tags")),
        reference_globs=_as_list(data.get("reference_globs")),
        asset_globs=_as_list(data.get("asset_globs")),
        applies_to_path_patterns=_as_list(applies_to.get("path_patterns")),
    )


def load_knowledge_base(repo_root: Path, index_path: Path) -> KnowledgeBase:
    resolved_index = index_path if index_path.is_absolute() else repo_root / index_path
    index_data = _load_document(resolved_index) or {}

    manifests = index_data.get("bundles") or []
    bundles: List[KnowledgeBundle] = []
    for entry in manifests:
        manifest_rel = entry.get("manifest") if isinstance(entry, dict) else entry
        if not manifest_rel:
            continue
        manifest_path = repo_root / str(manifest_rel)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Knowledge manifest not found: {manifest_path}")
        bundles.append(_load_bundle(manifest_path))

    if not bundles:
        raise ValueError("No bundles found in knowledge index.")

    return KnowledgeBase(
        index_path=resolved_index,
        global_reference_globs=_as_list(index_data.get("global_reference_globs")),
        bundles=sorted(bundles, key=lambda item: item.priority, reverse=True),
    )
