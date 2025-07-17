#!/bin/bash

# 診斷 Python 環境和套件安裝狀況

echo "=== Python 環境診斷 ==="
echo "Python 路徑: $(which python)"
echo "Python 版本: $(python --version)"
echo "Pip 路徑: $(which pip)"
echo "Pip 版本: $(pip --version)"

echo ""
echo "=== Python 路徑 ==="
python -c "import sys; print('Python 路徑:'); [print(p) for p in sys.path]"

echo ""
echo "=== 已安裝的套件 ==="
pip list

echo ""
echo "=== 檢查關鍵套件 ==="
echo "檢查 pandas:"
python -c "import pandas; print('pandas 版本:', pandas.__version__)" 2>/dev/null || echo "pandas 未安裝"

echo "檢查 numpy:"
python -c "import numpy; print('numpy 版本:', numpy.__version__)" 2>/dev/null || echo "numpy 未安裝"

echo "檢查 yaml:"
python -c "import yaml; print('yaml 已安裝')" 2>/dev/null || echo "yaml 未安裝"

echo "檢查 transformers:"
python -c "import transformers; print('transformers 版本:', transformers.__version__)" 2>/dev/null || echo "transformers 未安裝"

echo "檢查 crewai:"
python -c "import crewai; print('crewai 已安裝')" 2>/dev/null || echo "crewai 未安裝"

echo "檢查 pymilvus:"
python -c "import pymilvus; print('pymilvus 已安裝')" 2>/dev/null || echo "pymilvus 未安裝"

echo ""
echo "=== 環境變數 ==="
echo "PYTHONPATH: $PYTHONPATH"
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "PATH: $PATH" 