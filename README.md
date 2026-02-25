<div align="center">

<img src="https://raw.githubusercontent.com/yourusername/promptvc/main/assets/logo.png" alt="PromptVC Logo" width="120" />

# PromptVC

**Git-like version control for LLM prompts.**

Track changes. Diff versions. Roll back mistakes. Treat your prompts like code.

[![PyPI version](https://img.shields.io/pypi/v/promptvc?color=brightgreen&label=pypi)](https://pypi.org/project/promptvc/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-ff69b4)](CONTRIBUTING.md)

<br/>

```bash
pip install promptvc
```

<br/>

[Quick Start](#-quick-start) · [Commands](#-commands) · [Why PromptVC](#-why-promptvc) · [Roadmap](#-roadmap) · [Contributing](#-contributing)

</div>

---

## 🤔 Why PromptVC?

You wouldn't write software without version control. So why are you managing your LLM prompts in a Google Doc?

| Without PromptVC | With PromptVC |
|---|---|
| 😬 Overwrote a prompt that was working great | ✅ Every version is saved and recoverable |
| 😬 Can't remember what you changed last week | ✅ Full commit history with messages |
| 😬 Two prompts, no idea which is newer | ✅ Diff any two versions instantly |
| 😬 Broke production — no way to roll back | ✅ Checkout any past version in seconds |
| 😬 Prompts scattered across Notion, Slack, txt files | ✅ One local database, all your prompts |

---

## ✨ Features

- 🔖 **Commit** — Save prompt versions with messages, model targets, and tags
- 🔍 **Diff** — Compare any two versions line-by-line with colorized output
- ⏪ **Checkout** — Restore any past version to a file instantly
- 📜 **Log** — Browse full commit history for any prompt
- 📊 **Status** — See the latest version and content preview at a glance
- 🏷️ **Tag** — Label important commits like `production` or `v2-stable`
- 💾 **Local-first** — SQLite database at `~/.promptvc/` — your data stays yours

---

## 🚀 Quick Start

```bash
# Install
pip install promptvc

# Write your first prompt
echo "You are a helpful assistant. Answer in 3 sentences max." > my-prompt.txt

# Commit it
promptvc commit assistant my-prompt.txt -m "initial version" --model gpt-4

# Iterate and commit again
echo "You are a helpful assistant. Be concise and direct. Max 2 sentences." > my-prompt.txt
promptvc commit assistant my-prompt.txt -m "shorter and more direct" --model gpt-4

# See what changed
promptvc log assistant
promptvc diff assistant <hash_1> <hash_2>
```

That's it. Your prompt history is now tracked forever.

---

## 📖 Commands

### `commit` · Save a new version

```bash
promptvc commit <name> <file> -m "message" [--model gpt-4] [--tags prod,v2]
```

```bash
# Examples
promptvc commit summarizer prompt.txt -m "initial version"
promptvc commit summarizer prompt.txt -m "add JSON output format" --model claude-3 --tags "prod,tested"
```

---

### `log` · Browse history

```bash
promptvc log <name>
```

```
commit a3f92c1b7e4d9f2c...          ← full hash
Model:   gpt-4
Date:    2024-03-12T10:30:00
Tags:    prod, tested

    add JSON output format          ← your commit message

commit 31e0e29bfd18a7c4...
Model:   gpt-4
Date:    2024-03-10T08:15:00

    initial version
```

---

### `diff` · Compare two versions

```bash
promptvc diff <name> <hash_a> <hash_b>
```

```diff
--- version a3f92c1b
+++ version fcfeceb2

  You are a helpful assistant.
- Answer in 3 sentences max.
+ Be concise and direct. Max 2 sentences.
+ Always respond in JSON format.

  +2 lines  -1 lines  1 unchanged
```

---

### `checkout` · Restore a past version

```bash
promptvc checkout <name> <hash>
promptvc checkout <name> <hash> --output restored.txt
```

---

### `status` · Inspect the latest version

```bash
promptvc status <name>
```

```
Prompt:  summarizer
Latest:  fcfeceb2  —  add JSON output format
Model:   gpt-4
Date:    2024-03-12T10:30:00
Tags:    prod, tested

Content preview:
──────────────────────────────────────────────────
You are a helpful assistant.
Be concise and direct. Max 2 sentences.
Always respond in JSON format.
──────────────────────────────────────────────────
```

---

### `ls` · List all tracked prompts

```bash
promptvc ls
```

```
Tracked prompts:
  • summarizer     (6 versions)  [fcfeceb2]
  • classifier     (3 versions)  [b1c22f09]
  • chat-system    (12 versions) [9a3e10de]
  • email-writer   (2 versions)  [4d71bc88]
```

---

### `tag` · Label an important commit

```bash
promptvc tag <name> <hash>
# → Enter tag label: production
```

---

## 🗂️ Project Structure

```
promptvc/
├── promptvc/
│   ├── __init__.py       # version
│   ├── cli.py            # all CLI commands (click)
│   ├── store.py          # SQLite storage backend
│   ├── differ.py         # line-by-line diff engine
│   └── display.py        # colorized terminal output
├── tests/
│   └── test_core.py      # full test suite
├── setup.py
└── README.md
```

---

## 🔒 Privacy & Data

All data lives in a single SQLite file at `~/.promptvc/prompts.db`.

- ✅ No accounts, no cloud, no telemetry
- ✅ Fully offline — works with no internet connection
- ✅ Back it up with `cp ~/.promptvc/prompts.db ./backup.db`
- ✅ Inspect it directly with any SQLite viewer

---

## 🛣️ Roadmap

| Status | Feature |
|---|---|
| ✅ Done | Commit, log, diff, checkout, status, tag |
| 🔜 Next | Branch support for parallel experiments |
| 🔜 Next | Export prompt history to Markdown |
| 💡 Planned | Remote sync to S3 / GitHub Gist |
| 💡 Planned | Web UI for visual diffing |
| 💡 Planned | LangChain & LlamaIndex integration |
| 💡 Planned | LLM-judge scoring across versions |

Have an idea? [Open an issue](https://github.com/yourusername/promptvc/issues) — contributions welcome.

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 🤝 Contributing

Pull requests are very welcome. For large changes, open an issue first so we can discuss direction.

```bash
git clone https://github.com/yourusername/promptvc
cd promptvc
pip install -e ".[dev]"
pytest tests/
```

Please follow conventional commit messages: `feat:`, `fix:`, `docs:`, `test:`, etc.

---

## 📄 License

[MIT](LICENSE) — free to use, fork, and build on.

---

<div align="center">

**If PromptVC saves you from a bad prompt deployment, consider giving it a ⭐**

Made with 🧠 for prompt engineers who care about their craft.

</div>
