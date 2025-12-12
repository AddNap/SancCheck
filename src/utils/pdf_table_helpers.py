"""
Pomocnicze funkcje do generowania tabel PDF
"""

from typing import List, Tuple, Any, Optional, Dict
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
import pandas as pd

# Inicjalizacja czcionki dla polskich znaków
def _init_polish_font():
    """Inicjalizuje czcionkę z polskimi znakami"""
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os
        
        # Sprawdź czy czcionka już jest zarejestrowana
        if 'BodyFont' in pdfmetrics.getRegisteredFontNames():
            return True
            
        # Preferuj lokalny DejaVuSans.ttf
        here = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
        local_ttf = os.path.join(here, "DejaVuSans.ttf")
        if os.path.exists(local_ttf):
            try:
                pdfmetrics.registerFont(TTFont("BodyFont", local_ttf))
                print(f"Zarejestrowano czcionkę: {local_ttf}")
                return True
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
                    return True
                except Exception as e:
                    print(f"Nie można zarejestrować {font_path}: {e}")
                    continue
        
        print("Użyto fallback czcionki Helvetica")
        return False
        
    except ImportError:
        print("ReportLab nie jest zainstalowany")
        return False

# Inicjalizuj czcionkę przy imporcie modułu
_init_polish_font()


def safe_pandas_to_str(value) -> str:
    """Bezpiecznie konwertuje wartość pandas (w tym Timestamp) na string"""
    if value is None or pd.isna(value):
        return ""
    try:
        # Handle pandas Timestamp objects
        if hasattr(value, 'strftime'):
            return str(value)
        return str(value).strip()
    except Exception:
        return ""


def _wrap_text(text: str, max_length: int = 50) -> str:
    """
    Zawija długi tekst na linie dla lepszego wyświetlania w tabelach
    
    Args:
        text: Tekst do zawinięcia
        max_length: Maksymalna długość linii
        
    Returns:
        Zawinięty tekst z znakami nowej linii
    """
    if not text or len(text) <= max_length:
        return text
    
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_length:
            current_line += (" " + word) if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return "\n".join(lines)


def create_key_value_table(
    data: List[Tuple[str, str]], 
    col_widths: Optional[List[float]] = None,
    zebra: bool = False,
    header_bg: Optional[colors.Color] = None
) -> Table:
    """
    Tworzy tabelę klucz-wartość
    
    Args:
        data: Lista tupli (klucz, wartość)
        col_widths: Szerokości kolumn w mm
        zebra: Czy zastosować kolorowanie zebra
        header_bg: Kolor tła nagłówka
        
    Returns:
        Obiekt Table
    """
    if not data:
        return Table([["Brak danych"]], colWidths=[150*mm])
    
    # Przygotuj dane z zawijaniem tekstu
    table_data = []
    for key, value in data:
        # Bezpiecznie konwertuj wartość na string (obsługa Timestamp objects)
        if value is None:
            value = "—"
        else:
            try:
                # Handle pandas Timestamp objects
                if hasattr(value, 'strftime'):
                    value = str(value)
                else:
                    value = str(value).strip()
                if not value:
                    value = "—"
            except Exception:
                value = "—"
        
        # Użyj Paragraph dla zawijania tekstu
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'BodyFont'
        normal_style.fontSize = 9
        
        # Utwórz Paragraph dla długich tekstów
        key_para = Paragraph(key, normal_style)
        value_para = Paragraph(value, normal_style)
        
        table_data.append([key_para, value_para])
    
    # Szerokości kolumn - równomierne rozłożenie
    if col_widths is None:
        available_width = 170 * mm  # Dostępna szerokość na stronie A4
        col_widths = [available_width / 2, available_width / 2]  # Równomierne rozłożenie na 2 kolumny
    
    # Stwórz tabelę
    table = Table(table_data, colWidths=col_widths, repeatRows=0)
    
    # Style
    styles = []
    
    # Nagłówek (jeśli podano kolor tła)
    if header_bg:
        styles.extend([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ])
    
    # Podstawowe style z zawijaniem tekstu
    styles.extend([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'BodyFont'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ])
    
    # Kolorowanie zebra - subtelne
    if zebra:
        for i in range(len(table_data)):
            if i % 2 == 1:
                styles.append(('BACKGROUND', (0, i), (-1, i), colors.whitesmoke))
    
    # Styl dla pierwszej kolumny (klucze) - jasny szary tło
    styles.extend([
        ('FONTNAME', (0, 0), (0, -1), 'BodyFont'),
        ('FONTSIZE', (0, 0), (0, -1), 8),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
    ])
    
    table.setStyle(TableStyle(styles))
    return table


