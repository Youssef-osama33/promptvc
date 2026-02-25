"""
cli.py — Command-line interface for PromptVC.

Every user-facing command is defined here. Command logic is intentionally
thin: validate input → delegate to PromptStore → render via display.py.
No business logic lives in this module.

Commands
--------
  commit    Save a new version of a prompt from a file.
  log       Show the full commit history for a prompt.
  diff      Compare two versions of a prompt side-by-side.
  checkout  Restore a prompt to any past version.
  status    Show the latest version info and a content preview.
  ls        List all tracked prompts.
  tag       Attach a label to a specific commit.

Invocation
----------
  $ promptvc --help
  $ promptvc commit summarizer prompt.txt -m "initial version"
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from promptvc import __version__
from promptvc.display import (
    print_checkout_success,
    print_commit_success,
    print_diff,
    print_error,
    print_log,
    print_prompt_list,
    print_status,
    print_tag_success,
)
from promptvc.differ import diff_prompts
from promptvc.store import AmbiguousHashError, CommitNotFoundError, PromptStore

# ---------------------------------------------------------------------------
# Shared state — the store is instantiated once per process.
# ---------------------------------------------------------------------------

_store = PromptStore()


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(__version__, prog_name="promptvc")
def cli() -> None:
    """
    PromptVC — version control for LLM prompts.

    Commit your prompts. Diff your thinking. Never lose what worked.

    \b
    Quick start:
      promptvc commit summarizer prompt.txt -m "initial version"
      promptvc log summarizer
      promptvc diff summarizer <hash_a> <hash_b>
      promptvc checkout summarizer <hash>

    Full documentation: https://github.com/Youssef-osama33/promptvc
    """


# ---------------------------------------------------------------------------
# commit
# ---------------------------------------------------------------------------


@cli.command("commit")
@click.argument("prompt_name", metavar="<prompt-name>")
@click.argument("file", metavar="<file>", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--message", "-m",
    required=True,
    metavar="<message>",
    help="Short description of this version.",
)
@click.option(
    "--model",
    default="gpt-4",
    show_default=True,
    metavar="<model>",
    help="Target LLM model for this prompt.",
)
@click.option(
    "--tags",
    default="",
    metavar="<tags>",
    help="Comma-separated labels, e.g. 'prod,stable'.",
)
def cmd_commit(
    prompt_name: str,
    file: str,
    message: str,
    model: str,
    tags: str,
) -> None:
    """
    Save a new version of <prompt-name> from <file>.

    \b
    Examples:
      promptvc commit summarizer prompt.txt -m "initial draft"
      promptvc commit chatbot system.txt -m "add JSON output" --model claude-3 --tags prod
    """
    content = Path(file).read_text(encoding="utf-8")

    if not content.strip():
        print_error(f"'{file}' is empty. Nothing to commit.")
        sys.exit(1)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    commit_hash = _store.commit(
        prompt_name=prompt_name,
        content=content,
        message=message,
        model=model,
        tags=tag_list,
    )

    print_commit_success(commit_hash, message)


# ---------------------------------------------------------------------------
# log
# ---------------------------------------------------------------------------


@cli.command("log")
@click.argument("prompt_name", metavar="<prompt-name>")
@click.option(
    "--limit", "-n",
    default=20,
    show_default=True,
    metavar="<n>",
    help="Maximum number of commits to display.",
)
def cmd_log(prompt_name: str, limit: int) -> None:
    """
    Show commit history for <prompt-name>.

    \b
    Example:
      promptvc log summarizer
      promptvc log summarizer -n 5
    """
    history = _store.get_history(prompt_name)

    if not history:
        click.echo(
            click.style(f"  No history found for '{prompt_name}'.", dim=True)
        )
        return

    print_log(history[:limit])

    if len(history) > limit:
        omitted = len(history) - limit
        click.echo(
            click.style(
                f"  … {omitted} older commit(s) not shown. Use -n to see more.",
                dim=True,
            )
        )


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


@cli.command("diff")
@click.argument("prompt_name", metavar="<prompt-name>")
@click.argument("hash_a", metavar="<hash-a>")
@click.argument("hash_b", metavar="<hash-b>")
@click.option(
    "--context", "-c",
    default=3,
    show_default=True,
    metavar="<lines>",
    help="Lines of context around each change.",
)
def cmd_diff(prompt_name: str, hash_a: str, hash_b: str, context: int) -> None:
    """
    Compare two versions of <prompt-name>.

    \b
    <hash-a> and <hash-b> can be full or partial (≥4 chars) commit hashes.

    \b
    Example:
      promptvc diff summarizer a3f92c1b fcfeceb2
    """
    try:
        version_a = _store.get_version(prompt_name, hash_a)
        version_b = _store.get_version(prompt_name, hash_b)
    except (CommitNotFoundError, AmbiguousHashError) as exc:
        print_error(str(exc))
        sys.exit(1)

    diff_lines = diff_prompts(version_a["content"], version_b["content"])

    label_a = f"{version_a['hash'][:8]}  ({version_a['message']})"
    label_b = f"{version_b['hash'][:8]}  ({version_b['message']})"

    print_diff(diff_lines, label_a, label_b, context_lines=context)


# ---------------------------------------------------------------------------
# checkout
# ---------------------------------------------------------------------------


@cli.command("checkout")
@click.argument("prompt_name", metavar="<prompt-name>")
@click.argument("commit_hash", metavar="<hash>")
@click.option(
    "--output", "-o",
    default=None,
    metavar="<file>",
    help="Destination file path. Defaults to <prompt-name>.txt.",
)
def cmd_checkout(prompt_name: str, commit_hash: str, output: str | None) -> None:
    """
    Restore <prompt-name> to a specific version.

    \b
    Example:
      promptvc checkout summarizer a3f92c1b
      promptvc checkout summarizer a3f92c1b --output restored.txt
    """
    try:
        version = _store.get_version(prompt_name, commit_hash)
    except (CommitNotFoundError, AmbiguousHashError) as exc:
        print_error(str(exc))
        sys.exit(1)

    out_path = output or f"{prompt_name}.txt"
    Path(out_path).write_text(version["content"], encoding="utf-8")

    print_checkout_success(version["hash"], out_path)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@cli.command("status")
@click.argument("prompt_name", metavar="<prompt-name>")
def cmd_status(prompt_name: str) -> None:
    """
    Show the latest committed version of <prompt-name>.

    \b
    Example:
      promptvc status summarizer
    """
    latest = _store.get_latest(prompt_name)

    if latest is None:
        click.echo(
            click.style(f"  No versions found for '{prompt_name}'.", dim=True)
        )
        click.echo(
            click.style(
                f"  Tip: promptvc commit {prompt_name} <file> -m \"initial version\"",
                dim=True,
            )
        )
        return

    print_status(prompt_name, latest)


# ---------------------------------------------------------------------------
# ls
# ---------------------------------------------------------------------------


@cli.command("ls")
def cmd_ls() -> None:
    """
    List all tracked prompts.

    \b
    Example:
      promptvc ls
    """
    prompts = _store.list_prompts()

    version_counts = {p: _store.count_versions(p) for p in prompts}
    latest_hashes = {
        p: (latest["hash"] if (latest := _store.get_latest(p)) else "")
        for p in prompts
    }

    print_prompt_list(prompts, version_counts, latest_hashes)


# ---------------------------------------------------------------------------
# tag
# ---------------------------------------------------------------------------


@cli.command("tag")
@click.argument("prompt_name", metavar="<prompt-name>")
@click.argument("commit_hash", metavar="<hash>")
@click.option(
    "--label", "-l",
    default=None,
    metavar="<label>",
    help="Tag label (prompted interactively if omitted).",
)
def cmd_tag(prompt_name: str, commit_hash: str, label: str | None) -> None:
    """
    Attach a label to a specific commit.

    \b
    Example:
      promptvc tag summarizer a3f92c1b --label production
      promptvc tag summarizer a3f92c1b   # prompts for label
    """
    if label is None:
        label = click.prompt("Tag label")

    if not label.strip():
        print_error("Tag label cannot be empty.")
        sys.exit(1)

    try:
        _store.add_tag(prompt_name, commit_hash, label.strip())
    except (CommitNotFoundError, AmbiguousHashError) as exc:
        print_error(str(exc))
        sys.exit(1)

    # Resolve full hash for display.
    version = _store.get_version(prompt_name, commit_hash)
    print_tag_success(label.strip(), version["hash"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    cli()
