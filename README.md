# konzerte_bot 🎶

A Telegram bot that keeps you up to date with concerts and events in and around
Frankfurt, Germany. It scrapes the event pages of several venues on a schedule,
stores them in a local SQLite database, and pushes personalised recommendations,
reminders and change notifications to subscribed users.

The bot is non-commercial and fully open source (MIT). All code lives in this
repository, including the privacy policy — see [Privacy & legal](#privacy--legal).

## Features

- **Concert recommendations** based on the venues you subscribe to (`/go`, `/next`)
- **Source filters** — pick which organisers/venues you want to hear from (`/sources`)
- **Genre filters** — exclude music genres you are not interested in (`/genres`)
- **Reminders** — daily reminder if a concert you marked as interesting is today
  or within the next week
- **Change notifications** — interested users are notified automatically when an
  event's date, venue, status, etc. changes
- **Band enrichment** — band images (as Telegram stickers), genres and a Deezer
  top-track link are looked up automatically via Deezer
- **Changelog** — new features are broadcast to all users (`/changelog`)
- **GDPR-friendly** — explicit consent flow, `/mydata` (data access), `/delete`
  (right to erasure) and a public privacy policy served via `/datenschutz`
- **Admin extras** — a separate admin bot receives logs, progress bars and user
  interest notifications; `/pairings` shows events multiple users are interested in

## Available commands

| Command       | Description |
|---------------|-------------|
| `/start`      | Register and give consent |
| `/sources`    | Choose which organisers/venues you want to receive events from |
| `/genres`     | Choose which music genres you do **not** want to receive |
| `/go [n]`     | Load the next `n` unobserved concerts (default: 1) |
| `/next [n]`   | Load the next `n` concerts you are interested in (default: 100) |
| `/changelog`  | Show the latest changelog entry |
| `/datenschutz`| Show the privacy policy |
| `/mydata`     | Show all data stored about you |
| `/delete`     | Permanently delete all your stored data |
| `/pairings`   | Show events multiple users are interested in (admins only) |

## Tech stack

- **Python 3** (3.10+)
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) — Telegram Bot API
- [SQLAlchemy](https://www.sqlalchemy.org/) 2.x + [Alembic](https://alembic.sqlalchemy.org/) — ORM and schema migrations
- [schedule](https://github.com/dbader/schedule) — scheduling (daily reminders, daily scraping)
- [requests](https://requests.readthedocs.io/) + [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — web scraping
- [deezer-python](https://github.com/browniebroke/deezer-python) — band image / genre / top-track lookup
- [Pillow](https://python-pillow.org/) — image resizing/conversion to WebP stickers
- [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) — testing

## Project structure

```
konzerte_bot/
├── main.py                     # Entry point: sets up commands, starts scheduler + polling
├── scheduler.py                # Background scheduler (reminders + daily scraping)
├── repository.py               # Database engine/session (SQLAlchemy)
├── telegram/                   # Telegram bot logic (commands, callbacks, polls, ...)
├── web_scraping/               # Scraping + persistence + Deezer enrichment
│   ├── load_and_persist.py     # Orchestrates scraping → DB → notifications
│   ├── deezer.py               # Band image/genre/audio lookup via Deezer
│   └── scrapers/               # Per-venue scrapers (git submodule)
├── models/                     # SQLAlchemy ORM models
├── alembic/                    # Alembic migrations
├── changelog/                  # Changelog entries broadcast to users
├── setup/                      # Deployment scripts (clone, setup, deploy)
└── tests/                      # Unit + integration tests
```

> **Note:** `web_scraping/scrapers` is a **git submodule**
> ([`konzerte_bot_scrapers`](https://github.com/Simon198/konzerte_bot_scrapers)).
> It must be initialised separately (see below).

## Getting started (local development)

### 1. Clone the repository including submodules

```bash
git clone --recurse-submodules https://github.com/Simon198/konzerte_bot.git
cd konzerte_bot
```

If you already cloned without submodules:

```bash
git submodule update --init --recursive
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for running the tests
```

### 3. Configure environment variables

Copy the example file and fill in your tokens:

```bash
cp env.example .env
```

| Variable | Description |
|----------|-------------|
| `TOKEN` | Telegram bot API token (from [@BotFather](https://t.me/BotFather)) |
| `ADMIN_TOKEN` | Token of a second bot used to message admins |
| `ADMIN_CHAT_ID` | Chat ID(s) that receive admin messages (`;`-separated for multiple) |

Optional overrides:

| Variable | Default | Description |
|----------|---------|-------------|
| `KONZERTE_BOT_DATABASE_URL` | `sqlite:///concerts.db` | Database URL (used by app and Alembic) |
| `KONZERTE_BOT_IMAGES_DIR` | `<project>/images/bands` | Where downloaded band images are stored |

### 4. Apply the database migrations

```bash
alembic upgrade head
```

The schema is managed **exclusively** by Alembic — do not call `create_all`.

### 5. (Optional) Configure logging

Copy `config.ini.example` to `config.ini` and adjust the `log_folder` /
`log_level` as needed.

### 6. Run the bot

```bash
python main.py
```

On startup the bot:

1. Registers the command list with Telegram (`setup_bot_commands`),
2. Broadcasts the newest changelog entry if there is one,
3. Starts the scheduler in a background thread (and kicks off an immediate
   scraping run so events are available right away),
4. Begins long-polling for messages.

## Running the tests

```bash
# Unit tests only (fast, no database/network)
pytest -m unit

# Integration tests (require database and/or network access)
pytest -m integration

# Everything, with coverage
pytest --cov
```

## Production deployment (systemd)

The repository ships ready-to-use scripts for a systemd-based Linux host.
They install the bot under `/opt/konzerte_bot`, run it as a dedicated
`konzertebot` system user and keep secrets out of the repository (the `.env`
is written to `/etc/konzerte_bot/.env` with mode `600`).

### Initial setup

```bash
# 1. Create the target directory owned by you, so git runs as you (not root).
sudo install -d -o "$USER" -g "$(id -gn)" /opt/konzerte_bot

# 2. Clone the repository and its submodules using your SSH keys.
git clone --recurse-submodules git@github.com:Simon198/konzerte_bot.git /opt/konzerte_bot

# 3. Run the setup as root (forward your SSH agent so submodule ops work).
sudo -E bash /opt/konzerte_bot/setup/setup.sh
```

`setup.sh` creates the system user, virtual environment, runtime directories,
writes the secured `.env` (prompting for the tokens), applies migrations and
installs/enables/starts a hardened `konzerte_bot.service` systemd unit.

To supply the tokens non-interactively:

```bash
sudo -E TOKEN=... ADMIN_TOKEN=... ADMIN_CHAT_ID=... bash /opt/konzerte_bot/setup/setup.sh
# or from a file:
sudo bash /opt/konzerte_bot/setup/setup.sh --env-file /path/to/env
```

### Deploying updates

```bash
sudo bash /opt/konzerte_bot/setup/deploy.sh
```

This stops the service, pulls the latest code (including submodules), updates
dependencies, applies migrations and restarts the service.

### Useful commands

```bash
sudo systemctl status konzerte_bot        # service status
sudo journalctl -u konzerte_bot -f        # follow logs
tail -f /var/log/konzerte_bot/application.log
```

## Privacy & legal

The bot handles personal data and ships a full **German GDPR privacy policy**
stored in this repository:

- [`DATENSCHUTZ.md`](DATENSCHUTZ.md) — the privacy policy (Datenschutzerklärung).
  This is the authoritative document served to users via the `/datenschutz`
  command and the consent flow, which links directly to
  [`https://github.com/Simon198/konzerte_bot/blob/main/DATENSCHUTZ.md`](DATENSCHUTZ.md).
- [`IMPRESSUM.md`](IMPRESSUM.md) — legal notice / contact (Impressum)
- [`VERARBEITUNGSVERZEICHNIS.md`](VERARBEITUNGSVERZEICHNIS.md) — record of processing activities (Art. 30 GDPR)
- [`DATENPANNE.md`](DATENPANNE.md) — data breach notification procedure

Keeping these documents in the repository means the privacy policy is versioned,
publicly auditable and always in sync with what the code actually does.

## License

[MIT](LICENSE) © 2026 Simon Heinrich