def create_detailed_entitlements_table(entitlements: List[Dict[str, Any]]) -> Table:
    """
    Tworzy tabelę ze szczegółowymi uprawnieniami beneficjenta
    
    Args:
        entitlements: Lista szczegółowych uprawnień
        
    Returns:
        Table z szczegółowymi uprawnieniami
    """
    if not entitlements:
        return None
    
    # Przygotuj style
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontName = 'BodyFont'
    normal_style.fontSize = 9
    
    table_data = []
    
    for i, entitlement in enumerate(entitlements, 1):
        # Nagłówek uprawnienia
        typ = entitlement.get("typ", "")
        header_text = f"{i}. {typ}"
        table_data.append([Paragraph(header_text, normal_style), Paragraph("", normal_style)])
        
        # Szczegóły uprawnienia
        if entitlement.get("kod"):
            kod = safe_pandas_to_str(entitlement["kod"]) or "—"
            table_data.append([Paragraph("Kod uprawnień", normal_style), Paragraph(kod, normal_style)])
        if entitlement.get("rodzaj"):
            rodzaj = safe_pandas_to_str(entitlement["rodzaj"]) or "—"
            table_data.append([Paragraph("Rodzaj uprawnień", normal_style), Paragraph(rodzaj, normal_style)])
        if entitlement.get("ilosc") and entitlement.get("jednostka_miary"):
            ilosc = safe_pandas_to_str(entitlement["ilosc"])
            jednostka = safe_pandas_to_str(entitlement["jednostka_miary"])
            wielkosc = f"{ilosc} {jednostka}"
            table_data.append([Paragraph("Wielkość udziału", normal_style), Paragraph(wielkosc, normal_style)])
        if entitlement.get("rodzaj_uprzywilejowania"):
            uprzyw = safe_pandas_to_str(entitlement["rodzaj_uprzywilejowania"]) or "—"
            table_data.append([Paragraph("Rodzaj uprzywilejowania", normal_style), Paragraph(uprzyw, normal_style)])
        if entitlement.get("opis_uprzywilejowania"):
            opis = safe_pandas_to_str(entitlement["opis_uprzywilejowania"]) or "—"
            table_data.append([Paragraph("Opis uprzywilejowania", normal_style), Paragraph(opis, normal_style)])
        
        # Dodaj pustą linię między uprawnieniami (oprócz ostatniego)
        if i < len(entitlements):
            table_data.append([Paragraph("", normal_style), Paragraph("", normal_style)])
    
    # Szerokości kolumn - równomierne rozłożenie
    available_width = 170 * mm
    col_widths = [available_width / 2, available_width / 2]
    
    table = Table(table_data, colWidths=col_widths)
    
    # Style tabeli - identyczne jak w create_key_value_table
    table_styles = []
    
    # Podstawowe style
    table_styles.extend([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ])
    
    # Kolorowanie - jasny szary dla kolumny z etykietami
    table_styles.append(("BACKGROUND", (0,0), (0,-1), colors.lightgrey))
    
    # Zebra coloring dla wierszy z danymi (pomijając nagłówki)
    for i, row in enumerate(table_data):
        if len(row) >= 2 and hasattr(row[0], 'text'):
            if row[0].text and row[0].text.startswith(("Kod", "Rodzaj", "Wielkość", "Opis")):
                if i % 2 == 1:  # Co drugi wiersz z danymi
                    table_styles.append(("BACKGROUND", (1,i), (1,i), colors.whitesmoke))
    
    table.setStyle(TableStyle(table_styles))
    return table


