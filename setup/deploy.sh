#!/usr/bin/env bash
#
# konzerte_bot — deployment
#
# Stops the service, pulls the newest version of the repository (including
# submodules), installs/updates Python dependencies, and restarts the bot.
# Run as root:
#
#     sudo ./setup/deploy.sh
#
# Git operations run as the account set in GIT_USER (default: the user who
# invoked sudo, i.e. you), with your forwarded SSH agent. Forward the agent
# with `ssh -A` and make sure SSH_AUTH_SOCK reaches this script (run sudo
# with `-E`, or add `Defaults env_keep += "SSH_AUTH_SOCK SSH_AGENT_PID"` to
# sudoers). Override the user if needed:
#     sudo GIT_USER=yourname ./setup/deploy.sh

set -euo pipefail

# ── Configuration (keep in sync with setup.sh) ────────────────────────────
APP_DIR="/opt/konzerte_bot"
VENV_DIR="$APP_DIR/.venv"
SERVICE_NAME="konzerte_bot"
SERVICE_USER="konzertebot"
DB_DIR="/var/lib/konzerte_bot"
DB_FILE="$DB_DIR/concerts.db"
DB_URL="sqlite:///$DB_FILE"
GIT_USER="${GIT_USER:-${SUDO_USER:-root}}"

# ── Helpers ────────────────────────────────────────────────────────────────
say()  { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\n\033[1;33mWARNING: %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root. Try: sudo ./setup/deploy.sh"
fi
[[ -d "$APP_DIR/.git" ]] || die "No git repository found at $APP_DIR."
[[ -x "$VENV_DIR/bin/pip" ]] || die "No virtualenv found at $VENV_DIR. Run ./setup/setup.sh first."

# Run a command as another user, forwarding the SSH agent socket so git can
# use the invoking user's keys. Only rewrites the user when running as root.
run_as() {
    local user="$1"; shift
    if [[ "$(id -un)" == "root" && "$user" != "root" ]] && id "$user" >/dev/null 2>&1; then
        runuser -u "$user" -- env \
            SSH_AUTH_SOCK="${SSH_AUTH_SOCK:-}" \
            SSH_AGENT_PID="${SSH_AGENT_PID:-}" \
            "$@"
    else
        "$@"
    fi
}

# Apply Alembic migrations to the same database the application uses.
run_migrations() {
    say "Applying database migrations"
    (
        cd "$APP_DIR"
        export KONZERTE_BOT_DATABASE_URL="$DB_URL"
        if [[ ! -f "$DB_FILE" ]] || "$VENV_DIR/bin/alembic" current >/dev/null 2>&1; then
            "$VENV_DIR/bin/alembic" upgrade head
        else
            # Existing database without an alembic_version table (created by
            # SQLAlchemy's create_all before migrations were adopted): stamp it.
            warn "No Alembic version table found; stamping existing database as 'head'."
            "$VENV_DIR/bin/alembic" stamp head
        fi
    )
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DB_DIR"
}

# ── Stop ───────────────────────────────────────────────────────────────────
say "Stopping service $SERVICE_NAME"
systemctl stop "$SERVICE_NAME.service"

# ── Pull ───────────────────────────────────────────────────────────────────
say "Pulling latest code as '$GIT_USER'"
if ! run_as "$GIT_USER" git -C "$APP_DIR" pull --ff-only; then
    die "git pull failed — service left stopped. Resolve the issue, then run: sudo systemctl start $SERVICE_NAME"
fi

say "Updating submodules"
if ! run_as "$GIT_USER" git -C "$APP_DIR" submodule update --init --recursive; then
    die "Submodule update failed — service left stopped. Resolve the issue, then run: sudo systemctl start $SERVICE_NAME"
fi

# ── Dependencies ───────────────────────────────────────────────────────────
say "Installing/updating dependencies"
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

run_migrations

# ── Start ──────────────────────────────────────────────────────────────────
say "Starting service $SERVICE_NAME"
systemctl start "$SERVICE_NAME.service"

say "Deployment complete"
systemctl --no-pager --lines=0 status "$SERVICE_NAME.service" || true
