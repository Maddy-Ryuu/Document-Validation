#!/usr/bin/env bash
# AICTE Application Validation Platform - Render Build Script
set -e

echo "=== [1/2] Installing Python dependencies with CPU-only PyTorch index ==="
pip install -r backend/requirements.txt

echo "=== [2/2] Pre-provisioning EasyOCR model weights into storage/models/easyocr ==="
python backend/provision_models.py

echo "=== Build and model provisioning completed successfully ==="
