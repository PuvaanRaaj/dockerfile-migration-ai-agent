import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from agent.config import AgentConfig
from agent.context import ReferenceLoader
from agent.knowledge_base import load_knowledge_base
from agent.prompts import build_system_prompt
from agent.reference_assets import find_newrelic_assets, pick_latest_asset
from agent.reference_selection import detect_base, detect_php_tag, select_references
from agent.related_files import discover_related_files
from agent.ui import Spinner, prompt_choice, render_response, supports_color
from agent.utils import (
    backup_path,
    default_output_path,
    ensure_exists,
    extract_dockerfile,
    extract_file_blocks,
    migrated_output_path,
    parse_dockerfile_from_blocks,
    resolve_output_path,
    trim_text,
    write_text,
)


def build_user_prompt(
    target_path: Path,
    task: str,
    mode: str,
    related_files: List[Path],
    binary_files: List[Path],
    requested_php_tag: Optional[str],
    target_php_tag: Optional[str],
) -> str:
    lines: List[str] = []
    lines.append(f"Target Dockerfile: {target_path.as_posix()}")
    lines.append(f"Task: {task}")
    lines.append("")
    lines.append("Instructions:")
    lines.append("- Read the target Dockerfile before proposing changes.")
    if mode == "apply":
        lines.append("- You may use edit tools to apply changes.")
    else:
        lines.append("- Do not edit files. Output the updated Dockerfile in a code block.")
    if requested_php_tag:
        lines.append(f"- Requested PHP version: {requested_php_tag}. Keep this version even if references differ.")
    elif target_php_tag:
        lines.append(f"- No PHP version was specified. Preserve the target's PHP version: {target_php_tag}.")
    else:
        lines.append("- No PHP version detected. Ask if a specific version is required before changing it.")
    lines.append("- Update related config files when they are part of the image.")
    lines.append("- If `.gitlab-ci.yml` is present and the task is multi-arch, align CI jobs/stages with the CI reference.")
    if related_files:
        lines.append("")
        lines.append("Related files to review/update:")
        for path in related_files:
            lines.append(f"- {path.as_posix()}")
    if binary_files:
        lines.append("")
        lines.append("Binary assets referenced (do not print contents):")
        for path in binary_files:
            lines.append(f"- {path.as_posix()}")
        lines.append("If you update a binary asset version, state the filename to copy.")
    lines.append("- Keep changes minimal and aligned with the references.")
    return "\n".join(lines)


def discover_ci_files(target_path: Path, max_parent_levels: int = 4) -> List[Path]:
    ci_files: List[Path] = []
    seen: set[Path] = set()

    current = target_path.parent if target_path.is_file() else target_path
    for _ in range(max_parent_levels + 1):
        for name in (".gitlab-ci.yml", ".gitlab-ci.yaml"):
            candidate = current / name
            if not candidate.exists() or not candidate.is_file():
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            ci_files.append(candidate)
        if current.parent == current:
            break
        current = current.parent

    return ci_files


async def run_agent(
    prompt: str,
    system_prompt: str,
    allowed_tools: List[str],
    debug: bool,
    ui_enabled: bool,
    spinner_enabled: bool,
) -> str:
    import time

    from claude_agent_sdk import ClaudeAgentOptions, AssistantMessage, ResultMessage, query

    options = ClaudeAgentOptions(
        allowed_tools=allowed_tools,
        permission_mode="acceptEdits",
        system_prompt=system_prompt,
    )

    output_chunks: List[str] = []
    start = time.monotonic()
    if debug:
        print("[debug] agent start", file=sys.stderr)

    spinner = Spinner(message="Thinking", enabled=spinner_enabled and not debug)
    spinner.start()

    async for message in query(prompt=prompt, options=options):
        if debug:
            elapsed = time.monotonic() - start
            msg_type = message.__class__.__name__
            print(f"[debug] +{elapsed:.2f}s {msg_type}", file=sys.stderr)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                text = getattr(block, "text", None)
                if text:
                    if not ui_enabled:
                        print(text, end="", flush=True)
                    output_chunks.append(text)
                elif debug:
                    block_type = getattr(block, "type", block.__class__.__name__)
                    name = getattr(block, "name", None)
                    info = f"{block_type}"
                    if name:
                        info += f" name={name}"
                    print(f"[debug]   block: {info}", file=sys.stderr)
        elif isinstance(message, ResultMessage):
            if not ui_enabled:
                print(f"\n\n[done] {message.subtype}")
            elif debug:
                print(f"[debug] done: {message.subtype}", file=sys.stderr)
            if debug:
                elapsed = time.monotonic() - start
                print(f"[debug] done after {elapsed:.2f}s", file=sys.stderr)

    spinner.stop()

    return "".join(output_chunks)


