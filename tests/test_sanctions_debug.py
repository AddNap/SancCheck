#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup
import time

def test_mf_website():
    """Test function to debug MF website access"""
    url = "https://www.gov.pl/web/finanse/lista-osob-i-podmiotow-wobec-ktorych-stosuje-sie-szczegolne-srodki-ograniczajace-na-podstawie-art-118-ustawy-z-dnia-1-marca-2018-r-o-przeciwdzialaniu-praniu-pieniedzy-i-finansowaniu-terroryzmu"
    
    print("🔍 Testuję dostęp do strony MF...")
    print(f"URL: {url}")
    
    try:
        print("📡 Wysyłam żądanie HTTP...")
        start_time = time.time()
        
        # Test with shorter timeout first
        page = requests.get(url, timeout=10)
        
        end_time = time.time()
        print(f"⏱️  Czas odpowiedzi: {end_time - start_time:.2f} sekund")
        print(f"📊 Status HTTP: {page.status_code}")
        print(f"📏 Rozmiar odpowiedzi: {len(page.text)} znaków")
        
        if page.status_code == 200:
            print("✅ Strona załadowana pomyślnie")
            
            soup = BeautifulSoup(page.text, "html.parser")
            all_links = soup.find_all("a", href=True)
            print(f"🔗 Znaleziono {len(all_links)} linków na stronie")
            
            # Look for Excel files
            excel_links = []
            for a in all_links:
                href = a.get('href', '')
                if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.excel']):
                    excel_links.append(href)
                    print(f"📎 Link Excel: {href}")
            
            if excel_links:
                print(f"✅ Znaleziono {len(excel_links)} linków do plików Excel")
                return excel_links[0]
            else:
                print("⚠️  Nie znaleziono linków do plików Excel")
                
                # Show first 10 links for debugging
                print("🔍 Pierwsze 10 linków na stronie:")
                for i, a in enumerate(all_links[:10]):
                    href = a.get('href', '')
                    text = a.get_text().strip()[:50]
                    print(f"  {i+1}. {href} - '{text}'")
                
                return None
        else:
            print(f"❌ Błąd HTTP: {page.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout - strona nie odpowiada w ciągu 10 sekund")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"🌐 Błąd połączenia: {e}")
        return None
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Rozpoczynam test debugowania...")
    result = test_mf_website()
    
    if result:
        print(f"✅ Test zakończony pomyślnie. Znaleziony link: {result}")
    else:
        print("❌ Test nie znalazł odpowiedniego linku")
