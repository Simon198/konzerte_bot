#!/usr/bin/env bash
#
# konzerte_bot — initial setup
#
# Prepares a systemd-based Linux machine to run the Konzerte Bot.
# Run as root:
#
#     sudo ./setup/setup.sh
#
# ── Prerequisites ──────────────────────────────────────────────────────────
# 1. Clone the repository to /opt/konzerte_bot as YOUR OWN user (so the
#    checkout is owned by you). The commands are in ./setup/clone.sh.
#
#    Git operations (submodule init here, `git pull` in deploy.sh) run as
#    your user with your forwarded SSH agent. Forward the agent with `ssh -A`
#    and make sure SSH_AUTH_SOCK reaches this script (run sudo with `-E`, or
#    add `Defaults env_keep += "SSH_AUTH_SOCK SSH_AGENT_PID"` to sudoers).
#
# 2. python3 with the `venv` module (e.g. `sudo apt install python3-venv`).
#
# ── Secrets ────────────────────────────────────────────────────────────────
# The `.env` is NOT part of the repository. This script writes it to
# /etc/konzerte_bot/.env with mode 600 (readable by root only). The systemd
# service injects the variables via `EnvironmentFile`, so the secrets never
# live in the repo, in shell history, or in this script.
#
# You can supply the values non-interactively, highest precedence first:
#   * export them and preserve the environment:
#         sudo -E TOKEN=... ADMIN_TOKEN=... ADMIN_CHAT_ID=... ./setup/setup.sh
#   * pass a KEY=VALUE file:
#         sudo ./setup/setup.sh --env-file /path/to/env
#   * otherwise this script prompts for each value (tokens are hidden).

set -euo pipefail

# ── Configuration (keep in sync with the systemd unit below) ──────────────
APP_DIR="/opt/konzerte_bot"
VENV_DIR="$APP_DIR/.venv"
SERVICE_NAME="konzerte_bot"
SCRAPER_SERVICE_NAME="konzerte_bot_scraper"
REMINDER_SERVICE_NAME="konzerte_bot_reminder"
UPGRADE_SERVICE_NAME="konzerte_bot-upgrade"
SERVICE_USER="konzertebot"
CONFIG_DIR="/etc/konzerte_bot"
ENV_FILE="$CONFIG_DIR/.env"
CONFIG_FILE="$CONFIG_DIR/config.ini"
DB_DIR="/var/lib/konzerte_bot"
LOG_DIR="/var/log/konzerte_bot"
UNIT_FILE="/etc/systemd/system/$SERVICE_NAME.service"
SCRAPER_UNIT_FILE="/etc/systemd/system/$SCRAPER_SERVICE_NAME.service"
REMINDER_UNIT_FILE="/etc/systemd/system/$REMINDER_SERVICE_NAME.service"
NIGHT_SYNC_SCRIPT="/usr/local/bin/konzerte_bot-night-sync"
NIGHT_SYNC_SERVICE="konzerte_bot-night-sync.service"
NIGHT_SYNC_TIMER="konzerte_bot-night-sync.timer"
DB_FILE="$DB_DIR/concerts.db"
DB_URL="sqlite:///$DB_FILE"
IMAGES_DIR="$DB_DIR/images/bands"
GIT_USER="${GIT_USER:-${SUDO_USER:-root}}"

# ── Helpers ────────────────────────────────────────────────────────────────
say()  { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }
warn() { printf '\n\033[1;33mWARNING: %s\033[0m\n' "$*"; }
die()  { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

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

if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root. Try: sudo ./setup/setup.sh"
fi
command -v systemctl >/dev/null 2>&1 \
    || die "systemctl not found; this script requires a systemd-based distribution."
command -v python3 >/dev/null 2>&1 \
    || die "python3 not found; install it first."

# ── Optional --env-file argument ──────────────────────────────────────────
ENV_FILE_SRC=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file)
            ENV_FILE_SRC="${2:-}"
            shift 2
            ;;
        *)
            die "Unknown argument: $1"
            ;;
    esac
done

# ── Repository check ──────────────────────────────────────────────────────
[[ -d "$APP_DIR/.git" ]] || die \
    "No git repository found at $APP_DIR. Clone it first: sudo ./setup/clone.sh"
[[ -f "$APP_DIR/requirements.txt" ]] || die "requirements.txt not found in $APP_DIR."

