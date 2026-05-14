set -ex

python3 --version

pip3 install --upgrade pip
pip3 install \
  mkdocs \
  mkdocs-material \
  mkdocs-jupyter \
  mkdocstrings-python
