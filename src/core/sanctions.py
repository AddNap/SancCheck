import requests
import pandas as pd
from io import BytesIO
from bs4 import BeautifulSoup

# 1. Pobieranie najnowszego XLSX z listą sankcyjną MF
def get_mf_sanctions():
    url = "https://www.gov.pl/web/finanse/lista-osob-i-podmiotow-wobec-ktorych-stosuje-sie-szczegolne-srodki-ograniczajace-na-podstawie-art-118-ustawy-z-dnia-1-marca-2018-r-o-przeciwdzialaniu-praniu-pieniedzy-i-finansowaniu-terroryzmu"
    
    try:
        print("🔍 Sprawdzam stronę MF:", url)
        print("⏳ Wysyłam żądanie HTTP (może potrwać do 30 sekund)...")
        
        # Add user agent to avoid potential blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        page = requests.get(url, timeout=30, headers=headers)
        page.raise_for_status()
        print("✅ Strona załadowana pomyślnie")
        
        soup = BeautifulSoup(page.text, "html.parser")
        
        # Debug: sprawdź wszystkie linki na stronie
        all_links = soup.find_all("a", href=True)
        print(f"📊 Znaleziono {len(all_links)} linków na stronie")
        
        # Szukamy linków do plików Excel/XLSX
        excel_links = []
        for a in all_links:
            href = a.get('href', '')
            if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.excel']):
                excel_links.append(href)
                print(f"📎 Znaleziono link Excel: {href}")
        
        # Jeśli nie ma bezpośrednich linków .xlsx, szukaj innych formatów
        if not excel_links:
            print("⚠️  Nie znaleziono bezpośrednich linków Excel, szukam alternatyw...")
            
            # Szukaj linków zawierających słowa kluczowe
            keywords = ['sankcje', 'lista', 'xlsx', 'excel', 'download', 'pobierz']
            for a in all_links:
                href = a.get('href', '')
                text = a.get_text().lower()
                if any(keyword in text or keyword in href.lower() for keyword in keywords):
                    print(f"🔗 Potencjalny link: {href} (tekst: {text[:50]}...)")
        
        # Wybierz pierwszy znaleziony link Excel
        link = excel_links[0] if excel_links else None
        
        if not link:
            # Spróbuj alternatywnych źródeł
            print("🔄 Próbuję alternatywnych źródeł...")
            alternative_urls = [
                "https://www.gov.pl/web/finanse/sankcje",
                "https://www.gov.pl/web/finanse/lista-sankcji",
                "https://www.gov.pl/web/finanse/lista-osob-i-podmiotow"
            ]
            
            for alt_url in alternative_urls:
                try:
                    print(f"🔍 Sprawdzam alternatywną stronę: {alt_url}")
                    alt_page = requests.get(alt_url, timeout=30, headers=headers)
                    alt_soup = BeautifulSoup(alt_page.text, "html.parser")
                    
                    for a in alt_soup.find_all("a", href=True):
                        href = a.get('href', '')
                        if any(ext in href.lower() for ext in ['.xlsx', '.xls']):
                            link = href
                            print(f"✅ Znaleziono link na alternatywnej stronie: {link}")
                            break
                    
                    if link:
                        break
                except Exception as e:
                    print(f"❌ Błąd przy sprawdzaniu {alt_url}: {e}")
                    continue
        
        if not link:
            print("⚠️  Nie znaleziono linku do pliku XLSX na żadnej ze stron MF")
            print("🔍 Sprawdzam załączniki na stronie...")
            
            # Check for attachment links that might contain the data
            attachment_links = []
            for a in all_links:
                href = a.get('href', '')
                text = a.get_text().strip().lower()
                if '/attachment/' in href and ('lista' in text or 'sankcje' in text):
                    attachment_links.append(href)
                    print(f"📎 Znaleziono załącznik: {href}")
            
            if attachment_links:
                print(f"🔄 Próbuję pobrać dane z załączników...")
                for attachment_url in attachment_links:
                    try:
                        if attachment_url.startswith("/"):
                            attachment_url = "https://www.gov.pl" + attachment_url
                        
                        print(f"📥 Pobieram załącznik: {attachment_url}")
                        response = requests.get(attachment_url, timeout=30, headers=headers)
                        response.raise_for_status()
                        
                        # Check content type first
                        content_type = response.headers.get('Content-Type', '').lower()
                        print(f"📊 Content-Type: {content_type}")
                        
                        # Try to read as Excel
                        if 'excel' in content_type or 'spreadsheet' in content_type or response.content.startswith(b'PK'):
                            try:
                                import pandas as pd
                                df_mf = pd.read_excel(BytesIO(response.content))
                                print(f"✅ Pomyślnie pobrano {len(df_mf)} rekordów z załącznika Excel")
                                print(f"📋 Kolumny: {list(df_mf.columns)}")
                                return df_mf
                            except Exception as excel_error:
                                print(f"❌ Błąd odczytu Excel: {excel_error}")
                                continue
                        else:
                            print(f"⚠️  Załącznik nie jest plikiem Excel (Content-Type: {content_type})")
                            continue
                    except Exception as e:
                        print(f"❌ Błąd przy pobieraniu załącznika: {e}")
                        continue
            
            raise Exception("Nie znaleziono linku do pliku XLSX na żadnej ze stron MF")
        
        # Czasem link jest względny, dodaj domenę
        if link.startswith("/"):
            link = "https://www.gov.pl" + link
        elif not link.startswith("http"):
            link = "https://www.gov.pl" + "/" + link
        
        print("📥 Pobieram plik MF:", link)
        response = requests.get(link, timeout=60, headers=headers)
        response.raise_for_status()
        
        df_mf = pd.read_excel(BytesIO(response.content))
        print(f"✅ Pomyślnie pobrano {len(df_mf)} rekordów z MF")
        return df_mf
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Błąd połączenia z serwerem MF: {e}")
    except pd.errors.ExcelFileError as e:
        raise Exception(f"Błąd odczytu pliku Excel: {e}")
    except Exception as e:
        raise Exception(f"Nieoczekiwany błąd: {e}")


