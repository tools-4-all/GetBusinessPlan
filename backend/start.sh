#!/bin/bash
# Script di avvio per Render
# Render userà questo se specificato, altrimenti userà il comando nel render.yaml

cd "$(dirname "$0")"
uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}