say "Initializing git submodules"
# The checkout may be owned by a different user (e.g. root when cloned via
# `sudo git clone`), which trips git's "dubious ownership" check when the
# submodule update runs as $GIT_USER. Mark the repository safe for that user.
run_as "$GIT_USER" git config --global --add safe.directory "$APP_DIR"
if ! run_as "$GIT_USER" git -C "$APP_DIR" submodule update --init --recursive; then
    warn "Could not initialize submodules. Run this manually as your user with your SSH agent:
  cd $APP_DIR && git submodule update --init --recursive"
fi

# ── System user ───────────────────────────────────────────────────────────
if id "$SERVICE_USER" >/dev/null 2>&1; then
    say "System user '$SERVICE_USER' already exists"
else
    say "Creating system user '$SERVICE_USER'"
    useradd --system --no-create-home --shell /usr/sbin/nologin "$SERVICE_USER"
fi

# ── Runtime directories (owned by the service user) ──────────────────────
say "Creating runtime directories"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "$DB_DIR"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "$IMAGES_DIR"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "$LOG_DIR"
install -d -m 0755 "$CONFIG_DIR"

# ── Virtualenv + dependencies ─────────────────────────────────────────────
say "Creating virtual environment"
# Re-create the venv if it is missing or incomplete. A venv created without
# ensurepip (python3-venv not installed) can contain `python` but no `pip`.
if [[ ! -x "$VENV_DIR/bin/python" || ! -x "$VENV_DIR/bin/pip" ]]; then
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" \
        || die "Failed to create the virtualenv. Install python3-venv (e.g. 'apt install python3-venv')."
fi
if [[ ! -x "$VENV_DIR/bin/pip" ]]; then
    die "pip is missing from $VENV_DIR. Install python3-venv (ensurepip) and re-run."
fi
"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

run_migrations

# ── Logging config ────────────────────────────────────────────────────────
# Mirrors config.ini.example; the application reads "log_folder".
say "Writing logging config to $CONFIG_FILE"
cat > "$CONFIG_FILE" <<'EOF'
[logging]
# Directory where the rotating log files are written.
log_folder = /var/log/konzerte_bot
log_level = INFO
EOF
chmod 0644 "$CONFIG_FILE"

# ── Secured .env ──────────────────────────────────────────────────────────
TOKEN="${TOKEN:-}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"
ADMIN_CHAT_ID="${ADMIN_CHAT_ID:-}"

# Parse a KEY=VALUE file without evaluating it as shell (so values such as
# "123;456" are kept verbatim and can never execute commands).
read_env_file() {
    local file="$1" line key value
    [[ -r "$file" ]] || die "Cannot read env file: $file"
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        [[ "$line" == *=* ]] || continue
        key="${line%%=*}"
        value="${line#*=}"
        case "$key" in
            TOKEN)          TOKEN="$value" ;;
            ADMIN_TOKEN)    ADMIN_TOKEN="$value" ;;
            ADMIN_CHAT_ID)  ADMIN_CHAT_ID="$value" ;;
        esac
    done < "$file"
}

if [[ -f "$ENV_FILE" ]]; then
    say "$ENV_FILE already exists — leaving it unchanged (remove it to re-run the prompts)."