# 2. Pobieranie listy sankcyjnej MSWiA
def get_mswia_sanctions():
    mswia_url = "https://www.gov.pl/web/mswia/lista-osob-i-podmiotow-objetych-sankcjami"
    
    try:
        print("🔍 Sprawdzam stronę MSWiA:", mswia_url)
        print("⏳ Wysyłam żądanie HTTP (może potrwać do 30 sekund)...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        page = requests.get(mswia_url, timeout=30, headers=headers)
        page.raise_for_status()
        print("✅ Strona MSWiA załadowana pomyślnie")
        
        soup = BeautifulSoup(page.text, "html.parser")
        
        # Znajdź wszystkie linki na stronie
        all_links = soup.find_all("a", href=True)
        print(f"📊 Znaleziono {len(all_links)} linków na stronie MSWiA")
        
        # Szukamy linków do plików Excel/XLSX - szczególnie w sekcji "Materiały"
        excel_links = []
        
        # Najpierw szukaj bezpośrednich linków .xlsx
        for a in all_links:
            href = a.get('href', '')
            text = a.get_text().strip().lower()
            if any(ext in href.lower() for ext in ['.xlsx', '.xls', '.excel']):
                excel_links.append((href, text))
                print(f"📎 Znaleziono link Excel MSWiA: {href}")
        
        # Jeśli nie ma bezpośrednich linków, szukaj w sekcji "Materiały" lub linków z tekstem o sankcjach
        if not excel_links:
            print("⚠️  Nie znaleziono bezpośrednich linków Excel, szukam w sekcji Materiały...")
            
            # Szukaj linków zawierających słowa kluczowe związane z sankcjami
            keywords = ['sankcje', 'lista', 'tabela', 'xlsx', 'excel', 'download', 'pobierz', 'attachment', 'materiały']
            for a in all_links:
                href = a.get('href', '')
                text = a.get_text().strip().lower()
                
                # Sprawdź czy link zawiera słowa kluczowe lub jest w sekcji materiałów
                if any(keyword in text or keyword in href.lower() for keyword in keywords):
                    print(f"🔗 Potencjalny link MSWiA: {href} (tekst: '{text[:50]}...')")
                    
                    # Dodaj link jeśli to plik Excel lub załącznik
                    if any(ext in href.lower() for ext in ['.xlsx', '.xls']) or '/attachment/' in href:
                        excel_links.append((href, text))
                        print(f"✅ Dodano link Excel: {href}")
        
        # Jeśli nadal nie ma linków, spróbuj znaleźć linki z konkretnym wzorcem nazwy pliku
        if not excel_links:
            print("⚠️  Szukam linków z wzorcem nazwy pliku sankcyjnego...")
            for a in all_links:
                href = a.get('href', '')
                text = a.get_text().strip().lower()
                
                # Szukaj linków z wzorcem "tabela_lista_sankcyjna" lub podobnym
                if ('tabela' in text and 'sankcyjna' in text) or 'lista_sankcyjna' in href.lower():
                    print(f"🔗 Znaleziono link z wzorcem sankcyjnym: {href} (tekst: '{text[:50]}...')")
                    excel_links.append((href, text))
                    break
        
        # Wybierz link z listą sankcyjną (preferuj linki z tekstem "lista sankcyjna" lub "tabela_lista")
        link = None
        if excel_links:
            # Szukaj linku z tekstem "lista sankcyjna" lub "tabela_lista"
            for potential_link, potential_text in excel_links:
                # Sprawdź czy tekst zawiera słowa kluczowe związane z listą sankcyjną
                if any(keyword in potential_text for keyword in ['lista sankcyjna', 'tabela_lista', 'lista', 'sankcyjna', 'tabela']):
                    link = potential_link
                    print(f"✅ Wybrano link z listą sankcyjną: {link} (tekst: '{potential_text[:50]}...')")
                    break
            
            # Jeśli nie znaleziono linku z listą sankcyjną, wybierz pierwszy dostępny
            if not link:
                link, text = excel_links[0]
                print(f"⚠️  Wybrano pierwszy dostępny link: {link} (tekst: '{text[:50]}...')")
        
        if not link:
            raise Exception("Nie znaleziono linku do pliku XLSX na stronie MSWiA")
        
        # Czasem link jest względny, dodaj domenę
        if link.startswith("/"):
            link = "https://www.gov.pl" + link
        elif not link.startswith("http"):
            link = "https://www.gov.pl" + "/" + link
        
        print("📥 Pobieram plik MSWiA:", link)
        response = requests.get(link, timeout=60, headers=headers)
        response.raise_for_status()
        
        # Check content type first
        content_type = response.headers.get('Content-Type', '').lower()
        print(f"📊 Content-Type: {content_type}")
        
        # Try to read as Excel
        if 'excel' in content_type or 'spreadsheet' in content_type or response.content.startswith(b'PK'):
            try:
                import pandas as pd
                df_mswia = pd.read_excel(BytesIO(response.content))
                print(f"✅ Pomyślnie pobrano {len(df_mswia)} rekordów z MSWiA")
                print(f"📋 Kolumny: {list(df_mswia.columns)}")
                return df_mswia
            except Exception as excel_error:
                print(f"❌ Błąd odczytu Excel MSWiA: {excel_error}")
                raise
        else:
            print(f"⚠️  Plik MSWiA nie jest plikiem Excel (Content-Type: {content_type})")
            raise Exception(f"Nieoczekiwany typ pliku: {content_type}")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Błąd połączenia z serwerem MSWiA: {e}")
        
    except Exception as e:
        raise Exception(f"Nieoczekiwany błąd przy pobieraniu danych MSWiA: {e}")


# 3. Pobieranie listy sankcyjnej UE (CSV z portalu data.europa.eu)
def get_eu_sanctions():
    eu_url = "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList/content?token=dummy"
    
    try:
        print("📥 Pobieram listę UE:", eu_url)
        response = requests.get(eu_url, timeout=60)
        response.raise_for_status()
        
        df_eu = pd.read_csv(BytesIO(response.content), sep=";")
        print(f"✅ Pomyślnie pobrano {len(df_eu)} rekordów z UE")
        return df_eu
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Błąd połączenia z serwerem UE: {e}")
        
    except pd.errors.ParserError as e:
        raise Exception(f"Błąd parsowania pliku CSV UE: {e}")
        
    except Exception as e:
        raise Exception(f"Nieoczekiwany błąd przy pobieraniu danych UE: {e}")


