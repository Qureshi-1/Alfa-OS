import re
from typing import List

from prototype.common import Episode


class Memory:
    def __init__(self):
        self._loaded = False
        self._working_memory: List[Episode] = []
        self._long_term_memory: List[Episode] = []

    def load(self) -> None:
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def clear(self) -> None:
        self._working_memory.clear()
        self._long_term_memory.clear()

    def shutdown(self) -> None:
        self.clear()
        self._loaded = False

    def remember(self, content: str, tags: List[str] = None, importance: int = 0) -> Episode:
        episode = Episode(
            content=content,
            tags=tags or [],
            importance=importance,
        )
        self._working_memory.append(episode)
        return episode

    def recall(self, query: str = "", limit: int = 10) -> List[Episode]:
        if not query:
            return self._working_memory[-limit:]

        query_lower = query.lower()
        query_terms = {
            term
            for term in re.findall(r"[a-z0-9]+", query_lower)
            if len(term) > 1
            and term not in {"about", "does", "from", "have", "into", "that", "this", "what", "when", "where", "which", "with", "your"}
        }
        ranked: List[tuple[int, Episode]] = []
        for episode in self._working_memory:
            searchable = f"{episode.content} {' '.join(episode.tags)}".lower()
            if query_lower in searchable:
                score = len(query_terms) + 1
            else:
                episode_terms = set(re.findall(r"[a-z0-9]+", searchable))
                score = len(query_terms & episode_terms)
            if score:
                ranked.append((score, episode))

        ranked.sort(key=lambda item: (item[0], item[1].timestamp), reverse=True)
        return [episode for _, episode in ranked[:limit]]

    def get_working_memory(self) -> List[Episode]:
        return self._working_memory.copy()

    def promote_to_long_term(self, episode: Episode) -> None:
        if episode in self._working_memory:
            self._working_memory.remove(episode)
            self._long_term_memory.append(episode)

    def get_long_term_memory(self) -> List[Episode]:
        return self._long_term_memory.copy()

    def forget(self, memory_id: str) -> bool:
        for i, ep in enumerate(self._working_memory):
            if ep.id.startswith(memory_id) or ep.id == memory_id:
                self._working_memory.pop(i)
                return True
        return False
