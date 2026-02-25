<div align="center">

<br/>

```
 ____  ____  ____  __  __  ____  ____  _  _  ___
(  _ \(  _ \(  _ \(  \/  )(  _ \(_  _)( \/ )/ __)
 ) _/  )   / ) _ < )    (  ) __/  )(   \  /( (__
(__)  (_)\_)(____/(_/\/\_)(__)   (__)   (__) \___)
```

<h2>Version control for the age of LLMs.</h2>

<p><i>Commit your prompts. Diff your thinking. Never lose what worked.</i></p>

<br/>

[![PyPI](https://img.shields.io/pypi/v/promptvc?color=blueviolet&style=for-the-badge)](https://pypi.org/project/promptvc/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](https://github.com/Youssef-osama33/promptvc/blob/main/LICENSE)
[![Stars](https://img.shields.io/github/stars/Youssef-osama33/promptvc?style=for-the-badge&color=f59e0b&label=⭐%20Stars)](https://github.com/Youssef-osama33/promptvc/stargazers)

<br/>

```bash
pip install promptvc
```

<br/>

<table>
<tr>
<td><a href="#-the-problem">The Problem</a></td>
<td><a href="#-installation">Install</a></td>
<td><a href="#-quick-start">Quick Start</a></td>
<td><a href="#-commands">Commands</a></td>
<td><a href="#-how-it-works">How It Works</a></td>
<td><a href="#-philosophy">Philosophy</a></td>
</tr>
</table>

<br/>

</div>

---

## 💀 The Problem

You've been there.

You spend hours — sometimes days — tuning a prompt. Testing edge cases. Getting the tone right. Fixing the format. Watching it finally behave exactly the way you need it to. It's working. It's *really* working.

So you make one more small tweak. Just a word or two. You save the file.

Then something breaks. The responses drift. The model ignores your instructions. You open the file and stare at it. You try to remember what it looked like before that last change.

You can't.

There's no history. No rollback. No diff. Just you, a blank cursor, and the dawning horror that the version that worked — **is gone forever.**

---

This is not a niche problem. It happens to every prompt engineer, every AI team, every developer building on top of LLMs. Prompts are the most critical, most fragile, and most poorly managed artifact in the modern AI stack.

We have Git for code. We have Figma history for design. We have nothing for prompts.

**Until now.**

---

## ✦ What Is PromptVC?

PromptVC is a **local-first, Git-inspired version control system built exclusively for LLM prompts.**

It gives you the same workflow discipline you use for code — commit, log, diff, checkout, tag — applied to the prompts that power your AI products.

No cloud. No account. No SaaS. Just a clean CLI and a SQLite file that lives on your machine and preserves every version of every prompt you've ever written.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  $ promptvc commit summarizer prompt.txt -m "initial version"       │
│  ✓ Committed [a3f92c1b] initial version                             │
│                                                                     │
│  $ promptvc status summarizer                                       │
│  Latest:  a3f92c1b  —  initial version                              │
│  Model:   gpt-4                                                     │
│                                                                     │
│  $ promptvc checkout summarizer a3f92c1b                            │
│  ✓ Checked out [a3f92c1b] → summarizer.txt                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Installation

```bash
pip install promptvc
```

Zero configuration. Works immediately. Your history is stored at `~/.promptvc/prompts.db` — a plain SQLite file you own completely.

---

## 🚀 Quick Start

**In under 2 minutes, your prompts will be versioned forever.**

```bash
# 1. Write your prompt
echo "You are a helpful assistant. Answer in 3 sentences max." > prompt.txt

# 2. Commit it — like Git, but for prompts
promptvc commit summarizer prompt.txt -m "initial version" --model gpt-4

# 3. Check its status anytime
promptvc status summarizer

# 4. See your full history
promptvc log summarizer

# 5. Restore it anytime
promptvc checkout summarizer <hash>
```

That's the whole loop. **Write → Commit → Track → Recover.**

---

## 📖 Commands

### `commit` — Preserve a version forever

```bash
promptvc commit <prompt-name> <file> -m "your message" [--model gpt-4] [--tags prod,stable]
```

Think of this like `git commit`. Every time you reach a version worth keeping — commit it. You'll thank yourself later.

```bash
promptvc commit summarizer prompt.txt -m "initial version"
promptvc commit chatbot system.txt -m "first draft" --model claude-3 --tags "v1"
```

---

### `log` — See the full story of a prompt

```bash
promptvc log <prompt-name>
```

```
commit a3f92c1b9e4d2f7a8c3b1e6d9f0a2c5b
Model:   gpt-4
Date:    2024-03-14T11:00:00

    initial version
```

Every decision, recorded. Every message a breadcrumb back to what you were thinking.

---

### `diff` — See exactly what changed between any two versions

```bash
promptvc diff <prompt-name> <hash_a> <hash_b>
```

```diff
--- version 31e0e29b
+++ version a3f92c1b

  You are a helpful assistant.
- Answer in 3 sentences max.
+ Be direct. Max 2 sentences.
+ Always return a JSON object.

  +2 lines  -1 lines  1 unchanged
```

This is the feature that changes everything. Seeing the *exact* difference between a prompt that worked and one that didn't is how prompt engineering stops being guesswork.

---

### `checkout` — Go back to any version

```bash
promptvc checkout <prompt-name> <hash>
promptvc checkout <prompt-name> <hash> --output recovered.txt
```

Instant. Exact. No data loss. The version that worked is always one command away.

---

### `status` — What does my prompt look like right now?

```bash
promptvc status <prompt-name>
```

```
Prompt:  summarizer
Latest:  a3f92c1b  —  initial version
Model:   gpt-4
Date:    2024-03-14T11:00:00

Content preview:
──────────────────────────────────────────────────
You are a helpful assistant.
Answer in 3 sentences max.
──────────────────────────────────────────────────
```

---

### `ls` — Everything you've ever tracked

```bash
promptvc ls
```

```
Tracked prompts:
  • summarizer    (1 version)   [a3f92c1b]
```

---

### `tag` — Mark what matters

```bash
promptvc tag <prompt-name> <hash>
# → Tag label: production-v1
```

Tag the version that's live in production. Tag the version that passed QA. Tags make history navigable.

---

## 🔬 How It Works

PromptVC is deliberately simple. There is no magic.

```
~/.promptvc/
└── prompts.db        ← one SQLite file. your entire prompt history.
```

Every commit stores:
- The **full prompt content** (not a diff — a complete snapshot)
- A **SHA-256 hash** (your commit identifier)
- A **message, model, tags, and timestamp**

Because we store full snapshots, every version is perfectly reconstructable. Nothing is derived. Nothing can be corrupted. The SQLite file is readable with any database viewer.

**PromptVC makes zero network requests.** It has no telemetry. It does not know you exist. It runs entirely on your machine, forever, even without internet.

---

## 🗂️ Project Structure

```
promptvc/
├── promptvc/
│   ├── __init__.py       # v0.1.0
│   ├── cli.py            # all CLI commands (click)
│   ├── store.py          # SQLite storage backend
│   ├── differ.py         # line-by-line diff engine
│   └── display.py        # colorized terminal output
├── tests/
│   └── test_core.py
├── setup.py
└── README.md
```

---

## 🧠 Philosophy

PromptVC is built on a simple belief: **prompts are intellectual work, and intellectual work deserves to be preserved.**

A great system prompt can take days to engineer. It encodes your understanding of a model's behavior, your product's tone, your users' needs, and dozens of small discoveries made through trial and error. It is not disposable. It should not live in a Notion doc with no version history.

This tool will stay small. It will do one thing — version your prompts — and do it perfectly. It will never become a platform. It will never add a subscription. It will never require an account.

PromptVC is a **craftsman's tool.** Built once, built right, useful forever.

---

## 🛣️ What's Next

PromptVC `v0.1.0` is the foundation — stable, tested, and complete for its core purpose.

Future versions will explore:

- **Branches** — parallel prompt experiments that don't interfere with your main line
- **Export** — generate a full Markdown changelog of a prompt's evolution over time
- **Remote backup** — optional sync to S3 or GitHub Gist for team sharing
- **LLM Judge scoring** — automatically score prompt quality across versions using a judge model

These are planned, not promised. The core will never be broken in service of features.

---

## 🧪 Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 🤝 Contributing

The codebase is small by design. You can read the entire source in an afternoon. Contributions are welcome — please open an issue before large changes.

```bash
git clone https://github.com/Youssef-osama33/promptvc
cd promptvc
pip install -e .
pytest tests/
```

Commit style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

---

## 📄 License

[MIT](https://github.com/Youssef-osama33/promptvc/blob/main/LICENSE) — use it, fork it, build on it, ship it.

---

<div align="center">

<br/>

```
Prompts are not throwaway text.
They are the interface between human intent and machine intelligence.
They deserve to be treated that way.
```

<br/>

**If PromptVC saved a prompt you would have lost — leave a ⭐**

*It takes 2 seconds and means the world to an open source maintainer.*

<br/>

---

Made with obsession by [Youssef Osama](https://github.com/Youssef-osama33).

</div>
