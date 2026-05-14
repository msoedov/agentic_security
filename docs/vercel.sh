set -ex

python3 --version

# Vercel's Python is uv-managed (PEP 668 externally-managed), so pip needs
# --break-system-packages. Safe here: the build container is ephemeral.
pip3 install --break-system-packages \
  mkdocs \
  mkdocs-material \
  mkdocs-jupyter \
  mkdocstrings-python
