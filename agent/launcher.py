import subprocess
import sys
from pathlib import Path
from typing import List, Optional

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
except ModuleNotFoundError:
    box = None
    Console = None
    Panel = None
    Prompt = None
    Confirm = None
    Table = None
    Text = None

console = Console() if Console else None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _agent_cmd() -> List[str]:
    root = _repo_root()
    return [str(root / "bin" / "agent")]


def run_agent(args: List[str], title: str = "Running Agent") -> int:
    cmd = _agent_cmd() + args
    if console:
        console.rule(f"[bold cyan]{title}")
        console.print("[dim]$ " + " ".join(cmd) + "[/dim]")
    else:
        print(f"== {title} ==")
        print("$ " + " ".join(cmd))

    try:
        if console:
            with console.status("[bold cyan]Executing...", spinner="dots"):
                completed = subprocess.run(cmd, check=False)
        else:
            completed = subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        if console:
            console.print("\n[yellow]Cancelled.[/yellow]")
        else:
            print("\nCancelled.")
        return 130

    if completed.returncode == 0 and console:
        console.print("[bold green]Completed successfully.[/bold green]")
    elif completed.returncode == 0:
        print("Completed successfully.")
    else:
        if console:
            console.print(f"[bold red]Exited with code {completed.returncode}.[/bold red]")
        else:
            print(f"Exited with code {completed.returncode}.")

    return completed.returncode


def validate_knowledge() -> int:
    root = _repo_root()
    python_bin = root / ".venv" / "bin" / "python"
    cmd = [str(python_bin), "-m", "agent.validate_knowledge"] if python_bin.exists() else ["python3", "-m", "agent.validate_knowledge"]

    if console:
        console.rule("[bold cyan]Validate Knowledge")
        console.print("[dim]$ " + " ".join(cmd) + "[/dim]")
    else:
        print("== Validate Knowledge ==")
        print("$ " + " ".join(cmd))

    try:
        if console:
            with console.status("[bold cyan]Validating knowledge base...", spinner="earth"):
                completed = subprocess.run(cmd, check=False)
        else:
            completed = subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        if console:
            console.print("\n[yellow]Cancelled.[/yellow]")
        else:
            print("\nCancelled.")
        return 130

    if completed.returncode == 0 and console:
        console.print("[bold green]Knowledge validation passed.[/bold green]")
    elif completed.returncode == 0:
        print("Knowledge validation passed.")
    else:
        if console:
            console.print(f"[bold red]Knowledge validation failed ({completed.returncode}).[/bold red]")
        else:
            print(f"Knowledge validation failed ({completed.returncode}).")
    return completed.returncode


def select_menu() -> str:
    if not console:
        print("\nDocker Migration Console")
        print("1) Guided Migration")
        print("2) Guided Migration (Debug)")
        print("3) List Knowledge Bundles")
        print("4) Validate Knowledge Base")
        print("5) Quick Wizard")
        print("6) Exit")
        return input("Choose [1-6]: ").strip() or "1"

    table = Table(title="Docker Migration Console", box=box.ROUNDED, border_style="cyan")
    table.add_column("Option", style="bold yellow", justify="right", width=8)
    table.add_column("Action", style="white")
    table.add_row("1", "Guided Migration")
    table.add_row("2", "Guided Migration (Debug)")
    table.add_row("3", "List Knowledge Bundles")
    table.add_row("4", "Validate Knowledge Base")
    table.add_row("5", "Quick Wizard")
    table.add_row("6", "Exit")
    console.print(table)

    return Prompt.ask("Choose", choices=["1", "2", "3", "4", "5", "6"], default="1")


