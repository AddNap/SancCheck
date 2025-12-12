#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uruchamianie nowoczesnej wersji GUI SancCheck
"""

import sys
import os
import subprocess
import importlib.util

# Dodaj ścieżkę src do PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def check_dependencies():
    """Sprawdza czy wszystkie wymagane pakiety są zainstalowane"""
    required_packages = [
        'requests',
        'lxml', 
        'reportlab',
        'pandas',
        'ttkbootstrap'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'ttkbootstrap':
                import ttkbootstrap
            else:
                importlib.import_module(package)
            print(f"✓ {package} - zainstalowane")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} - BRAK")
    
    return missing_packages

def install_package(package):
    """Instaluje pakiet używając pip"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Główna funkcja"""
    print("SancCheck - Sprawdzanie zależności...")
    print("=" * 50)
    
    # Sprawdź zależności
    missing = check_dependencies()
    
    if missing:
        print(f"\nBrakuje {len(missing)} pakietów:")
        for package in missing:
            print(f"  - {package}")
        
        print("\nCzy chcesz zainstalować brakujące pakiety? (t/n): ", end="")
        response = input().lower().strip()
        
        if response in ['t', 'tak', 'y', 'yes']:
            print("\nInstalowanie pakietów...")
            for package in missing:
                print(f"Instalowanie {package}...")
                if install_package(package):
                    print(f"✓ {package} zainstalowany")
                else:
                    print(f"✗ Błąd instalacji {package}")
                    sys.exit(1)
        else:
            print("Instalacja anulowana.")
            sys.exit(1)
    
    print("\n✓ Wszystkie wymagane pakiety są zainstalowane")
    print("Uruchamianie SancCheck...")
    print("=" * 50)
    
    # Uruchom nowoczesną wersję GUI
    try:
        from gui.crbr_gui_modern import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Błąd importu: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Błąd uruchamiania GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