def sync_newrelic_asset(
    repo_root: Path,
    target_path: Path,
    base: Optional[str],
    assets,
    binary_files: List[Path],
) -> None:
    import shutil

    if not assets:
        print("[newrelic] No reference assets available to sync.")
        return

    latest = pick_latest_asset(assets, base)
    if not latest:
        print("[newrelic] Unable to determine latest asset.")
        return

    candidate_targets = [
        path
        for path in binary_files
        if path.name.startswith("newrelic-php5-") and path.suffixes[-2:] == [".tar", ".gz"]
    ]
    dest_dir = candidate_targets[0].parent if candidate_targets else None
    default_dir = target_path.parent / "core" / "newrelic"
    if dest_dir is None and default_dir.exists():
        dest_dir = default_dir

    if dest_dir is None:
        print("[newrelic] Target newrelic directory not found. Skipping asset sync.")
        return

    source_path = repo_root / latest.path
    if not source_path.exists():
        print(f"[newrelic] Reference asset missing on disk: {source_path}")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / source_path.name
    if dest_path.exists():
        print(f"[newrelic] Latest asset already present: {dest_path}")
        return

    shutil.copy2(source_path, dest_path)
    print(f"[newrelic] Copied {source_path} -> {dest_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dockerfile migration agent")
    parser.add_argument("--target", help="Path to Dockerfile to migrate")
    parser.add_argument("--task", help="Migration task description")
    parser.add_argument(
        "--mode",
        choices=["propose", "apply"],
        default="propose",
        help="propose: read-only; apply: allow edits",
    )
    parser.add_argument(
        "--output",
        help="Write extracted Dockerfile to this path",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write extracted files to default .migrated paths",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a .backup file next to the target before writing output",
    )
    parser.add_argument(
        "--reference-glob",
        action="append",
        default=[],
        help="Additional glob(s) to include in reference bundle",
    )
    parser.add_argument(
        "--reference-group",
        action="append",
        default=[],
        help="Force-include a knowledge bundle ID (use --list-reference-groups to see options)",
    )
    parser.add_argument(
        "--knowledge-index",
        help="Override knowledge index path (default: KNOWLEDGE_INDEX_PATH or knowledge/index.json)",
    )
    parser.add_argument(
        "--list-reference-groups",
        action="store_true",
        help="List available reference group names and exit",
    )
    parser.add_argument(
        "--base",
        choices=["alpine", "debian"],
        help="Override base selection when it cannot be inferred",
    )
    parser.add_argument(
        "--no-related",
        action="store_true",
        help="Disable related file discovery",
    )
    parser.add_argument(
        "--sync-newrelic",
        action="store_true",
        help="Copy latest New Relic tarball from references into the target repo when detected",
    )
    parser.add_argument(
        "--print-system-prompt",
        action="store_true",
        help="Print system prompt and exit (debug)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print tool-call timing and event info to stderr",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for follow-up requests after the first response",
    )
    parser.add_argument(
        "--followup-context-chars",
        type=int,
        default=6000,
        help="How many chars of the last response to include in follow-ups",
    )
    parser.add_argument(
        "--ui",
        dest="ui",
        action="store_true",
        help="Enable styled output and spinner",
    )
    parser.add_argument(
        "--no-ui",
        dest="ui",
        action="store_false",
        help="Disable styled output and spinner",
    )
    parser.set_defaults(ui=None)
    parser.add_argument(
        "--no-spinner",
        action="store_true",
        help="Disable loading spinner",
    )
    parser.add_argument(
        "--wizard",
        action="store_true",
        help="Interactive prompts for target/task/options",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()

    args = parse_args()
    ui_enabled = args.ui if args.ui is not None else sys.stdout.isatty()
    color_enabled = ui_enabled and supports_color(sys.stdout)

    if args.wizard:
        print(render_response("## Dockerfile Migration Agent", color_enabled))
        if not args.target:
            while True:
                target_input = input("Target Dockerfile path: ").strip()
                if target_input:
                    args.target = target_input
                if args.target and Path(args.target).exists():
                    break
                print("Please enter a valid Dockerfile path.")
        if not args.task:
            args.task = input("Task: ").strip()
        args.mode = prompt_choice(
            f"Mode [propose/apply] (default {args.mode}): ",
            ["propose", "apply"],
            default=args.mode,
        )
        base_choice = prompt_choice(
            "Base image [auto/alpine/debian] (default auto): ",
            ["auto", "alpine", "debian"],
            default="auto",
        )
        if base_choice != "auto":
            args.base = base_choice
        if args.mode == "propose":
            write_choice = prompt_choice(
                "Write .migrated outputs? [y/n] (default n): ",
                ["y", "n"],
                default="n",
            )
            args.write = write_choice == "y"
        backup_choice = prompt_choice(
            "Create backups before writing? [y/n] (default n): ",
            ["y", "n"],
            default="n",
        )
        args.backup = args.backup or backup_choice == "y"
        interactive_choice = prompt_choice(
            "Enable interactive follow-ups? [y/n] (default n): ",
            ["y", "n"],
            default="n",
        )
        args.interactive = args.interactive or interactive_choice == "y"
        related_choice = prompt_choice(
            "Include related files? [y/n] (default y): ",
            ["y", "n"],
            default="y",
        )
        args.no_related = related_choice == "n"
        newrelic_choice = prompt_choice(
            "Sync latest New Relic tarball? [y/n] (default n): ",
            ["y", "n"],
            default="n",
        )
        args.sync_newrelic = args.sync_newrelic or newrelic_choice == "y"
        debug_choice = prompt_choice(
            "Enable debug logging? [y/n] (default n): ",
            ["y", "n"],
            default="n",
        )
        args.debug = args.debug or debug_choice == "y"

    config = AgentConfig()
    knowledge_index_path = Path(args.knowledge_index) if args.knowledge_index else config.knowledge_index_path
    knowledge_base = load_knowledge_base(config.repo_root, knowledge_index_path)

    if args.list_reference_groups:
        for bundle_id in knowledge_base.bundle_ids:
            print(bundle_id)
        return
    if not args.target or not args.task:
        raise SystemExit("Missing --target or --task. Use --wizard for interactive mode.")

    target_path = Path(args.target)
    error = ensure_exists(target_path)
    if error:
        raise SystemExit(error)

    target_text = target_path.read_text(encoding="utf-8")
    related_result = None
    if not args.no_related:
        related_result = discover_related_files(target_path, target_text)
        for item in related_result.skipped:
            print(f"[related] {item}")

    requested_php_tag = detect_php_tag(args.task, "")
    target_php_tag = detect_php_tag("", target_text)

    base_override = args.base or detect_base(args.task, target_text)
    if base_override is None:
        while True:
            choice = input("Base image not clear. Choose base (alpine/debian): ").strip().lower()
            if choice in {"alpine", "debian"}:
                base_override = choice
                break
            print("Please enter 'alpine' or 'debian'.")

    selection = select_references(
        task=args.task,
        target_path=target_path,
        target_text=target_text,
        bundles=knowledge_base.bundles,
        base_override=base_override,
        forced_groups=args.reference_group,
    )
    if selection.selected:
        print("[refs] " + ", ".join(bundle.id for bundle in selection.selected))
    for warning in selection.warnings:
        print(f"[warn] {warning}")

    globs: List[str] = []
    globs.extend(knowledge_base.global_reference_globs)
    for selected_bundle in selection.selected:
        globs.extend(selected_bundle.reference_globs)
    globs.extend(args.reference_glob)
    loader = ReferenceLoader(
        repo_root=config.repo_root,
        globs=globs,
        max_total_chars=config.max_reference_chars_total,
        max_chars_per_file=config.max_reference_chars_per_file,
    )
    bundle = loader.load()

    assets = find_newrelic_assets(config.repo_root, selection.selected)
    if args.sync_newrelic and related_result:
        sync_newrelic_asset(
            repo_root=config.repo_root,
            target_path=target_path,
            base=base_override,
            assets=assets,
            binary_files=related_result.binary_files,
        )
    system_prompt = build_system_prompt(bundle, selection, assets)
    if args.print_system_prompt:
        print(system_prompt)
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. Add it to .env or your shell environment.")

    allowed_tools = ["Read"]
    if args.mode == "apply":
        allowed_tools.append("Edit")

    related_files = [item.path for item in related_result.files] if related_result else []
    binary_files = related_result.binary_files if related_result else []
    if not args.no_related:
        known_paths = {path.resolve() for path in related_files if path.exists()}
        for ci_file in discover_ci_files(target_path):
            resolved = ci_file.resolve()
            if resolved in known_paths:
                continue
            related_files.append(ci_file)
            known_paths.add(resolved)
            print(f"[related] CI config added: {ci_file}")
    user_prompt = build_user_prompt(
        target_path,
        args.task,
        args.mode,
        related_files,
        binary_files,
        requested_php_tag,
        target_php_tag,
    )
    def write_outputs(response: str) -> None:
        if not (args.output or args.write):
            return

        blocks = extract_file_blocks(response)
        if args.output:
            output_path = Path(args.output)
            dockerfile = parse_dockerfile_from_blocks(blocks) or extract_dockerfile(response)
            if not dockerfile:
                raise SystemExit("No Dockerfile code block found in response.")
            if args.backup and output_path.exists():
                backup_file = backup_path(output_path)
                write_text(backup_file, output_path.read_text(encoding="utf-8"))
                print(f"\n[backup] {backup_file}")
            write_text(output_path, dockerfile)
            print(f"\n[written] {output_path}")
            return

        if not blocks:
            dockerfile = extract_dockerfile(response)
            if not dockerfile:
                raise SystemExit("No Dockerfile code block found in response.")
            output_path = default_output_path(target_path)
            if args.backup and target_path.exists():
                backup_file = backup_path(target_path)
                write_text(backup_file, target_path.read_text(encoding="utf-8"))
                print(f"\n[backup] {backup_file}")
            write_text(output_path, dockerfile)
            print(f"\n[written] {output_path}")
            return

        for block in blocks:
            source_path = resolve_output_path(target_path, block.path)
            output_path = migrated_output_path(source_path)
            if args.backup and source_path.exists():
                backup_file = backup_path(source_path)
                write_text(backup_file, source_path.read_text(encoding="utf-8"))
                print(f"\n[backup] {backup_file}")
            write_text(output_path, block.content)
            print(f"\n[written] {output_path}")

    spinner_enabled = ui_enabled and not args.no_spinner
    response_text = asyncio.run(
        run_agent(
            user_prompt,
            system_prompt,
            allowed_tools,
            args.debug,
            ui_enabled,
            spinner_enabled,
        )
    )
    if ui_enabled:
        print(render_response(response_text, color_enabled))
    write_outputs(response_text)

    if args.interactive:
        print("\n[interactive] Follow-up mode enabled. Press enter on empty input to finish.")
        last_response = response_text
        while True:
            print("[interactive] Awaiting follow-up input...")
            followup = input("> ").strip()
            if not followup:
                print("[interactive] Session finished.")
                break
            context = trim_text(last_response, args.followup_context_chars)
            followup_prompt = (
                "Follow-up request:\n"
                f"{followup}\n\n"
                "Context from previous response (truncated if needed):\n"
                f"{context}\n"
            )
            last_response = asyncio.run(
                run_agent(
                    followup_prompt,
                    system_prompt,
                    allowed_tools,
                    args.debug,
                    ui_enabled,
                    spinner_enabled,
                )
            )
            if ui_enabled:
                print(render_response(last_response, color_enabled))
            write_outputs(last_response)


if __name__ == "__main__":
    main()
