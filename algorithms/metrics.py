import tracemalloc
import time
from algorithms.search_result import SearchResult
from state import State


class SearchMetrics:
    def __init__(self):
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        tracemalloc.reset_peak()
        self.time_starting=time.perf_counter()


    def result(
        self,
        *,
        goal_state: State | None = None,
        expanded_nodes: int = 0,
        generated_nodes: int = 0,
        peak_frontier: int = 0,
    ) -> SearchResult:


        self.search_time=time.perf_counter()-self.time_starting
        current_memory, peak_memory=tracemalloc.get_traced_memory()
        tracemalloc.stop()

        successful_found=goal_state is not None
        return SearchResult(
            path=goal_state.get_path() if successful_found else [],
            expanded_nodes=expanded_nodes,
            generated_nodes=generated_nodes,
            peak_frontier=peak_frontier,
            search_time=self.search_time,
            memory_usage=peak_memory,
            solution_cost=goal_state.cost if successful_found else 0.0,
            found=successful_found
        )
