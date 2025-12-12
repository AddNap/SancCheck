#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt uruchamiający SancCheck GUI z sprawdzeniem zależności
"""

import sys
import subprocess
import importlib

def check_dependencies():
    """Sprawdza czy wszystkie wymagane biblioteki są zainstalowane"""
    required_packages = [
        'requests',
        'lxml', 
        'reportlab',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} - zainstalowane")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} - brakuje")
    
    if missing_packages:
        print(f"\nBrakujące pakiety: {', '.join(missing_packages)}")
        print("Zainstaluj je poleceniem:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("\n✓ Wszystkie wymagane pakiety są zainstalowane")
    return True

def main():
    """Główna funkcja"""
    # Ustawienia UTF-8
    from utils.utf8_config import setup_utf8
    setup_utf8()
    
    print("SancCheck - Sprawdzanie zależności...")
    print("=" * 50)
    
    if not check_dependencies():
        print("\nNie można uruchomić aplikacji - brakuje wymaganych pakietów.")
        input("Naciśnij Enter aby zakończyć...")
        sys.exit(1)
    
    print("\nUruchamianie SancCheck...")
    print("=" * 50)
    
    try:
        # Import i uruchomienie GUI
        from gui.crbr_gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"Błąd podczas uruchamiania GUI: {e}")
        input("Naciśnij Enter aby zakończyć...")
        sys.exit(1)

if __name__ == "__main__":
    main()
