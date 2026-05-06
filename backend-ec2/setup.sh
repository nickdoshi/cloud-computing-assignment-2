#!/bin/bash
# Run on Amazon Linux 2023 EC2 instance with LabRole attached.
# Usage: sudo bash setup.sh

set -e

# ── 1. Install Java 17 and Nginx ──────────────────────────────────────────────
dnf install -y java-17-amazon-corretto nginx

# ── 2. Copy the Spring Boot JAR ───────────────────────────────────────────────
# Run this from the repo root after: ./mvnw -q package -DskipTests
# Accept JAR from ~/target/ (scp'd separately) or from a local Maven build
if [ -f "$HOME/target/backend-0.0.1-SNAPSHOT.jar" ]; then
    cp "$HOME/target/backend-0.0.1-SNAPSHOT.jar" /opt/backend.jar
elif [ -f "$(dirname "$0")/../target/backend-0.0.1-SNAPSHOT.jar" ]; then
    cp "$(dirname "$0")/../target/backend-0.0.1-SNAPSHOT.jar" /opt/backend.jar
else
    echo "ERROR: JAR not found. Copy target/backend-0.0.1-SNAPSHOT.jar to ~/target/ first."
    exit 1
fi

# ── 3. Nginx reverse proxy: port 80 → 8080 ────────────────────────────────────
cat > /etc/nginx/conf.d/backend.conf <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass         http://127.0.0.1:8080;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }
}
EOF

# Remove the default server block that also listens on 80
sed -i '/listen.*80/d' /etc/nginx/nginx.conf 2>/dev/null || true

systemctl enable --now nginx

# ── 4. Systemd service for the Spring Boot app ────────────────────────────────
cat > /etc/systemd/system/backend.service <<'EOF'
[Unit]
Description=Music App Spring Boot Backend
After=network.target

[Service]
ExecStart=/usr/bin/java -jar /opt/backend.jar
Restart=on-failure
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now backend

echo "Done. Spring Boot running on :8080, Nginx proxying :80 → :8080"
