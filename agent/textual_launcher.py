import asyncio
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.markdown import Markdown
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, DataTable, Footer, Header, Input, RichLog, Static


DEFAULT_TASK = "Migrate this repo to multi-arch format while preserving current PHP version"
ASCII_BRAND = r"""
  ____             _               __  __ _                 _   _
 |  _ \  ___   ___| | _____ _ __  |  \/  (_) __ _ _ __ __ _| |_(_) ___  _ __
 | | | |/ _ \ / __| |/ / _ \ '__| | |\/| | |/ _` | '__/ _` | __| |/ _ \| '_ \
 | |_| | (_) | (__|   <  __/ |    | |  | | | (_| | | | (_| | |_| | (_) | | | |
 |____/ \___/ \___|_|\_\___|_|    |_|  |_|_|\__, |_|  \__,_|\__|_|\___/|_| |_|
                                             |___/
"""


class MigrationLauncherApp(App):
    TITLE = "Docker Migration Agent"
    SUB_TITLE = "SaaS Console"

    CSS = """
    Screen {
      background: #060b16;
      color: #e6edf3;
    }

    #brand {
      height: auto;
      border: round #fd7e14;
      background: #0d1117;
      color: #f0f6fc;
      padding: 1 2;
      margin: 0 0 1 0;
    }

    #body {
      height: 1fr;
    }

    #actions {
      width: 34;
      min-width: 28;
      border: round #1f6feb;
      padding: 1;
      margin: 0 1 0 0;
      background: #0d1117;
    }

    #form {
      width: 56;
      min-width: 44;
      border: round #238636;
      padding: 1;
      margin: 0 1 0 0;
      background: #0d1117;
    }

    #right {
      width: 1fr;
    }

    #logs {
      width: 100%;
      height: 2fr;
      border: round #8957e5;
      padding: 1;
      margin: 0 0 1 0;
      background: #0d1117;
    }

    #history {
      width: 100%;
      height: 1fr;
      border: round #d29922;
      padding: 1;
      background: #0d1117;
    }

    .section-title {
      text-style: bold;
      color: #79c0ff;
      margin: 0 0 1 0;
    }

    .field-label {
      color: #a5d6ff;
      margin: 1 0 0 0;
    }

    .hint {
      color: #8b949e;
      margin: 0 0 1 0;
    }

    Button {
      width: 100%;
      margin: 0 0 1 0;
    }

    Input {
      margin: 0 0 1 0;
    }

    Checkbox {
      margin: 0 0 1 0;
    }

    #status {
      margin: 1 0 0 0;
      color: #8b949e;
    }

    #log_view {
      height: 1fr;
    }

    #reply_bar {
      height: auto;
      margin: 1 0 0 0;
    }

    #reply_input {
      width: 1fr;
      margin: 0 1 0 0;
    }

    #btn_send_reply {
      width: 18;
      min-width: 14;
      margin: 0;
    }

    #history_table {
      height: 1fr;
    }
    """

    BINDINGS = [
        ("ctrl+r", "run_guided", "Run Guided"),
        ("ctrl+l", "clear_logs", "Clear Logs"),
        ("ctrl+h", "clear_history", "Clear History"),
        ("ctrl+s", "send_reply", "Send Reply"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.repo_root = Path(__file__).resolve().parents[1]
        self.running = False
        self._active_process: Optional[asyncio.subprocess.Process] = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            f"[#ffa657]{ASCII_BRAND}[/#ffa657]\n[bold #79c0ff]SaaS Console[/bold #79c0ff] [#8b949e]| Press q to quit[/#8b949e]",
            id="brand",
        )
        with Horizontal(id="body"):
            with Vertical(id="actions"):
                yield Static("Actions", classes="section-title")
                yield Button("Run Guided", id="btn_guided", variant="success")
                yield Button("Run Guided (Debug)", id="btn_guided_debug", variant="primary")
                yield Button("Quick Wizard", id="btn_quick_wizard", variant="default")
                yield Button("List Bundles", id="btn_list_bundles", variant="default")
                yield Button("Validate Knowledge", id="btn_validate", variant="default")
                yield Button("Clear Logs", id="btn_clear", variant="default")
                yield Button("Clear History", id="btn_clear_history", variant="warning")
                yield Button("Quit", id="btn_quit", variant="error")
                yield Static("Tip: ctrl+r run, ctrl+l logs, ctrl+h history, ctrl+s send, q quit", classes="hint")

            with Vertical(id="form"):
                yield Static("Migration Form", classes="section-title")
                yield Static("Target Dockerfile", classes="field-label")
                yield Input(placeholder="/absolute/path/to/Dockerfile", id="target")
                yield Static("Task", classes="field-label")
                yield Input(value=DEFAULT_TASK, id="task")
                yield Static("Mode (propose/apply)", classes="field-label")
                yield Input(value="propose", id="mode")
                yield Static("Base (auto/alpine/debian)", classes="field-label")
                yield Input(value="auto", id="base")

                yield Checkbox("Write .migrated outputs", value=False, id="opt_write")
                yield Checkbox("Backup before write", value=True, id="opt_backup")
                yield Checkbox("Include related files", value=True, id="opt_related")
                yield Checkbox("Sync latest New Relic", value=False, id="opt_newrelic")
                yield Checkbox("Interactive follow-ups", value=False, id="opt_interactive")
                yield Checkbox("Debug logs", value=False, id="opt_debug")

                yield Static("Status: idle", id="status")

            with Vertical(id="right"):
                with Vertical(id="logs"):
                    yield Static("Live Logs", classes="section-title")
                    yield RichLog(id="log_view", wrap=True, markup=False, highlight=True)
                    with Horizontal(id="reply_bar"):
                        yield Input(
                            placeholder="Reply to agent prompts (enable Interactive follow-ups)",
                            id="reply_input",
                        )
                        yield Button("Send Reply", id="btn_send_reply", variant="warning")
                with Vertical(id="history"):
                    yield Static("Job History", classes="section-title")
                    yield DataTable(id="history_table", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#history_table", DataTable)
        table.add_columns("Time", "Action", "Status", "Duration", "Target")

    def action_run_guided(self) -> None:
        self._start_guided(debug_override=None)

    def action_clear_logs(self) -> None:
        self.query_one("#log_view", RichLog).clear()

    def action_clear_history(self) -> None:
        self.query_one("#history_table", DataTable).clear(columns=False)

    def action_send_reply(self) -> None:
        self._send_reply_from_input()

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "btn_guided":
            self._start_guided(debug_override=None)
        elif button_id == "btn_guided_debug":
            self._start_guided(debug_override=True)
        elif button_id == "btn_quick_wizard":
            self._run_cmd(self._agent_cmd() + ["--wizard", "--ui"], "Quick Wizard")
        elif button_id == "btn_list_bundles":
            self._run_cmd(self._agent_cmd() + ["--list-reference-groups"], "List Bundles")
        elif button_id == "btn_validate":
            self._run_cmd(self._validate_cmd(), "Validate Knowledge")
        elif button_id == "btn_clear":
            self.action_clear_logs()
        elif button_id == "btn_clear_history":
            self.action_clear_history()
        elif button_id == "btn_send_reply":
            self._send_reply_from_input()
        elif button_id == "btn_quit":
            self.exit()

    def _agent_cmd(self) -> List[str]:
        return [str(self.repo_root / "bin" / "agent")]

    def _validate_cmd(self) -> List[str]:
        python_bin = self.repo_root / ".venv" / "bin" / "python"
        if python_bin.exists():
            return [str(python_bin), "-m", "agent.validate_knowledge"]
        return ["python3", "-m", "agent.validate_knowledge"]

    def _set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(f"Status: {text}")

    def _looks_like_markdown(self, text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if stripped.startswith(("# ", "## ", "### ", "- ", "* ")):
            return True
        if re.search(r"\*\*[^*]+\*\*", stripped):
            return True
        if re.match(r"^\d+\.\s", stripped):
            return True
        return False

    def _render_table_line(self, text: str) -> Text:
        def clean_inline(value: str) -> str:
            cleaned = value.replace("**", "").replace("`", "")
            cleaned = cleaned.replace(":white_check_mark:", "OK").replace(":x:", "X")
            return cleaned.strip()

        line = Text()
        for index, part in enumerate(text.split("|")):
            content = clean_inline(part)
            if not content:
                continue
            if set(content) <= {"-", ":"}:
                continue
            if index == 1:
                line.append(content, style="bold cyan")
            elif index == 2:
                line.append(content, style="bold green")
            elif index == 3:
                line.append(content, style="bold yellow")
            else:
                line.append(content, style="white")
            line.append("  ")
        return line

    def _log(self, text: str) -> None:
        log = self.query_one("#log_view", RichLog)
        stripped = text.strip()

        if stripped.startswith("|") and stripped.count("|") >= 3:
            log.write(self._render_table_line(stripped))
            return
        if self._looks_like_markdown(text):
            log.write(Markdown(text))
            return
        if text.startswith("[run]"):
            log.write(Text(text, style="bold cyan"))
            return
        if text.startswith("[done]") and "success" in text:
            log.write(Text(text, style="bold green"))
            return
        if text.startswith("[done]") and "failed" in text:
            log.write(Text(text, style="bold red"))
            return
        if text.startswith("[error]"):
            log.write(Text(text, style="bold red"))
            return
        if text.startswith("[warn]"):
            log.write(Text(text, style="yellow"))
            return
        if text.startswith("[reply]"):
            log.write(Text(text, style="bold magenta"))
            return

        log.write(Text(text))

    def _set_inputs_disabled(self, disabled: bool) -> None:
        for button in self.query(Button):
            if button.id != "btn_send_reply":
                button.disabled = disabled
        for inp in self.query(Input):
            if inp.id != "reply_input":
                inp.disabled = disabled
        for chk in self.query(Checkbox):
            chk.disabled = disabled

    def _target_from_cmd(self, cmd: List[str]) -> str:
        if "--target" in cmd:
            idx = cmd.index("--target")
            if idx + 1 < len(cmd):
                return cmd[idx + 1]
        return "-"

    def _append_history(self, title: str, cmd: List[str], returncode: int, duration_s: float) -> None:
        table = self.query_one("#history_table", DataTable)
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "OK" if returncode == 0 else f"FAIL({returncode})"
        duration = f"{duration_s:.1f}s"
        target = self._target_from_cmd(cmd)
        table.add_row(timestamp, title, status, duration, target)

    def _start_guided(self, debug_override: Optional[bool]) -> None:
        args = self._build_guided_args(debug_override)
        if not args:
            return
        self._run_cmd(self._agent_cmd() + args, "Guided Migration")

    def _build_guided_args(self, debug_override: Optional[bool]) -> Optional[List[str]]:
        target = self.query_one("#target", Input).value.strip()
        task = self.query_one("#task", Input).value.strip()
        mode = self.query_one("#mode", Input).value.strip().lower() or "propose"
        base = self.query_one("#base", Input).value.strip().lower() or "auto"

        if not target:
            self._log("[error] target is required")
            self._set_status("target missing")
            return None

        target_path = Path(target).expanduser()
        if target_path.is_dir():
            candidate = target_path / "Dockerfile"
            if candidate.exists():
                target_path = candidate

        if not target_path.exists():
            self._log(f"[error] target path not found: {target_path}")
            self._set_status("target path invalid")
            return None

        if not task:
            self._log("[error] task is required")
            self._set_status("task missing")
            return None

        if mode not in {"propose", "apply"}:
            self._log("[error] mode must be propose or apply")
            self._set_status("invalid mode")
            return None

        if base not in {"auto", "alpine", "debian"}:
            self._log("[error] base must be auto, alpine, or debian")
            self._set_status("invalid base")
            return None

        write_outputs = self.query_one("#opt_write", Checkbox).value
        backup = self.query_one("#opt_backup", Checkbox).value
        include_related = self.query_one("#opt_related", Checkbox).value
        sync_newrelic = self.query_one("#opt_newrelic", Checkbox).value
        followups = self.query_one("#opt_interactive", Checkbox).value
        debug = self.query_one("#opt_debug", Checkbox).value

        if debug_override is True:
            debug = True

        args = [
            "--target",
            str(target_path),
            "--task",
            task,
            "--mode",
            mode,
            "--ui",
        ]

        if base != "auto":
            args += ["--base", base]
        if mode == "propose" and write_outputs:
            args.append("--write")
        if backup:
            args.append("--backup")
        if not include_related:
            args.append("--no-related")
        if sync_newrelic:
            args.append("--sync-newrelic")
        if followups:
            args.append("--interactive")
        if debug:
            args.append("--debug")

        return args

    def _send_reply_from_input(self) -> None:
        reply_input = self.query_one("#reply_input", Input)
        message = reply_input.value.strip()
        if not message:
            self._log("[warn] reply input is empty")
            return
        reply_input.value = ""
        self.run_worker(self._send_reply_async(message), exclusive=False)

    async def _send_reply_async(self, message: str) -> None:
        if self._active_process is None or self._active_process.stdin is None:
            self._log("[warn] no active interactive session. Enable Interactive follow-ups before running.")
            return
        if self._active_process.returncode is not None:
            self._log("[warn] session already finished. Start a new run.")
            return

        try:
            self._active_process.stdin.write((message + "\n").encode("utf-8"))
            await self._active_process.stdin.drain()
            self._log(f"[reply] {message}")
        except Exception as exc:
            self._log(f"[error] failed to send reply: {exc}")

    def _run_cmd(self, cmd: List[str], title: str) -> None:
        if self.running:
            self._log("[warn] another command is already running")
            return
        self.run_worker(self._run_cmd_async(cmd, title), exclusive=True)

    async def _run_cmd_async(self, cmd: List[str], title: str) -> None:
        self.running = True
        self._set_inputs_disabled(True)
        self._set_status(f"running {title}")
        self._log("\n" + "=" * 72)
        self._log(f"[run] {title}")
        self._log("$ " + " ".join(cmd))
        started = time.monotonic()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.repo_root),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            self._active_process = process

            assert process.stdout is not None
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                self._log(line.decode("utf-8", errors="replace").rstrip("\n"))

            returncode = await process.wait()
            elapsed = time.monotonic() - started
            if returncode == 0:
                self._set_status("completed")
                self._log("[done] success")
            else:
                self._set_status(f"failed ({returncode})")
                self._log(f"[done] failed ({returncode})")
            self._append_history(title, cmd, returncode, elapsed)
        except Exception as exc:  # pragma: no cover - defensive UI path
            self._set_status("error")
            self._log(f"[error] {exc}")
            elapsed = time.monotonic() - started
            self._append_history(title, cmd, 1, elapsed)
        finally:
            self._active_process = None
            self.running = False
            self._set_inputs_disabled(False)


def run() -> int:
    app = MigrationLauncherApp()
    app.run()
    return 0
