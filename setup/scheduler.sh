#!/usr/bin/env bash
#
# konzerte_bot — event scraper control
#
# The daily event scraping is scheduled by a systemd timer
# (konzerte_bot_scraper.timer, daily at 17:00). This script shows the scheduled
# timers and lets you trigger a scrape manually. Run as root:
#
#     sudo bash setup/scheduler.sh          # show the scheduled timers (default)
#     sudo bash setup/scheduler.sh status   # same as above
#     sudo bash setup/scheduler.sh scrape   # run the event scraper now

set -euo pipefail

SCRAPER_SERVICE_NAME="konzerte_bot_scraper"

action="${1:-status}"

case "$action" in
    status)
        systemctl --no-pager list-timers --all 'konzerte_bot*'
        ;;
    scrape)
        systemctl start --no-block "$SCRAPER_SERVICE_NAME.service"
        systemctl --no-pager --lines=0 status "$SCRAPER_SERVICE_NAME.service" || true
        ;;
    *)
        echo "Usage: $0 {status|scrape}" >&2
        exit 1
        ;;
esac
