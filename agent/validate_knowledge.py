from pathlib import Path

from agent.config import AgentConfig
from agent.knowledge_base import load_knowledge_base


def _expand(repo_root: Path, patterns):
    files = []
    for pattern in patterns:
        files.extend([path for path in repo_root.glob(pattern) if path.is_file()])
    return files


def main() -> int:
    config = AgentConfig()
    kb = load_knowledge_base(config.repo_root, config.knowledge_index_path)

    print(f"Knowledge index: {kb.index_path}")
    print(f"Bundles: {len(kb.bundles)}")

    errors = []
    for bundle in kb.bundles:
        ref_files = _expand(config.repo_root, bundle.reference_globs)
        asset_files = _expand(config.repo_root, bundle.asset_globs)

        if not ref_files:
            errors.append(f"[{bundle.id}] no files match reference_globs")

        for pattern in bundle.reference_globs:
            if not _expand(config.repo_root, [pattern]):
                errors.append(f"[{bundle.id}] no files matched pattern: {pattern}")

        for pattern in bundle.asset_globs:
            if not _expand(config.repo_root, [pattern]):
                errors.append(f"[{bundle.id}] no files matched asset pattern: {pattern}")

        print(
            f"- {bundle.id}: refs={len(ref_files)} assets={len(asset_files)} "
            f"base={bundle.base_os or '-'} stack={bundle.stack or '-'} php={bundle.php_tag or '-'}"
        )

    if errors:
        print("\nKnowledge validation failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print("\nKnowledge validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
