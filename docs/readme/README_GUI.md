# CRBR GUI - Generator Raportów PDF

## Opis
Aplikacja z interfejsem graficznym do generowania raportów PDF z danych CRBR (Centralny Rejestr Beneficjentów Rzeczywistych). Aplikacja umożliwia dodawanie NIP-ów do weryfikacji i automatyczne generowanie raportów PDF.

## Funkcjonalności

### 🎯 Główne funkcje
- **Dodawanie NIP-ów** - możliwość dodawania pojedynczych NIP-ów do listy weryfikacji
- **Import z CSV** - import listy NIP-ów z pliku CSV
- **Eksport do CSV** - eksport listy NIP-ów do pliku CSV
- **Generowanie PDF** - automatyczne generowanie raportów PDF dla wszystkich NIP-ów
- **Śledzenie postępu** - pasek postępu i logi operacji
- **Zarządzanie listą** - usuwanie, czyszczenie listy NIP-ów

### 📋 Interfejs użytkownika
- **Sekcja dodawania NIP-ów** - pole tekstowe + przyciski
- **Lista NIP-ów** - tabela z statusem i ścieżkami do plików
- **Sekcja operacji** - konfiguracja katalogu wyjściowego i timeout
- **Logi** - okno z logami operacji w czasie rzeczywistym

## Instalacja i uruchomienie

### Wymagania
```bash
pip install requests lxml reportlab pandas
```

### Uruchomienie GUI
```bash
python crbr_gui.py
```

### Uruchomienie wersji konsolowej
```bash
python crbr_bulk_to_pdf.py --nip 1234567890 --out output_pdfs
```

## Instrukcja użytkowania

### 1. Dodawanie NIP-ów
- Wpisz NIP w pole tekstowe (10 cyfr)
- Kliknij "Dodaj NIP" lub naciśnij Enter
- NIP zostanie dodany do listy z statusem "Oczekuje"

### 2. Import z pliku CSV
- Kliknij "Import CSV"
- Wybierz plik CSV z kolumną 'nip'
- Aplikacja automatycznie wyczyści NIP-y (usunie znaki niebędące cyframi)
- Zaimportowane NIP-y pojawią się na liście

### 3. Konfiguracja operacji
- **Katalog wyjściowy**: wybierz gdzie zapisać pliki PDF
- **Timeout**: czas oczekiwania na odpowiedź serwera (domyślnie 45s)

### 4. Generowanie raportów
- Kliknij "Generuj raporty PDF"
- Aplikacja będzie przetwarzać NIP-y jeden po drugim
- Postęp będzie widoczny na pasku postępu
- Logi pokażą szczegóły operacji

### 5. Zarządzanie listą
- **Usuń zaznaczone**: usuwa wybrane NIP-y z listy
- **Wyczyść listę**: usuwa wszystkie NIP-y
- **Eksport do CSV**: zapisuje listę NIP-ów do pliku

## Statusy NIP-ów
- **Oczekuje** - NIP dodany do listy, czeka na przetworzenie
- **Przetwarzanie...** - aktualnie pobierane dane z CRBR
- **Gotowe** - PDF został wygenerowany pomyślnie
- **Błąd** - wystąpił błąd podczas przetwarzania

## Struktura plików wyjściowych
```
output_pdfs/
├── crbr_1234567890_ABC123.pdf
├── crbr_9876543210_DEF456.pdf
└── ...
```

Format nazwy: `crbr_{NIP}_{identyfikator}.pdf`

## Rozwiązywanie problemów

### Błąd 500 Internal Server Error
- Serwis CRBR może być tymczasowo niedostępny
- NIP może nie istnieć w bazie danych CRBR
- Spróbuj z innym NIP-em lub sprawdź połączenie internetowe

### Błąd timeout
- Zwiększ wartość timeout w sekcji operacji
- Sprawdź połączenie internetowe
- Serwis może być przeciążony

### Błąd importu CSV
- Upewnij się, że plik CSV ma kolumnę 'nip'
- Sprawdź format pliku (UTF-8)
- NIP-y powinny składać się z 10 cyfr

## Funkcje techniczne

### Architektura
- **GUI**: tkinter (wbudowany w Python)
- **Wątki**: przetwarzanie w tle bez blokowania interfejsu
- **Kolejka**: komunikacja między wątkami
- **Integracja**: wykorzystuje funkcje z `crbr_bulk_to_pdf.py`

### Bezpieczeństwo
- Walidacja NIP-ów (tylko cyfry, 10 znaków)
- Obsługa błędów sieciowych
- Możliwość zatrzymania operacji w trakcie

### Wydajność
- Przetwarzanie w tle
- Pauza między zapytaniami (0.5s)
- Pasek postępu w czasie rzeczywistym

## Przykłady użycia

### Przykład 1: Pojedynczy NIP
1. Uruchom aplikację
2. Wpisz NIP: `1234567890`
3. Kliknij "Dodaj NIP"
4. Wybierz katalog wyjściowy
5. Kliknij "Generuj raporty PDF"

### Przykład 2: Import z CSV
1. Przygotuj plik `nip_list.csv`:
   ```csv
   nip
   1234567890
   9876543210
   5555555555
   ```
2. Kliknij "Import CSV"
3. Wybierz plik
4. Kliknij "Generuj raporty PDF"

### Przykład 3: Eksport listy
1. Dodaj NIP-y do listy
2. Kliknij "Eksport do CSV"
3. Wybierz lokalizację zapisu

## Wsparcie
W przypadku problemów sprawdź:
1. Logi operacji w dolnej części aplikacji
2. Połączenie internetowe
3. Poprawność formatu NIP-ów
4. Dostępność serwisu CRBR

---
**Autor**: (C) 2025  
**Wersja**: 1.0  
**Licencja**: Open Source
