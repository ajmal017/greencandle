#!/usr/bin/env bash

set -xe

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Setup local env
apt-get -y update
apt-get -y install docker.io ntpdate mysql-client screen atop jq iotop ntp awscli vim atop htop
apt-get dist-upgrade -y
curl -L https://github.com/docker/compose/releases/download/1.24.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
echo "export HOSTNAME >> ~/.bashrc"

cat > /etc/docker/daemon.json << EOF
{
  "live-restore": true,
  "log-driver": "syslog",
  "raw-logs": true,
  "log-opts": {
    "syslog-facility": "local1",
    "tag": "{{.Name}}"
  }
}
EOF

# Start services
systemctl start ntp
systemctl unmask docker.service
systemctl unmask docker.socket
systemctl start docker.service
systemctl start atop

usermod -aG docker ubuntu || true

# Create shared volume
docker volume create data
mkdir -p /data/{mysql,config,graphs,reports}

# Create and mount swap
fallocate -l 1G /swapfile
dd if=/dev/zero of=/swapfile bs=1024 count=1048576
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo "/swapfile swap swap defaults 0 0" >> /etc/fstab

reboot