def prompt_target_path() -> str:
    while True:
        value = Prompt.ask("Target Dockerfile path").strip() if Prompt else input("Target Dockerfile path: ").strip()
        if not value:
            console.print("[red]Target path is required.[/red]")
            continue
        path = Path(value).expanduser()
        if not path.exists():
            console.print(f"[red]Path not found:[/red] {path}")
            continue
        if path.is_dir():
            candidate = path / "Dockerfile"
            if candidate.exists():
                if (Confirm.ask(f"Use {candidate}?", default=True) if Confirm else True):
                    return str(candidate)
            console.print("[red]Directory provided. Please pass a Dockerfile path.[/red]")
            continue
        return str(path)


def build_guided_args(debug: bool = False) -> List[str]:
    if console:
        console.print(Panel.fit("Guided Migration Setup", border_style="magenta", box=box.DOUBLE))
    else:
        print("\n== Guided Migration Setup ==")

    target = prompt_target_path()
    task_default = "Migrate this repo to multi-arch format while preserving current PHP version"
    if Prompt:
        task = Prompt.ask("Migration task", default=task_default).strip()
        mode = Prompt.ask("Mode", choices=["propose", "apply"], default="propose")
        base = Prompt.ask("Base image", choices=["auto", "alpine", "debian"], default="auto")
    else:
        task = input(f"Migration task [{task_default}]: ").strip() or task_default
        mode = input("Mode [propose/apply] (propose): ").strip() or "propose"
        base = input("Base image [auto/alpine/debian] (auto): ").strip() or "auto"

    if Confirm:
        write_outputs = mode == "propose" and Confirm.ask("Write .migrated outputs", default=False)
        backup = Confirm.ask("Create backups before writing", default=True)
        include_related = Confirm.ask("Include related files", default=True)
        sync_newrelic = Confirm.ask("Sync latest New Relic asset", default=False)
        followups = Confirm.ask("Enable interactive follow-ups", default=False)
    else:
        write_outputs = mode == "propose" and input("Write .migrated outputs? [y/N]: ").strip().lower() == "y"
        backup = input("Create backups before writing? [Y/n]: ").strip().lower() not in {"n", "no"}
        include_related = input("Include related files? [Y/n]: ").strip().lower() not in {"n", "no"}
        sync_newrelic = input("Sync latest New Relic asset? [y/N]: ").strip().lower() == "y"
        followups = input("Enable interactive follow-ups? [y/N]: ").strip().lower() == "y"

    args: List[str] = [
        "--target",
        target,
        "--task",
        task,
        "--mode",
        mode,
        "--ui",
    ]

    if base != "auto":
        args += ["--base", base]
    if write_outputs:
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


def render_banner() -> None:
    if not console:
        print("\n==============================")
        print("  Docker Migration Agent CLI")
        print("==============================")
        print("Tip: install `rich` for improved UI: pip install rich")
        return

    title = Text("Docker Migration Agent", style="bold cyan")
    subtitle = Text("SaaS Console", style="bold magenta")
    console.print(Panel.fit(Text.assemble(title, "\n", subtitle), border_style="bright_blue", box=box.DOUBLE_EDGE))


def run_launcher() -> int:
    render_banner()

    while True:
        choice = select_menu()

        if choice == "1":
            args = build_guided_args(debug=False)
            run_agent(args, title="Guided Migration")
        elif choice == "2":
            args = build_guided_args(debug=True)
            run_agent(args, title="Guided Migration (Debug)")
        elif choice == "3":
            run_agent(["--list-reference-groups"], title="Knowledge Bundles")
        elif choice == "4":
            validate_knowledge()
        elif choice == "5":
            run_agent(["--wizard", "--ui"], title="Quick Wizard")
        elif choice == "6":
            if console:
                console.print("[bold]Bye.[/bold]")
            else:
                print("Bye.")
            return 0

        if Confirm:
            keep = Confirm.ask("Return to menu", default=True)
        else:
            keep = input("Return to menu? [Y/n]: ").strip().lower() not in {"n", "no"}
        if not keep:
            return 0


def main() -> int:
    passthrough = sys.argv[1:]
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    if passthrough:
        return run_agent(passthrough, title="Direct Agent Run")

    return run_launcher()


if __name__ == "__main__":
    raise SystemExit(main())
