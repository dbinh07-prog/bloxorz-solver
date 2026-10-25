"""Ket qua chung de cac solver va GUI cung su dung."""


class SearchResult:
    def __init__(
        self,
        path:list[str] =None,
        expanded_nodes:int=0,
        generated_nodes:int=0,
        peak_frontier:int=0,
        search_time:float=0.0,
        memory_usage:int=0,
        solution_cost:float=0.0,
        found:bool=False,
    ):
        self.path=path if path else []
        self.expanded_nodes=expanded_nodes
        self.generated_nodes=generated_nodes
        self.peak_frontier=peak_frontier
        self.search_time=search_time
        self.memory_usage=memory_usage      # bytes used to solve problems.
        self.solution_cost=solution_cost
        self.found=found

    
    @property
    def steps(self):
        return len(self.path)

    @property
    def memory_usage_mb(self)->float:
        return self.memory_usage/(1024**2)
        

    def __str__(self):
        status="SUCCESS" if self.found else "FAILED"
        
        if self.path and self.found:
            step_counts=self.steps
            path_string="->".join(self.path)
            if step_counts>100:
                path_string=path_string[:101]+"..."
        else:
            step_counts=0
            path_string="No path found" if not self.path else "Empty Path"
        return (
            f"_________________ Search Result __________________\n"
            f"Status            :{status}\n"
            f"Solution Length   :{self.steps} moves\n"
            f"Solution Cost     :{self.solution_cost}\n"
            f"Path              :{path_string}\n"

            f"__________________ Performance _____________________\n"
            f"Expanded Nodes    :{self.expanded_nodes}\n"
            f"Generated Nodes   :{self.generated_nodes}\n"
            f"Search Time       :{self.search_time:.4f}s\n"
            f"Memory Usage      :{self.memory_usage_mb:.3f} MiB ({self.memory_usage:,}  bytes)\n"
            f"Peak Frontier     :{self.peak_frontier}\n"

            f"_____________________________________________________\n"
        )

                


        
