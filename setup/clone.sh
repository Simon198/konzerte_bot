# ── konzerte_bot — clone to /opt/konzerte_bot ──────────────────────────────
# Copy each command below into your terminal and run it as a normal user
# (not root). Each command is a single self-contained line.

# 1. Create the target directory owned by you, so git runs as you (not root).
sudo install -d -o "$USER" -g "$(id -gn)" /opt/konzerte_bot

# 2. Clone the repository and its submodules using your SSH keys.
git clone --recurse-submodules git@github.com:Simon198/konzerte_bot.git /opt/konzerte_bot

# 3. Run setup as root, forwarding your SSH agent so git submodule ops work.
sudo -E bash /opt/konzerte_bot/setup/setup.sh
