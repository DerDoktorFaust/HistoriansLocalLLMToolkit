#!/bin/bash
set -e

rm -rf build dist HistoriansLocalLLMToolkit.spec

pyinstaller \
  --name HistoriansLocalLLMToolkit \
  --windowed \
  --onedir \
  --collect-all mlx \
  --icon assets/icon.icns \
  src/main.py