else
    if [[ -n "$ENV_FILE_SRC" ]]; then
        read_env_file "$ENV_FILE_SRC"
    fi

    if [[ -z "$TOKEN" ]]; then
        IFS= read -r -s -p "TOKEN (Telegram bot token): " TOKEN; echo
    fi
    if [[ -z "$ADMIN_TOKEN" ]]; then
        IFS= read -r -s -p "ADMIN_TOKEN (admin bot token): " ADMIN_TOKEN; echo
    fi
    if [[ -z "$ADMIN_CHAT_ID" ]]; then
        IFS= read -r -p "ADMIN_CHAT_ID (admin chat id, ';' separated if multiple): " ADMIN_CHAT_ID
    fi

    [[ -n "$TOKEN" ]] || die "TOKEN is required."
    [[ -n "$ADMIN_TOKEN" ]] || die "ADMIN_TOKEN is required."
    [[ -n "$ADMIN_CHAT_ID" ]] || die "ADMIN_CHAT_ID is required."

    # Light sanity checks (warnings only).
    [[ "$TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]] || warn "TOKEN does not look like a Telegram bot token."
    [[ "$ADMIN_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]] || warn "ADMIN_TOKEN does not look like a Telegram bot token."

    say "Writing $ENV_FILE (mode 600, root only)"
    umask 077
    {
        printf 'TOKEN=%s\n' "$TOKEN"
        printf 'ADMIN_TOKEN=%s\n' "$ADMIN_TOKEN"
        printf 'ADMIN_CHAT_ID=%s\n' "$ADMIN_CHAT_ID"
    } > "$ENV_FILE"
    chown root:root "$ENV_FILE"
    chmod 600 "$ENV_FILE"
fi

# ── systemd units ─────────────────────────────────────────────────────────
say "Installing systemd service $SERVICE_NAME.service"
cat > "$UNIT_FILE" <<EOF
[Unit]
Description=Konzerte Bot (Telegram)
Wants=network-online.target
After=network-online.target
# Restart no matter how often the bot fails. systemd otherwise gives up after
# its default start-rate limit (5 starts within 10 seconds).
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=KONZERTE_BOT_DATABASE_URL=$DB_URL
Environment=KONZERTE_BOT_IMAGES_DIR=$IMAGES_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$VENV_DIR/bin/python main.py
# Restart automatically whenever the bot exits or crashes.
Restart=always
RestartSec=5
TimeoutStopSec=20

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DB_DIR $LOG_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
UMask=0077

[Install]
WantedBy=multi-user.target
EOF
chmod 0644 "$UNIT_FILE"

# The two scheduled jobs (daily event scraping, daily reminders) run as their
# own one-shot services triggered by systemd timers, instead of an in-process
# Python cron loop. A crash in one job therefore cannot take down the bot or the
# other job, and every run is tracked individually by systemd.
#
# NOTE: systemd timers fire in the system's local timezone. For the 17:00
# scraping and 09:00 reminder times to be Europe/Berlin, ensure the host is set
# to that timezone (e.g. `timedatectl set-timezone Europe/Berlin`).
say "Installing systemd service $SCRAPER_SERVICE_NAME.service + timer"
cat > "$SCRAPER_UNIT_FILE" <<EOF
[Unit]
Description=Konzerte Bot event scraper (daily web scraping)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=KONZERTE_BOT_DATABASE_URL=$DB_URL
Environment=KONZERTE_BOT_IMAGES_DIR=$IMAGES_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$VENV_DIR/bin/python scrape_events.py

# Security hardening (same as the bot)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DB_DIR $LOG_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
UMask=0077
EOF
chmod 0644 "$SCRAPER_UNIT_FILE"

cat > "/etc/systemd/system/$SCRAPER_SERVICE_NAME.timer" <<EOF
[Unit]
Description=Run the Konzerte Bot event scraper daily at 17:00

[Timer]
OnCalendar=*-*-* 17:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
chmod 0644 "/etc/systemd/system/$SCRAPER_SERVICE_NAME.timer"

say "Installing systemd service $REMINDER_SERVICE_NAME.service + timer"
cat > "$REMINDER_UNIT_FILE" <<EOF
[Unit]
Description=Konzerte Bot daily reminder
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=KONZERTE_BOT_DATABASE_URL=$DB_URL
Environment=KONZERTE_BOT_IMAGES_DIR=$IMAGES_DIR
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$VENV_DIR/bin/python send_reminders.py

# Security hardening (same as the bot)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DB_DIR $LOG_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
UMask=0077
EOF
chmod 0644 "$REMINDER_UNIT_FILE"

cat > "/etc/systemd/system/$REMINDER_SERVICE_NAME.timer" <<EOF
[Unit]
Description=Run the Konzerte Bot daily reminder at 09:00

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
chmod 0644 "/etc/systemd/system/$REMINDER_SERVICE_NAME.timer"

# ── Night window: stop the bot between 01:00 and 05:00 ─────────────────────
# A timer fires at 01:00 and 05:00 (and on boot if a trigger was missed while
# the machine was off) and runs a helper that starts/stops the bot based on the
# current hour.
say "Installing night-window helper and timer (bot off 01:00-05:00)"
cat > "$NIGHT_SYNC_SCRIPT" <<'EOF'
#!/usr/bin/env bash
#
# konzerte_bot — night sync
#
# Stops the Konzerte Bot between 01:00 and 05:00 and starts it outside that
# window. Triggered by konzerte_bot-night-sync.timer at 01:00 and 05:00 (and on
# boot when a trigger was missed while the machine was off).

set -euo pipefail

SERVICE_NAME="konzerte_bot"
hour="$(date +%H)"

# Force base-10 so "08"/"09" are not parsed as invalid octal.
if (( 10#$hour >= 1 && 10#$hour < 5 )); then
    systemctl stop "$SERVICE_NAME.service" || true
else
    systemctl start "$SERVICE_NAME.service" || true
fi
EOF
chmod 0755 "$NIGHT_SYNC_SCRIPT"

cat > "/etc/systemd/system/$NIGHT_SYNC_SERVICE" <<EOF
[Unit]
Description=Stop/start the Konzerte Bot according to the night window (01:00-05:00)

[Service]
Type=oneshot
ExecStart=$NIGHT_SYNC_SCRIPT
EOF
chmod 0644 "/etc/systemd/system/$NIGHT_SYNC_SERVICE"

cat > "/etc/systemd/system/$NIGHT_SYNC_TIMER" <<EOF
[Unit]
Description=Trigger the Konzerte Bot night sync daily at 01:00 and 05:00

[Timer]
OnCalendar=*-*-* 01:00:00
OnCalendar=*-*-* 05:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
chmod 0644 "/etc/systemd/system/$NIGHT_SYNC_TIMER"

# ── Automatic dependency upgrade (nightly at 03:00) ────────────────────────
# Runs inside the night window. It pulls the newest main, upgrades only the
# packages with known vulnerabilities (pip-audit), records the fixes in
# requirements.txt, runs the full test suite, and keeps the new versions only if
# every test passes (otherwise it rolls back). On success it commits and pushes
# the requirements.txt update. The bot is left stopped for the 05:00 night-sync.
say "Installing automatic dependency-upgrade service + timer (daily at 03:00)"
cat > "/etc/systemd/system/$UPGRADE_SERVICE_NAME.service" <<EOF
[Unit]
Description=Konzerte Bot automatic dependency upgrade (vulnerability fixes)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
Environment=KONZERTE_BOT_GIT_USER=$GIT_USER
Environment=KONZERTE_BOT_DATABASE_URL=sqlite:///:memory:
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$VENV_DIR/bin/python upgrade_dependencies.py
EOF
chmod 0644 "/etc/systemd/system/$UPGRADE_SERVICE_NAME.service"

cat > "/etc/systemd/system/$UPGRADE_SERVICE_NAME.timer" <<EOF
[Unit]
Description=Run the Konzerte Bot dependency upgrade daily at 03:00

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
chmod 0644 "/etc/systemd/system/$UPGRADE_SERVICE_NAME.timer"

# ── Remove the obsolete scheduler service ──────────────────────────────────
# Older versions ran the daily jobs in an in-process `scheduler.py` service.
# That is now replaced by the systemd timers above, so remove the old unit.
if [[ -f "/etc/systemd/system/konzerte_bot_scheduler.service" ]]; then
    say "Removing obsolete konzerte_bot_scheduler.service (replaced by systemd timers)"
    systemctl disable --now konzerte_bot_scheduler.service 2>/dev/null || true
    rm -f /etc/systemd/system/konzerte_bot_scheduler.service
fi

# ── Enable & start ────────────────────────────────────────────────────────
say "Reloading systemd, enabling and starting the services"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME.service"
systemctl enable "$SCRAPER_SERVICE_NAME.timer"
systemctl enable "$REMINDER_SERVICE_NAME.timer"
systemctl enable "$NIGHT_SYNC_TIMER"
systemctl enable "$UPGRADE_SERVICE_NAME.timer"
systemctl restart "$SERVICE_NAME.service"
systemctl start "$SCRAPER_SERVICE_NAME.timer"
systemctl start "$REMINDER_SERVICE_NAME.timer"
systemctl start "$NIGHT_SYNC_TIMER"
systemctl start "$UPGRADE_SERVICE_NAME.timer"

# Apply the night window immediately (e.g. when setup runs between 01:00-05:00).
"$NIGHT_SYNC_SCRIPT" || true

# Populate events right away instead of waiting for the next 17:00 run.
systemctl start --no-block "$SCRAPER_SERVICE_NAME.service" || true

say "Setup complete"
systemctl --no-pager --lines=0 status "$SERVICE_NAME.service" || true
systemctl --no-pager list-timers --all 'konzerte_bot*' || true

cat <<'MSG'

Useful commands:
  sudo systemctl status konzerte_bot
  sudo systemctl list-timers 'konzerte_bot*'     # show the scheduled jobs
  sudo bash setup/scheduler.sh                   # show timers / run the scraper
  sudo journalctl -u konzerte_bot -f
  tail -f /var/log/konzerte_bot/application.log
MSG
