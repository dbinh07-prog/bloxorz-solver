"""Đo search time và peak memory thống nhất. Owner: thành viên 4."""

from algorithms.search_result import SearchResult
from state import State


class SearchMetrics:
    def __init__(self) -> None:
        raise NotImplementedError

    def result(
        self,
        *,
        goal_state: State | None = None,
        expanded_nodes: int = 0,
        generated_nodes: int = 0,
        peak_frontier: int = 0,
    ) -> SearchResult:
        raise NotImplementedError
