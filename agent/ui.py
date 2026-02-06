import os
import sys
import threading
import time
from dataclasses import dataclass
from typing import Iterable, Optional


ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_MAGENTA = "\033[35m"


def supports_color(stream) -> bool:
    if os.getenv("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def style(text: str, color: str = "", bold: bool = False, dim: bool = False) -> str:
    parts = []
    if bold:
        parts.append(ANSI_BOLD)
    if dim:
        parts.append(ANSI_DIM)
    if color:
        parts.append(color)
    if not parts:
        return text
    return "".join(parts) + text + ANSI_RESET


@dataclass
class Spinner:
    message: str = "Working"
    enabled: bool = True
    interval: float = 0.12

    def __post_init__(self) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not self.enabled:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self.enabled:
            return
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        sys.stderr.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stderr.flush()

    def _run(self) -> None:
        frames = ["|", "/", "-", "\\"]
        i = 0
        while not self._stop.is_set():
            frame = frames[i % len(frames)]
            sys.stderr.write(f"\r{self.message} {frame}")
            sys.stderr.flush()
            i += 1
            time.sleep(self.interval)


def render_response(text: str, use_color: bool) -> str:
    if not use_color:
        return text

    lines = []
    for raw in text.splitlines():
        line = raw
        if line.startswith("## "):
            line = style(line, ANSI_CYAN, bold=True)
        elif line.startswith("### "):
            line = style(line, ANSI_MAGENTA, bold=True)
        elif line.startswith("- "):
            line = style(line, ANSI_GREEN)
        elif line.startswith("```"):
            line = style(line, ANSI_YELLOW, dim=True)
        elif line.startswith("**") and line.endswith("**"):
            line = style(line, "", bold=True)
        lines.append(line)
    return "\n".join(lines)


def prompt_choice(prompt: str, options: Iterable[str], default: Optional[str] = None) -> str:
    options_lower = {opt.lower(): opt for opt in options}
    while True:
        value = input(prompt).strip()
        if not value and default:
            return default
        normalized = value.lower()
        if normalized in options_lower:
            return options_lower[normalized]
        print(f"Please enter one of: {', '.join(options)}")
