# SancCheck

Aplikacja do generowania raportów PDF z danych Centralnego Rejestru Beneficjentów Rzeczywistych (CRBR) z automatyczną weryfikacją list sankcyjnych.

## Struktura projektu

```
raport/
├── src/                    # Kod źródłowy aplikacji
│   ├── gui/               # Interfejsy użytkownika
│   │   ├── crbr_gui.py           # Podstawowy GUI (tkinter)
│   │   └── crbr_gui_modern.py    # Nowoczesny GUI (ttkbootstrap)
│   ├── core/              # Logika biznesowa
│   │   ├── crbr_bulk_to_pdf.py   # Główny moduł generowania PDF
│   │   ├── sanctions.py          # Moduł sankcji
│   │   └── sanctions_old.py      # Stara wersja modułu sankcji
│   ├── utils/             # Moduły pomocnicze
│   │   ├── logger_config.py      # Konfiguracja logowania
│   │   ├── nip_validator.py      # Walidacja NIP
│   │   ├── pdf_table_helpers.py  # Pomocnicze funkcje PDF
│   │   ├── utf8_config.py        # Konfiguracja UTF-8
│   │   └── xml_parsing_helpers.py # Parsowanie XML
│   ├── run_gui.py         # Uruchamianie podstawowego GUI
│   └── run_modern_gui.py  # Uruchamianie nowoczesnego GUI
├── tests/                 # Pliki testowe
├── docs/                  # Dokumentacja
│   ├── api/              # Dokumentacja API CRBR
│   └── readme/           # Pliki README
├── data/                  # Dane i pliki wyjściowe
│   ├── output_pdfs/      # Wygenerowane pliki PDF
│   ├── sanctions/        # Listy sankcyjne (CSV, JSON)
│   ├── sanctions_reports/ # Raporty sankcyjne (HTML)
│   ├── test_*/           # Dane testowe
│   └── test_docs/        # Pliki testowe dokumentacji
├── config/               # Pliki konfiguracyjne
│   └── exclusion_keywords.txt  # Słowa kluczowe wykluczeń
├── temp/                 # Pliki tymczasowe
├── requirements.txt      # Zależności Python
├── run_gui.py           # Uruchamianie podstawowego GUI (wrapper)
└── run_modern_gui.py    # Uruchamianie nowoczesnego GUI (wrapper)
```

## Instalacja

1. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```

## Uruchamianie

### Nowoczesny GUI (zalecany)
```bash
python run_modern_gui.py
```

### Podstawowy GUI
```bash
python run_gui.py
```

## Funkcje

- Generowanie raportów PDF z danych CRBR
- Walidacja numerów NIP
- Obsługa plików CSV z danymi
- Nowoczesny interfejs użytkownika
- Logowanie operacji
- Obsługa polskich znaków

## Wymagania

- Python 3.8+
- requests
- lxml
- reportlab
- pandas
- ttkbootstrap (dla nowoczesnego GUI)

## Dokumentacja

Szczegółowa dokumentacja znajduje się w folderze `docs/`:
- `docs/api/` - dokumentacja API CRBR
- `docs/readme/` - dodatkowe pliki README z opisami funkcji
