#!/usr/bin/env bash
# Vercel build command for the MkDocs site.
# Set Vercel "Build Command" to: bash docs/vercel.sh
# Set Vercel "Output Directory" to: site
set -euo pipefail

python3 --version

pip3 install --upgrade pip
pip3 install \
  mkdocs \
  mkdocs-material \
  mkdocs-jupyter \
  mkdocstrings-python

mkdocs build --site-dir site
