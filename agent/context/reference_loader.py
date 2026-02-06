from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class ReferenceEntry:
    path: Path
    content: str
    truncated: bool = False


@dataclass
class ReferenceBundle:
    entries: List[ReferenceEntry]
    total_chars: int
    skipped_files: int


class ReferenceLoader:
    def __init__(
        self,
        repo_root: Path,
        globs: Iterable[str],
        max_total_chars: int,
        max_chars_per_file: int,
    ) -> None:
        self.repo_root = repo_root
        self.globs = list(globs)
        self.max_total_chars = max_total_chars
        self.max_chars_per_file = max_chars_per_file

    def _collect_paths(self) -> List[Path]:
        paths = set()
        for pattern in self.globs:
            for path in self.repo_root.glob(pattern):
                if path.is_file():
                    paths.add(path.resolve())
        return sorted(paths)

    def load(self) -> ReferenceBundle:
        entries: List[ReferenceEntry] = []
        total_chars = 0
        skipped_files = 0

        for path in self._collect_paths():
            rel_path = path.relative_to(self.repo_root)
            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                skipped_files += 1
                continue

            truncated = False
            if len(content) > self.max_chars_per_file:
                content = content[: self.max_chars_per_file]
                content += "\n# ... truncated ...\n"
                truncated = True

            if total_chars + len(content) > self.max_total_chars:
                skipped_files += 1
                continue

            entries.append(ReferenceEntry(path=rel_path, content=content, truncated=truncated))
            total_chars += len(content)

        return ReferenceBundle(entries=entries, total_chars=total_chars, skipped_files=skipped_files)
