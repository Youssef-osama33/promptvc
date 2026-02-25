"""
test_core.py — Comprehensive test suite for PromptVC.

Tests are organised into three classes that mirror the three core modules:

  TestPromptStore   — persistence, retrieval, partial hashes, error handling
  TestDiffer        — diff correctness, edge cases, summary statistics
  TestCLI           — end-to-end command invocation via Click's test runner

Each test is self-contained: a fresh temporary directory is used as the
store's base_dir so tests never touch ~/.promptvc and never interfere
with each other.

Run with:
  pytest tests/ -v
  pytest tests/ -v --tb=short    # compact tracebacks
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from promptvc.cli import cli
from promptvc.differ import DiffKind, diff_prompts, summarise
from promptvc.store import (
    AmbiguousHashError,
    CommitNotFoundError,
    PromptStore,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path) -> PromptStore:
    """Return a PromptStore backed by a fresh temporary directory."""
    return PromptStore(base_dir=tmp_path)


@pytest.fixture()
def runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """
    Return a Click test runner whose PromptStore writes to tmp_path.

    We monkeypatch the module-level ``_store`` in ``cli`` so all commands
    use the isolated store without modifying ~/.promptvc.
    """
    import promptvc.cli as cli_module

    isolated_store = PromptStore(base_dir=tmp_path)
    monkeypatch.setattr(cli_module, "_store", isolated_store)
    return CliRunner()


# ---------------------------------------------------------------------------
# TestPromptStore
# ---------------------------------------------------------------------------


class TestPromptStore:
    """Unit tests for the SQLite persistence layer."""

    # --- commit & retrieve -------------------------------------------------

    def test_commit_returns_64_char_sha256(self, store: PromptStore) -> None:
        h = store.commit("summarizer", "Be helpful.", "v1", "gpt-4", [])
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_commit_is_idempotent_on_same_content_different_time(
        self, store: PromptStore
    ) -> None:
        """Two commits of the same content produce different hashes (timestamp differs)."""
        h1 = store.commit("bot", "Hello", "first", "gpt-4", [])
        h2 = store.commit("bot", "Hello", "second", "gpt-4", [])
        # Hashes differ because timestamps differ.
        assert h1 != h2

    def test_get_latest_returns_most_recent(self, store: PromptStore) -> None:
        store.commit("p", "v1", "first commit", "gpt-4", [])
        store.commit("p", "v2", "second commit", "gpt-4", [])
        latest = store.get_latest("p")
        assert latest is not None
        assert latest["message"] == "second commit"
        assert latest["content"] == "v2"

    def test_get_latest_returns_none_for_unknown_prompt(
        self, store: PromptStore
    ) -> None:
        result = store.get_latest("does-not-exist")
        assert result is None

    def test_stored_tags_round_trip(self, store: PromptStore) -> None:
        h = store.commit("p", "content", "msg", "gpt-4", ["prod", "stable"])
        version = store.get_version("p", h)
        assert version["tags"] == ["prod", "stable"]

    def test_stored_model_round_trip(self, store: PromptStore) -> None:
        h = store.commit("p", "content", "msg", "claude-3", [])
        version = store.get_version("p", h)
        assert version["model"] == "claude-3"

    # --- history -----------------------------------------------------------

    def test_get_history_newest_first(self, store: PromptStore) -> None:
        messages = ["first", "second", "third"]
        for msg in messages:
            store.commit("p", msg, msg, "gpt-4", [])

        history = store.get_history("p")
        assert [e["message"] for e in history] == list(reversed(messages))

    def test_get_history_empty_for_unknown_prompt(
        self, store: PromptStore
    ) -> None:
        assert store.get_history("unknown") == []

    # --- partial hash lookup -----------------------------------------------

    def test_get_version_by_full_hash(self, store: PromptStore) -> None:
        h = store.commit("p", "hello", "msg", "gpt-4", [])
        v = store.get_version("p", h)
        assert v["hash"] == h

    def test_get_version_by_partial_hash_8_chars(
        self, store: PromptStore
    ) -> None:
        h = store.commit("p", "hello", "msg", "gpt-4", [])
        v = store.get_version("p", h[:8])
        assert v["hash"] == h

    def test_get_version_raises_for_unknown_hash(
        self, store: PromptStore
    ) -> None:
        store.commit("p", "hello", "msg", "gpt-4", [])
        with pytest.raises(CommitNotFoundError):
            store.get_version("p", "deadbeef")

    def test_get_version_raises_ambiguous_for_colliding_prefix(
        self, store: PromptStore
    ) -> None:
        """
        Manufacture two hashes that share the same first character so that a
        single-character prefix lookup is ambiguous.  We can't control SHA-256
        output, so we instead directly insert two rows with a known shared
        prefix using the internal connection.
        """
        import hashlib, json
        from datetime import datetime, timezone

        store.init("p")

        fake_hashes = ["aaaa1111" + "0" * 56, "aaaa2222" + "0" * 56]
        now = datetime.now(timezone.utc).isoformat()

        with store._connect() as conn:
            for fh in fake_hashes:
                conn.execute(
                    """INSERT OR IGNORE INTO commits
                       (hash, project, prompt_name, content, message, model, tags, created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (fh, "p", "p", "content", "msg", "gpt-4", "[]", now),
                )

        with pytest.raises(AmbiguousHashError):
            store.get_version("p", "aaaa")

    # --- list & count -------------------------------------------------------

    def test_list_prompts_empty_initially(self, store: PromptStore) -> None:
        assert store.list_prompts() == []

    def test_list_prompts_sorted(self, store: PromptStore) -> None:
        for name in ["zebra", "alpha", "mango"]:
            store.commit(name, "content", "msg", "gpt-4", [])
        assert store.list_prompts() == ["alpha", "mango", "zebra"]

    def test_count_versions(self, store: PromptStore) -> None:
        assert store.count_versions("p") == 0
        store.commit("p", "v1", "first", "gpt-4", [])
        assert store.count_versions("p") == 1
        store.commit("p", "v2", "second", "gpt-4", [])
        assert store.count_versions("p") == 2

    # --- tagging ------------------------------------------------------------

    def test_add_tag_success(self, store: PromptStore) -> None:
        h = store.commit("p", "content", "msg", "gpt-4", [])
        store.add_tag("p", h[:8], "production")  # should not raise

    def test_add_tag_raises_for_unknown_hash(self, store: PromptStore) -> None:
        store.commit("p", "content", "msg", "gpt-4", [])
        with pytest.raises(CommitNotFoundError):
            store.add_tag("p", "deadbeef", "production")


