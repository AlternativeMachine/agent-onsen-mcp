#!/usr/bin/env bash
set -euo pipefail
uvicorn app.mcp_server:app --host 0.0.0.0 --port "${PORT:-8001}"