def create_beneficiaries_table(beneficiaries: List[Dict[str, Any]]) -> Table:
    """
    Tworzy tabelę beneficjentów
    
    Args:
        beneficiaries: Lista słowników z danymi beneficjentów
        
    Returns:
        Obiekt Table
    """
    if not beneficiaries:
        return Table([["Brak beneficjentów"]], colWidths=[150*mm])
    
    # Nagłówki
    headers = ["Imię i nazwisko", "PESEL", "Obywatelstwo", "Kraj zamieszkania", "Uprawnienia"]
    
    # Przygotuj dane
    table_data = [headers]
    
    for beneficiary in beneficiaries:
        # Imię i nazwisko
        imie = beneficiary.get("imie", "")
        nazwisko = beneficiary.get("nazwisko", "")
        imiona_kolejne = beneficiary.get("imiona_kolejne", "")
        
        # Pełne imię (łącznie z kolejnymi imionami)
        if imiona_kolejne:
            full_name = f"{imie} {imiona_kolejne} {nazwisko}".strip()
        else:
            full_name = f"{imie} {nazwisko}".strip()
        
        if not full_name:
            full_name = "—"
        
        # PESEL
        pesel = beneficiary.get("pesel", "") or "—"
        
        # Obywatelstwo
        obywatelstwo = beneficiary.get("obywatelstwo", "") or "—"
        
        # Kraj zamieszkania
        kraj = beneficiary.get("panstwo_zamieszkania", "") or "—"
        
        # Uprawnienia
        uprawnienia = beneficiary.get("uprawnienia", [])
        uprawnienia_text = ", ".join(uprawnienia) if uprawnienia else "—"
        
        # Użyj Paragraph dla zawijania tekstu
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = 'BodyFont'
        normal_style.fontSize = 9
        
        # Utwórz Paragraph dla długich tekstów
        full_name_para = Paragraph(full_name, normal_style)
        uprawnienia_para = Paragraph(uprawnienia_text, normal_style)
        
        table_data.append([full_name_para, pesel, obywatelstwo, kraj, uprawnienia_para])
    
    # Dopasuj szerokości kolumn do strony A4 (210mm) minus marginesy (40mm) = 170mm dostępne
    available_width = 170 * mm  # Dostępna szerokość na stronie A4
    col_widths = [available_width / 5] * 5  # Równomierne rozłożenie na 5 kolumn
    
    # Stwórz tabelę z dopasowaniem do strony i zawijaniem tekstu
    table = Table(table_data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
    
    # Style z subtelnym kolorowaniem i zawijaniem tekstu
    styles = [
        # Nagłówek - jasny szary tło
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTNAME', (0, 0), (-1, 0), 'BodyFont'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Zawartość z zawijaniem tekstu
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'BodyFont'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        
        # Kolorowanie zebra - bardzo subtelne
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
    ]
    
    table.setStyle(TableStyle(styles))
    return table


def create_address_table(address_data: Dict[str, str]) -> Table:
    """
    Tworzy tabelę adresu
    
    Args:
        address_data: Słownik z danymi adresu
        
    Returns:
        Obiekt Table
    """
    # Przygotuj dane adresu
    address_items = [
        ("Województwo", address_data.get("wojewodztwo", "")),
        ("Powiat", address_data.get("powiat", "")),
        ("Gmina", address_data.get("gmina", "")),
        ("Miejscowość", address_data.get("miejscowosc", "")),
        ("Ulica", address_data.get("ulica", "")),
        ("Nr domu", address_data.get("nr_domu", "")),
        ("Nr lokalu", address_data.get("nr_lokalu", "")),
        ("Kod pocztowy", address_data.get("kod_pocztowy", "")),
    ]
    
    return create_key_value_table(address_items, col_widths=[40*mm, None], zebra=True)


def create_entity_info_table(entity_data: Dict[str, Any]) -> Table:
    """
    Tworzy tabelę informacji o podmiocie
    
    Args:
        entity_data: Słownik z danymi podmiotu
        
    Returns:
        Obiekt Table
    """
    # Podstawowe informacje
    basic_info = [
        ("Nazwa", entity_data.get("nazwa", "")),
        ("NIP", entity_data.get("nip", "")),
        ("KRS", entity_data.get("krs", "")),
        ("Forma organizacyjna", entity_data.get("forma", "")),
    ]
    
    return create_key_value_table(basic_info, col_widths=[60*mm, None], zebra=True)


def create_meta_info_table(meta_data: Dict[str, str]) -> Table:
    """
    Tworzy tabelę metainformacji
    
    Args:
        meta_data: Słownik z metadanymi
        
    Returns:
        Obiekt Table
    """
    meta_items = [
        ("Identyfikator złożonego wniosku", meta_data.get("id_wniosku", "")),
        ("Data i godzina złożenia wniosku", meta_data.get("data_zlozenia", "")),
        ("Data i czas udostępnienia wniosku", meta_data.get("data_udostepnienia", "")),
    ]
    
    return create_key_value_table(meta_items, col_widths=[80*mm, None], zebra=True)


def create_declarant_table(declarant_data: Dict[str, str]) -> Table:
    """
    Tworzy tabelę danych zgłaszającego
    
    Args:
        declarant_data: Słownik z danymi zgłaszającego
        
    Returns:
        Obiekt Table
    """
    if not declarant_data:
        return Table([["Brak danych o zgłaszającym"]], colWidths=[150*mm])
    
    declarant_items = [
        ("Imię", declarant_data.get("imie", "")),
        ("Nazwisko", declarant_data.get("nazwisko", "")),
        ("PESEL", declarant_data.get("pesel", "")),
        ("Funkcja", declarant_data.get("funkcja", "")),
    ]
    
    return create_key_value_table(declarant_items, col_widths=[40*mm, None], zebra=True)
