import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass
class RelatedFile:
    path: Path
    reason: str
    is_binary: bool
    size_bytes: int


@dataclass
class RelatedFilesResult:
    files: List[RelatedFile]
    skipped: List[str]
    binary_files: List[Path]


def _join_lines(dockerfile_text: str) -> List[str]:
    lines: List[str] = []
    buffer = ""
    for raw in dockerfile_text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
            continue
        buffer += stripped
        lines.append(buffer)
        buffer = ""
    if buffer:
        lines.append(buffer)
    return lines


def _parse_copy_sources(line: str) -> Tuple[List[str], Optional[str]]:
    match = re.match(r"^(COPY|ADD)\s+(.+)$", line, re.IGNORECASE)
    if not match:
        return [], None

    payload = match.group(2).strip()
    has_from = "--from=" in payload

    json_start = payload.find("[")
    json_end = payload.rfind("]")
    if json_start != -1 and json_end != -1 and json_end > json_start:
        try:
            json_payload = payload[json_start : json_end + 1]
            items = json.loads(json_payload)
            if not isinstance(items, list) or len(items) < 2:
                return [], None
            if has_from:
                return [], None
            return items[:-1], "json"
        except json.JSONDecodeError:
            return [], None

    try:
        tokens = shlex.split(payload, comments=False, posix=True)
    except ValueError:
        return [], None

    if any(token.startswith("--from=") for token in tokens):
        return [], None

    tokens = [t for t in tokens if not t.startswith("--")]
    if len(tokens) < 2:
        return [], None

    return tokens[:-1], "shell"


def _is_probably_binary(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except Exception:
        return True
    if b"\x00" in data[:1024]:
        return True
    try:
        data.decode("utf-8")
        return False
    except UnicodeDecodeError:
        return True


def _expand_source(source: str, base_dir: Path) -> List[Path]:
    if source.startswith("http://") or source.startswith("https://"):
        return []
    cleaned = source.lstrip("/")
    if any(char in cleaned for char in "*?["):
        return [p for p in base_dir.glob(cleaned) if p.is_file()]
    path = base_dir / cleaned
    return [path] if path.exists() else []


def discover_related_files(
    dockerfile_path: Path,
    dockerfile_text: str,
    max_files: int = 40,
    max_file_bytes: int = 200_000,
) -> RelatedFilesResult:
    base_dir = dockerfile_path.parent
    files: List[RelatedFile] = []
    skipped: List[str] = []
    binary_files: List[Path] = []

    seen: set[Path] = set()

    for line in _join_lines(dockerfile_text):
        sources, _ = _parse_copy_sources(line)
        if not sources:
            continue
        for source in sources:
            for path in _expand_source(source, base_dir):
                if path in seen:
                    continue
                seen.add(path)
                if path.is_dir():
                    skipped.append(f"Directory skipped: {path}")
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    skipped.append(f"Unreadable file: {path}")
                    continue
                if size > max_file_bytes:
                    skipped.append(f"Large file skipped: {path} ({size} bytes)")
                    continue
                is_binary = _is_probably_binary(path)
                if is_binary:
                    binary_files.append(path)
                    continue
                files.append(
                    RelatedFile(
                        path=path,
                        reason=f"Referenced by: {line}",
                        is_binary=is_binary,
                        size_bytes=size,
                    )
                )
                if len(files) >= max_files:
                    skipped.append("Related file limit reached.")
                    return RelatedFilesResult(files=files, skipped=skipped, binary_files=binary_files)

    return RelatedFilesResult(files=files, skipped=skipped, binary_files=binary_files)


def list_newrelic_tarballs(paths: Sequence[Path]) -> List[Path]:
    tarballs: List[Path] = []
    for path in paths:
        if path.name.startswith("newrelic-php5-") and path.suffixes[-2:] == [".tar", ".gz"]:
            tarballs.append(path)
    return tarballs
