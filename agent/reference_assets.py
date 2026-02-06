import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from agent.knowledge_base import KnowledgeBundle


@dataclass(frozen=True)
class ReferenceAsset:
    path: Path
    version: Optional[Tuple[int, ...]]
    is_musl: bool


def _parse_version(name: str) -> Optional[Tuple[int, ...]]:
    match = re.search(r"newrelic-php5-([0-9]+(?:\.[0-9]+)*)-linux", name)
    if not match:
        return None
    parts = match.group(1).split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def _asset_from_path(path: Path) -> ReferenceAsset:
    version = _parse_version(path.name)
    is_musl = "musl" in path.name
    return ReferenceAsset(path=path, version=version, is_musl=is_musl)


def find_newrelic_assets(repo_root: Path, bundles: Iterable[KnowledgeBundle]) -> List[ReferenceAsset]:
    assets: List[ReferenceAsset] = []
    seen: set[Path] = set()

    for bundle in bundles:
        for pattern in bundle.asset_globs:
            for path in repo_root.glob(pattern):
                if not path.is_file() or "newrelic-php5-" not in path.name:
                    continue
                rel = path.relative_to(repo_root)
                if rel in seen:
                    continue
                seen.add(rel)
                assets.append(_asset_from_path(rel))

    return assets


def pick_latest_asset(assets: List[ReferenceAsset], base: Optional[str]) -> Optional[ReferenceAsset]:
    if not assets:
        return None

    filtered = assets
    if base == "alpine":
        filtered = [asset for asset in assets if asset.is_musl] or assets
    elif base == "debian":
        filtered = [asset for asset in assets if not asset.is_musl] or assets

    def sort_key(asset: ReferenceAsset) -> Tuple[int, ...]:
        return asset.version or tuple()

    return max(filtered, key=sort_key)
