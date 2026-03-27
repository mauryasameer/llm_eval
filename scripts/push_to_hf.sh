#!/bin/bash
# push_to_hf.sh — direct push to HuggingFace Space, bypassing GitHub Actions
# Usage: HF_TOKEN=hf_xxx bash scripts/push_to_hf.sh

set -e

if [ -z "$HF_TOKEN" ]; then
  echo "Error: HF_TOKEN is not set."
  echo "Usage: HF_TOKEN=hf_xxx bash scripts/push_to_hf.sh"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HF_SPACE_URL="https://mauryasameer:${HF_TOKEN}@huggingface.co/spaces/mauryasameer/llm-eval-v2"
DEPLOY_DIR="/tmp/hf_deploy_$(date +%s)"

echo "==> Cloning HuggingFace Space to $DEPLOY_DIR ..."
git clone "$HF_SPACE_URL" "$DEPLOY_DIR"

git config --global user.email "ci@github.com"
git config --global user.name "GitHub Actions"

echo "==> Wiping stale directories to prevent recursive nesting ..."
rm -rf "$DEPLOY_DIR/core" "$DEPLOY_DIR/configs" "$DEPLOY_DIR/data" "$DEPLOY_DIR/reports"

echo "==> Copying fresh source files ..."
cp -r "$REPO_ROOT/hf_space/." "$DEPLOY_DIR/"
cp -r "$REPO_ROOT/core"         "$DEPLOY_DIR/"
cp -r "$REPO_ROOT/configs"      "$DEPLOY_DIR/"
cp -r "$REPO_ROOT/data"         "$DEPLOY_DIR/"
mkdir -p "$DEPLOY_DIR/reports/templates" "$DEPLOY_DIR/reports/plots"
cp -r "$REPO_ROOT/reports/templates" "$DEPLOY_DIR/reports/"

echo "==> Committing and pushing to HuggingFace ..."
cd "$DEPLOY_DIR"
# Write a timestamp file so there's always a real file diff (HF ignores empty commits)
echo "Deploy: $(date +'%Y-%m-%d %H:%M:%S')" > deploy_timestamp.txt
git add -A
git commit -m "chore: direct sync from local $(date +'%Y-%m-%d %H:%M')"
git push

echo ""
echo "✅ Done! Your HuggingFace Space will rebuild in ~60 seconds."
echo "   Monitor: https://huggingface.co/spaces/mauryasameer/llm-eval"
