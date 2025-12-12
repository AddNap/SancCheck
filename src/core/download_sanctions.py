#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania i zapisywania list sankcyjnych
"""

import os
import sys
import pandas as pd
from datetime import datetime
from .sanctions import get_mf_sanctions, get_mswia_sanctions, get_eu_sanctions

def save_sanctions_data():
    """Pobiera i zapisuje dane sankcyjne do plików"""
    
    # Utwórz katalog na dane sankcyjne
    sanctions_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sanctions')
    os.makedirs(sanctions_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("🚀 Rozpoczynam pobieranie i zapisywanie list sankcyjnych...")
    print(f"📁 Katalog docelowy: {sanctions_dir}")
    
    # Pobierz dane MF
    try:
        print("\n" + "="*50)
        print("📥 Pobieranie danych MF...")
        df_mf = get_mf_sanctions()
        
        # Zapisz dane MF
        mf_filename = f"mf_sanctions_{timestamp}.xlsx"
        mf_path = os.path.join(sanctions_dir, mf_filename)
        df_mf.to_excel(mf_path, index=False)
        print(f"✅ Zapisano dane MF: {mf_path}")
        print(f"📊 Liczba rekordów MF: {len(df_mf)}")
        
        # Zapisz też jako CSV
        mf_csv_filename = f"mf_sanctions_{timestamp}.csv"
        mf_csv_path = os.path.join(sanctions_dir, mf_csv_filename)
        df_mf.to_csv(mf_csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ Zapisano dane MF (CSV): {mf_csv_path}")
        
    except Exception as e:
        print(f"❌ Błąd przy pobieraniu danych MF: {e}")
        df_mf = None
    
    # Pobierz dane UE
    try:
        print("\n" + "="*50)
        print("📥 Pobieranie danych UE...")
        df_eu = get_eu_sanctions()
        
        # Zapisz dane UE
        eu_filename = f"eu_sanctions_{timestamp}.xlsx"
        eu_path = os.path.join(sanctions_dir, eu_filename)
        df_eu.to_excel(eu_path, index=False)
        print(f"✅ Zapisano dane UE: {eu_path}")
        print(f"📊 Liczba rekordów UE: {len(df_eu)}")
        
        # Zapisz też jako CSV
        eu_csv_filename = f"eu_sanctions_{timestamp}.csv"
        eu_csv_path = os.path.join(sanctions_dir, eu_csv_filename)
        df_eu.to_csv(eu_csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ Zapisano dane UE (CSV): {eu_csv_path}")
        
    except Exception as e:
        print(f"❌ Błąd przy pobieraniu danych UE: {e}")
        df_eu = None
    
    # Pobierz dane MSWiA
    try:
        print("\n" + "="*50)
        print("📥 Pobieranie danych MSWiA...")
        df_mswia = get_mswia_sanctions()
        
        # Zapisz dane MSWiA
        mswia_filename = f"mswia_sanctions_{timestamp}.xlsx"
        mswia_path = os.path.join(sanctions_dir, mswia_filename)
        df_mswia.to_excel(mswia_path, index=False)
        print(f"✅ Zapisano dane MSWiA: {mswia_path}")
        print(f"📊 Liczba rekordów MSWiA: {len(df_mswia)}")
        
        # Zapisz też jako CSV
        mswia_csv_filename = f"mswia_sanctions_{timestamp}.csv"
        mswia_csv_path = os.path.join(sanctions_dir, mswia_csv_filename)
        df_mswia.to_csv(mswia_csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ Zapisano dane MSWiA (CSV): {mswia_csv_path}")
        
    except Exception as e:
        print(f"❌ Błąd przy pobieraniu danych MSWiA: {e}")
        df_mswia = None

    print("\n" + "="*50)
    print("📋 PODSUMOWANIE:")
    
    if df_mf is not None:
        print(f"✅ MF: {len(df_mf)} rekordów zapisanych")
        print(f"   📄 Excel: {mf_filename}")
        print(f"   📄 CSV: {mf_csv_filename}")
    else:
        print("❌ MF: Błąd pobierania")
    
    if df_mswia is not None:
        print(f"✅ MSWiA: {len(df_mswia)} rekordów zapisanych")
        print(f"   📄 Excel: {mswia_filename}")
        print(f"   📄 CSV: {mswia_csv_filename}")
    else:
        print("❌ MSWiA: Błąd pobierania")
    
    if df_eu is not None:
        print(f"✅ UE: {len(df_eu)} rekordów zapisanych")
        print(f"   📄 Excel: {eu_filename}")
        print(f"   📄 CSV: {eu_csv_filename}")
    else:
        print("❌ UE: Błąd pobierania")
    
    print(f"\n📁 Wszystkie pliki zapisane w: {sanctions_dir}")
    
    return df_mf, df_mswia, df_eu

if __name__ == "__main__":
    save_sanctions_data()
