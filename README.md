# fusion360-mcp

Lets Claude Code drive Fusion 360: runs Python inside the live session with
the full API available — build geometry, read dimensions, walk the timeline.

*[Leia em português](README.pt-BR.md)*
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/artapo)

```python
result = snapshot()
# doc: bearing.f3d  [mm]  sketches:7  timeline:16
# bodies: 11
#   outer_ring_flanged       173.978 mm3  17x17x4.6  faces:10
#   ball x7                    2.572 mm3  1.7x1.7x1.7  faces:1
```

## What's new

Newest first. To update, close Fusion and run
`uvx fusion360-mcp@latest install`: it replaces the add-in and the skill.

### 0.1.3 (2026-11-18)

- **October 2026 Fusion API (2706).** The skill now covers what changed:
  retired, removed and renamed members with their replacements, sheet metal
  rules and overrides, configuration rules, the new drawing `View` members,
  and creating a drawing from code. The sheet metal and drawing notes were
  checked against a live Fusion 2706.
- The API index was regenerated from Autodesk's docs (1981 classes and enums,
  up from 1832), and the official Sheet Metal and Configuration Rules guides
  were added to the bundled references.
- `snapshot()` lists mesh bodies, with size, triangle count and hidden
  state. An imported STL used to be invisible to it.
- Skill: which component a sheet metal flange lands in ([#14](https://github.com/artapo/fusion360-mcp/pull/14)), and how
  `addExistingComponent` combines its matrix with the first occurrence ([#15](https://github.com/artapo/fusion360-mcp/pull/15)).

### 0.1.2 (2026-11-08)

- Rollback acts on the document the call changed, works with the timeline
  marker in the middle, and no longer breaks when a call closes the document
  it started in.
- Skill: drawing API traps, plus four notes contributed by
  [ArnaudUnreal](https://github.com/ArnaudUnreal): extrude direction on each
  origin plane, dimensions from the origin point, making a feature count
  follow a parameter, and a missing proxy that shows up as "Invalid entity".

### 0.1.1 (2026-09-04)

- Fixed rollback and undo, including rollback on an empty document.
- New `api()` helper, which lists an object's methods and signatures.
- Skill: sketch plane orientation, `participantBodies`, accented names, and
  appearances.

### 0.1.0 (2026-09-04)

- First release: the MCP server, the Fusion add-in, `snapshot()`,
  `screenshot()`, `undo()` with automatic rollback, the `fusion360-api`
  skill, and the `uvx` installer.

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

- Fusion 360 (Windows or macOS), version **2704.1.36 or newer** — that is the
  oldest build this was verified on. Older ones are untested, not known to be
  broken. The API changes between versions: `TimelineObject.deleteObject`, for
  instance, is missing before ~2705, so the bridge falls back to
  `entity.deleteMe()` for undo and rollback. Check yours with
  `result = app.version`.
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
`result`. `adsk`, `app`, `ui`, `design` and `root` are pre-bound, plus four
helpers:

| | |
|---|---|
| `snapshot()` | Model state as compact text. Identical bodies collapse into one line, so a 50-instance pattern costs the same as one body. |
| `screenshot(w, h, view)` | Renders the viewport and returns the image inline. Expensive (~10k tokens) — prefer `snapshot()` when numbers are what matter. |
| `undo()` | Reverts the last call that changed the model. One level. A call that raises is rolled back automatically. |
| `api(obj, grep)` | Lists an object's methods, signatures and properties, optionally filtered. Cheaper than guessing a signature and reading the error. |

## The skill

The package also installs the `fusion360-api` skill, which documents the
API's traps — internal units in cm and radians, signatures that vary per
feature, material names that follow the UI language. Every section came from
a real mistake.

The skill is the part that compounds. Code gets written once; the traps keep
being discovered, and each one someone writes down is a trap nobody after
them loses an hour to.

## Found a trap? Send it back

**If the API surprised you, that's worth a PR.** A method whose real name
differs from the obvious one, a signature that changes per feature, an
operation that fails silently, a value that only works in one unit — that is
exactly what belongs in the skill, and it's the kind of thing no
documentation lists because it only shows up in practice.

The bar is low on purpose. You don't need to fix anything or write well:

- **Two calls are enough** — the one that failed and the one that worked.
  Paste the real `fusion_eval` output, including the error message; that's
  what someone will search for when they hit the same wall.
- **Say what you were building.** Context separates a general trap from a
  one-off accident, and it's usually the difference between a note that
  helps and one that confuses.
- **One PR per finding.** Unrelated findings on separate branches review
  faster and don't block each other.
- **Corrections beat additions.** If something in the skill is wrong or went
  stale, saying so is more valuable than a new section — a skill that
  describes the tool wrongly is worse than an incomplete one. Put it in the
  title and it gets reviewed first.

The file is `src/fusion360_mcp/skill/SKILL.md`; the full rules are at the
top of it. It's written in English so contributors anywhere can maintain it.

Not sure it's worth reporting? Open the PR anyway. Deciding is the
maintainer's job, and an unreported trap costs the next person the same hour
it cost you.

## Contributing code

```bash
git clone https://github.com/artapo/fusion360-mcp
cd fusion360-mcp
python test_mcp_server.py    # passes whether Fusion is open or closed
```

The test runs without Fusion installed — it accepts either a live answer or
"Cannot reach Fusion". CI runs it on Linux, macOS and Windows.

## License

[Apache 2.0](LICENSE) — as permissive as MIT, plus an explicit patent grant
that protects both users and contributors.

Fusion 360 is a trademark of Autodesk, Inc. This project is not affiliated
with or endorsed by Autodesk.
