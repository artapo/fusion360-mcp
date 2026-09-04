"""Installer for the Fusion 360 MCP bridge.

Three things have to land in three different places, which is why this exists:
the add-in inside Fusion's AddIns folder, the skill in ~/.claude/skills, and
an entry in Claude Code's MCP config. Doing it by hand means absolute paths
typed correctly on every machine.

    uvx fusion360-mcp install     # everything
    uvx fusion360-mcp status      # what is installed where
    uvx fusion360-mcp uninstall   # take it back out
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).parent
ADDIN_NAME = 'Claude MCP'
SERVER_NAME = 'fusion360'


def addins_dir() -> Path:
    """Where Fusion looks for add-ins. Differs per OS; nothing else does."""
    if platform.system() == 'Windows':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming'))
        return base / 'Autodesk/Autodesk Fusion 360/API/AddIns'
    # macOS. Fusion is not shipped for Linux.
    return (Path.home() / 'Library/Application Support/Autodesk'
            / 'Autodesk Fusion 360/API/AddIns')


def skills_dir() -> Path:
    return Path.home() / '.claude/skills'


def _on_rm_error(func, path, _exc):
    """Windows refuses to delete read-only files; clear the bit and retry."""
    os.chmod(path, 0o700)
    func(path)


def _copy_tree(src: Path, dst: Path) -> None:
    """Replace dst with src. Overwrites in place rather than deleting first,
    so a reinstall works even when something holds a file open.
    """
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob('*'):
        target = dst / item.relative_to(src)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _fusion_running() -> bool:
    """Fusion holds its add-in files open; copying over them fails mid-write."""
    try:
        if platform.system() == 'Windows':
            out = subprocess.run(['tasklist'], capture_output=True, text=True,
                                 timeout=10).stdout
            return 'Fusion360.exe' in out
        out = subprocess.run(['pgrep', '-f', 'Autodesk Fusion360'],
                             capture_output=True, text=True, timeout=10).stdout
        return bool(out.strip())
    except (OSError, subprocess.SubprocessError):
        return False  # can't tell: let the copy try and report a real error


def install_addin(force: bool = False) -> str:
    target = addins_dir() / ADDIN_NAME
    if _fusion_running() and not force:
        return ('SKIPPED: Fusion 360 is running and holds these files open. '
                'Close Fusion and run again, or pass --force to try anyway.')
    src = PKG / 'addin'
    target.parent.mkdir(parents=True, exist_ok=True)
    for name in ('Claude MCP.py', 'Claude MCP.manifest', 'ScriptIcon.svg'):
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / name, target / name)
    return f'add-in  -> {target}'


def install_skill() -> str:
    target = skills_dir() / 'fusion360-api'
    _copy_tree(PKG / 'skill', target)
    return f'skill   -> {target}'


def install_mcp() -> str:
    """Register the server with Claude Code via its own CLI.

    Writing ~/.claude.json directly would mean parsing a file that holds every
    project's state -- the CLI owns that format, so let it.
    """
    server = PKG / 'server.py'
    claude = shutil.which('claude')
    if not claude:
        return ('SKIPPED: the `claude` CLI is not on PATH. Register manually:\n'
                f'    claude mcp add {SERVER_NAME} -- '
                f'"{sys.executable}" "{server}"')
    # --scope user, or it lands in the current project only and the bridge
    # silently stops existing the moment you cd somewhere else.
    proc = subprocess.run(
        [claude, 'mcp', 'add', '--scope', 'user', SERVER_NAME,
         '--', sys.executable, str(server)],
        capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout).strip()
        if 'already exists' in err.lower():
            return f'MCP     -> already registered as "{SERVER_NAME}" (kept)'
        return f'MCP     -> FAILED: {err}'
    return f'MCP     -> registered as "{SERVER_NAME}"'


def cmd_install(args) -> int:
    print('Installing Fusion 360 MCP bridge\n')
    for line in (install_addin(args.force), install_skill(), install_mcp()):
        print('  ' + line)
    print('\nNext: open Fusion 360 -> Utilities -> ADD-INS -> Add-Ins tab,')
    print('select "Claude MCP" and press Run. It must be running for the')
    print('bridge to answer. Tick "Run on Startup" to skip this next time.')
    return 0


def cmd_status(_args) -> int:
    addin = addins_dir() / ADDIN_NAME
    skill = skills_dir() / 'fusion360-api'
    print(f'  add-in  {"OK " if addin.exists() else "-- "} {addin}')
    print(f'  skill   {"OK " if skill.exists() else "-- "} {skill}')

    cfg = Path.home() / '.claude.json'
    registered = False
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding='utf-8'))
            registered = SERVER_NAME in data.get('mcpServers', {})
        except (json.JSONDecodeError, OSError):
            pass
    print(f'  MCP     {"OK " if registered else "-- "} server "{SERVER_NAME}"'
          f' in {cfg}')
    print(f'  Fusion  {"running" if _fusion_running() else "not running"}')
    return 0


def cmd_uninstall(_args) -> int:
    for path in (addins_dir() / ADDIN_NAME, skills_dir() / 'fusion360-api'):
        if path.exists():
            shutil.rmtree(path, onerror=_on_rm_error)
            print(f'  removed {path}')
    claude = shutil.which('claude')
    if claude:
        subprocess.run([claude, 'mcp', 'remove', '--scope', 'user', SERVER_NAME],
                       capture_output=True, text=True)
        print(f'  removed MCP server "{SERVER_NAME}"')
    print('\nThe token at ~/.claude-fusion-secret was left in place.')
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='fusion360-mcp', description=__doc__.split('\n')[0])
    sub = parser.add_subparsers(dest='cmd')

    p_inst = sub.add_parser('install', help='install add-in, skill and MCP entry')
    p_inst.add_argument('--force', action='store_true',
                        help='copy the add-in even while Fusion is running')
    p_inst.set_defaults(func=cmd_install)

    sub.add_parser('status', help='show what is installed').set_defaults(
        func=cmd_status)
    sub.add_parser('uninstall', help='remove add-in, skill and MCP entry'
                   ).set_defaults(func=cmd_uninstall)

    args = parser.parse_args(argv)
    if not getattr(args, 'func', None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
