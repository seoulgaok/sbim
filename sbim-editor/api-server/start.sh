#!/bin/bash
# SBIM Editor API 서버 시작 스크립트
cd "$(dirname "$0")"

# venv가 없으면 생성
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

echo "Starting SBIM Editor API on http://localhost:8765"
.venv/bin/python main.py
