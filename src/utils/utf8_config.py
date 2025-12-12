#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfiguracja UTF-8 dla aplikacji CRBR
"""

import sys
import os
import locale

def setup_utf8():
    """Konfiguruje UTF-8 dla aplikacji"""
    
    # Ustaw kodowanie dla Windows
    if os.name == 'nt':
        try:
            os.system('chcp 65001 > nul')
        except:
            pass
    
    # Ustaw kodowanie dla stdout/stderr
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    
    # Ustaw locale
    try:
        locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Polish_Poland.1250')
        except:
            pass
    
    # Ustaw zmienne środowiskowe
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'pl_PL.UTF-8'
    os.environ['LC_ALL'] = 'pl_PL.UTF-8'

def get_utf8_encoding():
    """Zwraca kodowanie UTF-8"""
    return 'utf-8'

def get_csv_encoding():
    """Zwraca kodowanie dla plików CSV"""
    return 'utf-8'

def get_xml_encoding():
    """Zwraca kodowanie dla plików XML"""
    return 'utf-8'

if __name__ == "__main__":
    setup_utf8()
    print("✓ Konfiguracja UTF-8 została ustawiona")
    print(f"✓ Kodowanie stdout: {sys.stdout.encoding}")
    print(f"✓ Kodowanie stderr: {sys.stderr.encoding}")
    print(f"✓ Locale: {locale.getlocale()}")
