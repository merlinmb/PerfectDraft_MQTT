#!/usr/bin/env bash
# Deploys this project to the homebridge Pi and (re)builds the container.
set -euo pipefail

HOST="pi@homebridge.local"
REMOTE_DIR="/home/pi/portainer_data/perfectdraft"

ssh "$HOST" "mkdir -p $REMOTE_DIR"

scp -r \
  Dockerfile docker-compose.yml requirements.txt src \
  "$HOST:$REMOTE_DIR/"

echo "Code deployed. If this is a first-time deploy, copy config.example.yaml"
echo "to $REMOTE_DIR/config.yaml on the Pi and fill in credentials, then run:"
echo "  ssh $HOST 'cd $REMOTE_DIR && docker compose up -d --build'"
