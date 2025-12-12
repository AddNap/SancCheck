#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("🚀 Test rozpoczęty")

try:
    import requests
    print("✅ Moduł requests załadowany")
    
    import pandas as pd
    print("✅ Moduł pandas załadowany")
    
    from bs4 import BeautifulSoup
    print("✅ Moduł BeautifulSoup załadowany")
    
    print("🔍 Testuję prostą stronę...")
    response = requests.get("https://httpbin.org/get", timeout=10)
    print(f"✅ Prosta strona działa: {response.status_code}")
    
    print("🔍 Testuję stronę MF...")
    url = "https://www.gov.pl/web/finanse/lista-osob-i-podmiotow-wobec-ktorych-stosuje-sie-szczegolne-srodki-ograniczajace-na-podstawie-art-118-ustawy-z-dnia-1-marca-2018-r-o-przeciwdzialaniu-praniu-pieniedzy-i-finansowaniu-terroryzmu"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, timeout=15, headers=headers)
    print(f"✅ Strona MF odpowiedziała: {response.status_code}")
    print(f"📏 Rozmiar: {len(response.text)} znaków")
    
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    print(f"🔗 Znaleziono {len(links)} linków")
    
    excel_links = [a['href'] for a in links if any(ext in a['href'].lower() for ext in ['.xlsx', '.xls'])]
    print(f"📎 Znaleziono {len(excel_links)} linków Excel")
    
    if excel_links:
        print("✅ Linki Excel:", excel_links[:3])
    else:
        print("⚠️  Brak linków Excel")
        print("🔍 Pierwsze 5 linków:")
        for i, link in enumerate(links[:5]):
            print(f"  {i+1}. {link['href']}")
    
except Exception as e:
    print(f"❌ Błąd: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Test zakończony")
