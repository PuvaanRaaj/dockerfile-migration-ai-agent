from typing import List, Optional

from agent.config import AgentConfig
from agent.knowledge_base import KnowledgeBundle, load_knowledge_base


def _load() -> List[KnowledgeBundle]:
    config = AgentConfig()
    return load_knowledge_base(config.repo_root, config.knowledge_index_path).bundles


def find_group(name: str) -> Optional[KnowledgeBundle]:
    for bundle in _load():
        if bundle.id == name:
            return bundle
    return None


def list_group_names() -> List[str]:
    return [bundle.id for bundle in _load()]
