# BookWhisperer Deployment Guide

Complete guide for deploying BookWhisperer to production environments.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development](#local-development)
4. [Production Deployment](#production-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Security Considerations](#security-considerations)
7. [Performance Tuning](#performance-tuning)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

---

## Overview

BookWhisperer can be deployed in several configurations:

- **Local Development** - Single machine with Docker Compose
- **Production Single Server** - VPS/dedicated server with Docker
- **Production Distributed** - Multiple servers with load balancing (future)

This guide focuses on the first two scenarios.

---

## Prerequisites

### Hardware Requirements

**Minimum (Development):**
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space
- No GPU required (CPU-only Ollama)

**Recommended (Production):**
- 8+ CPU cores
- 16 GB RAM
- 100 GB SSD storage
- GPU optional (significantly speeds up LLM processing)

**With GPU:**
- NVIDIA GPU with 6+ GB VRAM
- CUDA 11.8+ support
- Additional 10-20 GB disk for CUDA libraries

### Software Requirements

- **Docker** 24.0+
- **Docker Compose** 2.20+
- **Git** (for cloning repository)
- **Linux** (Ubuntu 22.04+ recommended, or other distributions)
- **Windows** with WSL2 (for Windows deployments)

### Network Requirements

- Open ports:
  - `3000` - Frontend (HTTP)
  - `8000` - Backend API (HTTP)
  - `5432` - PostgreSQL (internal only)
  - `6379` - Redis (internal only)
  - `11434` - Ollama (internal only)
  - `4123` - Chatterbox TTS (internal only)
  - `5555` - Flower (monitoring, optional)

---

## Local Development

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/BookWhisperer.git
cd BookWhisperer
```

2. **Create environment file:**
```bash
cp backend/.env.example backend/.env
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Pull Ollama model (first time only):**
```bash
# Linux/Mac
cd backend
chmod +x scripts/setup_ollama.sh
./scripts/setup_ollama.sh

# Windows
cd backend
scripts\setup_ollama.bat
```

5. **Access the application:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Flower: http://localhost:5555

### Development Commands

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

**Restart services:**
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

**Stop services:**
```bash
docker-compose down
```

**Clean restart (removes volumes):**
```bash
docker-compose down -v
docker-compose up -d
```

---

## Production Deployment

### Server Setup

#### 1. Prepare Server

**Update system:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Install Docker:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Install Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Verify installations:**
```bash
docker --version
docker-compose --version
```

#### 2. Clone and Configure

**Clone repository:**
```bash
git clone https://github.com/yourusername/BookWhisperer.git
cd BookWhisperer
```

**Create production environment:**
```bash
cp backend/.env.example backend/.env
nano backend/.env
```

**Edit key settings:**
```env
# Database
DATABASE_URL=postgresql://bookwhisperer:CHANGE_THIS_PASSWORD@db:5432/bookwhisperer

# Security
SECRET_KEY=your-secret-key-here-change-this

# Ollama
OLLAMA_MODEL=llama2  # or mistral for production

# Storage
MAX_UPLOAD_SIZE=52428800  # 50MB

# Environment
ENVIRONMENT=production
DEBUG=false
```

**Generate secret key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:16
    container_name: bookwhisperer_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: bookwhisperer
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: bookwhisperer
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bookwhisperer"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: bookwhisperer_redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    container_name: bookwhisperer_ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    # Uncomment for GPU support:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: bookwhisperer_backend
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://bookwhisperer:${DB_PASSWORD}@db:5432/bookwhisperer
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_URL=http://ollama:11434
      - ENVIRONMENT=production
    volumes:
      - ./backend/storage:/app/storage
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    container_name: bookwhisperer_celery
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://bookwhisperer:${DB_PASSWORD}@db:5432/bookwhisperer
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_URL=http://ollama:11434
    volumes:
      - ./backend/storage:/app/storage
    depends_on:
      - db
      - redis
      - backend
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2

  nginx:
    image: nginx:alpine
    container_name: bookwhisperer_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend

volumes:
  postgres_data:
  ollama_data:
```

#### 4. SSL/TLS Setup (Recommended)

**Install Certbot:**
```bash
sudo apt install certbot
```

**Get SSL certificate:**
```bash
sudo certbot certonly --standalone -d your-domain.com
```

**Update nginx config:**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

#### 5. Deploy

**Start services:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Pull Ollama model:**
```bash
docker exec -it bookwhisperer_ollama ollama pull llama2
```

**Check status:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

---

## Environment Configuration

### Backend Environment Variables

**Required:**
```env
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://host:6379/0
OLLAMA_URL=http://ollama:11434
SECRET_KEY=your-secret-key
```

**Optional:**
```env
# Ollama
OLLAMA_MODEL=llama2
OLLAMA_MAX_TOKENS=4000

# Chatterbox TTS
CHATTERBOX_URL=http://chatterbox:4123

# Storage
MAX_UPLOAD_SIZE=52428800  # 50MB
STORAGE_PATH=/app/storage

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Frontend Environment Variables

```env
VITE_API_URL=https://your-domain.com/api/v1
```

---

## Security Considerations

### Critical Security Steps

1. **Change default passwords**
   - PostgreSQL password
   - Any admin accounts (when auth is added)

2. **Use strong secret keys**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Enable SSL/TLS**
   - Use Let's Encrypt for free certificates
   - Force HTTPS redirects

4. **Configure firewall**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

5. **Restrict database access**
   - Only allow connections from backend container
   - Use internal Docker network

6. **File upload validation**
   - Validate file types
   - Scan for malware (optional)
   - Limit file sizes

7. **Regular updates**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

### Security Headers

Add to nginx config:
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

---

## Performance Tuning

### Celery Workers

**Adjust concurrency:**
```yaml
celery_worker:
  command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
```

**Recommendations:**
- CPU-only: concurrency = CPU cores
- With GPU: concurrency = 2-4 (GPU is bottleneck)

### Database Optimization

**PostgreSQL tuning:**
```sql
-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '4GB';

-- Increase work mem
ALTER SYSTEM SET work_mem = '64MB';

-- Reload config
SELECT pg_reload_conf();
```

### Redis Optimization

**Set memory limits:**
```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Ollama Optimization

**Use GPU if available:**
```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**Choose appropriate model:**
- Production: `llama2` (good balance)
- High quality: `mixtral` (slower, requires more resources)
- Fast processing: `mistral` (slightly lower quality)

---

## Monitoring & Logging

### Application Logs

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

**Configure log rotation:**

Create `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Celery Monitoring with Flower

Access Flower at http://your-domain:5555

**Features:**
- Task monitoring
- Worker status
- Task history
- Resource usage

### System Monitoring

**Install monitoring tools:**
```bash
sudo apt install htop iotop nethogs
```

**Monitor resources:**
```bash
# CPU and memory
htop

# Disk I/O
iotop

# Network
nethogs
```

### Health Checks

**Automated health checks:**
```bash
#!/bin/bash
# healthcheck.sh

curl -f http://localhost:8000/api/v1/health/all || exit 1
```

**Add to cron:**
```bash
*/5 * * * * /path/to/healthcheck.sh
```

---

## Backup & Recovery

### Database Backup

**Manual backup:**
```bash
docker exec bookwhisperer_db pg_dump -U bookwhisperer bookwhisperer > backup.sql
```

**Automated daily backups:**
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

docker exec bookwhisperer_db pg_dump -U bookwhisperer bookwhisperer | gzip > "${BACKUP_DIR}/db_${DATE}.sql.gz"

# Keep only last 7 days
find ${BACKUP_DIR} -name "db_*.sql.gz" -mtime +7 -delete
```

**Add to cron:**
```bash
0 2 * * * /path/to/backup.sh
```

### Storage Backup

**Backup uploaded files:**
```bash
tar -czf storage_backup.tar.gz backend/storage/
```

**Sync to remote:**
```bash
rsync -avz backend/storage/ user@backup-server:/backups/bookwhisperer/
```

### Restore from Backup

**Restore database:**
```bash
gunzip < backup.sql.gz | docker exec -i bookwhisperer_db psql -U bookwhisperer bookwhisperer
```

**Restore files:**
```bash
tar -xzf storage_backup.tar.gz
```

---

## Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check logs
docker-compose logs backend

# Common causes:
# - Database not ready
# - Environment variables missing
# - Port already in use
```

**Celery worker not processing:**
```bash
# Check worker logs
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker
```

**Ollama connection failed:**
```bash
# Check if Ollama is running
docker-compose ps ollama

# Check if model is pulled
docker exec -it bookwhisperer_ollama ollama list

# Pull model if missing
docker exec -it bookwhisperer_ollama ollama pull llama2
```

**High memory usage:**
```bash
# Check container stats
docker stats

# Reduce Celery concurrency
# Reduce Redis maxmemory
# Use smaller Ollama model
```

**Database connection errors:**
```bash
# Check database logs
docker-compose logs db

# Test connection
docker exec -it bookwhisperer_db psql -U bookwhisperer
```

### Performance Issues

**Slow LLM processing:**
- Use GPU if available
- Reduce Celery concurrency to match resources
- Use faster model (llama2 vs mixtral)
- Increase server resources

**High disk usage:**
- Clean old backups
- Remove unused Docker images/volumes
- Implement log rotation
- Archive old books

### Emergency Recovery

**Complete restart:**
```bash
docker-compose down
docker-compose up -d
```

**Reset database (WARNING: DELETES ALL DATA):**
```bash
docker-compose down -v
docker-compose up -d
```

---

## Scaling Considerations

### Vertical Scaling

- Increase server CPU/RAM
- Add GPU for LLM processing
- Use faster storage (SSD/NVMe)
- Increase Celery workers

### Future Horizontal Scaling

- Separate database server
- Multiple Celery workers on different machines
- Load balancer for backend
- Distributed file storage (S3/MinIO)

---

## Maintenance Schedule

### Daily
- Monitor logs for errors
- Check disk space
- Verify all services running

### Weekly
- Review Flower for failed tasks
- Check database size
- Review backup logs

### Monthly
- Update Docker images
- Review and optimize queries
- Clean up old data
- Security updates

### Quarterly
- Full system backup test
- Performance review
- Capacity planning
- Security audit

---

## Support

For deployment issues:
- Check logs first
- Review this guide
- Search GitHub issues
- Create new issue with:
  - System specs
  - Error messages
  - Steps to reproduce

---

**Good luck with your deployment! 🚀**
