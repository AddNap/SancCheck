# Poprawka błędu logowania GUI

## Problem
Błąd: `'GUILogHandler' object has no attribute 'level'`

## Przyczyna
Klasa `GUILogHandler` nie miała atrybutu `level`, który jest wymagany przez system logowania Python.

## Rozwiązanie

### 1. Dodanie atrybutu level
```python
class GUILogHandler:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.level = 0  # Dodaj brakujący atrybut level
```

### 2. Poprawka walidacji NIP-ów
```python
# Filtruj puste i niepoprawne NIP-y
valid_nips = []
for nip in df["nip"].unique():
    if nip and len(nip) == 10:
        is_valid, _ = validate_nip(nip)
        if is_valid:
            valid_nips.append(nip)
        else:
            self.log_message(f"Niepoprawny NIP (suma kontrolna): {nip}", "WARNING")
```

### 3. Poprawka generowania PDF
```python
# Upewnij się, że NIP jest czysty (bez myślników)
clean_nip = nip.replace('-', '') if nip else ""
if not clean_nip:
    self.log_message(f"Pusty NIP, pomijam", "WARNING")
    continue
```

## Status
✅ **POPRAWIONE** - System logowania działa poprawnie

## Uwagi
- GUILogHandler wymaga atrybutu `level`
- NIP-y muszą być czyste (bez myślników) dla API
- Walidacja NIP-ów z sumą kontrolną działa poprawnie
