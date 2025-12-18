# Setup Scripts

This directory contains utility scripts for setting up and configuring BookWhisperer services.

## setup_ollama.sh / setup_ollama.bat

Downloads and configures the Ollama LLM model for text formatting.

### Usage

**Linux/Mac:**
```bash
chmod +x setup_ollama.sh
./setup_ollama.sh
```

**Windows:**
```bash
setup_ollama.bat
```

### What it does

1. Waits for Ollama service to be ready (max 30 attempts, 2s intervals)
2. Checks if the configured model is already available
3. If not available, pulls the model from Ollama registry
4. Verifies successful installation

### Configuration

The script uses environment variables:
- `OLLAMA_URL` - Ollama service URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model to download (default: llama2)

### Example

```bash
# Use different model
export OLLAMA_MODEL=mistral
./setup_ollama.sh

# Use remote Ollama instance
export OLLAMA_URL=http://ollama.example.com:11434
./setup_ollama.sh
```

### Troubleshooting

**"Ollama service did not become ready in time"**
- Ensure Ollama container is running: `docker ps | grep ollama`
- Check Ollama logs: `docker logs bookwhisperer_ollama`
- Verify network connectivity to Ollama service

**"Failed to pull model"**
- Check internet connectivity
- Verify model name is correct: https://ollama.ai/library
- Check available disk space (models can be several GB)

### Available Models

Popular models for text formatting:

| Model | Size | Download Time* | Quality |
|-------|------|---------------|---------|
| llama2 | 3.8 GB | ~5-10 min | Good |
| llama2:13b | 7.4 GB | ~10-20 min | Better |
| mistral | 4.1 GB | ~5-10 min | Good |
| mixtral | 26 GB | ~30-60 min | Best |

*Approximate times on 50 Mbps connection

### Running in Docker

When using docker-compose, you can run the script from within the container:

```bash
# Linux/Mac
docker-compose exec backend bash -c "chmod +x scripts/setup_ollama.sh && scripts/setup_ollama.sh"

# Windows
docker-compose exec backend bash -c "scripts/setup_ollama.sh"
```

### First-Time Setup

On first installation:
1. Start services: `docker-compose up -d`
2. Wait for containers to be ready (~30 seconds)
3. Run setup script
4. Restart backend and celery worker: `docker-compose restart backend celery_worker`

The model persists in the `ollama_data` Docker volume, so you only need to run this once.
