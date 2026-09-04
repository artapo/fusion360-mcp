# fusion360-mcp

Lets Claude Code drive Fusion 360: runs Python inside the live session with
the full API available — build geometry, read dimensions, walk the timeline.

*[Leia em português](README.pt-BR.md)*

```python
result = snapshot()
# doc: bearing.f3d  [mm]  sketches:7  timeline:16
# bodies: 11
#   outer_ring_flanged       173.978 mm3  17x17x4.6  faces:10
#   ball x7                    2.572 mm3  1.7x1.7x1.7  faces:1
```

## Install

```bash
uvx fusion360-mcp install
```

Installs all three pieces: the add-in inside Fusion, the `fusion360-api`
skill in `~/.claude/skills/`, and the MCP entry in Claude Code.

Then in Fusion: **Utilities → ADD-INS → Add-Ins**, select "Claude MCP" and
press **Run**. Tick *Run on Startup* to skip this next time. The add-in has
to be running for the bridge to answer.

```bash
uvx fusion360-mcp status      # what is installed where
uvx fusion360-mcp uninstall   # take it back out
```

Close Fusion before installing — it holds the add-in files open. The
installer detects this and tells you rather than corrupting the copy.

## Requirements

- Fusion 360 (Windows or macOS)
- Claude Code
- Python 3.9+

No runtime dependencies: the MCP server speaks JSON-RPC using only the
standard library.

## How it works

Fusion only accepts API calls on its main thread. The add-in runs an HTTP
server on a background thread and hands each request to the main thread via
a `CustomEvent`; the HTTP thread blocks until the result comes back.

```
Claude Code  --stdio-->  server.py  --HTTP:8766-->  add-in  -->  Fusion
```

Requests carry a bearer token from `~/.claude-fusion-secret`, created on
first run. Without it any local process could execute Python in your Fusion
session.

## The tool

`fusion_eval` takes Python source and returns whatever you assign to
`result`. `adsk`, `app`, `ui`, `design` and `root` are pre-bound, plus three
helpers:

| | |
|---|---|
| `snapshot()` | Model state as compact text. Identical bodies collapse into one line, so a 50-instance pattern costs the same as one body. |
| `screenshot(w, h, view)` | Renders the viewport and returns the image inline. Expensive (~10k tokens) — prefer `snapshot()` when numbers are what matter. |
| `undo()` | Reverts the last call that changed the model. One level. A call that raises is rolled back automatically. |

## The skill

The package also installs the `fusion360-api` skill, which documents the
API's traps — internal units in cm and radians, signatures that vary per
feature, material names that follow the UI language. Every section came from
a real mistake.

It asks for contributions: if you hit a trap that isn't there, document it.
The file is `src/fusion360_mcp/skill/SKILL.md` and the rules are at the top.

## Contributing

Pull requests welcome. One PR per finding, with the `fusion_eval` output
that proves the behaviour — the call that failed and the one that worked.

```bash
git clone https://github.com/artapo/fusion360-mcp
cd fusion360-mcp
python test_mcp_server.py    # passes whether Fusion is open or closed
```

## License

[Apache 2.0](LICENSE) — as permissive as MIT, plus an explicit patent grant
that protects both users and contributors.

Fusion 360 is a trademark of Autodesk, Inc. This project is not affiliated
with or endorsed by Autodesk.
