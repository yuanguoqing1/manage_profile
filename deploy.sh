#!/usr/bin/env bash
set -euo pipefail

APP="/www/manage_profile"
FRONT="$APP/frontend"
BACK="$APP/backend"
WEB="/var/www/manage_profile"

echo "==> git pull"
cd "$APP"
git pull --rebase

echo "==> build frontend"
cd "$FRONT"
rm -rf dist node_modules/.vite
npm ci --silent || npm install --silent
npm run build

echo "==> publish frontend"
rsync -av --delete "$FRONT/dist/" "$WEB/"
systemctl reload nginx

echo "==> restart backend"
systemctl restart manage_profile_backend

echo "==> health check"
curl -sS -I http://127.0.0.1:8000/ | head -n 5 || true
echo "==> done"
