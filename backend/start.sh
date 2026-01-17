#!/bin/bash
# Script di avvio per Render

uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}
