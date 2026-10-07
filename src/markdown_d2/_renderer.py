"""The long-running Node process that renders diagrams."""

from __future__ import annotations

import atexit
import contextlib
import json
import queue
import subprocess
import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any, Literal, NoReturn

from ._paths import RENDER_SCRIPT

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path


class D2Error(Exception):
    """D2 refused a diagram."""

    def __init__(self, messages: list[str]) -> None:
        super().__init__("; ".join(messages))
        self.messages = messages
        """Each problem D2 reported, such as `index.d2:4:3: unknown shape`."""


class RendererError(Exception):
    """The render process died or stopped answering."""


class ProcessExited(RendererError):
    """The render process ended, so a new one may answer."""


def node_command(node: Path) -> list[str]:
    """Return the command that starts the render script with *node*."""
    return [str(node), str(RENDER_SCRIPT)]


def d2_messages(text: str) -> list[str]:
    """Return the problems in an error D2 sent, one per item when it is a list."""
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        return [text]
    match items:
        case [*entries] if all(isinstance(e, dict) and "errmsg" in e for e in entries):
            return [str(entry["errmsg"]) for entry in entries]
        case _:
            return [text]


class Renderer:
    """One render process, started on first use and restarted once if it dies.

    Requests are sent one at a time, so threads may share a renderer.
    """

    def __init__(self, command: Sequence[str], timeout: float) -> None:
        self._command = list(command)
        self._timeout = timeout
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._replies: queue.Queue[str | None] = queue.Queue()
        self._stderr: deque[str] = deque(maxlen=40)
        self._error_reader: threading.Thread | None = None
        self._next_id = 0
        atexit.register(self.close)

    def boards(self, files: Mapping[str, str]) -> list[str]:
        """Return the path of every board of the diagram, the top board as `""`.

        Raises
        ------
        D2Error
            If D2 cannot compile the diagram.
        RendererError
            If the process dies twice or does not answer in time.
        """
        reply = self._request({"op": "boards", "files": dict(files)})
        return [str(path) for path in reply["boards"]]

    def render(
        self,
        files: Mapping[str, str],
        board: str,
        variant: Literal["light", "dark"],
        light_theme: int,
        dark_theme: int,
        salt: str,
    ) -> str:
        """Return the SVG of one board in one theme.

        Raises
        ------
        D2Error
            If D2 cannot compile or render the diagram.
        RendererError
            If the process dies twice or does not answer in time.
        """
        reply = self._request(
            {
                "op": "render",
                "files": dict(files),
                "board": board,
                "variant": variant,
                "light_theme": light_theme,
                "dark_theme": dark_theme,
                "salt": salt,
            }
        )
        return str(reply["svg"])

    def close(self) -> None:
        """Stop the process; it ends by itself once its input closes."""
        process, self._process = self._process, None
        if process is None:
            return
        if process.stdin is not None:
            with contextlib.suppress(OSError):
                process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            try:
                return self._exchange(payload)
            except ProcessExited:
                self.close()
                return self._exchange(payload)

    def _exchange(self, payload: dict[str, Any]) -> dict[str, Any]:
        process = self._process or self._start()
        self._next_id += 1
        line = json.dumps({"id": self._next_id, **payload}, ensure_ascii=False)
        try:
            assert process.stdin is not None
            process.stdin.write(line + "\n")
            process.stdin.flush()
        except OSError:
            self._exited(process)
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                text = self._replies.get(timeout=max(deadline - time.monotonic(), 0))
            except queue.Empty:
                process.kill()
                self._process = None
                raise RendererError(f"no answer within {self._timeout:g} s") from None
            if text is None:
                self._exited(process)
            reply = self._reply(text)
            if reply is not None:
                break
        if "error" in reply:
            raise D2Error(d2_messages(str(reply["error"])))
        return reply

    def _reply(self, text: str) -> dict[str, Any] | None:
        # D2 writes its own log lines to standard output, between the replies
        try:
            reply = json.loads(text)
        except json.JSONDecodeError:
            reply = None
        if isinstance(reply, dict) and reply.get("id") == self._next_id:
            return reply
        self._stderr.append(text)
        return None

    def _exited(self, process: subprocess.Popen[str]) -> NoReturn:
        process.wait()
        if self._error_reader is not None:
            self._error_reader.join(timeout=2)
        output = "".join(self._stderr).strip()
        raise ProcessExited(f"the render process exited: {output}")

    def _start(self) -> subprocess.Popen[str]:
        self._replies = queue.Queue()
        self._stderr = deque(maxlen=40)
        try:
            process = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as error:
            raise RendererError(f"cannot start {self._command[0]}: {error}") from error
        threading.Thread(
            target=self._read_replies, args=(process, self._replies), daemon=True
        ).start()
        self._error_reader = threading.Thread(
            target=self._read_errors, args=(process, self._stderr), daemon=True
        )
        self._error_reader.start()
        self._process = process
        return process

    def _read_replies(
        self, process: subprocess.Popen[str], replies: queue.Queue[str | None]
    ) -> None:
        # its own process's queue and buffer, so the end of a killed process
        # can't reach those of the one that replaced it
        assert process.stdout is not None
        for line in process.stdout:
            replies.put(line)
        replies.put(None)

    def _read_errors(self, process: subprocess.Popen[str], lines: deque[str]) -> None:
        assert process.stderr is not None
        for line in process.stderr:
            lines.append(line)
