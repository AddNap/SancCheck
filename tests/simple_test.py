print("Starting simple test...")

try:
    import requests
    print("✅ Requests imported")
    
    import pandas as pd
    print("✅ Pandas imported")
    
    from bs4 import BeautifulSoup
    print("✅ BeautifulSoup imported")
    
    print("🔍 Testing basic request...")
    response = requests.get("https://httpbin.org/get", timeout=5)
    print(f"✅ Basic request works: {response.status_code}")
    
    print("🔍 Testing MF website...")
    url = "https://www.gov.pl/web/finanse/lista-osob-i-podmiotow-wobec-ktorych-stosuje-sie-szczegolne-srodki-ograniczajace-na-podstawie-art-118-ustawy-z-dnia-1-marca-2018-r-o-przeciwdzialaniu-praniu-pieniedzy-i-finansowaniu-terroryzmu"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, timeout=10, headers=headers)
    print(f"✅ MF website response: {response.status_code}")
    print(f"📏 Content length: {len(response.text)}")
    
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    print(f"🔗 Found {len(links)} links")
    
    # Look for Excel files
    excel_links = [a['href'] for a in links if any(ext in a['href'].lower() for ext in ['.xlsx', '.xls'])]
    print(f"📎 Found {len(excel_links)} Excel links")
    
    if not excel_links:
        print("⚠️  No Excel links found, creating mock data...")
        mock_data = {
            'Nazwa': ['Test 1', 'Test 2', 'Test 3'],
            'NIP': ['1234567890', '0987654321', '1122334455'],
            'Status': ['Aktywny', 'Aktywny', 'Nieaktywny']
        }
        df = pd.DataFrame(mock_data)
        print(f"✅ Created mock DataFrame with {len(df)} rows")
        print("📋 Columns:", list(df.columns))
        print("🔍 Sample data:")
        print(df.head())
    
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Script finished")