# ---------------------------------------------------------------------------
# TestDiffer
# ---------------------------------------------------------------------------


class TestDiffer:
    """Unit tests for the line-by-line diff engine."""

    def test_identical_content_produces_no_changes(self) -> None:
        text = "You are a helpful assistant.\nAnswer concisely."
        lines = diff_prompts(text, text)
        stats = summarise(lines)
        assert stats.added == 0
        assert stats.removed == 0
        assert stats.unchanged == 2
        assert stats.is_identical

    def test_single_addition(self) -> None:
        a = "Line 1\nLine 2"
        b = "Line 1\nLine 2\nLine 3"
        stats = summarise(diff_prompts(a, b))
        assert stats.added >= 1
        assert stats.removed == 0

    def test_single_deletion(self) -> None:
        a = "Line 1\nLine 2\nLine 3"
        b = "Line 1\nLine 3"
        stats = summarise(diff_prompts(a, b))
        assert stats.removed >= 1

    def test_replacement_produces_both_added_and_removed(self) -> None:
        a = "Be verbose and thorough in every response."
        b = "Be concise. One sentence max."
        stats = summarise(diff_prompts(a, b))
        assert stats.added >= 1
        assert stats.removed >= 1

    def test_diff_line_kinds_are_correct(self) -> None:
        a = "old content"
        b = "new content"
        lines = diff_prompts(a, b)
        kinds = {dl.kind for dl in lines}
        assert DiffKind.REMOVED in kinds
        assert DiffKind.ADDED in kinds

    def test_empty_to_content(self) -> None:
        lines = diff_prompts("", "Hello\nWorld")
        stats = summarise(lines)
        assert stats.added == 2
        assert stats.removed == 0

    def test_content_to_empty(self) -> None:
        lines = diff_prompts("Hello\nWorld", "")
        stats = summarise(lines)
        assert stats.removed == 2
        assert stats.added == 0

    def test_line_numbers_assigned_correctly(self) -> None:
        a = "A\nB\nC"
        b = "A\nX\nC"
        lines = diff_prompts(a, b)

        unchanged = [dl for dl in lines if dl.is_unchanged()]
        # Lines "A" and "C" are unchanged
        assert len(unchanged) == 2
        # Line numbers on both sides must be set for unchanged lines
        for dl in unchanged:
            assert dl.line_num_a is not None
            assert dl.line_num_b is not None

        removed = [dl for dl in lines if dl.is_removed()]
        for dl in removed:
            assert dl.line_num_a is not None
            assert dl.line_num_b is None

        added = [dl for dl in lines if dl.is_added()]
        for dl in added:
            assert dl.line_num_a is None
            assert dl.line_num_b is not None

    def test_summary_str(self) -> None:
        lines = diff_prompts("a\nb", "a\nc\nd")
        stats = summarise(lines)
        s = str(stats)
        assert "+" in s
        assert "-" in s

    def test_multiline_real_world_prompt(self) -> None:
        a = textwrap.dedent("""\
            You are a helpful assistant.
            Answer questions clearly and concisely.
            Do not make up facts.
        """)
        b = textwrap.dedent("""\
            You are a helpful assistant.
            Answer questions clearly and concisely.
            Do not make up facts.
            Always cite your sources.
        """)
        stats = summarise(diff_prompts(a, b))
        assert stats.added >= 1
        assert stats.removed == 0
        assert stats.unchanged >= 3


