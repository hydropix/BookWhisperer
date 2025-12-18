#!/bin/bash

# Setup script for Ollama - pulls the required model

set -e

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-llama2}"

echo "============================================"
echo "Ollama Setup Script"
echo "============================================"
echo "Ollama URL: $OLLAMA_URL"
echo "Model to pull: $OLLAMA_MODEL"
echo ""

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi

    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - Ollama not ready yet, waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Ollama service did not become ready in time"
    exit 1
fi

# Check if model is already available
echo ""
echo "Checking if model '$OLLAMA_MODEL' is already available..."

if curl -s "$OLLAMA_URL/api/tags" | grep -q "\"name\":\"$OLLAMA_MODEL\""; then
    echo "Model '$OLLAMA_MODEL' is already available!"
    echo "Setup complete!"
    exit 0
fi

# Pull the model
echo ""
echo "Model '$OLLAMA_MODEL' not found. Pulling model..."
echo "This may take several minutes depending on model size..."
echo ""

curl -X POST "$OLLAMA_URL/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$OLLAMA_MODEL\"}" \
    || {
        echo "ERROR: Failed to pull model '$OLLAMA_MODEL'"
        exit 1
    }

echo ""
echo "============================================"
echo "Setup complete! Model '$OLLAMA_MODEL' is ready."
echo "============================================"
