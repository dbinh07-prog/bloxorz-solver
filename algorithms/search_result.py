"""Ket qua chung de cac solver va GUI cung su dung."""


class SearchResult:
    def __init__(
        self,
        path=None,
        expanded_nodes=0,
        generated_nodes=0,
        peak_frontier=0,
        search_time=0.0,
        memory_usage=0,
        solution_cost=0.0,
        found=False,
    ):
        raise NotImplementedError

    @property
    def memory_usage_mb(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError
