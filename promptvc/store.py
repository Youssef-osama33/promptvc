"""
store.py — SQLite persistence layer for PromptVC.

All prompt versions are stored in a single SQLite database at
~/.promptvc/prompts.db. Each commit is a full snapshot — not a delta —
so every version is self-contained and perfectly reconstructable.

Schema
------
  projects(name, created_at)
  commits(hash, project, prompt_name, content, message, model, tags, created_at)
  tags(id, project, prompt_name, commit_hash, label, created_at)

Design decisions
----------------
- Full snapshots over deltas: simpler, safer, always restorable.
- SHA-256 over sequential IDs: content-addressable, collision-proof.
- SQLite over flat files: atomic writes, queryable, portable.
- Partial hash lookups: usability mirror of Git's short-hash UX.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Optional


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PromptVCError(Exception):
    """Base exception for all PromptVC storage errors."""


class ProjectNotFoundError(PromptVCError):
    """Raised when a referenced project does not exist."""


class CommitNotFoundError(PromptVCError):
    """Raised when a referenced commit hash cannot be resolved."""


class AmbiguousHashError(PromptVCError):
    """Raised when a short hash matches more than one commit."""


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    name       TEXT PRIMARY KEY,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS commits (
    hash        TEXT PRIMARY KEY,
    project     TEXT NOT NULL,
    prompt_name TEXT NOT NULL,
    content     TEXT NOT NULL,
    message     TEXT NOT NULL,
    model       TEXT NOT NULL DEFAULT 'gpt-4',
    tags        TEXT NOT NULL DEFAULT '[]',
    created_at  TEXT NOT NULL,
    FOREIGN KEY (project) REFERENCES projects (name)
);

CREATE INDEX IF NOT EXISTS idx_commits_prompt_name
    ON commits (prompt_name, created_at DESC);

CREATE TABLE IF NOT EXISTS tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT    NOT NULL,
    prompt_name TEXT    NOT NULL,
    commit_hash TEXT    NOT NULL,
    label       TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    FOREIGN KEY (commit_hash) REFERENCES commits (hash)
);
"""


# ---------------------------------------------------------------------------
# PromptStore
# ---------------------------------------------------------------------------


