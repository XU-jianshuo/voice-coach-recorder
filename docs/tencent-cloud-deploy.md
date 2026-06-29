# Tencent Cloud Deployment Notes

This document describes a private Tencent Cloud deployment path for the backend. No secrets should be committed. Keep `.env` only on the server.

## Recommended Server

For mock ASR and DeepSeek text analysis:

- Ubuntu 22.04 or 24.04
- 4 CPU cores minimum
- 8 GB RAM minimum
- 100 GB disk minimum
- No GPU required

For FunASR / SenseVoice later:

- 8 CPU cores recommended
- 16 GB RAM recommended
- GPU optional, not required for tests
- 200 GB disk recommended

## Basic Setup

```bash
sudo apt update
sudo apt install -y git curl wget vim ufw ca-certificates
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and back in, then verify:

```bash
docker --version
docker compose version
```

## Clone And Configure

```bash
git clone https://github.com/XU-jianshuo/voice-coach-recorder.git
cd voice-coach-recorder
cp .env.example .env
vim .env
```

Recommended first private deployment:

```env
APP_ENV=production
DEVICE_TOKEN=replace-with-long-random-token
SECRET_KEY=replace-with-long-random-secret
DATABASE_URL=sqlite:////app/data/voice_coach.db
STORAGE_DIR=/app/data/storage
ASR_PROVIDER=mock
USE_DEEPSEEK=false
RAW_AUDIO_RETENTION_DAYS=30
BACKUP_RETENTION_DAYS=14
REQUIRE_HTTPS=true
```

Enable DeepSeek only after the key is configured:

```env
USE_DEEPSEEK=true
DEEPSEEK_API_KEY=your_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_REASONING_MODEL=
```

## Development Start

```bash
docker compose up --build
curl http://localhost:8000/health
```

## Production Compose

Use the production template:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f backend
```

Production layout:

```text
Nginx HTTPS reverse proxy
  -> FastAPI backend container
  -> SQLite/PostgreSQL and storage volume
  -> optional FunASR/SenseVoice runtime
  -> optional DeepSeek API
```

## Firewall And Nginx

Open only required ports:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

The repository includes `deploy/nginx/voice-coach.conf`. It proxies to the backend container and keeps port `8000` off the public internet. Use Tencent Cloud SSL certificates or Let's Encrypt for HTTPS.

HTTPS checklist:

- Point DNS to the Tencent Cloud CVM public IP.
- Open ports 80 and 443 in the Tencent Cloud security group.
- Issue and mount certificates under `deploy/certs/`.
- Redirect HTTP to HTTPS after certificate verification.
- Do not expose FastAPI port 8000 directly after Nginx is configured.

## FunASR / SenseVoice Runtime

The backend starts without FunASR installed. Keep this default for local tests:

```env
ASR_PROVIDER=mock
```

To test FunASR later, install model dependencies in a deliberate model runtime or custom image:

```bash
python -m venv .venv-funasr
source .venv-funasr/bin/activate
pip install --upgrade pip
pip install funasr modelscope
```

Place models in configurable directories:

```text
/opt/voice-coach/models/funasr/
/opt/voice-coach/models/sensevoice/
```

Then configure:

```env
ASR_PROVIDER=funasr
FUNASR_MODEL_DIR=/app/models/funasr
SENSEVOICE_MODEL_DIR=/app/models/sensevoice
ENABLE_DIARIZATION=false
```

The optional adapter accepts hotwords from the database, requests VAD, punctuation and timestamps when supported, and normalizes speaker labels to neutral `Speaker 0`, `Speaker 1`, etc. If dependencies or model files are missing, processing fails clearly for that session instead of preventing the API from starting.

## Storage And Retention

Recommended host layout:

```text
/opt/voice-coach/app/
/opt/voice-coach/data/db/
/opt/voice-coach/data/storage/
/opt/voice-coach/data/logs/
/opt/voice-coach/backups/
```

Retention settings:

```env
RAW_AUDIO_RETENTION_DAYS=30
BACKUP_RETENTION_DAYS=14
```

Recommended policy:

- Raw audio: keep 30 days by default, shorter if privacy risk is high.
- Transcripts and analysis: keep until the user deletes the session.
- Backups: keep 14 daily snapshots for MVP.
- Logs: rotate container logs and avoid raw transcript/audio content.

Automated deletion jobs are future work. Until then, clean up manually only after confirming user needs and backups.

## Backups

SQLite example:

```bash
mkdir -p backups
sqlite3 data/voice_coach.db ".backup backups/voice_coach_$(date +%F).db"
```

Production notes:

- Keep backups outside the application container.
- Encrypt backups if transcripts or audio are included.
- Rotate backups according to `BACKUP_RETENTION_DAYS`.
- Test restore regularly in a separate directory.
- For PostgreSQL later, use `pg_dump` with least-privilege credentials.

## Systemd Example

Create `/etc/systemd/system/voice-coach.service`:

```ini
[Unit]
Description=Voice Coach Recorder backend
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
WorkingDirectory=/opt/voice-coach
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable voice-coach
sudo systemctl start voice-coach
```

## Log Rotation

The production Compose template limits Docker JSON logs:

```yaml
logging:
  driver: json-file
  options:
    max-size: "20m"
    max-file: "5"
```

Also rotate Nginx logs if they are persisted on the host or in a named volume.

## Security Checklist

- Use HTTPS before connecting Android outside LAN.
- Change `DEVICE_TOKEN` and `SECRET_KEY`.
- Do not commit `.env` or model/API secrets.
- Keep Tencent Cloud security groups minimal.
- Rotate the DeepSeek key if leaked.
- Avoid logging raw transcript text in production.
- Keep `ASR_PROVIDER=mock` until FunASR dependencies and model paths are intentionally installed.
- Keep model directories read-only inside the backend container where possible.
- Restrict SSH to key-based login and disable password login if feasible.
- Keep server, Docker and Python images patched.
- Use least-privilege database credentials when moving to PostgreSQL.
- Add delete endpoints before using real personal data heavily.
