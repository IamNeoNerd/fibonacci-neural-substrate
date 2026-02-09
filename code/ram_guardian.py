#!/usr/bin/env python3
"""
RAMU RAM Guardian - OOM Prevention
Prevents memory exhaustion crashes.

Monitors WSL RAM every 5 seconds:
- Warn at 80%
- Halt non-critical tasks at 90%
- Emergency cleanup at 95%
"""

import time
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
import sys

# Configuration
CHECK_INTERVAL = 5  # seconds (F5 Fibonacci base)
WARN_THRESHOLD = 80.0
HALT_THRESHOLD = 90.0
EMERGENCY_THRESHOLD = 95.0

# Logging
LOG_FILE = Path("./logs/ram_guardian.log")

def log(level: str, message: str):
    """Simple logging to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def get_wsl_ram():
    """Get WSL RAM usage percentage."""
    try:
        mem = psutil.virtual_memory()
        return mem.percent, mem.available / (1024**3)  # GB
    except Exception as e:
        log("ERROR", f"Failed to get RAM stats: {e}")
        return None, None

def halt_non_critical_tasks():
    """Halt non-critical background tasks."""
    log("ACTION", "Halting non-critical tasks")
    
    # List of processes that can be safely paused/killed
    non_critical = [
        "lead-scraper",
        "backtest",
        "research-shadow",
    ]
    
    halted = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if any(nc in name.lower() for nc in non_critical):
                proc.terminate()
                halted.append(f"{name} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if halted:
        log("INFO", f"Halted: {', '.join(halted)}")
    else:
        log("WARN", "No non-critical tasks found to halt")

def emergency_cleanup():
    """Emergency memory cleanup - kill oldest Python processes."""
    log("CRITICAL", "Emergency cleanup - killing oldest Python processes")
    
    # Get all Python processes sorted by age
    python_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'create_time', 'memory_info']):
        try:
            if 'python' in proc.info['name'].lower():
                # Skip critical processes
                cmdline = ' '.join(proc.cmdline())
                if any(critical in cmdline for critical in ['brain_api', 'heartbeat_monitor', 'ram_guardian']):
                    continue
                
                python_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Sort by age (oldest first)
    python_procs.sort(key=lambda p: p.info['create_time'])
    
    # Kill oldest 3
    killed = []
    for proc in python_procs[:3]:
        try:
            proc.kill()
            killed.append(f"{proc.info['name']} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed:
        log("INFO", f"Killed: {', '.join(killed)}")
    else:
        log("WARN", "No Python processes found to kill")

def check_ram():
    """Main check routine."""
    ram_pct, ram_avail_gb = get_wsl_ram()
    
    if ram_pct is None:
        return
    
    # Log every check at INFO level (suppressed unless debugging)
    if ram_pct >= WARN_THRESHOLD:
        log("DEBUG", f"RAM: {ram_pct:.1f}% ({ram_avail_gb:.2f} GB available)")
    
    # Thresholds
    if ram_pct < WARN_THRESHOLD:
        # All good
        return
    elif ram_pct < HALT_THRESHOLD:
        log("WARN", f"RAM: {ram_pct:.1f}% (threshold: {WARN_THRESHOLD}%)")
    elif ram_pct < EMERGENCY_THRESHOLD:
        log("ALERT", f"RAM: {ram_pct:.1f}% - HALTING NON-CRITICAL TASKS")
        halt_non_critical_tasks()
    else:
        log("CRITICAL", f"RAM: {ram_pct:.1f}% - EMERGENCY CLEANUP")
        emergency_cleanup()

def main():
    """Main loop."""
    log("INFO", "RAM Guardian started")
    log("INFO", f"Check interval: {CHECK_INTERVAL}s (F5 Fibonacci)")
    log("INFO", f"Thresholds: WARN={WARN_THRESHOLD}%, HALT={HALT_THRESHOLD}%, EMERGENCY={EMERGENCY_THRESHOLD}%")
    
    while True:
        try:
            check_ram()
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("INFO", "RAM Guardian stopped by user")
            sys.exit(0)
        except Exception as e:
            log("ERROR", f"Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
