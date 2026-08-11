# executor: disable arbitrary process spawning in hosted builds
import os

HOSTED_SANITIZED = os.environ.get("HOSTED_SANITIZED", "1") == "1"

from asyncio import create_subprocess_exec, subprocess


class Terminal:
    """
    Class for running terminal commands asynchronously.
    Disabled in hosted sanitized builds to avoid arbitrary process execution.
    """

    def __init__(self) -> None:
        self._processes = {}

    @staticmethod
    def _to_str(data: bytes) -> str:
        return data.decode("utf-8").strip()

    async def run(self, *args) -> int:
        if HOSTED_SANITIZED:
            raise RuntimeError("Process spawning disabled in hosted deployments.")
        process = await create_subprocess_exec(
            *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        pid = process.pid
        self._processes[pid] = process
        return pid

    def terminate(self, pid: int) -> bool:
        try:
            self._processes.pop(pid)
            self._processes[pid].kill()
            return True
        except KeyError:
            return False

    async def output(self, pid: int) -> str:
        output = []
        while True:
            out = self._to_str(await self._processes[pid].stdout.readline())
            if not out:
                break
            output.append(out)
        return "\n".join(output)

    async def error(self, pid: int) -> str:
        error = []
        while True:
            err = self._to_str(await self._processes[pid].stderr.readline())
            if not err:
                break
            error.append(err)
        return "\n".join(error)

    @property
    def _auto_remove_processes(self) -> None:
        while self._processes:
            for proc in list(self._processes.keys()):
                p = self._processes.get(proc)
                try:
                    if p.returncode is not None:  # process is finished
                        try:
                            del self._processes[proc]
                        except KeyError:
                            pass
                except Exception:
                    pass