class PromptStore:
    """
    Manages all read/write operations against the PromptVC SQLite database.

    Parameters
    ----------
    base_dir : str or Path, optional
        Directory where prompts.db is stored. Defaults to ``~/.promptvc``.

    Examples
    --------
    >>> store = PromptStore()
    >>> commit_hash = store.commit(
    ...     prompt_name="summarizer",
    ...     content="You are a helpful assistant.",
    ...     message="initial version",
    ...     model="gpt-4",
    ...     tags=["prod"],
    ... )
    >>> version = store.get_latest("summarizer")
    """

    _DB_NAME = "prompts.db"

    def __init__(self, base_dir: Optional[str | Path] = None) -> None:
        self._base_dir = Path(base_dir or os.path.expanduser("~/.promptvc"))
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._base_dir / self._DB_NAME
        self._initialise_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a thread-local SQLite connection with row_factory set."""
        conn = sqlite3.connect(str(self._db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialise_schema(self) -> None:
        """Apply DDL statements idempotently on first use."""
        with self._connect() as conn:
            conn.executescript(_DDL)

    @staticmethod
    def _now() -> str:
        """Return a UTC ISO-8601 timestamp string."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _hash(prompt_name: str, content: str, timestamp: str) -> str:
        """
        Derive a deterministic SHA-256 commit hash.

        The hash is computed over the triple (prompt_name, content, timestamp)
        so two commits with identical content but different timestamps produce
        different hashes — matching real Git semantics.
        """
        payload = f"{prompt_name}\x00{content}\x00{timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init(self, name: str) -> None:
        """
        Register a prompt project.

        This is called automatically by :meth:`commit`, so explicit
        invocation is optional — but available for tooling that wants
        to declare a project before any commits exist.

        Parameters
        ----------
        name : str
            The project / prompt name.
        """
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects (name, created_at) VALUES (?, ?)",
                (name, self._now()),
            )

    def commit(
        self,
        prompt_name: str,
        content: str,
        message: str,
        model: str = "gpt-4",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Persist a new version of a prompt and return its commit hash.

        Parameters
        ----------
        prompt_name : str
            Logical name that groups versions together (e.g. ``"summarizer"``).
        content : str
            The full text of the prompt at this version.
        message : str
            A human-readable description of what changed.
        model : str
            The target LLM model (informational, default ``"gpt-4"``).
        tags : list of str, optional
            Arbitrary labels attached to this commit (e.g. ``["prod", "v1"]``).

        Returns
        -------
        str
            The 64-character SHA-256 hex digest identifying this commit.
        """
        tags = tags or []
        timestamp = self._now()
        commit_hash = self._hash(prompt_name, content, timestamp)

        self.init(prompt_name)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO commits
                    (hash, project, prompt_name, content, message, model, tags, created_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    commit_hash,
                    prompt_name,
                    prompt_name,
                    content,
                    message,
                    model,
                    json.dumps(tags),
                    timestamp,
                ),
            )

        return commit_hash

    def get_history(self, prompt_name: str) -> List[dict]:
        """
        Return all commits for *prompt_name*, newest first.

        Parameters
        ----------
        prompt_name : str
            The prompt to query.

        Returns
        -------
        list of dict
            Each dict contains: ``hash``, ``message``, ``model``,
            ``tags``, ``created_at``.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT hash, message, model, tags, created_at
                  FROM commits
                 WHERE prompt_name = ?
                 ORDER BY created_at DESC
                """,
                (prompt_name,),
            ).fetchall()

        return [self._row_to_summary(r) for r in rows]

    def get_version(self, prompt_name: str, commit_hash: str) -> dict:
        """
        Resolve a full or partial commit hash and return the commit record.

        Supports short hashes (minimum 4 characters) exactly like Git.

        Parameters
        ----------
        prompt_name : str
            The owning prompt.
        commit_hash : str
            Full or partial (prefix) commit hash.

        Returns
        -------
        dict
            Commit record with keys: ``hash``, ``content``, ``message``,
            ``model``, ``tags``, ``created_at``.

        Raises
        ------
        CommitNotFoundError
            If no commit matches the given hash prefix.
        AmbiguousHashError
            If more than one commit matches a short hash prefix.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT hash, content, message, model, tags, created_at
                  FROM commits
                 WHERE prompt_name = ?
                   AND hash LIKE ?
                """,
                (prompt_name, f"{commit_hash}%"),
            ).fetchall()

        if not rows:
            raise CommitNotFoundError(
                f"No commit matching '{commit_hash}' found for prompt '{prompt_name}'."
            )
        if len(rows) > 1:
            candidates = ", ".join(r["hash"][:8] for r in rows)
            raise AmbiguousHashError(
                f"Short hash '{commit_hash}' is ambiguous. "
                f"Candidates: {candidates}. Use more characters."
            )

        return self._row_to_full(rows[0])

    def get_latest(self, prompt_name: str) -> Optional[dict]:
        """
        Return the most recent commit for *prompt_name*, or ``None``.

        Parameters
        ----------
        prompt_name : str
            The prompt to query.

        Returns
        -------
        dict or None
            Full commit record, or ``None`` if no commits exist.
        """
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT hash, content, message, model, tags, created_at
                  FROM commits
                 WHERE prompt_name = ?
                 ORDER BY created_at DESC
                 LIMIT 1
                """,
                (prompt_name,),
            ).fetchone()

        return self._row_to_full(row) if row else None

    def list_prompts(self) -> List[str]:
        """
        Return a sorted list of all prompt names that have at least one commit.

        Returns
        -------
        list of str
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT prompt_name FROM commits ORDER BY prompt_name ASC"
            ).fetchall()

        return [r["prompt_name"] for r in rows]

    def count_versions(self, prompt_name: str) -> int:
        """Return the total number of committed versions for *prompt_name*."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM commits WHERE prompt_name = ?",
                (prompt_name,),
            ).fetchone()

        return row["n"] if row else 0

    def add_tag(self, prompt_name: str, commit_hash: str, label: str) -> None:
        """
        Attach a human-readable label to an existing commit.

        Parameters
        ----------
        prompt_name : str
            The owning prompt.
        commit_hash : str
            Full or partial hash of the commit to label.
        label : str
            The tag label (e.g. ``"production"``).

        Raises
        ------
        CommitNotFoundError
            If the referenced commit does not exist.
        """
        # Resolve — raises CommitNotFoundError / AmbiguousHashError if bad.
        version = self.get_version(prompt_name, commit_hash)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tags (project, prompt_name, commit_hash, label, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (prompt_name, prompt_name, version["hash"], label, self._now()),
            )

    # ------------------------------------------------------------------
    # Private serialisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_summary(row: sqlite3.Row) -> dict:
        return {
            "hash": row["hash"],
            "message": row["message"],
            "model": row["model"],
            "tags": json.loads(row["tags"]),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _row_to_full(row: sqlite3.Row) -> dict:
        return {
            "hash": row["hash"],
            "content": row["content"],
            "message": row["message"],
            "model": row["model"],
            "tags": json.loads(row["tags"]),
            "created_at": row["created_at"],
        }
