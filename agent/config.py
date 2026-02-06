import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentConfig:
    repo_root: Path = Path(__file__).resolve().parents[1]
    knowledge_index_path: Path = Path(
        os.getenv("KNOWLEDGE_INDEX_PATH", "knowledge/index.yaml")
    )
    max_reference_chars_total: int = int(
        os.getenv("MAX_REFERENCE_CHARS_TOTAL", "60000")
    )
    max_reference_chars_per_file: int = int(
        os.getenv("MAX_REFERENCE_CHARS_PER_FILE", "12000")
    )

    @property
    def repo_name(self) -> str:
        return self.repo_root.name
