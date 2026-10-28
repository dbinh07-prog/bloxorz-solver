from multiprocessing import get_context


def _run_solver(connection, level_path, block, bridge_states, algorithm):
    try:
        from algorithms.solver import solve
        from board import Board

        result = solve(Board(level_path), block, algorithm, bridge_states)
        connection.send((result, None))
    except Exception as error:
        connection.send((None, f"{type(error).__name__}: {error}"))
    finally:
        connection.close()


class SolverJob:
    def __init__(self, level_path, block, bridge_states, algorithm):
        context = get_context("spawn")
        self.connection, sender = context.Pipe(duplex=False)
        self.process = context.Process(
            target=_run_solver,
            args=(sender, str(level_path), block.copy(), bridge_states, algorithm),
            daemon=True,
        )
        try:
            self.process.start()
        except Exception:
            self.connection.close()
            raise
        finally:
            sender.close()

    def poll(self):
        if self.connection.poll():
            try:
                message = self.connection.recv()
            except EOFError:
                message = (None, "Tiến trình solver kết thúc mà không trả kết quả.")
            self.cancel()
            return message
        if not self.process.is_alive():
            code = self.process.exitcode
            self.cancel()
            return None, f"Tiến trình solver dừng với mã lỗi {code}."
        return None

    def cancel(self):
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=0.2)
        self.connection.close()
