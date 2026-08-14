# Gideon

A coding agent that lives in your terminal. Point it at a project and it'll read files, search your codebase, run commands, and make edits, checking with you first before doing anything permanent.

> Demo video coming soon.

## Install

**Linux / macOS**

```bash
curl -fsSL https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.sh | sh
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/GabrielOlufemi/gideon/master/install.ps1 | iex
```

That's it. Gideon is bundled as a standalone binary — no Python, no dependencies. Supports Linux, macOS (Intel + Apple Silicon), and Windows.

<details>
<summary>Build from source</summary>

```bash
git clone https://github.com/GabrielOlufemi/gideon.git
cd gideon
python -m venv .venv && source .venv/bin/activate
pip install -e .
gideon
```

To build the standalone binary yourself:

```bash
./build.sh
```

</details>

## Quick start

1. Run `gideon` in any project directory
2. Enter your OpenRouter API key, it walks you through this on first run
3. Pick a model [I recommend Deepseek V4 flash]

Then just talk to it. It knows what's in your project and can act on it.

## Features

- **Terminal-native chat** — streaming responses rendered with Markdown, right in your terminal
- **Autonomous tool use** — reads files, searches code, runs commands, edits and writes files on your behalf
- **Permission gating** — destructive actions (writes, edits, shell commands) always ask first; you can allow once or always
- **Session persistence** — every conversation is saved per project; resume, restore, or delete anytime
- **Multi-model** — pick from recommended models or browse everything on OpenRouter

## Commands

| Command | What it does |
|---|---|
| `/commands` | View all commands |
| `/config` | Change model, update API key, view config |
| `/sessions` | List sessions for this project |
| `/restore <n>` | Restore a previous session |
| `/delete <n>` | Delete a session |
| `quit` / `exit` / `leave` | End the session |

## How it works

Gideon talks to models through [OpenRouter](https://openrouter.ai), using function calling to operate on your codebase. It streams responses in real time, maintains a per-project session log in `~/.gideon/`, and caps file operations to the directory you launched it in.

Configuration lives in `~/.gideon/config.json` — your API key, model, and context length. You can update it in-app via `/config`.

## Project structure

```
src/gideon/          # package source
  main.py            # entry point
  loop.py            # the interactive chat loop
  tools/             # the tools the agent can use
  tools_config.py    # tool schemas + destructive tool list
  commands/          # slash commands (/config, etc.)
  system_prompt.py   # the prompt that shapes the agent
build.sh             # builds the standalone binary
install.sh           # the curl | sh installer (Linux/macOS)
install.ps1          # the irm | iex installer (Windows)
.github/workflows/   # CI — builds release binaries on tag
```

## License

MIT
