# Tencent Cloud Deployment Notes

This document describes the intended deployment path for a personal Tencent Cloud server.

## Recommended Server

For MVP:

- Ubuntu 22.04 or 24.04
- 4 CPU cores minimum
- 8 GB RAM minimum
- 100 GB disk minimum
- No GPU required for mock backend and DeepSeek analysis

For real FunASR/SenseVoice processing:

- 8 CPU cores recommended
- 16 GB RAM recommended
- GPU optional but helpful
- 200 GB disk recommended

## Basic Server Setup

```bash
sudo apt update
sudo apt install -y git curl wget vim ufw ca-certificates
```

Install Docker:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and log back in, then verify:

```bash
docker --version
docker compose version
```

## Clone Repository

```bash
git clone https://github.com/XU-jianshuo/voice-coach-recorder.git
cd voice-coach-recorder
```

## Environment

```bash
cp .env.example .env
vim .env
```

Required values for real analysis:

```env
DEEPSEEK_API_KEY=your_key
USE_DEEPSEEK=true
DEVICE_TOKEN=replace-with-long-random-token
SECRET_KEY=replace-with-long-random-secret
```

For first backend skeleton, keep:

```env
ASR_PROVIDER=mock
USE_DEEPSEEK=false
```

## Development Start

After Milestone 1 exists:

```bash
docker compose up --build
```

Health check:

```bash
curl http://localhost:8000/health
```

## Production Direction

Later production layout:

```text
Nginx HTTPS reverse proxy
        ↓
FastAPI backend container
        ↓
PostgreSQL + Redis + storage volume
        ↓
FunASR/SenseVoice worker
        ↓
DeepSeek API
```

## Firewall

Open only necessary ports:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

During development, if exposing FastAPI directly:

```bash
sudo ufw allow 8000
```

Do not leave port 8000 open after Nginx HTTPS is configured.

## Nginx Example

Future example:

```nginx
server {
    listen 80;
    server_name your-domain.example.com;

    client_max_body_size 300M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Use Tencent Cloud SSL certificate or Let's Encrypt for HTTPS.

## Storage

Recommended directories:

```text
/opt/voice-coach/
├── app/
├── data/
│   ├── db/
│   ├── storage/
│   └── logs/
└── backups/
```

Audio retention should be configurable. For example:

- Keep raw audio for 30 days.
- Keep transcripts and analysis indefinitely unless deleted.
- Allow manual deletion.

## Backups

Minimum backup strategy:

- Daily database backup.
- Weekly compressed transcript/analysis export.
- Raw audio backup optional, depending on storage and privacy preference.

Example SQLite backup:

```bash
sqlite3 data/voice_coach.db ".backup backups/voice_coach_$(date +%F).db"
```

## Security Checklist

- Use HTTPS before connecting Android app outside LAN.
- Change `DEVICE_TOKEN` and `SECRET_KEY`.
- Do not commit `.env`.
- Keep Tencent Cloud security group minimal.
- Rotate DeepSeek API key if leaked.
- Avoid logging raw transcript text in production.
- Add delete endpoints before using real personal data heavily.

## FunASR/SenseVoice Notes

Real model deployment should be introduced after backend skeleton is stable.

Suggested path:

1. Start with mock ASR.
2. Add local FunASR Python adapter.
3. Test a short Chinese audio file.
4. Add VAD and punctuation.
5. Add diarization.
6. Add hotwords.
7. Optimize speed and memory.

Keep model dependencies isolated so the API server can start even if the model environment is not installed.
