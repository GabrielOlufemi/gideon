# gideon

A model-agnostic coding agent that lives in your terminal. Point it at a project and it'll read files, search your codebase, run commands, write and edit code, checking with you first before doing anything permanent.

## Install

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.sh | sh
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.ps1 | iex
```

That's it. Gideon is bundled as a standalone binary with no external dependencies. Supports Linux, macOS (Intel + Apple Silicon), and Windows.

<details>
<summary>Build from source</summary>

```bash
git clone https://github.com/GabrielOlufemi/gideon.git
cd gideon
python -m venv .venv && source .venv/bin/activate
pip install -e .
gideon
```

To build a standalone binary:

```bash
./build.sh
```

</details>

## Quick start

1. Run `gideon` in any project directory
2. Enter your OpenRouter API key when prompted (first run only)
3. Pick a model

Then just talk to it like you would a pair programmer. It already knows what's in your project.

## Commands

| Command | What it does |
|---|---|
| `/mode` | Switch between auto and manual permission mode |
| `/config` | Change model, update API key, view config |
| `/sessions` | List saved sessions for this project |
| `/restore <n>` | Restore a previous session |
| `/delete <n>` | Delete a session |
| `/rewind` | Rewind conversation history and restore codebase to a previous turn |
| `quit` / `exit` / `leave` | End the session |

## Features

- **Streaming Markdown chat** — responses render in real time with syntax-highlighted code blocks
- **Tool use** — reads files, searches code, runs shell commands, edits and writes files on your behalf
- **Permission gating** — destructive actions (writes, edits, shell commands) ask first; you can allow once, always, or deny
- **Auto mode** — skip permission prompts and let Gideon act autonomously
- **Session persistence** — every conversation is saved per project; resume, restore, or rewind anytime
- **Multi-model** — pick from recommended models or browse everything on OpenRouter
- **Project memory** — Gideon can save durable facts about your project to `.gideon/memory.md` so future sessions pick up where you left off. Cap at 2 KB.
- **Git awareness** — Gideon sees branch, recent commits, and working tree state automatically
- **Codebase rewind** — `/rewind` undoes not just the conversation but also any file edits made during those turns
- **Path safety** — operations are scoped to the directory you launched Gideon in

## How it works

Gideon talks to models through [OpenRouter](https://openrouter.ai), using function calling to read, search, and modify your codebase. It streams responses in real time, maintains per-project session logs in `~/.gideon/sessions/`, and caps file operations to the directory you launched it in.

Configuration lives in `~/.gideon/config.json` — your API key, model, and context length. Update it in-app via `/config`.

## Project structure

```
src/gideon/          # package source
  main.py            # entry point
  loop.py            # the interactive chat loop
  display.py         # streaming output, panels, context bar, diff display
  tools/             # tools the agent can use (read, write, edit, bash, grep, etc.)
  tools_config.py    # tool schemas + destructive tool list
  commands/          # slash commands (/config, etc.)
  system_prompt.py   # the prompt that shapes the agent
  config.py          # config management (~/.gideon/config.json)
  session_manager.py # session persistence and metadata
  openrouter.py      # API client (streaming, model list, key validation)
  picker.py          # terminal selection UI
build.sh             # builds the standalone binary
install.sh           # the curl | sh installer (Linux/macOS)
install.ps1          # the irm | iex installer (Windows)
.github/workflows/   # CI — builds release archives on tag
```

## License

MIT