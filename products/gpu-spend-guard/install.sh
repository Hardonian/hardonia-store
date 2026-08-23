#!/bin/bash
# GPU Spend Guard — Install Script
# Run as the user who will receive alerts (not root)

set -euo pipefail

INSTALL_DIR="${HOME}/.local/share/gpu-spend-guard"
CONFIG_DIR="${HOME}/.config/gpu-spend-guard"
LOG_DIR="${HOME}/.local/var/log"
STATE_DIR="${HOME}/.local/var/lib/gpu-spend-guard"

echo "=== GPU Spend Guard Installer ==="
echo "Install dir: ${INSTALL_DIR}"
echo "Config dir:  ${CONFIG_DIR}"
echo "Log dir:     ${LOG_DIR}"
echo "State dir:   ${STATE_DIR}"
echo

# Create directories
mkdir -p "${INSTALL_DIR}" "${CONFIG_DIR}" "${LOG_DIR}" "${STATE_DIR}"

# Copy notifier.py
cp "$(dirname "$0")/notifier.py" "${INSTALL_DIR}/notifier.py"
chmod +x "${INSTALL_DIR}/notifier.py"

# Copy config.yaml if not exists
if [[ ! -f "${CONFIG_DIR}/config.yaml" ]]; then
    cp "$(dirname "$0")/config.yaml" "${CONFIG_DIR}/config.yaml"
    echo "Created config at ${CONFIG_DIR}/config.yaml"
    echo ">>> EDIT THIS FILE with your Telegram/Discord/Email credentials <<<"
else
    echo "Config already exists at ${CONFIG_DIR}/config.yaml (skipping)"
fi

# Create systemd user service
SYSTEMD_DIR="${HOME}/.config/systemd/user"
mkdir -p "${SYSTEMD_DIR}"

cat > "${SYSTEMD_DIR}/gpu-spend-guard.service" <<'EOF'
[Unit]
Description=GPU Spend Guard — Per-minute spend check
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=%h/.local/share/gpu-spend-guard/notifier.py
Environment=GPU_SPEND_GUARD_CONFIG=%h/.config/gpu-spend-guard/config.yaml
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

cat > "${SYSTEMD_DIR}/gpu-spend-guard.timer" <<'EOF'
[Unit]
Description=Run GPU Spend Guard every minute

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
Persistent=true
RandomizedDelaySec=10

[Install]
WantedBy=timers.target
EOF

cat > "${SYSTEMD_DIR}/gpu-spend-guard-summary.service" <<'EOF'
[Unit]
Description=GPU Spend Guard — Daily summary
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=%h/.local/share/gpu-spend-guard/notifier.py summary
Environment=GPU_SPEND_GUARD_CONFIG=%h/.config/gpu-spend-guard/config.yaml
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

cat > "${SYSTEMD_DIR}/gpu-spend-guard-summary.timer" <<'EOF'
[Unit]
Description=Run GPU Spend Guard daily summary at 08:00

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable --now gpu-spend-guard.timer
systemctl --user enable --now gpu-spend-guard-summary.timer

echo
echo "=== Installation Complete ==="
echo
echo "Next steps:"
echo "1. Edit config: ${CONFIG_DIR}/config.yaml"
echo "   - Add your Telegram bot token & chat_id"
echo "   - Add your Discord webhook URL"
echo "   - Configure email if desired"
echo "   - Adjust GPU pricing for your hardware"
echo "   - Set thresholds for your budget"
echo
echo "2. Test the notifier:"
echo "   ${INSTALL_DIR}/notifier.py"
echo
echo "3. Check logs:"
echo "   journalctl --user -u gpu-spend-guard -f"
echo
echo "4. View timer status:"
echo "   systemctl --user status gpu-spend-guard.timer"
echo "   systemctl --user status gpu-spend-guard-summary.timer"
echo
echo "The service will run every minute and send daily summary at 08:00."