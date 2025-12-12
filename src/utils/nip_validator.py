# -*- coding: utf-8 -*-
"""
Walidator NIP (Numer Identyfikacji Podatkowej)
Implementuje algorytm sumy kontrolnej zgodny z polskim prawem podatkowym.
"""

import re
from typing import Tuple, Optional


def validate_nip(nip: str) -> Tuple[bool, str]:
    """
    Waliduje NIP pod kątem formatu i sumy kontrolnej.
    
    Args:
        nip: NIP do walidacji (może zawierać spacje, myślniki)
        
    Returns:
        Tuple[bool, str]: (czy_poprawny, komunikat_błędu)
    """
    if not nip:
        return False, "NIP nie może być pusty"
    
    # Usuń wszystkie znaki niebędące cyframi
    clean_nip = re.sub(r'\D', '', nip)
    
    # Sprawdź długość
    if len(clean_nip) != 10:
        return False, f"NIP musi mieć dokładnie 10 cyfr (otrzymano {len(clean_nip)})"
    
    # Sprawdź czy wszystkie znaki to cyfry
    if not clean_nip.isdigit():
        return False, "NIP może zawierać tylko cyfry"
    
    # Sprawdź sumę kontrolną
    if not _check_nip_checksum(clean_nip):
        return False, "Nieprawidłowa suma kontrolna NIP"
    
    return True, ""


def _check_nip_checksum(nip: str) -> bool:
    """
    Sprawdza sumę kontrolną NIP.
    
    Algorytm:
    1. Mnożymy każdą cyfrę przez odpowiednią wagę: 6,5,7,2,3,4,5,6,7
    2. Sumujemy wyniki
    3. Reszta z dzielenia przez 11 powinna być równa ostatniej cyfrze NIP
    4. Jeśli reszta = 10, to ostatnia cyfra powinna być 0
    
    Args:
        nip: 10-cyfrowy NIP (tylko cyfry)
        
    Returns:
        bool: True jeśli suma kontrolna jest poprawna
    """
    if len(nip) != 10:
        return False
    
    # Wagi dla pierwszych 9 cyfr
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    
    # Oblicz sumę ważoną pierwszych 9 cyfr
    weighted_sum = 0
    for i in range(9):
        weighted_sum += int(nip[i]) * weights[i]
    
    # Oblicz resztę z dzielenia przez 11
    remainder = weighted_sum % 11
    
    # Ostatnia cyfra NIP
    last_digit = int(nip[9])
    
    # Sprawdź warunki
    if remainder == 10:
        return last_digit == 0
    else:
        return remainder == last_digit


def format_nip(nip: str) -> Optional[str]:
    """
    Formatuje NIP do standardowej postaci XXX-XXX-XX-XX.
    
    Args:
        nip: NIP do sformatowania
        
    Returns:
        str: Sformatowany NIP lub None jeśli nieprawidłowy
    """
    is_valid, _ = validate_nip(nip)
    if not is_valid:
        return None
    
    # Usuń wszystkie znaki niebędące cyframi
    clean_nip = re.sub(r'\D', '', nip)
    
    # Formatuj: XXX-XXX-XX-XX
    return f"{clean_nip[:3]}-{clean_nip[3:6]}-{clean_nip[6:8]}-{clean_nip[8:10]}"


def clean_nip(nip: str) -> str:
    """
    Czyści NIP z wszystkich znaków niebędących cyframi.
    
    Args:
        nip: NIP do wyczyszczenia
        
    Returns:
        str: NIP zawierający tylko cyfry
    """
    return re.sub(r'\D', '', nip)


def validate_nips_from_csv_content(csv_content: str) -> dict:
    """
    Waliduje NIP-y z zawartości pliku CSV.
    
    Args:
        csv_content: Zawartość pliku CSV jako string
        
    Returns:
        dict: Słownik z kluczami 'valid' i 'invalid' zawierającymi listy NIP-ów
    """
    import io
    import csv
    
    valid_nips = []
    invalid_nips = []
    duplicate_nips = []
    seen_nips = set()
    
    try:
        # Utwórz StringIO z zawartości CSV
        csv_buffer = io.StringIO(csv_content)
        
        # Spróbuj wykryć delimiter
        sample = csv_content[:1024]  # Pobierz próbkę
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
        
        # Przeczytaj CSV
        reader = csv.reader(csv_buffer, delimiter=delimiter)
        
        for row_num, row in enumerate(reader, 1):
            for col_num, cell in enumerate(row):
                if cell and cell.strip():  # Pomiń puste komórki
                    # Sprawdź czy komórka może zawierać NIP
                    cell_clean = clean_nip(cell)
                    if len(cell_clean) == 10:  # Potencjalny NIP
                        is_valid, error = validate_nip(cell_clean)
                        if is_valid:
                            if cell_clean not in seen_nips:
                                valid_nips.append(cell_clean)
                                seen_nips.add(cell_clean)
                            else:
                                duplicate_nips.append(cell_clean)
                        else:
                            invalid_nips.append({
                                'nip': cell_clean,
                                'error': error,
                                'row': row_num,
                                'col': col_num,
                                'original': cell
                            })
        
    except Exception as e:
        # Jeśli nie udało się sparsować jako CSV, spróbuj jako zwykły tekst
        lines = csv_content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if line.strip():
                # Znajdź potencjalne NIP-y w linii
                potential_nips = re.findall(r'\b\d{10}\b', line)
                for nip in potential_nips:
                    is_valid, error = validate_nip(nip)
                    if is_valid:
                        if nip not in seen_nips:
                            valid_nips.append(nip)
                            seen_nips.add(nip)
                        else:
                            duplicate_nips.append(nip)
                    else:
                        invalid_nips.append({
                            'nip': nip,
                            'error': error,
                            'row': line_num,
                            'col': 0,
                            'original': nip
                        })
    
    return {
        'valid': valid_nips,
        'invalid': invalid_nips,
        'duplicates': duplicate_nips,
        'total': len(valid_nips) + len(invalid_nips) + len(duplicate_nips)
    }


# Testy jednostkowe
if __name__ == "__main__":
    # Testy poprawnych NIP-ów
    valid_nips = [
        "1234563218",  # Przykładowy poprawny NIP
        "7393873360",  # NIP z przykładu
        "123-456-32-18",
        "123 456 32 18",
        "123.456.32.18"
    ]
    
    # Testy niepoprawnych NIP-ów
    invalid_nips = [
        "1234563219",  # Błędna suma kontrolna
        "123456321",   # Za krótki
        "12345632180", # Za długi
        "123456321a",  # Zawiera literę
        "",            # Pusty
        "0000000000"   # Wszystkie zera
    ]
    
    print("=== Testy walidacji NIP ===")
    
    print("\nPoprawne NIP-y:")
    for nip in valid_nips:
        is_valid, error = validate_nip(nip)
        formatted = format_nip(nip)
        print(f"  {nip:15} -> {is_valid:5} | {formatted}")
    
    print("\nNiepoprawne NIP-y:")
    for nip in invalid_nips:
        is_valid, error = validate_nip(nip)
        print(f"  {nip:15} -> {is_valid:5} | {error}")
