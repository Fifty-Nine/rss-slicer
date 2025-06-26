#!/bin/bash
python -m venv --upgrade-deps --prompt="rss-slicer" ./.venv
source ./.venv/bin/activate
poetry install -n