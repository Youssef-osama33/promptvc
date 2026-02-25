"""
display.py — Colorized terminal output for PromptVC.

All user-facing rendering lives here so that ``cli.py`` stays focused on
command logic and ``store.py`` / ``differ.py`` stay free of I/O concerns.

Colour palette
--------------
  Yellow  — commit hashes  (familiar from git-log)
  Green   — added lines    (+)
  Red     — removed lines  (-)
  Cyan    — metadata keys  (Model, Date, Tags)
  Bright  — section headers
  Dim     — unchanged lines in diff context

The module writes exclusively via :func:`click.echo` so output is
redirectable and plays well with Click's test runner.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import click

from promptvc.differ import DiffKind, DiffLine, DiffSummary, summarise


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------


def _hash_style(text: str) -> str:
    return click.style(text, fg="yellow")


def _key_style(text: str) -> str:
    return click.style(text, fg="cyan", bold=False)


def _added_style(text: str) -> str:
    return click.style(text, fg="green")


def _removed_style(text: str) -> str:
    return click.style(text, fg="red")


def _dim_style(text: str) -> str:
    return click.style(text, dim=True)


def _bold(text: str) -> str:
    return click.style(text, bold=True)


def _rule(width: int = 50, char: str = "─") -> str:
    return char * width


# ---------------------------------------------------------------------------
# Public rendering functions
# ---------------------------------------------------------------------------


def print_log(history: List[dict]) -> None:
    """
    Render commit history in a git-log style.

    Parameters
    ----------
    history : list of dict
        As returned by :meth:`PromptStore.get_history` — newest first.
    """
    if not history:
        click.echo(click.style("  No commits found.", dim=True))
        return

    for i, entry in enumerate(history):
        if i > 0:
            click.echo()

        click.echo(_hash_style(f"commit {entry['hash']}"))

        click.echo(f"{_key_style('Model:  ')} {entry['model']}")
        click.echo(f"{_key_style('Date:   ')} {_format_date(entry['created_at'])}")

        if entry.get("tags"):
            tags_str = ", ".join(
                click.style(t, fg="magenta") for t in entry["tags"]
            )
            click.echo(f"{_key_style('Tags:   ')} {tags_str}")

        click.echo()
        click.echo(f"    {entry['message']}")

    click.echo()


def print_diff(
    diff_lines: Sequence[DiffLine],
    label_a: str,
    label_b: str,
    context_lines: int = 3,
) -> None:
    """
    Render a colorized, context-aware unified diff.

    Only lines within *context_lines* of a change are shown; the rest
    are collapsed into a ``@@ ... @@`` hunk header — matching the
    familiar unified-diff format.

    Parameters
    ----------
    diff_lines : sequence of DiffLine
        Output of :func:`differ.diff_prompts`.
    label_a : str
        Short label for the old version (e.g. the first 8 chars of the hash).
    label_b : str
        Short label for the new version.
    context_lines : int
        Number of surrounding unchanged lines to show around each change.
    """
    stats: DiffSummary = summarise(diff_lines)

    click.echo(_dim_style(f"--- {label_a}"))
    click.echo(_dim_style(f"+++ {label_b}"))
    click.echo()

    if stats.is_identical:
        click.echo(click.style("  Versions are identical.", dim=True))
        return

    # Identify which indices are "interesting" (changed) so we can
    # compute context windows.
    changed_indices = {
        i for i, dl in enumerate(diff_lines) if not dl.is_unchanged()
    }

    context_set: set[int] = set()
    for idx in changed_indices:
        for offset in range(-context_lines, context_lines + 1):
            neighbour = idx + offset
            if 0 <= neighbour < len(diff_lines):
                context_set.add(neighbour)

    last_printed: Optional[int] = None

    for i, dl in enumerate(diff_lines):
        if i not in context_set:
            continue

        # Emit a separator when there is a gap since the last printed line.
        if last_printed is not None and i > last_printed + 1:
            click.echo(click.style("  ···", dim=True))

        if dl.kind is DiffKind.ADDED:
            click.echo(_added_style(f"+ {dl.content}"))
        elif dl.kind is DiffKind.REMOVED:
            click.echo(_removed_style(f"- {dl.content}"))
        else:
            click.echo(_dim_style(f"  {dl.content}"))

        last_printed = i

    click.echo()
    _print_diff_stats(stats)


def print_status(prompt_name: str, latest: dict) -> None:
    """
    Render the current status of a prompt — latest commit + content preview.

    Parameters
    ----------
    prompt_name : str
        The prompt being displayed.
    latest : dict
        As returned by :meth:`PromptStore.get_latest`.
    """
    short = latest["hash"][:8]

    click.echo()
    click.echo(f"{_key_style('Prompt: ')} {_bold(prompt_name)}")
    click.echo(
        f"{_key_style('Latest: ')} {_hash_style(short)}  —  {latest['message']}"
    )
    click.echo(f"{_key_style('Model:  ')} {latest['model']}")
    click.echo(f"{_key_style('Date:   ')} {_format_date(latest['created_at'])}")

    if latest.get("tags"):
        tags_str = ", ".join(
            click.style(t, fg="magenta") for t in latest["tags"]
        )
        click.echo(f"{_key_style('Tags:   ')} {tags_str}")

    click.echo()
    click.echo(_bold("Content preview:"))
    click.echo(_rule())

    content = latest["content"]
    preview_limit = 400
    preview = content[:preview_limit]
    if len(content) > preview_limit:
        preview += click.style("\n  … (truncated)", dim=True)
    click.echo(preview)

    click.echo(_rule())
    click.echo()


def print_commit_success(commit_hash: str, message: str) -> None:
    """Print the confirmation line after a successful commit."""
    short = commit_hash[:8]
    click.echo(
        click.style("✓ ", fg="green")
        + f"Committed [{_hash_style(short)}] {message}"
    )


def print_checkout_success(commit_hash: str, output_path: str) -> None:
    """Print the confirmation line after a successful checkout."""
    short = commit_hash[:8]
    click.echo(
        click.style("✓ ", fg="green")
        + f"Checked out [{_hash_style(short)}] → {click.style(output_path, underline=True)}"
    )


def print_prompt_list(prompts: List[str], version_counts: dict, latest_hashes: dict) -> None:
    """
    Render the ``ls`` listing of all tracked prompts.

    Parameters
    ----------
    prompts : list of str
        Sorted list of prompt names.
    version_counts : dict
        Maps prompt name → number of commits.
    latest_hashes : dict
        Maps prompt name → latest commit hash (full).
    """
    if not prompts:
        click.echo(
            click.style(
                "  No prompts tracked yet. Use 'promptvc commit' to start.",
                dim=True,
            )
        )
        return

    click.echo(_bold("Tracked prompts:"))
    click.echo()

    name_width = max(len(p) for p in prompts) + 2

    for name in prompts:
        n = version_counts.get(name, 0)
        unit = "version" if n == 1 else "versions"
        h = latest_hashes.get(name, "")[:8]

        padded_name = click.style(name.ljust(name_width), bold=True)
        count_str = click.style(f"({n} {unit})", dim=True)
        hash_str = _hash_style(f"[{h}]")

        click.echo(f"  • {padded_name}  {count_str}  {hash_str}")

    click.echo()


def print_tag_success(label: str, commit_hash: str) -> None:
    """Print the confirmation line after successfully tagging a commit."""
    short = commit_hash[:8]
    click.echo(
        click.style("✓ ", fg="green")
        + f"Tagged [{_hash_style(short)}] as {click.style(repr(label), fg='magenta')}"
    )


def print_error(message: str) -> None:
    """Print a formatted error message to stderr."""
    click.echo(
        click.style("✗ Error: ", fg="red", bold=True) + message,
        err=True,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _format_date(iso_str: str) -> str:
    """
    Reformat an ISO-8601 UTC timestamp into a human-friendly string.

    ``2024-03-14T11:00:00.123456+00:00`` → ``2024-03-14  11:00 UTC``
    """
    try:
        # Trim microseconds and timezone noise for a clean display.
        return iso_str[:16].replace("T", "  ") + " UTC"
    except Exception:
        return iso_str


def _print_diff_stats(stats: DiffSummary) -> None:
    """Render the +/- summary line at the bottom of a diff."""
    added_str = _added_style(f"  +{stats.added}")
    removed_str = _removed_style(f"  -{stats.removed}")
    unchanged_str = _dim_style(f"  {stats.unchanged} unchanged")
    click.echo(added_str + removed_str + unchanged_str)
    click.echo()
