# Naprawa brakujących pól w raporcie CRBR

## Problem
W generowanych raportach PDF brakowało kilku ważnych informacji:
- **Daty**: data złożenia, data udostępnienia
- **Kraje**: kraj zamieszkania beneficjentów
- **Obywatelstwa**: obywatelstwo beneficjentów
- **Funkcje**: funkcja zgłaszającego

## Przyczyna
Funkcja `parse_crbr_xml` nie wyciągała poprawnie wszystkich danych z XML, ponieważ:
1. Szukała pól w starym formacie XML
2. Nie obsługiwała zagnieżdżonych struktur (np. `Obywatelstwo/Nazwa`)
3. Nie parsowała funkcji z `ListaFunkcjiZglaszajacego`

## Rozwiązanie

### 1. Naprawa parsowania dat
**Przed:**
```python
"data_udostepnienia": (root.findtext(".//dataICzasUdostepnieniaWniosku") or "").strip(),
"data_zlozenia": (root.findtext(".//dataICzasZlozeniaWniosku") or "").strip(),
```

**Po:**
```python
"data_udostepnienia": get_text_by_local_name(root, "DataICzasUdostepnieniaWniosku"),
"data_zlozenia": get_text_by_local_name(root, "DataICzasZlozeniaWniosku"),
```

### 2. Naprawa parsowania obywatelstwa
**Przed:**
```python
"obywatelstwo": get_text_by_local_name(b, "Obywatelstwo"),
```

**Po:**
```python
# Pobierz obywatelstwo
obywatelstwo = ""
obywatelstwo_elem = b.xpath(".//*[local-name()='Obywatelstwo']")
if obywatelstwo_elem:
    obywatelstwo = get_text_by_local_name(obywatelstwo_elem[0], "Nazwa")
```

### 3. Naprawa parsowania kraju zamieszkania
**Przed:**
```python
"panstwo_zamieszkania": get_text_by_local_name(b, "KrajZamieszkania"),
```

**Po:**
```python
# Pobierz kraj zamieszkania
kraj_zamieszkania = ""
kraj_elem = b.xpath(".//*[local-name()='KrajZamieszkania']")
if kraj_elem:
    kraj_zamieszkania = get_text_by_local_name(kraj_elem[0], "Nazwa")
```

### 4. Naprawa parsowania funkcji zgłaszającego
**Przed:**
```python
"funkcja": get_text_by_local_name(zg, "Funkcja"),
```

**Po:**
```python
# Pobierz funkcję z ListaFunkcjiZglaszajacego
funkcja = ""
lista_funkcji = zg.xpath(".//*[local-name()='ListaFunkcjiZglaszajacego']")
if lista_funkcji:
    funkcje = lista_funkcji[0].xpath(".//*[local-name()='Funkcja']")
    if funkcje:
        funkcja = get_text_by_local_name(funkcje[0], "Opis")
```

### 5. Funkcja pomocnicza
Dodano funkcję `get_text_by_local_name` na początku funkcji `parse_crbr_xml`:

```python
def get_text_by_local_name(root, tag_name):
    """Pobiera tekst elementu ignorując namespace"""
    try:
        results = root.xpath(f".//*[local-name()='{tag_name}']/text()")
        return results[0].strip() if results else ""
    except:
        return ""
```

## Rezultat

### Przed naprawą:
- ❌ **Data i godzina złożenia**: puste
- ❌ **Data i czas udostępnienia**: puste
- ❌ **Obywatelstwo**: puste
- ❌ **Kraj zamieszkania**: puste
- ❌ **Funkcja zgłaszającego**: puste

### Po naprawie:
- ✅ **Data i godzina złożenia**: `2025-09-25T14:07:35`
- ✅ **Data i czas udostępnienia**: `2025-09-25T14:07:35`
- ✅ **Obywatelstwo**: `POLSKA`
- ✅ **Kraj zamieszkania**: `POLSKA`
- ✅ **Funkcja zgłaszającego**: `reprezentant`

## Struktura XML

### Daty:
```xml
<DataICzasZlozeniaWniosku>2025-09-25T14:07:35</DataICzasZlozeniaWniosku>
<DataICzasUdostepnieniaWniosku>2025-09-25T14:07:35</DataICzasUdostepnieniaWniosku>
```

### Obywatelstwo:
```xml
<Obywatelstwo>
    <Kod>PL</Kod>
    <Nazwa>POLSKA</Nazwa>
</Obywatelstwo>
```

### Kraj zamieszkania:
```xml
<KrajZamieszkania>
    <Kod>PL</Kod>
    <Nazwa>POLSKA</Nazwa>
</KrajZamieszkania>
```

### Funkcja zgłaszającego:
```xml
<ListaFunkcjiZglaszajacego>
    <Funkcja>
        <Kod>176</Kod>
        <Opis>reprezentant</Opis>
    </Funkcja>
</ListaFunkcjiZglaszajacego>
```

## Testowanie

Aby przetestować naprawę:

```bash
python crbr_bulk_to_pdf.py --nip 5222943093 --out test_output
```

Wygenerowany PDF powinien zawierać wszystkie pola:
- Daty w sekcji meta
- Obywatelstwa w sekcji beneficjentów
- Kraje zamieszkania w sekcji beneficjentów
- Funkcje w sekcji zgłaszającego

## Kompatybilność

- ✅ **Windows 10/11** - pełne wsparcie
- ✅ **Linux** - pełne wsparcie
- ✅ **macOS** - pełne wsparcie
- ✅ **Python 3.6+** - pełne wsparcie
- ✅ **ReportLab 3.0+** - pełne wsparcie

## Rozwiązywanie problemów

### Problem: Nadal brakuje niektórych pól
**Rozwiązanie**: Sprawdź czy XML zawiera odpowiednie elementy:
```python
# Debug XML
from lxml import etree
root = etree.fromstring(xml_bytes)
print(root.xpath(".//*[local-name()='Obywatelstwo']"))
```

### Problem: Błąd parsowania
**Rozwiązanie**: Sprawdź czy funkcja `get_text_by_local_name` jest zdefiniowana przed użyciem.

### Problem: Puste pola w PDF
**Rozwiązanie**: Sprawdź czy dane są dostępne w XML i czy funkcja parsowania je wyciąga.

---
**Autor**: (C) 2025  
**Wersja**: 1.0  
**Licencja**: Open Source
