# Sowaan Cloud — Onboarding Frontend Deployment Guide

## Context
The `sowaan_cloud` Frappe app now includes a Vite/React frontend located at `apps/sowaan_cloud/frontend/`.
After every code update, the frontend must be built and assets published before restarting bench.

---

## Prerequisites (one-time setup on the server)

### Ensure Node.js 20+ is available
```bash
node --version   # must be v20.x or v22.x
```
If using `nvm`:
```bash
nvm install 20
nvm use 20
```

---

## Deployment Steps (run every release)

### 1. Pull latest code
```bash
cd /path/to/bench
bench update --pull --apps sowaan_cloud
```
Or if deploying manually:
```bash
cd /path/to/bench/apps/sowaan_cloud
git pull origin main
```

### 2. Install / update frontend dependencies
```bash
cd /path/to/bench/apps/sowaan_cloud/frontend
npm install
```

### 3. Build the frontend
```bash
# If using nvm, activate Node 20 first:
nvm use 20

npm run build
```
This outputs built assets to `sowaan_cloud/public/onboarding/`.

### 4. Publish assets via bench
```bash
cd /path/to/bench
bench build --app sowaan_cloud
```

### 5. Restart bench
```bash
bench restart
```
Or if running under `supervisor`:
```bash
sudo supervisorctl restart all
```

---

## Verification
After deployment, visit:
```
https://<your-domain>/onboarding
```
The onboarding app should load correctly.

---

## Notes
- **No `.env` changes needed** — both apps run on the same server, so the default `127.0.0.1` is always correct.
- **Steps 2–4 must be repeated** every time frontend source files change.
- **Step 4 (`bench build`)** is what copies assets from `public/` into the site's served `assets/` folder — do not skip it.
