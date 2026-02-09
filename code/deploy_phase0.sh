#!/bin/bash
# Deploy Phase 0 Emergency Monitoring

set -e

echo "=== RAMU Phase 0: Emergency Monitoring Deployment ==="
echo

# Install dependencies
echo "[1/5] Installing Python dependencies..."
pip3 install psutil python-dateutil -q

# Make scripts executable
echo "[2/5] Setting permissions..."
chmod +x ./projects/architecture/system-monitor/*.py

# Copy systemd service files
echo "[3/5] Installing systemd services..."
cp ./projects/architecture/system-monitor/*.service /etc/systemd/system/
systemctl daemon-reload

# Enable and start services
echo "[4/5] Enabling services..."
systemctl enable heartbeat-monitor.service
systemctl enable ram-guardian.service

echo "[5/5] Starting services..."
systemctl start heartbeat-monitor.service
systemctl start ram-guardian.service

echo
echo "=== Deployment Complete ==="
echo
echo "Service Status:"
systemctl status heartbeat-monitor.service --no-pager -l || true
echo
systemctl status ram-guardian.service --no-pager -l || true
echo
echo "Logs:"
echo "  Heartbeat: tail -f ./logs/heartbeat_monitor.log"
echo "  RAM:       tail -f ./logs/ram_guardian.log"
echo "  Journal:   journalctl -fu heartbeat-monitor -fu ram-guardian"
