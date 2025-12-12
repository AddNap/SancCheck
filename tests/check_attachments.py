#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def check_attachments():
    base_url = "https://www.gov.pl"
    attachments = [
        "/attachment/2fc03b3b-a5f6-4d08-80d1-728cdb71d2d6",
        "/attachment/56238b34-8a26-4431-a05a-e1d039f0defa"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attachment in attachments:
        url = base_url + attachment
        print(f"\n🔍 Sprawdzam załącznik: {url}")
        
        try:
            response = requests.get(url, timeout=15, headers=headers)
            print(f"📊 Status: {response.status_code}")
            print(f"📏 Rozmiar: {len(response.content)} bajtów")
            print(f"📋 Content-Type: {response.headers.get('content-type', 'Nieznany')}")
            
            # Check if it's a file download
            content_disposition = response.headers.get('content-disposition', '')
            if content_disposition:
                print(f"📎 Content-Disposition: {content_disposition}")
            
            # If it's HTML, parse it to look for download links
            if 'text/html' in response.headers.get('content-type', ''):
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.find_all("a", href=True)
                print(f"🔗 Znaleziono {len(links)} linków w załączniku")
                
                for link in links[:5]:  # Show first 5 links
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    print(f"  • {href} - '{text[:50]}'")
            
            # Check if content looks like a file
            if len(response.content) > 1000:  # Likely a file
                print("📄 To prawdopodobnie plik do pobrania")
                
                # Try to determine file type from content
                content_start = response.content[:100]
                if b'PK' in content_start:
                    print("📦 To prawdopodobnie plik ZIP/Excel")
                elif b'%PDF' in content_start:
                    print("📄 To prawdopodobnie plik PDF")
                elif b'<!DOCTYPE' in content_start or b'<html' in content_start:
                    print("🌐 To strona HTML")
                else:
                    print("❓ Nieznany typ pliku")
            
        except Exception as e:
            print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    check_attachments()
