#!/usr/bin/env python3
"""
RAMU Heartbeat Monitor - Emergency Freeze Detection
Prevents another 5.5-hour undetected freeze.

Checks heartbeat-state.json every 5 seconds:
- Warn if lag > 30s
- Alert if lag > 60s  
- Auto-restart gateway if lag > 120s
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import sys

# Configuration
HEARTBEAT_FILE = Path("./memory/heartbeat-state.json")
CHECK_INTERVAL = 5  # seconds (F5 Fibonacci base)
WARN_THRESHOLD = 30
ALERT_THRESHOLD = 60
RESTART_THRESHOLD = 120

# Logging
LOG_FILE = Path("./logs/heartbeat_monitor.log")

def log(level: str, message: str):
    """Simple logging to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def read_heartbeat_state():
    """Read and parse heartbeat-state.json."""
    try:
        if not HEARTBEAT_FILE.exists():
            return None
        
        with open(HEARTBEAT_FILE) as f:
            return json.load(f)
    except Exception as e:
        log("ERROR", f"Failed to read heartbeat file: {e}")
        return None

def calculate_lag():
    """Calculate seconds since last heartbeat."""
    state = read_heartbeat_state()
    if not state or "last_heartbeat" not in state:
        return None
    
    # Parse ISO format or epoch timestamp
    last_hb = state["last_heartbeat"]
    if isinstance(last_hb, str):
        # ISO format: "2026-02-07T19:58:00+05:30"
        from dateutil import parser
        last_time = parser.parse(last_hb).timestamp()
    else:
        last_time = float(last_hb)
    
    now = time.time()
    return now - last_time

def send_hud_alert(level: str, lag: float):
    """Send alert to HUD via WebSocket (if available)."""
    try:
        # TODO: Implement WebSocket notification to HUD
        # For now, just log
        log("HUD", f"Alert {level}: Heartbeat lag {lag:.1f}s")
    except Exception as e:
        log("ERROR", f"Failed to send HUD alert: {e}")

def restart_gateway():
    """Attempt to restart openclaw-gateway."""
    log("CRITICAL", "Attempting to restart openclaw-gateway")
    try:
        subprocess.run(["systemctl", "restart", "openclaw-gateway"], check=True)
        log("INFO", "Gateway restart command sent")
        return True
    except Exception as e:
        log("ERROR", f"Failed to restart gateway: {e}")
        return False

def check_heartbeat():
    """Main check routine."""
    lag = calculate_lag()
    
    if lag is None:
        log("WARN", "Could not determine heartbeat lag")
        return
    
    # Thresholds
    if lag < WARN_THRESHOLD:
        # All good
        return
    elif lag < ALERT_THRESHOLD:
        log("WARN", f"Heartbeat lag: {lag:.1f}s (threshold: {WARN_THRESHOLD}s)")
    elif lag < RESTART_THRESHOLD:
        log("ALERT", f"Heartbeat lag: {lag:.1f}s (threshold: {ALERT_THRESHOLD}s)")
        send_hud_alert("ALERT", lag)
    else:
        log("CRITICAL", f"Heartbeat lag: {lag:.1f}s - RESTARTING GATEWAY")
        send_hud_alert("CRITICAL", lag)
        restart_gateway()

def main():
    """Main loop."""
    log("INFO", "Heartbeat Monitor started")
    log("INFO", f"Monitoring: {HEARTBEAT_FILE}")
    log("INFO", f"Check interval: {CHECK_INTERVAL}s (F5 Fibonacci)")
    log("INFO", f"Thresholds: WARN={WARN_THRESHOLD}s, ALERT={ALERT_THRESHOLD}s, RESTART={RESTART_THRESHOLD}s")
    
    while True:
        try:
            check_heartbeat()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("INFO", "Heartbeat Monitor stopped by user")
            sys.exit(0)
        except Exception as e:
            log("ERROR", f"Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
