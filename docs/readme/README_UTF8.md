# Konfiguracja UTF-8 dla aplikacji CRBR

## Opis
Aplikacja CRBR została skonfigurowana do pełnego wsparcia kodowania UTF-8, co zapewnia prawidłowe wyświetlanie polskich znaków diakrytycznych.

## Zmiany wprowadzone

### 1. Plik konfiguracyjny UTF-8
- **`utf8_config.py`** - centralna konfiguracja kodowania UTF-8
- Automatyczne ustawienie kodowania dla Windows (`chcp 65001`)
- Konfiguracja stdout/stderr do UTF-8
- Ustawienie locale dla języka polskiego

### 2. Zaktualizowane pliki
- **`crbr_bulk_to_pdf.py`** - główna aplikacja
- **`crbr_gui.py`** - interfejs graficzny
- **`run_gui.py`** - skrypt uruchamiający

### 3. Operacje z plikami
- **Import CSV**: `encoding='utf-8'`
- **Eksport CSV**: `encoding='utf-8'`
- **Operacje XML**: UTF-8
- **Generowanie PDF**: UTF-8

## Funkcje UTF-8

### `setup_utf8()`
Konfiguruje pełne wsparcie UTF-8:
- Ustawia kodowanie terminala Windows
- Konfiguruje stdout/stderr
- Ustawia locale
- Definiuje zmienne środowiskowe

### `get_csv_encoding()`
Zwraca kodowanie dla plików CSV (UTF-8)

### `get_xml_encoding()`
Zwraca kodowanie dla plików XML (UTF-8)

## Użycie

### Automatyczne
Aplikacja automatycznie konfiguruje UTF-8 przy uruchomieniu:

```bash
python crbr_gui.py
python run_gui.py
python crbr_bulk_to_pdf.py --nip 1234567890 --out output
```

### Ręczne
Można też ręcznie skonfigurować UTF-8:

```python
from utf8_config import setup_utf8
setup_utf8()
```

## Obsługiwane znaki

Aplikacja teraz prawidłowo obsługuje:
- ✅ Polskie znaki diakrytyczne (ą, ć, ę, ł, ń, ó, ś, ź, ż)
- ✅ Znaki specjalne w nazwach firm
- ✅ Polskie nazwy miejscowości
- ✅ Znaki w adresach
- ✅ Wszystkie znaki Unicode

## Rozwiązywanie problemów

### Problem: Znaki wyświetlają się jako "?"
**Rozwiązanie**: Upewnij się, że terminal obsługuje UTF-8:
```bash
chcp 65001  # Windows
```

### Problem: Błędy kodowania w plikach CSV
**Rozwiązanie**: Sprawdź czy plik CSV jest zapisany w UTF-8

### Problem: Błędy w GUI
**Rozwiązanie**: Uruchom aplikację przez `run_gui.py` który automatycznie konfiguruje UTF-8

## Testowanie

Sprawdź konfigurację UTF-8:
```bash
python utf8_config.py
```

Powinno wyświetlić:
```
✓ Konfiguracja UTF-8 została ustawiona
✓ Kodowanie stdout: utf-8
✓ Kodowanie stderr: utf-8
✓ Locale: ('pl_PL', 'UTF-8')
```

## Kompatybilność

- ✅ **Windows 10/11** - pełne wsparcie
- ✅ **Linux** - pełne wsparcie
- ✅ **macOS** - pełne wsparcie
- ✅ **Python 3.6+** - pełne wsparcie

---
**Autor**: (C) 2025  
**Wersja**: 1.0  
**Licencja**: Open Source
