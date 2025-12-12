# Naprawa polskich znaków w PDF

## Problem
W generowanych plikach PDF polskie znaki diakrytyczne (ą, ć, ę, ł, ń, ó, ś, ź, ż) wyświetlały się jako czarne kwadraty zamiast prawidłowych liter.

## Przyczyna
ReportLab domyślnie używa czcionki Helvetica, która nie obsługuje polskich znaków diakrytycznych. Potrzebna była czcionka TTF (TrueType Font), która obsługuje pełny zestaw znaków Unicode.

## Rozwiązanie

### 1. Rejestracja czcionki TTF
Dodano automatyczną rejestrację czcionki systemowej, która obsługuje polskie znaki:

```python
# Rejestruj czcionkę TTF dla polskich znaków
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Spróbuj zarejestrować czcionkę systemową
    import os
    if os.name == 'nt':  # Windows
        # Czcionki Windows
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf", 
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/segoeui.ttf"
        ]
    else:  # Linux/Mac
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
    
    font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PolishFont', font_path))
                font_registered = True
                break
            except:
                continue
```

### 2. Zastąpienie wszystkich czcionek
Wszystkie wystąpienia czcionek w funkcji `render_pdf` zostały zmienione z `Helvetica` na `PolishFont`:

- **Nagłówek**: `c.setFont("PolishFont", 14)`
- **Meta**: `c.setFont("PolishFont", 9)`
- **Podmiot**: `c.setFont("PolishFont", 11)` i `c.setFont("PolishFont", 10)`
- **Beneficjenci**: `c.setFont("PolishFont", 11)` i `c.setFont("PolishFont", 10)`
- **Zgłaszający**: `c.setFont("PolishFont", 11)` i `c.setFont("PolishFont", 10)`
- **Stopka**: `c.setFont("PolishFont", 8)`

### 3. Obsługiwane czcionki

#### Windows:
- **Arial** - `C:/Windows/Fonts/arial.ttf`
- **Calibri** - `C:/Windows/Fonts/calibri.ttf`
- **Tahoma** - `C:/Windows/Fonts/tahoma.ttf`
- **Segoe UI** - `C:/Windows/Fonts/segoeui.ttf`

#### Linux:
- **DejaVu Sans** - `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- **Liberation Sans** - `/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf`

#### macOS:
- **Arial** - `/System/Library/Fonts/Arial.ttf`

### 4. Fallback
Jeśli żadna z czcionek systemowych nie jest dostępna, aplikacja próbuje użyć wbudowanej czcionki Helvetica jako fallback.

## Rezultat

### Przed naprawą:
- ❌ "Wpisy Podmiotu w CRBR – raport techniczny" → "Wpisy Podmiotu w CRBR [czarne kwadraty] raport techniczny"
- ❌ "Miejscowość" → "Miejscowo[czarne kwadraty]"
- ❌ "Zgłaszający" → "Zg[czarne kwadraty]aszaj[czarne kwadraty]cy"

### Po naprawie:
- ✅ "Wpisy Podmiotu w CRBR – raport techniczny"
- ✅ "Miejscowość"
- ✅ "Zgłaszający"
- ✅ Wszystkie polskie znaki diakrytyczne wyświetlają się prawidłowo

## Testowanie

Aby przetestować naprawę:

```bash
python crbr_bulk_to_pdf.py --nip 7393873360 --out test_output
```

Wygenerowany PDF powinien zawierać prawidłowe polskie znaki we wszystkich sekcjach:
- Nagłówku
- Metadanych
- Dane podmiotu
- Dane beneficjentów
- Dane zgłaszających
- Stopce

## Kompatybilność

- ✅ **Windows 10/11** - pełne wsparcie (Arial, Calibri, Tahoma, Segoe UI)
- ✅ **Linux** - pełne wsparcie (DejaVu Sans, Liberation Sans)
- ✅ **macOS** - pełne wsparcie (Arial)
- ✅ **Python 3.6+** - pełne wsparcie
- ✅ **ReportLab 3.0+** - pełne wsparcie

## Rozwiązywanie problemów

### Problem: Nadal widzę czarne kwadraty
**Rozwiązanie**: Sprawdź czy system ma zainstalowane czcionki TTF:
```bash
# Windows
dir C:\Windows\Fonts\arial.ttf

# Linux
ls /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf

# macOS
ls /System/Library/Fonts/Arial.ttf
```

### Problem: Błąd rejestracji czcionki
**Rozwiązanie**: Sprawdź uprawnienia do plików czcionek lub zainstaluj dodatkowe czcionki.

### Problem: Czcionka nie jest rozpoznawana
**Rozwiązanie**: Aplikacja automatycznie próbuje różne czcionki i używa fallback.

---
**Autor**: (C) 2025  
**Wersja**: 1.0  
**Licencja**: Open Source
