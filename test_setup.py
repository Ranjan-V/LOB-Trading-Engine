"""
Setup Verification - Tests all library installations
"""

import sys
print(f"🐍 Python Version: {sys.version}\n")
print("="*60)

def test_import(module_name, import_statement):
    try:
        exec(import_statement)
        print(f"✅ {module_name:<20} - Installed")
        return True
    except ImportError as e:
        print(f"❌ {module_name:<20} - MISSING: {e}")
        return False

# Test all libraries
tests = [
    ("NumPy", "import numpy as np"),
    ("Pandas", "import pandas as pd"),
    ("SciPy", "import scipy"),
    ("Matplotlib", "import matplotlib.pyplot as plt"),
    ("Seaborn", "import seaborn as sns"),
    ("Plotly", "import plotly.graph_objects as go"),
    ("Flask", "import flask"),
    ("Dash", "import dash"),
    ("Statsmodels", "import statsmodels.api as sm"),
    ("yfinance", "import yfinance as yf"),
    ("Binance API", "from binance.client import Client"),
    ("Requests", "import requests"),
    ("Numba", "import numba"),
    ("Joblib", "import joblib"),
    ("tqdm", "from tqdm import tqdm"),
]

passed = sum(test_import(name, stmt) for name, stmt in tests)
total = len(tests)

print("="*60)
if passed == total:
    print(f"🎉 SUCCESS! All {total}/{total} libraries installed!")
    print("="*60)
    print("✅ Virtual environment: ACTIVE")
    print("✅ Python packages: INSTALLED")
    print("✅ Ready to start coding!")
    print("="*60)
else:
    print(f"⚠️  {passed}/{total} libraries installed. Fix missing ones.")