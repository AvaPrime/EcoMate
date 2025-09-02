#!/usr/bin/env bash
set -euo pipefail
mkdir -p exports
for f in "$@"; do
  base=$(basename "$f" .md)
  pandoc "$f" -o "exports/${base}.docx"
done