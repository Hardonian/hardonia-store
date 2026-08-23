#!/usr/bin/env bash
# au-watchdog.sh — keep the AU bot intake server alive + observable.
# Runs every minute via au-watchdog.timer. If /au/health fails, restart the service
# and log the event. No silent death: the log is the source of truth.
set -Eeuo pipefail
LOG="/home/scott/hardonia.store/kb/feeds/au-watchdog.log"
URL="http://127.0.0.1:8071/au/health"
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

if curl -s --max-time 4 "$URL" >/dev/null 2>&1; then
  # healthy; record a heartbeat (keep log small)
  echo "$(ts) OK" >>"$LOG"
  # trim to last 200 lines
  tail -n 200 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  exit 0
fi

echo "$(ts) DOWN — restarting au-bot-server" >>"$LOG"
if systemctl --user restart au-bot-server.service 2>>"$LOG"; then
  sleep 2
  if curl -s --max-time 4 "$URL" >/dev/null 2>&1; then
    echo "$(ts) RECOVERED" >>"$LOG"
  else
    echo "$(ts) RESTART FAILED — manual intervention needed" >>"$LOG"
  fi
else
  echo "$(ts) restart command failed" >>"$LOG"
fi
