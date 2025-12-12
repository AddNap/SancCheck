# Poprawka polskich znaków w PDF (wersja PRO)

## Problem
W nowej wersji PRO z Platypus pojawił się problem z polskimi znakami - wyświetlały się jako czarne kwadraty zamiast polskich liter.

## Przyczyna
Funkcja `_pick_font_name()` miała błąd z importem modułu `os` - była zdefiniowana lokalnie w funkcji, ale używana wcześniej, co powodowało `UnboundLocalError`.

## Rozwiązanie
1. **Przeniesienie importu `os`** na początek funkcji `_pick_font_name()`
2. **Dodanie debugowania** - funkcja teraz wyświetla informacje o rejestrowanych czcionkach
3. **Fallback na czcionki systemowe** - jeśli lokalna czcionka DejaVuSans.ttf nie istnieje, próbuje zarejestrować czcionki systemowe (Arial, Calibri, Tahoma, Segoe UI na Windows)

## Kod poprawki
```python
def _pick_font_name() -> str:
    import os  # Przeniesiony na początek funkcji
    # Preferuj lokalny DejaVuSans.ttf dołączony do repo (pełne PL znaki)
    here = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
    local_ttf = os.path.join(here, "DejaVuSans.ttf")
    if os.path.exists(local_ttf):
        try:
            pdfmetrics.registerFont(TTFont("BodyFont", local_ttf))
            print(f"Zarejestrowano czcionkę: {local_ttf}")
            return "BodyFont"
        except Exception as e:
            print(f"Nie można zarejestrować {local_ttf}: {e}")
    
    # Fallback - spróbuj czcionek systemowych
    if os.name == 'nt':  # Windows
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
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("BodyFont", font_path))
                print(f"Zarejestrowano czcionkę systemową: {font_path}")
                return "BodyFont"
            except Exception as e:
                print(f"Nie można zarejestrować {font_path}: {e}")
                continue
    
    print("Użyto fallback czcionki Helvetica")
    return "Helvetica"  # fallback
```

## Test
```bash
python crbr_bulk_to_pdf.py --nip 7393873360 --out test_polish_fixed
```

**Wynik:**
```
Zarejestrowano czcionkę systemową: C:/Windows/Fonts/arial.ttf
Wygenerowane pliki:
test_polish_fixed\crbr_7393873360_EE81A53C31BD45F2A227251672950E7B.pdf
```

## Status
✅ **POPRAWIONE** - Polskie znaki są teraz poprawnie wyświetlane w PDF

## Uwagi
- Aplikacja automatycznie wybiera najlepszą dostępną czcionkę
- Na Windows preferuje Arial, która ma pełne wsparcie dla polskich znaków
- Jeśli żadna czcionka systemowa nie jest dostępna, używa fallback Helvetica
- Debugowanie pomaga w identyfikacji problemów z czcionkami