# ---------------------------------------------------------------------------
# TestCLI
# ---------------------------------------------------------------------------


class TestCLI:
    """End-to-end tests for every CLI command via Click's CliRunner."""

    # --- commit ------------------------------------------------------------

    def test_commit_creates_version(self, runner: CliRunner, tmp_path: Path) -> None:
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("You are a helpful assistant.", encoding="utf-8")

        result = runner.invoke(cli, ["commit", "summarizer", str(prompt_file), "-m", "initial"])
        assert result.exit_code == 0
        assert "Committed" in result.output
        assert "initial" in result.output

    def test_commit_requires_message(self, runner: CliRunner, tmp_path: Path) -> None:
        prompt_file = tmp_path / "prompt.txt"
        prompt_file.write_text("Hello", encoding="utf-8")
        result = runner.invoke(cli, ["commit", "p", str(prompt_file)])
        assert result.exit_code != 0

    def test_commit_rejects_empty_file(self, runner: CliRunner, tmp_path: Path) -> None:
        empty = tmp_path / "empty.txt"
        empty.write_text("   ", encoding="utf-8")
        result = runner.invoke(cli, ["commit", "p", str(empty), "-m", "oops"])
        assert result.exit_code != 0

    # --- log ---------------------------------------------------------------

    def test_log_shows_history(self, runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "p.txt"
        f.write_text("v1", encoding="utf-8")
        runner.invoke(cli, ["commit", "p", str(f), "-m", "first"])

        result = runner.invoke(cli, ["log", "p"])
        assert result.exit_code == 0
        assert "first" in result.output

    def test_log_empty_prompt(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["log", "nonexistent"])
        assert result.exit_code == 0
        assert "No history" in result.output

    # --- status ------------------------------------------------------------

    def test_status_shows_latest(self, runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "p.txt"
        f.write_text("Be helpful.", encoding="utf-8")
        runner.invoke(cli, ["commit", "p", str(f), "-m", "initial"])

        result = runner.invoke(cli, ["status", "p"])
        assert result.exit_code == 0
        assert "initial" in result.output
        assert "Be helpful." in result.output

    def test_status_unknown_prompt(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["status", "ghost"])
        assert result.exit_code == 0
        assert "No versions" in result.output

    # --- checkout ----------------------------------------------------------

    def test_checkout_restores_content(self, runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "p.txt"
        f.write_text("Original content.", encoding="utf-8")
        invoke = runner.invoke(cli, ["commit", "p", str(f), "-m", "v1"])

        # Extract the short hash from the commit output: "Committed [a3f92c1b] v1"
        hash_short = _extract_hash(invoke.output)

        output_file = tmp_path / "restored.txt"
        result = runner.invoke(
            cli,
            ["checkout", "p", hash_short, "--output", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.read_text(encoding="utf-8") == "Original content."

    def test_checkout_bad_hash(self, runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "p.txt"
        f.write_text("content", encoding="utf-8")
        runner.invoke(cli, ["commit", "p", str(f), "-m", "v1"])

        result = runner.invoke(cli, ["checkout", "p", "deadbeef"])
        assert result.exit_code != 0

    # --- diff --------------------------------------------------------------

    def test_diff_two_versions(self, runner: CliRunner, tmp_path: Path) -> None:
        f = tmp_path / "p.txt"

        f.write_text("Answer in 3 sentences.", encoding="utf-8")
        r1 = runner.invoke(cli, ["commit", "p", str(f), "-m", "v1"])
        h1 = _extract_hash(r1.output)

        f.write_text("Answer in 1 sentence.", encoding="utf-8")
        r2 = runner.invoke(cli, ["commit", "p", str(f), "-m", "v2"])
        h2 = _extract_hash(r2.output)

        result = runner.invoke(cli, ["diff", "p", h1, h2])
        assert result.exit_code == 0
        assert "+" in result.output or "-" in result.output

    # --- ls ----------------------------------------------------------------

    def test_ls_shows_all_prompts(self, runner: CliRunner, tmp_path: Path) -> None:
        for name in ["alpha", "beta"]:
            f = tmp_path / f"{name}.txt"
            f.write_text(f"prompt {name}", encoding="utf-8")
            runner.invoke(cli, ["commit", name, str(f), "-m", "init"])

        result = runner.invoke(cli, ["ls"])
        assert result.exit_code == 0
        assert "alpha" in result.output
        assert "beta" in result.output

    def test_ls_empty(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["ls"])
        assert result.exit_code == 0
        assert "No prompts" in result.output

    # --- version flag ------------------------------------------------------

    def test_version_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_hash(output: str) -> str:
    """
    Parse the 8-character short hash from a ``commit`` command's output.

    Expected format: ``✓ Committed [a3f92c1b] message``
    """
    import re
    match = re.search(r"\[([0-9a-f]{8})\]", output)
    assert match, f"Could not find hash in output: {output!r}"
    return match.group(1)
