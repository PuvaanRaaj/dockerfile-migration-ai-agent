import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


def extract_dockerfile(text: str) -> str:
    pattern = r"```dockerfile\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()

    pattern = r"```\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        if content.startswith("FROM "):
            return content

    return ""


@dataclass
class FileBlock:
    path: Optional[str]
    content: str


def extract_file_blocks(text: str) -> List[FileBlock]:
    blocks: List[FileBlock] = []
    pattern = r"```([^\n]*)\n(.*?)```"
    for match in re.finditer(pattern, text, re.DOTALL):
        info = match.group(1).strip()
        content = match.group(2).strip()
        path: Optional[str] = None

        if info.lower().startswith("file:") or info.lower().startswith("path:"):
            path = info.split(":", 1)[1].strip()
        elif "dockerfile" in info.lower() and not info.lower().startswith("bash"):
            path = "Dockerfile"

        if not content:
            continue

        if path is None and not content.startswith("FROM "):
            continue

        blocks.append(FileBlock(path=path, content=content))

    return blocks


def resolve_output_path(target: Path, path_hint: Optional[str]) -> Path:
    if not path_hint or path_hint == "Dockerfile":
        return target
    candidate = Path(path_hint)
    if candidate.is_absolute():
        return candidate
    return (target.parent / candidate).resolve()


def parse_dockerfile_from_blocks(blocks: List[FileBlock]) -> Optional[str]:
    for block in blocks:
        if block.path and Path(block.path).name == "Dockerfile":
            return block.content
    for block in blocks:
        if block.content.startswith("FROM "):
            return block.content
    return None


def migrated_output_path(path: Path) -> Path:
    if path.name == "Dockerfile":
        return path.with_name("Dockerfile.migrated")
    if path.suffix:
        return path.with_name(f"{path.stem}.migrated{path.suffix}")
    return path.with_name(f"{path.name}.migrated")


def trim_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[-max_chars:]


def default_output_path(target: Path) -> Path:
    if target.name == "Dockerfile":
        return target.with_name("Dockerfile.migrated")

    return target.with_name(f"{target.stem}.migrated{target.suffix}")


def backup_path(target: Path) -> Path:
    if target.name == "Dockerfile":
        return target.with_name("Dockerfile.backup")

    return target.with_name(f"{target.stem}.backup{target.suffix}")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_exists(path: Path) -> Optional[str]:
    if not path.exists():
        return f"File not found: {path}"
    if path.is_dir():
        return f"Expected file but found directory: {path}"
    return None
