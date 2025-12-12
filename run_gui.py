#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt uruchamiający SancCheck GUI z sprawdzeniem zależności
"""

import sys
import os

# Dodaj ścieżkę src do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import i uruchomienie
from src.run_gui import main

if __name__ == "__main__":
    main()
