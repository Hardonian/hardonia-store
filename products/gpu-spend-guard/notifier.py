#!/usr/bin/env python3
"""
GPU Spend Guard — Notifier
Reads GPU metrics, calculates spend, fires alerts via Telegram/Discord/Email.
Run via systemd timer every 60s.
"""

from __future__ import annotations
import os
import sys
import yaml
import time
import subprocess
import sqlite3
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

CONFIG_PATH = Path(os.getenv("GPU_SPEND_GUARD_CONFIG", "/etc/gpu-spend-guard/config.yaml"))
STATE_DB = Path("/var/lib/gpu-spend-guard/state.db")

@dataclass
class GPUStat:
    name: str
    util_pct: float
    mem_used_mib: int
    mem_total_mib: int

@dataclass
class AlertState:
    last_warn: Dict[str, float]
    last_critical: Dict[str, float]
    last_summary: float

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def init_db():
    STATE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            key TEXT PRIMARY KEY,
            last_sent REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spend_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            gpu_name TEXT NOT NULL,
            hourly_cost REAL NOT NULL,
            util_pct REAL NOT NULL
        )
    """)
    conn.commit()
    return conn

def get_gpu_stats_nvidia_smi() -> List[GPUStat]:
    """Parse nvidia-smi for GPU utilization and memory."""
    try:
        out = subprocess.check_output([
            "nvidia-smi",
            "--query-gpu=name,utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits"
        ], text=True, timeout=10)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return []
    
    stats = []
    for line in out.strip().split("\n"):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            continue
        name, util, mem_used, mem_total = parts
        stats.append(GPUStat(
            name=name,
            util_pct=float(util),
            mem_used_mib=int(mem_used),
            mem_total_mib=int(mem_total)
        ))
    return stats

def get_gpu_stats_prometheus(config: dict) -> List[GPUStat]:
    """Query Prometheus for GPU metrics."""
    # Implementation for Prometheus-based metrics
    # This is a placeholder - adapt to your Prometheus setup
    return []

def calculate_hourly_cost(gpu_name: str, config: dict) -> float:
    """Calculate hourly cost for a GPU based on pricing config."""
    pricing = config.get("gpu_pricing", {})
    return pricing.get(gpu_name, pricing.get("default", 0.50))

def check_alert_cooldown(conn: sqlite3.Connection, key: str, cooldown_seconds: int) -> bool:
    """Check if enough time has passed since last alert of this type."""
    row = conn.execute("SELECT last_sent FROM alerts WHERE key=?", (key,)).fetchone()
    if not row:
        return True
    return (time.time() - row[0]) >= cooldown_seconds

def record_alert(conn: sqlite3.Connection, key: str):
    """Record that an alert was sent."""
    conn.execute(
        "INSERT OR REPLACE INTO alerts (key, last_sent) VALUES (?, ?)",
        (key, time.time())
    )
    conn.commit()

def send_telegram(config: dict, message: str) -> bool:
    """Send message via Telegram Bot API."""
    tg = config.get("notifications", {}).get("telegram", {})
    if not tg.get("enabled"):
        return False
    token = tg.get("bot_token")
    chat_id = tg.get("chat_id")
    if not token or not chat_id or token == "YOUR_BOT_TOKEN_HERE":
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": tg.get("parse_mode", "HTML"),
                "disable_web_page_preview": True
            },
            timeout=10
        )
        return resp.ok
    except Exception:
        return False

def send_discord(config: dict, message: str) -> bool:
    """Send message via Discord webhook."""
    dc = config.get("notifications", {}).get("discord", {})
    if not dc.get("enabled"):
        return False
    webhook_url = dc.get("webhook_url")
    if not webhook_url or webhook_url == "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN":
        return False
    try:
        resp = requests.post(
            webhook_url,
            json={
                "content": message,
                "username": dc.get("username", "GPU Spend Guard"),
                "avatar_url": dc.get("avatar_url") or None
            },
            timeout=10
        )
        return resp.ok
    except Exception:
        return False

def send_email(config: dict, subject: str, body: str) -> bool:
    """Send email via SMTP."""
    em = config.get("notifications", {}).get("email", {})
    if not em.get("enabled"):
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = em.get("from_addr", "GPU Spend Guard <alerts@localhost>")
        msg["To"] = ", ".join(em.get("to_addrs", []))
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(em.get("smtp_server", "localhost"), em.get("smtp_port", 587)) as server:
            server.starttls()
            server.login(em.get("username"), em.get("password"))
            server.send_message(msg)
        return True
    except Exception:
        return False

def send_alert(config: dict, level: str, title: str, details: str):
    """Send alert via all configured channels."""
    emoji = "⚠️" if level == "warn" else "🚨"
    message = f"{emoji} <b>GPU Spend Guard — {level.upper()}</b>\n{title}\n\n{details}"
    
    sent = False
    if send_telegram(config, message):
        sent = True
    if send_discord(config, message):
        sent = True
    if send_email(config, f"GPU Spend Guard — {level.upper()}: {title}", f"{title}\n\n{details}"):
        sent = True
    
    return sent

def run_check(config: dict, conn: sqlite3.Connection):
    """Main check loop."""
    thresholds = config.get("thresholds", {})
    gpu_stats = get_gpu_stats_nvidia_smi()
    
    if not gpu_stats:
        gpu_stats = get_gpu_stats_prometheus(config)
    
    if not gpu_stats:
        print("No GPU stats available", file=sys.stderr)
        return
    
    total_hourly = 0.0
    alerts_fired = []
    
    for gpu in gpu_stats:
        hourly_cost = calculate_hourly_cost(gpu.name, config) * (gpu.util_pct / 100.0)
        total_hourly += hourly_cost
        
        # Record to history
        conn.execute(
            "INSERT INTO spend_history (timestamp, gpu_name, hourly_cost, util_pct) VALUES (?, ?, ?, ?)",
            (time.time(), gpu.name, hourly_cost, gpu.util_pct)
        )
        
        # Per-GPU alerts
        if hourly_cost >= thresholds.get("gpu_hourly_critical", 1.00):
            key = f"critical:{gpu.name}:hourly"
            if check_alert_cooldown(conn, key, thresholds.get("dedup", {}).get("critical_cooldown_minutes", 5) * 60):
                send_alert(config, "critical", 
                    f"GPU {gpu.name} critical spend: ${hourly_cost:.2f}/hr",
                    f"Utilization: {gpu.util_pct:.1f}%\nMemory: {gpu.mem_used_mib}/{gpu.mem_total_mib} MiB\nRate: ${calculate_hourly_cost(gpu.name, config):.2f}/hr at 100%")
                record_alert(conn, key)
                alerts_fired.append(key)
        
        elif hourly_cost >= thresholds.get("gpu_hourly_warn", 0.50):
            key = f"warn:{gpu.name}:hourly"
            if check_alert_cooldown(conn, key, thresholds.get("dedup", {}).get("warn_cooldown_minutes", 15) * 60):
                send_alert(config, "warn",
                    f"GPU {gpu.name} elevated spend: ${hourly_cost:.2f}/hr",
                    f"Utilization: {gpu.util_pct:.1f}%\nMemory: {gpu.mem_used_mib}/{gpu.mem_total_mib} MiB\nRate: ${calculate_hourly_cost(gpu.name, config):.2f}/hr at 100%")
                record_alert(conn, key)
                alerts_fired.append(key)
    
    # Aggregate alerts
    if total_hourly >= thresholds.get("total_hourly_critical", 5.00):
        key = "critical:total:hourly"
        if check_alert_cooldown(conn, key, thresholds.get("dedup", {}).get("critical_cooldown_minutes", 5) * 60):
            send_alert(config, "critical",
                f"Total lab spend critical: ${total_hourly:.2f}/hr",
                f"Active GPUs: {len(gpu_stats)}\nProjected daily: ${total_hourly * 24:.2f}\nProjected monthly: ${total_hourly * 24 * 30:.2f}")
            record_alert(conn, key)
            alerts_fired.append(key)
    
    elif total_hourly >= thresholds.get("total_hourly_warn", 2.00):
        key = "warn:total:hourly"
        if check_alert_cooldown(conn, key, thresholds.get("dedup", {}).get("warn_cooldown_minutes", 15) * 60):
            send_alert(config, "warn",
                f"Total lab spend elevated: ${total_hourly:.2f}/hr",
                f"Active GPUs: {len(gpu_stats)}\nProjected daily: ${total_hourly * 24:.2f}\nProjected monthly: ${total_hourly * 24 * 30:.2f}")
            record_alert(conn, key)
            alerts_fired.append(key)
    
    conn.commit()
    
    if alerts_fired:
        print(f"Fired alerts: {alerts_fired}")
    else:
        print(f"OK — Total: ${total_hourly:.2f}/hr across {len(gpu_stats)} GPUs")

def run_daily_summary(config: dict, conn: sqlite3.Connection):
    """Send daily spend summary."""
    summary_config = config.get("schedule", {})
    dedup_hours = summary_config.get("summary_dedup_hours", 24)
    
    key = "summary:daily"
    if not check_alert_cooldown(conn, key, dedup_hours * 3600):
        return
    
    # Get last 24h of spend data
    cutoff = time.time() - 86400
    rows = conn.execute(
        "SELECT gpu_name, SUM(hourly_cost)/COUNT(*) as avg_hourly, MAX(hourly_cost) as peak_hourly, COUNT(*) as samples "
        "FROM spend_history WHERE timestamp > ? GROUP BY gpu_name",
        (cutoff,)
    ).fetchall()
    
    if not rows:
        return
    
    total_avg = sum(r[1] for r in rows)
    total_peak = sum(r[2] for r in rows)
    estimated_daily = total_avg * 24
    estimated_monthly = estimated_daily * 30
    
    details = "Last 24h GPU spend:\n"
    for gpu_name, avg_hourly, peak_hourly, samples in rows:
        details += f"  {gpu_name}: avg ${avg_hourly:.2f}/hr, peak ${peak_hourly:.2f}/hr ({samples} samples)\n"
    details += f"\nTotal avg: ${total_avg:.2f}/hr\nTotal peak: ${total_peak:.2f}/hr\n"
    details += f"Estimated daily: ${estimated_daily:.2f}\nEstimated monthly: ${estimated_monthly:.2f}"
    
    send_alert(config, "warn", "Daily GPU Spend Summary", details)
    record_alert(conn, key)
    print("Sent daily summary")

def main():
    config = load_config()
    conn = init_db()
    
    # Clean old history (keep 30 days)
    conn.execute("DELETE FROM spend_history WHERE timestamp < ?", (time.time() - 30*86400,))
    conn.commit()
    
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        run_daily_summary(config, conn)
    else:
        run_check(config, conn)

if __name__ == "__main__":
    main()