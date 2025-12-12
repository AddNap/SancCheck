# SancCheck

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)

**SancCheck** to zaawansowana aplikacja do generowania raportów PDF z danych Centralnego Rejestru Beneficjentów Rzeczywistych (CRBR) z automatyczną weryfikacją list sankcyjnych. Aplikacja umożliwia szybką weryfikację kontrahentów pod kątem sankcji oraz generowanie profesjonalnych raportów PDF.

## 📋 Spis treści

- [Funkcje](#-funkcje)
- [Wymagania](#-wymagania)
- [Instalacja](#-instalacja)
- [Uruchamianie](#-uruchamianie)
- [Użytkowanie](#-użytkowanie)
- [Struktura projektu](#-struktura-projektu)
- [Dokumentacja](#-dokumentacja)
- [Rozwój](#-rozwój)
- [Licencja](#-licencja)
- [Wsparcie](#-wsparcie)

## ✨ Funkcje

### 🔍 Weryfikacja sankcji
- **Automatyczna weryfikacja** kontrahentów na listach sankcyjnych:
  - Lista sankcyjna Ministerstwa Finansów (MF)
  - Lista sankcyjna Ministerstwa Spraw Wewnętrznych i Administracji (MSWiA)
  - Lista sankcyjna Unii Europejskiej (UE)
- **Wykrywanie słów kluczowych** sugerujących wykluczenie z postępowania (art. 7 ust. 1 ustawy o przeciwdziałaniu wspieraniu agresji na Ukrainę)
- **Automatyczna aktualizacja** list sankcyjnych z oficjalnych źródeł

### 📄 Generowanie raportów PDF
- **Automatyczne generowanie** raportów PDF z danych CRBR
- **Szczegółowe informacje** o beneficjentach rzeczywistych
- **Oznaczenia sankcyjne** w raportach (kolorowe oznaczenia, ostrzeżenia)
- **Profesjonalny layout** z tabelami i formatowaniem

### 🎨 Interfejs użytkownika
- **Nowoczesny GUI** z biblioteką ttkbootstrap (wielokrotne motywy)
- **Podstawowy GUI** dla prostszych zastosowań
- **Drag & Drop** - przeciąganie plików CSV bezpośrednio do aplikacji
- **Pasek postępu** z wizualizacją przetwarzania
- **Logi w czasie rzeczywistym** z poziomami ważności

### 📊 Zarządzanie danymi
- **Import z CSV/Excel** - masowe importowanie NIP-ów
- **Eksport wyników** do plików tekstowych
- **Walidacja NIP** - automatyczna walidacja numerów NIP
- **Zarządzanie listą** - dodawanie, usuwanie, czyszczenie NIP-ów

### 🔧 Funkcje zaawansowane
- **Wielowątkowość** - równoległe przetwarzanie wielu NIP-ów
- **Retry mechanism** - automatyczne ponawianie nieudanych żądań
- **Timeout handling** - konfigurowalne limity czasu
- **Logowanie** - szczegółowe logi operacji do plików
- **Obsługa polskich znaków** - pełne wsparcie UTF-8

## 📦 Wymagania

### Systemowe
- **Python 3.8+** (zalecane 3.10+)
- **System operacyjny**: Windows, Linux, macOS

### Biblioteki Python
Wszystkie wymagane biblioteki są wymienione w pliku `requirements.txt`:

- `requests>=2.31.0` - komunikacja z API CRBR
- `lxml>=4.9.0` - parsowanie XML
- `reportlab>=4.0.0` - generowanie PDF
- `pandas>=2.0.0` - przetwarzanie danych
- `ttkbootstrap>=1.10.0` - nowoczesny interfejs GUI (opcjonalne)

## 🚀 Instalacja

### 1. Sklonuj repozytorium

```bash
git clone https://github.com/AddNap/SancCheck.git
cd SancCheck
```

### 2. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 3. (Opcjonalnie) Utwórz środowisko wirtualne

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Następnie zainstaluj zależności
pip install -r requirements.txt
```

## 🎯 Uruchamianie

### Nowoczesny GUI (zalecany)

```bash
python run_modern_gui.py
```

Nowoczesny interfejs z:
- Wieloma motywami (flatly, darkly, cosmo, itp.)
- Drag & Drop
- Kolorowymi przyciskami
- Paskiem postępu
- Tooltips

### Podstawowy GUI

```bash
python run_gui.py
```

Prostszy interfejs oparty na standardowym tkinter.

### Tryb konsolowy

```bash
python src/core/crbr_bulk_to_pdf.py --nip 1234567890 --out data/output_pdfs
```

## 📖 Użytkowanie

### 1. Dodawanie NIP-ów do weryfikacji

**Metoda 1: Ręczne dodawanie**
- Wpisz NIP w pole tekstowe (10 cyfr)
- Kliknij "Dodaj NIP" lub naciśnij Enter

**Metoda 2: Import z pliku**
- Kliknij "Import CSV" lub przeciągnij plik CSV do okna
- Plik CSV powinien zawierać kolumnę 'nip' lub 'NIP'
- Aplikacja automatycznie wyczyści i zwaliduje NIP-y

**Metoda 3: Drag & Drop**
- Przeciągnij plik CSV bezpośrednio do okna aplikacji
- Plik zostanie automatycznie zaimportowany

### 2. Konfiguracja

- **Katalog wyjściowy**: Wybierz folder, gdzie będą zapisywane pliki PDF
- **Timeout**: Ustaw czas oczekiwania na odpowiedź serwera (domyślnie 30s)
- **Zakres dat**: Określ zakres dat dla weryfikacji (opcjonalne)

### 3. Generowanie raportów

1. Kliknij "Generuj raporty PDF"
2. Aplikacja będzie przetwarzać NIP-y jeden po drugim
3. Postęp jest wyświetlany na pasku postępu i w logach
4. Po zakończeniu możesz otworzyć pliki PDF dwukrotnym kliknięciem

### 4. Weryfikacja sankcji

- Aplikacja automatycznie sprawdza każdy NIP na listach sankcyjnych
- Znalezione dopasowania są oznaczone w raporcie PDF
- Ostrzeżenia są wyświetlane w interfejsie i logach

### 5. Eksport wyników

- Kliknij "Eksport" aby zapisać wyniki do pliku tekstowego
- Plik zawiera listę wszystkich przetworzonych NIP-ów ze statusami

## 📁 Struktura projektu

```
SancCheck/
├── src/                          # Kod źródłowy aplikacji
│   ├── gui/                      # Interfejsy użytkownika
│   │   ├── crbr_gui.py          # Podstawowy GUI (tkinter)
│   │   └── crbr_gui_modern.py   # Nowoczesny GUI (ttkbootstrap)
│   ├── core/                     # Logika biznesowa
│   │   ├── crbr_bulk_to_pdf.py  # Główny moduł generowania PDF
│   │   ├── sanctions.py         # Moduł weryfikacji sankcji
│   │   └── download_sanctions.py # Pobieranie list sankcyjnych
│   ├── utils/                    # Moduły pomocnicze
│   │   ├── logger_config.py     # Konfiguracja logowania
│   │   ├── nip_validator.py     # Walidacja NIP
│   │   ├── pdf_table_helpers.py # Pomocnicze funkcje PDF
│   │   ├── utf8_config.py       # Konfiguracja UTF-8
│   │   └── xml_parsing_helpers.py # Parsowanie XML
│   ├── run_gui.py               # Uruchamianie podstawowego GUI
│   └── run_modern_gui.py        # Uruchamianie nowoczesnego GUI
├── tests/                        # Pliki testowe
│   ├── test_nip_validator.py    # Testy walidacji NIP
│   ├── test_crbr_parsing.py     # Testy parsowania CRBR
│   └── ...
├── docs/                         # Dokumentacja
│   ├── api/                     # Dokumentacja API CRBR
│   └── readme/                  # Dodatkowe pliki README
├── data/                         # Dane i pliki wyjściowe
│   ├── output_pdfs/            # Wygenerowane pliki PDF
│   ├── sanctions/               # Listy sankcyjne (CSV, JSON)
│   ├── sanctions_reports/       # Raporty sankcyjne (HTML)
│   ├── test_*/                  # Dane testowe
│   └── test_docs/               # Pliki testowe dokumentacji
├── config/                       # Pliki konfiguracyjne
│   └── exclusion_keywords.txt  # Słowa kluczowe wykluczeń
├── temp/                         # Pliki tymczasowe
├── requirements.txt             # Zależności Python
├── LICENSE                      # Licencja Apache 2.0
├── run_gui.py                   # Wrapper podstawowego GUI
└── run_modern_gui.py            # Wrapper nowoczesnego GUI
```

## 📚 Dokumentacja

Szczegółowa dokumentacja znajduje się w folderze `docs/`:

- **`docs/api/`** - Dokumentacja API CRBR
  - Specyfikacja API
  - Przykłady użycia
  - Opis endpointów

- **`docs/readme/`** - Dodatkowe pliki README
  - `README_GUI.md` - Opis interfejsu użytkownika
  - `README_MODERN_GUI.md` - Opis nowoczesnego GUI
  - `README_IMPROVEMENTS.md` - Lista ulepszeń
  - `README_REFACTORING.md` - Informacje o refaktoryzacji

## 🔧 Rozwój

### Uruchamianie testów

```bash
# Uruchom wszystkie testy
python -m pytest tests/

# Z pokryciem kodu
python -m pytest tests/ --cov=src
```

### Formatowanie kodu

```bash
# Użyj black do formatowania
black src/ tests/

# Sprawdź zgodność z PEP 8
flake8 src/ tests/
```

### Struktura modułów

- **`src/core/`** - Główna logika biznesowa
- **`src/gui/`** - Interfejsy użytkownika
- **`src/utils/`** - Narzędzia pomocnicze

### Dodawanie nowych funkcji

1. Utwórz branch: `git checkout -b feature/nazwa-funkcji`
2. Wprowadź zmiany
3. Dodaj testy
4. Utwórz Pull Request

## 🐛 Rozwiązywanie problemów

### Problem: Błąd importu modułów

**Rozwiązanie**: Upewnij się, że wszystkie zależności są zainstalowane:
```bash
pip install -r requirements.txt
```

### Problem: Błąd połączenia z API CRBR

**Rozwiązanie**: 
- Sprawdź połączenie internetowe
- Zwiększ timeout w ustawieniach
- Sprawdź czy API CRBR jest dostępne

### Problem: Błędy z polskimi znakami

**Rozwiązanie**: Upewnij się, że terminal/IDE obsługuje UTF-8:
```bash
# Windows PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## 📝 Licencja

Ten projekt jest licencjonowany na licencji Apache 2.0 - zobacz plik [LICENSE](LICENSE) aby uzyskać szczegóły.

## 🤝 Wsparcie

- **Issues**: Zgłoś problem lub sugestię na [GitHub Issues](https://github.com/AddNap/SancCheck/issues)
- **Discussions**: Dołącz do dyskusji na [GitHub Discussions](https://github.com/AddNap/SancCheck/discussions)

## 👥 Autorzy

- **Adrian Napora** - [@AddNap](https://github.com/AddNap)

## 🙏 Podziękowania

- Ministerstwo Finansów za udostępnienie API CRBR
- Wszystkim kontrybutorom projektu

---

**Uwaga**: Ta aplikacja jest narzędziem pomocniczym i nie zastępuje profesjonalnej weryfikacji prawnej. Zawsze weryfikuj wyniki z oficjalnymi źródłami.
