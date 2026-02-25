<div align="center">

<br/>

```
██████╗ ██████╗  ██████╗ ███╗   ███╗██████╗ ████████╗██╗   ██╗ ██████╗
██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗╚══██╔══╝██║   ██║██╔════╝
██████╔╝██████╔╝██║   ██║██╔████╔██║██████╔╝   ██║   ██║   ██║██║
██╔═══╝ ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝    ██║   ╚██╗ ██╔╝██║
██║     ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║        ██║    ╚████╔╝ ╚██████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝        ╚═╝     ╚═══╝   ╚═════╝
```

### *Because prompts deserve the same respect as code.*

<br/>

[![PyPI](https://img.shields.io/pypi/v/promptvc?color=blueviolet&style=for-the-badge&label=PyPI)](https://pypi.org/project/promptvc/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Stars](https://img.shields.io/github/stars/yourusername/promptvc?style=for-the-badge&color=f59e0b)](https://github.com/yourusername/promptvc/stargazers)

<br/>

> *"The difference between a prompt that works and one that doesn't is often a single word.*
> *PromptVC makes sure you never lose the one that worked."*

<br/>

</div>

---

## The Story

Every prompt engineer has felt it.

You spend two hours tuning a system prompt. You test it. It's perfect — it handles edge cases, it keeps the right tone, it does exactly what you need. You make one more small change. Deploy. Go to bed.

Next morning, something is broken. The model is behaving strangely. You open your prompt file and stare at it, trying to remember what it looked like before.

You can't.

There's no history. No diff. No rollback. Just a blank cursor and the sinking feeling that the perfect version is gone forever.

**PromptVC was built for that moment — before it happens.**

---

## What It Does

PromptVC brings the discipline of Git to the world of LLM prompt engineering. It is a local-first, zero-dependency*, command-line tool that lets you version, diff, tag, and restore your prompts exactly the way you manage your source code.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   promptvc commit summarizer prompt.txt -m "v1 — works"    │
│   promptvc commit summarizer prompt.txt -m "v2 — testing"  │
│   promptvc diff   summarizer <hash_1> <hash_2>             │
│   promptvc checkout summarizer <hash_1>                    │
│                                                             │
│   Your prompts. Tracked forever. Locally.                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

*\*Only requires `click` for the CLI interface. Storage is plain SQLite.*

---

## Installation

```bash
pip install promptvc
```

One command. No config files. No accounts. No cloud.

---

## Quick Start

```bash
# Step 1 — write your prompt
echo "You are a helpful assistant. Answer in 3 sentences max." > prompt.txt

# Step 2 — commit it
promptvc commit summarizer prompt.txt -m "initial version" --model gpt-4

# Step 3 — make changes and commit again
echo "You are a helpful assistant. Be direct. Max 2 sentences." > prompt.txt
promptvc commit summarizer prompt.txt -m "tighter constraint" --model gpt-4

# Step 4 — see exactly what changed
promptvc diff summarizer <hash_1> <hash_2>

# Step 5 — something broke? go back.
promptvc checkout summarizer <hash_1>
```

You now have full version control over your prompt. It took 30 seconds.

---

## Commands

<details>
<summary><b>📝 commit</b> — Save a new version of a prompt</summary>

<br/>

```bash
promptvc commit <name> <file> -m "message" [--model gpt-4] [--tags prod,stable]
```

| Flag | Required | Description |
|---|---|---|
| `-m` | ✅ Yes | Commit message |
| `--model` | No | Target LLM model (default: `gpt-4`) |
| `--tags` | No | Comma-separated labels |

```bash
# Examples
promptvc commit summarizer prompt.txt -m "initial draft"
promptvc commit chatbot system.txt -m "add persona" --model claude-3 --tags "prod"
```

</details>

<details>
<summary><b>📜 log</b> — View full commit history</summary>

<br/>

```bash
promptvc log <name>
```

```
commit a3f92c1b9e4d2f7a8c3b1e6d9f0a2c5b
Model:   gpt-4
Date:    2024-03-12T10:30:00
Tags:    prod, stable

    tighter constraint

commit 31e0e29bfd18a7c43d85f920b1c6e471
Model:   gpt-4
Date:    2024-03-10T08:15:00

    initial version
```

</details>

<details>
<summary><b>🔍 diff</b> — Compare any two versions</summary>

<br/>

```bash
promptvc diff <name> <hash_a> <hash_b>
```

```diff
--- version a3f92c1b
+++ version fcfeceb2

  You are a helpful assistant.
- Answer in 3 sentences max.
+ Be direct. Max 2 sentences.
+ Always respond in JSON.

  +2 lines  -1 lines  1 unchanged
```

</details>

<details>
<summary><b>⏪ checkout</b> — Restore any past version</summary>

<br/>

```bash
promptvc checkout <name> <hash>
promptvc checkout <name> <hash> --output restored-prompt.txt
```

Writes the exact content of that commit to a file. Safe, instant, reversible.

</details>

<details>
<summary><b>📊 status</b> — Inspect the current version</summary>

<br/>

```bash
promptvc status <name>
```

```
Prompt:  summarizer
Latest:  fcfeceb2  —  tighter constraint
Model:   gpt-4
Date:    2024-03-12T10:30:00
Tags:    prod

Content preview:
──────────────────────────────────────────────────
You are a helpful assistant.
Be direct. Max 2 sentences.
Always respond in JSON.
──────────────────────────────────────────────────
```

</details>

<details>
<summary><b>📁 ls</b> — List all tracked prompts</summary>

<br/>

```bash
promptvc ls
```

```
Tracked prompts:
  • summarizer     (2 versions)  [fcfeceb2]
  • classifier     (1 version)   [31e0e29b]
```

</details>

<details>
<summary><b>🏷️ tag</b> — Label an important commit</summary>

<br/>

```bash
promptvc tag <name> <hash>
# → Tag label: production
```

</details>

---

## How It Works

PromptVC stores everything in a single SQLite database at `~/.promptvc/prompts.db`.

```
~/.promptvc/
└── prompts.db        ← your entire prompt history, forever
```

Each commit stores the full prompt content, a SHA-256 hash, a message, a model target, tags, and a timestamp. Nothing is ever deleted unless you delete it. No diffs are stored — full snapshots — so you can always reconstruct any version perfectly.

**Your data never leaves your machine.** No API calls, no telemetry, no accounts.

---

## Philosophy

Most tools in the LLM space are built for speed — ship fast, move on. PromptVC is built on a different premise: that prompts are artifacts worth preserving.

A great system prompt can take days to get right. It encodes your intent, your constraints, your understanding of the model's behavior. It is intellectual work. It deserves the same care as the code that calls it.

PromptVC is small, focused, and does one thing well. It will not become a platform. It will not add a dashboard or a subscription tier. It will always be a CLI tool you can understand completely by reading the source in an afternoon.

---

## Roadmap

This is v0.1.0 — the foundation. Planned next:

- **Branch support** — run parallel prompt experiments without clobbering your main version
- **Export** — generate a full Markdown changelog of a prompt's evolution
- **Remote sync** — optional backup to S3 or GitHub Gist
- **LLM scoring** — automatically evaluate prompt quality across versions using a judge model

---

## Contributing

PromptVC is open source and contributions are welcome. The codebase is small and readable — a good place to start.

```bash
git clone https://github.com/yourusername/promptvc
cd promptvc
pip install -e .
python -m pytest tests/
```

Please open an issue before submitting large changes so we can align on direction.

---

## License

[MIT](LICENSE). Use it, fork it, build on it.

---

<div align="center">

<br/>

*Built for the engineers who know that the right prompt*
*is worth keeping forever.*

<br/>

**⭐ Star this repo if PromptVC saved a prompt you would have lost.**

<br/>

</div>
