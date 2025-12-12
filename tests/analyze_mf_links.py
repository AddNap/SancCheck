#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def analyze_mf_website():
    url = "https://www.gov.pl/web/finanse/lista-osob-i-podmiotow-wobec-ktorych-stosuje-sie-szczegolne-srodki-ograniczajace-na-podstawie-art-118-ustawy-z-dnia-1-marca-2018-r-o-przeciwdzialaniu-praniu-pieniedzy-i-finansowaniu-terroryzmu"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, timeout=15, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    print("🔍 Analizuję wszystkie linki na stronie MF...")
    
    # Get all links
    all_links = soup.find_all("a", href=True)
    
    # Categorize links
    categories = {
        'excel': [],
        'pdf': [],
        'doc': [],
        'download': [],
        'sankcje': [],
        'lista': [],
        'gov_pl': [],
        'external': [],
        'other': []
    }
    
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text().strip().lower()
        
        if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.excel']):
            categories['excel'].append((href, text))
        elif any(ext in href.lower() for ext in ['.pdf']):
            categories['pdf'].append((href, text))
        elif any(ext in href.lower() for ext in ['.doc', '.docx']):
            categories['doc'].append((href, text))
        elif 'download' in href.lower() or 'pobierz' in text:
            categories['download'].append((href, text))
        elif 'sankcje' in text or 'sankcje' in href.lower():
            categories['sankcje'].append((href, text))
        elif 'lista' in text or 'lista' in href.lower():
            categories['lista'].append((href, text))
        elif href.startswith('https://www.gov.pl') or href.startswith('/'):
            categories['gov_pl'].append((href, text))
        elif href.startswith('http'):
            categories['external'].append((href, text))
        else:
            categories['other'].append((href, text))
    
    # Print results
    for category, links in categories.items():
        if links:
            print(f"\n📂 {category.upper()} ({len(links)} linków):")
            for href, text in links[:10]:  # Show first 10
                print(f"  • {href} - '{text[:50]}'")
            if len(links) > 10:
                print(f"  ... i {len(links) - 10} więcej")
    
    # Look for specific patterns
    print("\n🔍 Szukam wzorców związanych z sankcjami...")
    
    # Check page content for keywords
    page_text = soup.get_text().lower()
    keywords = ['xlsx', 'excel', 'pobierz', 'download', 'lista', 'sankcje', 'sankcyjna']
    
    for keyword in keywords:
        if keyword in page_text:
            print(f"✅ Znaleziono słowo kluczowe: '{keyword}'")
        else:
            print(f"❌ Brak słowa kluczowego: '{keyword}'")
    
    # Check for any downloadable content
    print("\n📎 Sprawdzam potencjalne pliki do pobrania...")
    
    # Look for download buttons or file references
    download_elements = soup.find_all(['a', 'button', 'div'], 
                                    text=lambda x: x and any(word in x.lower() for word in ['pobierz', 'download', 'pobieranie']))
    
    if download_elements:
        print("✅ Znaleziono elementy pobierania:")
        for elem in download_elements:
            print(f"  • {elem.name}: {elem.get_text().strip()}")
    else:
        print("❌ Nie znaleziono elementów pobierania")

if __name__ == "__main__":
    analyze_mf_website()
