#!/usr/bin/env python3
"""konzerte_bot — automatic dependency upgrade (vulnerability fixes).

Runs nightly inside the bot's downtime window, scheduled by the
``konzerte_bot-upgrade.timer`` at 03:00 (the unit is defined in
``setup/setup.sh``). It:

  1. pulls the newest version of ``main`` (notifying the admin bot on failure),
  2. audits the virtualenv with ``pip-audit`` and upgrades only the packages
     with known vulnerabilities,
  3. records the fixed versions in ``requirements.txt``,
  4. runs the full test suite and keeps the new versions only if every test
     passes (otherwise it rolls the environment and ``requirements.txt`` back),
  5. commits and pushes any ``requirements.txt`` changes.

The bot is intentionally left stopped; ``konzerte_bot-night-sync.timer`` starts
it again at 05:00, with either the upgraded or the rolled-back versions.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# The script lives in the repository root, so that is the application directory.
APP_DIR = Path(__file__).resolve().parent
GIT_USER = os.environ.get("KONZERTE_BOT_GIT_USER", "root")
STATE_DIR = Path(os.environ.get("KONZERTE_BOT_STATE_DIR", "/var/lib/konzerte_bot/upgrade"))

REQUIREMENTS_REL = "requirements.txt"
REQUIREMENTS_FILE = APP_DIR / REQUIREMENTS_REL
DEV_REQUIREMENTS_FILE = APP_DIR / "requirements-dev.txt"

SNAPSHOT_FILE = STATE_DIR / "last-known-good.txt"
AUDIT_JSON = STATE_DIR / "audit.json"
FIX_JSON = STATE_DIR / "fix.json"

# ``pip-audit`` is installed as a console script next to the venv interpreter.
PIP_AUDIT = os.path.join(os.path.dirname(sys.executable), "pip-audit")


def log(message: str) -> None:
    """Write a line to the journal (stdout is captured by systemd)."""
    print(message, flush=True)


def notify_admin(level: int, message: str) -> None:
    """Send a message to the admin bot, reusing the handler from ``logger.py``.

    Importing ``logger`` registers the Telegram + file log handlers on the root
    logger, exactly as the application does, so the message reaches the admin
    bot with the same level emoji and notification behaviour.
    """
    try:
        import logger  # noqa: F401  (registers the Telegram + file handlers)
    except Exception:  # pragma: no cover - only if the app itself is broken
        pass
    logging.getLogger("konzerte_bot.upgrade").log(level, message)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    log(f"+ {shlex.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def run_git(*args: str) -> subprocess.CompletedProcess:
    """Run ``git`` in ``APP_DIR`` as ``GIT_USER``, forwarding the SSH agent.

    Mirrors the ``run_as`` helper in ``setup.sh``: when running as root the git
    command is executed via ``runuser`` as the repository owner, and the
    invoking user's SSH agent socket is passed through when present. When the
    agent is absent (e.g. triggered by the systemd timer), ssh falls back to the
    repository owner's default key.
    """
    prefix: list[str] = []
    # ``os.geteuid`` only exists on Unix; on other platforms (e.g. a Windows
    # dev box) fall back to running git directly.
    if hasattr(os, "geteuid") and os.geteuid() == 0 and GIT_USER not in ("", "root"):
        prefix = ["runuser", "-u", GIT_USER, "--"]
    if os.environ.get("SSH_AUTH_SOCK"):
        prefix += ["env", f"SSH_AUTH_SOCK={os.environ['SSH_AUTH_SOCK']}"]
    return run([*prefix, "git", "-C", str(APP_DIR), *args])


def run_pip_audit(extra: list[str], output: Path) -> subprocess.CompletedProcess:
    return run(
        [
            PIP_AUDIT,
            "--format", "json",
            "--progress-spinner", "off",
            "--output", str(output),
            *extra,
        ]
    )


def _canonical(name: str) -> str:
    """Normalise a package name so ``requests`` == ``Requests`` == ``requests-...``."""
    return re.sub(r"[-_.]+", "-", name).lower()


def bump_requirements(fixes: list[dict]) -> list[tuple[str, str]]:
    """Record pip-audit's fixes in ``requirements.txt``.

    Direct dependencies have their ``>=`` floor raised to the fixed version;
    transitive dependencies that pip-audit fixed are appended as new ``>=`` pins
    so the fix is reproducible on a fresh install. Returns ``(name, version)``
    for every recorded change.
    """
    lines = REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
    changed: list[tuple[str, str]] = []
    for fix in fixes:
        new_version = fix.get("new_version")
        if not new_version:
            continue  # skipped by pip-audit (no fix could be resolved)
        name = fix["name"]
        target = _canonical(name)
        matched = False
        for i, line in enumerate(lines):
            m = re.match(
                r"^\s*([A-Za-z0-9][A-Za-z0-9_.-]*)\s*(>=|==|~=|>|<=)\s*([^ \t;#]+)",
                line,
            )
            if m and _canonical(m.group(1)) == target:
                lines[i] = f"{m.group(1)}>={new_version}"
                matched = True
                break
        if not matched:
            lines.append(f"{name}>={new_version}")
        changed.append((name, new_version))
    REQUIREMENTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def _commit_and_push(changed: list[tuple[str, str]]) -> bool:
    """Stage, commit and push the ``requirements.txt`` update. True on success."""
    summary = ", ".join(name for name, _ in changed)

    if run_git("add", REQUIREMENTS_REL).returncode != 0:
        notify_admin(logging.ERROR, "konzerte_bot upgrade: `git add requirements.txt` failed")
        return False

    # Nothing staged (e.g. the floor was already satisfied) — nothing to push.
    if run_git("diff", "--cached", "--quiet", "--", REQUIREMENTS_REL).returncode == 0:
        return True

    committed = run_git("commit", "-m", f"chore(deps): update vulnerable dependencies ({summary})")
    if committed.returncode != 0:
        notify_admin(
            logging.ERROR,
            f"konzerte_bot upgrade: git commit failed\n{committed.stderr.strip()}",
        )
        return False

    pushed = run_git("push")
    if pushed.returncode != 0:
        notify_admin(
            logging.ERROR,
            "konzerte_bot upgrade: git push failed (the change is committed locally)\n"
            f"{pushed.stderr.strip()}",
        )
        return False

    notify_admin(
        logging.INFO,
        f"konzerte_bot upgrade: upgraded {len(changed)} package(s) and pushed requirements.txt ({summary})",
    )
    return True


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log("konzerte_bot dependency upgrade starting")

    # ── 1. Pull the newest main ─────────────────────────────────────────────
    log("Pulling the newest version of main")
    # Discard any stale uncommitted edit to requirements.txt left by an
    # interrupted run, so the pull can fast-forward cleanly.
    run_git("checkout", "--", REQUIREMENTS_REL)
    pulled = run_git("pull", "--ff-only")
    if pulled.returncode != 0:
        notify_admin(
            logging.ERROR,
            f"konzerte_bot upgrade aborted: git pull failed\n{pulled.stderr.strip()}",
        )
        return 1

    # ── 2. Tooling ──────────────────────────────────────────────────────────
    log("Installing upgrade tooling (pip-audit + test dependencies)")
    if run([sys.executable, "-m", "pip", "install", "--quiet", "pip-audit"]).returncode != 0:
        notify_admin(logging.ERROR, "konzerte_bot upgrade aborted: could not install pip-audit")
        return 1
    if DEV_REQUIREMENTS_FILE.exists():
        run([sys.executable, "-m", "pip", "install", "--quiet", "-r", str(DEV_REQUIREMENTS_FILE)])

    # ── 3. Snapshot (rollback point) ────────────────────────────────────────
    log("Snapshotting current versions")
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as fh:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=fh, check=True)

    # ── 4. Audit ────────────────────────────────────────────────────────────
    log("Auditing the environment for known vulnerabilities")
    AUDIT_JSON.unlink(missing_ok=True)
    audited = run_pip_audit([], AUDIT_JSON)

    deps: list[dict] = []
    if AUDIT_JSON.exists():
        try:
            deps = json.loads(AUDIT_JSON.read_text(encoding="utf-8")).get("dependencies", [])
        except (json.JSONDecodeError, OSError):
            deps = []
    vulnerable = [d for d in deps if d.get("vulns")]
    fixable = [d for d in vulnerable if any(v.get("fix_versions") for v in d["vulns"])]

    # pip-audit exits 1 on both findings and fatal errors; a fatal error (e.g.
    # the vulnerability service is unreachable) produces no report at all.
    if audited.returncode != 0 and not vulnerable:
        notify_admin(
            logging.WARNING,
            f"konzerte_bot upgrade skipped: pip-audit failed\n{audited.stderr.strip()}",
        )
        return 0

    if not vulnerable:
        log("No known vulnerabilities — nothing to upgrade")
        return 0

    log(f"Found {len(vulnerable)} vulnerable package(s), {len(fixable)} with a published fix")
    if not fixable:
        names = ", ".join(d["name"] for d in vulnerable)
        notify_admin(
            logging.WARNING,
            f"konzerte_bot upgrade: {len(vulnerable)} vulnerable package(s) have no fix yet ({names})",
        )
        return 0

    # ── 5. Fix ──────────────────────────────────────────────────────────────
    log("Upgrading vulnerable packages to fixed versions")
    FIX_JSON.unlink(missing_ok=True)
    fixed = run_pip_audit(["--fix"], FIX_JSON)
    if fixed.returncode != 0:
        log("pip-audit reported that not every vulnerability could be fixed (continuing)")
        log(fixed.stderr.strip())

    fixes: list[dict] = []
    if FIX_JSON.exists():
        try:
            fixes = json.loads(FIX_JSON.read_text(encoding="utf-8")).get("fixes", [])
        except (json.JSONDecodeError, OSError):
            fixes = []

    changed = bump_requirements(fixes)
    if not changed:
        log("No packages were actually changed — nothing to test")
        return 0
    log("Changed packages:")
    for name, version in changed:
        log(f"  {name} -> {version}")

    # ── 6. Tests ────────────────────────────────────────────────────────────
    log("Running the full test suite")
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        KONZERTE_BOT_DATABASE_URL="sqlite:///:memory:",
    )
    tested = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"],
        cwd=str(APP_DIR),
        env=env,
    )

    # ── 7. Keep or roll back ────────────────────────────────────────────────
    if tested.returncode == 0:
        log("All tests passed — keeping the upgraded versions")
        if _commit_and_push(changed):
            return 0
        return 1

    summary = ", ".join(name for name, _ in changed)
    log("Tests FAILED — rolling back to the last known-good versions")
    notify_admin(
        logging.ERROR,
        f"konzerte_bot upgrade: tests failed, rolling back ({summary})",
    )
    if subprocess.run(
        [sys.executable, "-m", "pip", "install", "--quiet", "-r", str(SNAPSHOT_FILE)]
    ).returncode != 0:
        notify_admin(
            logging.ERROR,
            "konzerte_bot upgrade: ROLLBACK FAILED — restore manually from the snapshot",
        )
    run_git("checkout", "--", REQUIREMENTS_REL)
    return 1


if __name__ == "__main__":
    sys.exit(main())
