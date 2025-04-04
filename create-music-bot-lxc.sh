#!/bin/bash

# Config
CT_ID=120
HOSTNAME="music-bot"
TEMPLATE="ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
DISK_SIZE="4G"
MEMORY="512"
CORES="2"
STORAGE="local-lvm"
BRIDGE="vmbr0"

# Create container
echo "[INFO] Creating LXC container..."
pct create $CT_ID $STORAGE:vztmpl/$TEMPLATE \
  --hostname $HOSTNAME \
  --rootfs $STORAGE:$DISK_SIZE \
  --memory $MEMORY \
  --cores $CORES \
  --net0 name=eth0,bridge=$BRIDGE,ip=dhcp \
  --features nesting=1 \
  --unprivileged 1

# Start container
echo "[INFO] Starting container..."
pct start $CT_ID

sleep 5

# Install dependencies
echo "[INFO] Installing dependencies inside container..."
pct exec $CT_ID -- bash -c "
apt update && apt install -y python3 python3-pip ffmpeg git logrotate
pip3 install --upgrade pip
"

# Copy project files
echo "[INFO] Copying bot files..."
pct push $CT_ID ./music-bot /root/music-bot -r
pct push $CT_ID ./logrotate.conf /etc/logrotate.d/music-bot
pct exec $CT_ID -- bash -c "chmod +x /root/music-bot/update-bot.sh"

# Install Python requirements
pct exec $CT_ID -- bash -c "pip3 install -r /root/music-bot/requirements.txt"

# Enable logrotate
pct exec $CT_ID -- bash -c "logrotate /etc/logrotate.d/music-bot"

# Enable systemd service
pct exec $CT_ID -- bash -c "
cp /root/music-bot/service/music-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable music-bot
systemctl start music-bot
"

# Auto-start container
pct set $CT_ID --onboot 1

echo "[INFO] Setup complete! Container ID: $CT_ID"
echo "[INFO] Start the container with: pct start $CT_ID"
