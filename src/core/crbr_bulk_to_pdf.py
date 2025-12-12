#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crbr_bulk_to_pdf.py — PRO wersja (Platypus)

- Profesjonalny PDF (Platypus, automatyczna paginacja, style)
- PL diakrytyki (DejaVuSans.ttf; fallback do Helvetica)
- Dynamiczny IP + czas (Europe/Warsaw)
- Lepszy layout Beneficjentów (tabele, brak kolizji)
- SOAP 1.2 'action' + retry/backoff
- Fallback na utf8_config, walidacja CSV/NIP
"""

import os
import re
import sys
import time
import argparse
import random
import socket
import sys
from typing import List, Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import pandas as pd
from lxml import etree

# Logging
from utils.logger_config import setup_logging, get_logger, log_soap_request, log_soap_response, log_pdf_generation, log_error

# ReportLab (Platypus)
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, Flowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Import naszych modułów pomocniczych
from utils.xml_parsing_helpers import parse_crbr_xml_refactored
from utils.pdf_table_helpers import (
    create_key_value_table, create_beneficiaries_table, 
    create_address_table, create_entity_info_table,
    create_meta_info_table, create_declarant_table,
    create_detailed_entitlements_table
)

# Endpoint + namespaces (MF, ApiPrzegladoweCRBR v3.0.4)
CRBR_ENDPOINT = "https://bramka-crbr.mf.gov.pl:5058/uslugiBiznesowe/uslugiESB/AP/ApiPrzegladoweCRBR/2022/12/01"
NS_SOAP = "http://www.w3.org/2003/05/soap-envelope"
NS_AP   = "http://www.mf.gov.pl/uslugiBiznesowe/uslugiESB/AP/ApiPrzegladoweCRBR/2022/12/01"
NS_XSD  = "http://www.mf.gov.pl/schematy/AP/ApiPrzegladoweCRBR/2022/12/01"
SOAP_ACTION = f"{NS_AP}/PobierzInformacjeOSpolkachIBeneficjentach"

HEADERS = {
    # SOAP 1.2 — action w Content-Type
    "Content-Type": f'application/soap+xml; charset=utf-8; action="{SOAP_ACTION}"'
}

# ---------- UTF-8 fallback ----------
try:
    from utils.utf8_config import setup_utf8, get_csv_encoding
except Exception:
    def setup_utf8():  # no-op
        pass
    def get_csv_encoding():
        return "utf-8"

# ---------- Sanctions checking ----------

def check_contractor_sanctions(crbr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Sprawdza kontrahenta pod kątem list sankcyjnych na podstawie danych CRBR
    
    Args:
        crbr_data: Dane kontrahenta z CRBR
        
    Returns:
        Lista dopasowań sankcyjnych lub None jeśli brak dopasowań
    """
    try:
        # Wczytaj dane sankcyjne
        sanctions_data = load_sanctions_data()
        if not sanctions_data:
            return None
        
        # Wyciągnij dane kontrahenta
        contractor_data = extract_contractor_data_from_crbr(crbr_data)
        
        # Sprawdź pod kątem list sankcyjnych
        matches = []
        
        # Sprawdź w danych MF
        if sanctions_data['mf'] is not None:
            mf_matches = check_against_mf_sanctions(contractor_data, sanctions_data['mf'])
            matches.extend(mf_matches)
        
        # Sprawdź w danych MSWiA
        if sanctions_data['mswia'] is not None:
            mswia_matches = check_against_mswia_sanctions(contractor_data, sanctions_data['mswia'])
            matches.extend(mswia_matches)
        
        # Sprawdź w danych UE
        if sanctions_data['eu'] is not None:
            eu_matches = check_against_eu_sanctions(contractor_data, sanctions_data['eu'])
            matches.extend(eu_matches)
        
        return matches if matches else None
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Błąd sprawdzania sankcji: {e}")
        return None

def load_sanctions_data():
    """Wczytuje dane sankcyjne z plików Excel"""
    try:
        import glob
        
        sanctions_dir = os.path.join("data", "sanctions")
        if not os.path.exists(sanctions_dir):
            return None
        
        sanctions_data = {
            'mf': None,
            'mswia': None,
            'eu': None
        }
        
        # Wczytaj dane MF
        mf_files = glob.glob(os.path.join(sanctions_dir, "mf_sanctions_*.xlsx"))
        mf_csv_files = glob.glob(os.path.join(sanctions_dir, "mf_sanctions_*.csv"))
        if mf_files:
            latest_mf = max(mf_files, key=os.path.getctime)
            sanctions_data['mf'] = pd.read_excel(latest_mf)
        elif mf_csv_files:
            latest_mf = max(mf_csv_files, key=os.path.getctime)
            sanctions_data['mf'] = pd.read_csv(latest_mf, encoding='utf-8')
        
        # Wczytaj dane MSWiA
        mswia_files = glob.glob(os.path.join(sanctions_dir, "mswia_sanctions_*.xlsx"))
        mswia_csv_files = glob.glob(os.path.join(sanctions_dir, "mswia_sanctions_*.csv"))
        if mswia_files:
            latest_mswia = max(mswia_files, key=os.path.getctime)
            sanctions_data['mswia'] = pd.read_excel(latest_mswia)
        elif mswia_csv_files:
            latest_mswia = max(mswia_csv_files, key=os.path.getctime)
            sanctions_data['mswia'] = pd.read_csv(latest_mswia, encoding='utf-8')
        
        # Wczytaj dane UE (jeśli istnieją)
        eu_files = glob.glob(os.path.join(sanctions_dir, "eu_sanctions_*.xlsx"))
        eu_csv_files = glob.glob(os.path.join(sanctions_dir, "eu_sanctions_*.csv"))
        if eu_files:
            latest_eu = max(eu_files, key=os.path.getctime)
            sanctions_data['eu'] = pd.read_excel(latest_eu)
        elif eu_csv_files:
            latest_eu = max(eu_csv_files, key=os.path.getctime)
            sanctions_data['eu'] = pd.read_csv(latest_eu, encoding='utf-8')
        
        return sanctions_data
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Błąd wczytywania danych sankcyjnych: {e}")
        return None

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

def extract_contractor_data_from_crbr(crbr_data: Dict[str, Any]) -> Dict[str, str]:
    """Wyciąga dane kontrahenta z danych CRBR"""
    contractor_data = {
        'nip': '',
        'name': '',
        'pesel': '',
        'regon': ''
    }
    
    def safe_str(value) -> str:
        """Bezpiecznie konwertuje wartość na string"""
        if value is None:
            return ""
        try:
            # Handle pandas Timestamp objects
            if hasattr(value, 'strftime'):
                return str(value)
            return str(value).strip()
        except Exception:
            return ""
    
    # Wyciągnij NIP
    podmiot = crbr_data.get("podmiot", {})
    contractor_data['nip'] = safe_str(podmiot.get("nip", ""))
    
    # Wyciągnij nazwę
    contractor_data['name'] = safe_str(podmiot.get("nazwa", ""))
    
    # Wyciągnij PESEL (jeśli dostępny)
    contractor_data['pesel'] = safe_str(podmiot.get("pesel", ""))
    
    # Wyciągnij REGON (jeśli dostępny)
    contractor_data['regon'] = safe_str(podmiot.get("regon", ""))
    
    return contractor_data

def check_against_mf_sanctions(contractor_data: Dict[str, str], mf_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Sprawdza kontrahenta w danych MF"""
    matches = []
    
    try:
        for _, row in mf_data.iterrows():
            match_found = False
            match_reason = []
            
            # Sprawdź nazwę
            if 'Imiona i nazwiska' in mf_data.columns and pd.notna(row.get('Imiona i nazwiska')):
                if fuzzy_name_match(contractor_data['name'], safe_pandas_to_str(row['Imiona i nazwiska'])):
                    match_found = True
                    match_reason.append("Nazwa")
            
            # Sprawdź NIP we wszystkich kolumnach tekstowych
            text_columns = ['Dane identyfikacyjne osoby', 'Uzasadnienie wpisu na listę', 'Inne informacje']
            for col in text_columns:
                if col in mf_data.columns and pd.notna(row.get(col)):
                    try:
                        text_content = safe_pandas_to_str(row[col])
                        if contractor_data['nip'] in text_content:
                            match_found = True
                            match_reason.append(f"NIP (w {col})")
                            break  # Znaleziono NIP, nie trzeba sprawdzać dalej
                        
                        # Sprawdź PESEL w danych identyfikacyjnych
                        if col == 'Dane identyfikacyjne osoby' and contractor_data['pesel']:
                            if contractor_data['pesel'] in text_content:
                                match_found = True
                                match_reason.append("PESEL")
                    except Exception as e:
                        # Ignoruj błędy konwersji, kontynuuj sprawdzanie
                        continue
            
            if match_found:
                matches.append({
                    'source': 'MF',
                    'name': safe_pandas_to_str(row.get('Imiona i nazwiska', '')),
                    'nip': contractor_data['nip'],
                    'reason': ', '.join(match_reason),
                    'decision': safe_pandas_to_str(row.get('Uzasadnienie wpisu na listę', '')),
                    'date': safe_pandas_to_str(row.get('Data umieszczenia na liście', '')),
                    'status': 'Aktywny' if pd.isna(row.get('Data wykreślenia z listy')) else 'Nieaktywny'
                })
        
        return matches
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Błąd sprawdzania w danych MF: {e}")
        return []

def check_against_mswia_sanctions(contractor_data: Dict[str, str], mswia_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Sprawdza kontrahenta w danych MSWiA"""
    matches = []
    
    try:
        for _, row in mswia_data.iterrows():
            match_found = False
            match_reason = []
            
            # Sprawdź nazwę
            if 'Nazwisko i imię' in mswia_data.columns and pd.notna(row.get('Nazwisko i imię')):
                if fuzzy_name_match(contractor_data['name'], safe_pandas_to_str(row['Nazwisko i imię'])):
                    match_found = True
                    match_reason.append("Nazwa")
            
            # Sprawdź NIP we wszystkich kolumnach (nie tylko określonych)
            for col in mswia_data.columns:
                if pd.notna(row.get(col)):
                    try:
                        text_content = safe_pandas_to_str(row[col])
                        if contractor_data['nip'] in text_content:
                            match_found = True
                            match_reason.append(f"NIP (w {col})")
                            break  # Znaleziono NIP, nie trzeba sprawdzać dalej
                        
                        # Sprawdź PESEL w danych identyfikacyjnych
                        if contractor_data['pesel'] and contractor_data['pesel'] in text_content:
                            match_found = True
                            match_reason.append(f"PESEL (w {col})")
                            break
                    except Exception as e:
                        # Ignoruj błędy konwersji, kontynuuj sprawdzanie
                        continue
            
            if match_found:
                matches.append({
                    'source': 'MSWiA',
                    'name': safe_pandas_to_str(row.get('Nazwisko i imię', '')),
                    'citizenship': 'Brak danych',
                    'reason': ', '.join(match_reason),
                    'decision': safe_pandas_to_str(row.get('Uzasadnienie wpisu na listę', '')),
                    'date': safe_pandas_to_str(row.get('Data umieszczenia na liście', '')),
                    'status': 'Aktywny' if pd.isna(row.get('Data wykreślenia z listy ')) else 'Nieaktywny'
                })
        
        return matches
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Błąd sprawdzania w danych MSWiA: {e}")
        return []

def check_against_eu_sanctions(contractor_data: Dict[str, str], eu_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Sprawdza kontrahenta w danych UE"""
    matches = []
    
    try:
        for _, row in eu_data.iterrows():
            match_found = False
            match_reason = []
            
            # Sprawdź nazwę
            if 'Name' in eu_data.columns and pd.notna(row.get('Name')):
                if fuzzy_name_match(contractor_data['name'], safe_pandas_to_str(row['Name'])):
                    match_found = True
                    match_reason.append("Nazwa")
            
            if match_found:
                matches.append({
                    'source': 'UE',
                    'name': safe_pandas_to_str(row.get('Name', '')),
                    'country': safe_pandas_to_str(row.get('Country', '')),
                    'reason': ', '.join(match_reason),
                    'decision': safe_pandas_to_str(row.get('Decision', '')),
                    'date': safe_pandas_to_str(row.get('Date', '')),
                    'status': safe_pandas_to_str(row.get('Status', ''))
                })
        
        return matches
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Błąd sprawdzania w danych UE: {e}")
        return []

def fuzzy_name_match(name1: str, name2: str) -> bool:
    """Sprawdza czy nazwy są podobne (fuzzy matching)"""
    if not name1 or not name2:
        return False
    
    # Normalizuj nazwy
    name1_norm = normalize_name(name1)
    name2_norm = normalize_name(name2)
    
    # Sprawdź dokładne dopasowanie
    if name1_norm == name2_norm:
        return True
    
    # Sprawdź czy jedna nazwa zawiera drugą
    if name1_norm in name2_norm or name2_norm in name1_norm:
        return True
    
    # Sprawdź podobieństwo (uproszczone)
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, name1_norm, name2_norm).ratio()
    return similarity > 0.8  # 80% podobieństwa

def normalize_name(name: str) -> str:
    """Normalizuje nazwę do porównania"""
    if not name:
        return ""
    
    # Konwertuj na małe litery
    normalized = name.lower()
    
    # Zamień kropki na spacje przed usunięciem znaków interpunkcyjnych
    normalized = normalized.replace('.', ' ')
    
    # Usuń znaki interpunkcyjne (ale zachowaj spacje)
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Usuń dodatkowe spacje
    normalized = ' '.join(normalized.split())
    
    return normalized

# ---------- SOAP helpers ----------

def build_soap_request_by_nip(nip: str) -> bytes:
    Envelope = etree.Element(etree.QName(NS_SOAP, "Envelope"), nsmap={
        "soap": NS_SOAP,
        "ns": NS_AP,
        "ns1": NS_XSD
    })
    etree.SubElement(Envelope, etree.QName(NS_SOAP, "Header"))
    Body = etree.SubElement(Envelope, etree.QName(NS_SOAP, "Body"))
    req = etree.SubElement(Body, etree.QName(NS_AP, "PobierzInformacjeOSpolkachIBeneficjentach"))
    dane = etree.SubElement(req, "PobierzInformacjeOSpolkachIBeneficjentachDane")
    szczeg = etree.SubElement(dane, etree.QName(NS_XSD, "SzczegolyWniosku"))
    etree.SubElement(szczeg, etree.QName(NS_XSD, "NIP")).text = nip
    return etree.tostring(Envelope, encoding="utf-8", xml_declaration=True)

def fetch_xml_by_nip(nip: str, timeout: int = 45, retries: int = 3) -> bytes:
    logger = get_logger()
    payload = build_soap_request_by_nip(nip)
    last = None
    
    log_soap_request(nip, CRBR_ENDPOINT, logger)
    
    for attempt in range(retries):
        try:
            resp = requests.post(CRBR_ENDPOINT, data=payload, headers=HEADERS, timeout=timeout)
            log_soap_response(nip, resp.status_code, len(resp.content), logger)
            
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            last = e
            logger.warning(f"Próba {attempt + 1}/{retries} nieudana dla NIP {nip}: {e}")
            if attempt < retries - 1:
                sleep_time = (2 ** attempt) + random.random()
                logger.debug(f"Oczekiwanie {sleep_time:.2f}s przed kolejną próbą")
                time.sleep(sleep_time)
    
    log_error(nip, last, logger)
    raise RuntimeError(f"Nie udało się pobrać XML dla NIP {nip}: {last}")

def extract_inner_xml_from_soap(soap_xml: bytes) -> bytes:
    try:
        root = etree.fromstring(soap_xml)
    except Exception:
        return soap_xml
    ns = {"soap": NS_SOAP}
    body = root.find(".//soap:Body", namespaces=ns)
    if body is None:
        return soap_xml
    children = [c for c in body if isinstance(c.tag, str)]
    if children:
        return etree.tostring(children[0], encoding="utf-8", xml_declaration=True)
    return soap_xml

# ---------- Parsing ----------

def parse_crbr_xml(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Parsuje XML CRBR używając refaktoryzowanych funkcji pomocniczych
    
    Args:
        xml_bytes: Bajty XML do sparsowania
        
    Returns:
        Słownik z danymi CRBR
    """
    return parse_crbr_xml_refactored(xml_bytes)

# ---------- PDF (Platypus) ----------

def _pick_font_name() -> str:
    import os
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

def _styles(font_name: str):
    """Uproszczone style z jedną czcionką bez kolorów"""
    styles = getSampleStyleSheet()
    
    # Nadpisanie wszystkich stylów jedną czcionką
    for s in styles.byName.values():
        s.fontName = font_name
    
    # Uproszczone style bez kolorów
    styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=1, spaceAfter=12))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="H3", parent=styles["Heading3"], spaceBefore=8, spaceAfter=4))
    styles.add(ParagraphStyle(name="Meta", parent=styles["Normal"], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontSize=9, spaceAfter=2))
    styles.add(ParagraphStyle(name="Value", parent=styles["Normal"], fontSize=10))
    styles.add(ParagraphStyle(name="TableHeader", parent=styles["Normal"], fontSize=9))
    
    return styles

def _header_footer(canvas, doc, font_name: str):
    canvas.saveState()
    w, h = A4
    margin = 20 * mm
    # header: IP, data
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "-"
    now_pl = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y %H:%M:%S")
    canvas.setFont(font_name, 8)
    canvas.drawRightString(w - margin, h - margin + 4*mm, f"{ip}, {now_pl}")
    # footer: numer strony
    canvas.drawCentredString(w/2, margin - 8*mm, f"Strona {canvas.getPageNumber()}")
    canvas.restoreState()

def _kv_table(data, col_widths=None, zebra=False):
    # data = [(label, value), ...]
    table = Table(data, colWidths=col_widths)
    style = TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ])
    if zebra:
        for i in range(0, len(data), 2):
            style.add("BACKGROUND", (0,i), (-1,i), colors.whitesmoke)
    table.setStyle(style)
    return table

def render_pdf(data: Dict[str, Any], out_path: str):
    font_name = _pick_font_name()
    styles = _styles(font_name)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    story = []

    # Tytuł
    story.append(Paragraph("Wpisy Podmiotu w Centralnym Rejestrze Beneficjentów Rzeczywistych", styles["TitleCenter"]))
    story.append(Spacer(1, 6))

    # Meta (identyfikator, daty)
    meta = data.get("meta", {})
    meta_rows = [
        ("Identyfikator złożonego wniosku", meta.get("id_wniosku","") or "—"),
        ("Data i godzina złożenia wniosku", meta.get("data_zlozenia","") or "—"),
        ("Data i czas udostępnienia wniosku", meta.get("data_udostepnienia","") or "—"),
    ]
    story.append(create_meta_info_table(meta))
    story.append(Spacer(1, 6))

    # Kryteria wyszukiwania
    story.append(Paragraph("Kryteria wyszukiwania", styles["H2"]))
    podmiot = data.get("podmiot", {})
    krows = [
        ("NIP/identyfikator trustu", podmiot.get("nip","") or "—"),
        ("Data od", meta.get("data_od","") or "—"),
        ("Data do", meta.get("data_do","") or "—"),
    ]
    story.append(create_key_value_table(krows))  # Użyj domyślnego równomiernego rozłożenia
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Dokument pochodzi z Centralnego Rejestru Beneficjentów Rzeczywistych. "
        "Organem właściwym w sprawach CRBR jest minister właściwy do spraw finansów publicznych. "
        "Dokument nie wymaga dodatkowego podpisu.",
        styles["Small"]
    ))
    story.append(Spacer(1, 10))

    # Podstawowe dane Podmiotu
    story.append(Paragraph("Podstawowe dane Podmiotu", styles["H2"]))
    adr = podmiot.get("adres", {})
    left = [
        ("Początkowa data prezentacji zgłoszenia", meta.get('data_od','') or "—"),
        ("Nazwa podmiotu", podmiot.get("nazwa","") or "—"),
        ("NIP/identyfikator trustu", podmiot.get("nip","") or "—"),
        ("KRS", podmiot.get("krs","") or "—"),
        ("Forma organizacyjna", podmiot.get("forma","") or "—"),
    ]
    right = [
        ("Końcowa data prezentacji zgłoszenia", meta.get('data_do','') or "—"),
        ("Miejscowość", adr.get("miejscowosc","") or "—"),
        ("Kod pocztowy", adr.get("kod_pocztowy","") or "—"),
        ("Ulica", adr.get("ulica","") or "—"),
        ("Numer domu", adr.get("nr_domu","") or "—"),
        ("Numer lokalu", adr.get("nr_lokalu","") or "—"),
    ]

    # Dwie kolumny jako tabela 2xN
    max_rows = max(len(left), len(right))
    rows = []
    for i in range(max_rows):
        l = left[i] if i < len(left) else ("", "")
        r = right[i] if i < len(right) else ("", "")
        rows.append([Paragraph(l[0], styles["Meta"]),
                     Paragraph(l[1], styles["Value"]),
                     Paragraph(r[0], styles["Meta"]),
                     Paragraph(r[1], styles["Value"])]
                    )
    # Równomierne rozłożenie kolumn na stronie
    available_width = 170 * mm  # Dostępna szerokość na stronie A4
    col_widths = [available_width / 4] * 4  # Równomierne rozłożenie na 4 kolumny
    
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        # Subtelne kolorowanie - jasny szary dla kolumn z etykietami
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),  # Pierwsza kolumna (etykiety)
        ("BACKGROUND", (2,0), (2,-1), colors.lightgrey),  # Trzecia kolumna (etykiety)
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Dane Beneficjentów
    story.append(Paragraph("Beneficjenci rzeczywiści", styles["H2"]))

    bens = data.get("beneficjenci", [])
    if not bens:
        story.append(Paragraph("— brak danych beneficjentów —", styles["Meta"]))
    else:
        # Użyj funkcji z pdf_table_helpers - uproszczonej tabeli bez kolorów
        story.append(create_beneficiaries_table(bens))
        
        # Dodaj szczegółowe uprawnienia dla każdego beneficjenta
        story.append(Spacer(1, 8))
        story.append(Paragraph("Szczegółowe uprawnienia beneficjentów", styles["H3"]))
        
        for i, beneficiary in enumerate(bens, 1):
            imie = beneficiary.get("imie", "")
            nazwisko = beneficiary.get("nazwisko", "")
            imiona_kolejne = beneficiary.get("imiona_kolejne", "")
            
            if imiona_kolejne:
                full_name = f"{imie} {imiona_kolejne} {nazwisko}".strip()
            else:
                full_name = f"{imie} {nazwisko}".strip()
            
            story.append(Paragraph(f"{i}. {full_name}", styles["Meta"]))
            
            # Szczegółowe uprawnienia
            detailed_entitlements = beneficiary.get("szczegolowe_uprawnienia", [])
            if detailed_entitlements:
                entitlements_table = create_detailed_entitlements_table(detailed_entitlements)
                if entitlements_table:
                    story.append(entitlements_table)
            else:
                story.append(Paragraph("— brak szczegółowych uprawnień —", styles["Meta"]))
            
            if i < len(bens):  # Dodaj odstęp między beneficjentami (oprócz ostatniego)
                story.append(Spacer(1, 6))
    
    story.append(Spacer(1, 10))
    
    # Dane Zgłaszającego/Reprezentanta
    story.append(Paragraph("Zgłaszający/Reprezentant", styles["H2"]))
    
    zglaszajacy = data.get("zglaszajacy", {})
    if not zglaszajacy:
        story.append(Paragraph("— brak danych zgłaszającego —", styles["Meta"]))
    else:
        # Pełne imię (łącznie z kolejnymi imionami)
        imie = zglaszajacy.get("imie", "")
        imiona_kolejne = zglaszajacy.get("imiona_kolejne", "")
        nazwisko = zglaszajacy.get("nazwisko", "")
        
        if imiona_kolejne:
            pelne_imie = f"{imie} {imiona_kolejne} {nazwisko}".strip()
        else:
            pelne_imie = f"{imie} {nazwisko}".strip()
        
        # Utwórz tabelę z danymi zgłaszającego
        zglaszajacy_data = [
            ("Imię i nazwisko", pelne_imie or "—"),
            ("PESEL", zglaszajacy.get("pesel", "") or "—"),
            ("Data urodzenia", zglaszajacy.get("data_urodzenia", "") or "—"),
            ("Obywatelstwo", zglaszajacy.get("obywatelstwo", "") or "—"),
            ("Kraj zamieszkania", zglaszajacy.get("kraj_zamieszkania", "") or "—"),
            ("Rodzaj reprezentacji", zglaszajacy.get("rodzaj_reprezentacji", "") or "—"),
            ("Funkcja", zglaszajacy.get("funkcja", "") or "—"),
        ]
        
        # Usuń puste pola
        zglaszajacy_data = [(k, v) for k, v in zglaszajacy_data if v != "—"]
        
        if zglaszajacy_data:
            story.append(create_key_value_table(zglaszajacy_data, zebra=True))
        
        # Inne informacje (jeśli są)
        inne_info = zglaszajacy.get("inne_informacje", "")
        if inne_info:
            story.append(Paragraph("Inne informacje:", styles["Meta"]))
            story.append(Paragraph(inne_info, styles["Value"]))

    # Sekcja sankcyjna
    sanctions = data.get("sankcje")
    if sanctions:
        story.append(Spacer(1, 10))
        story.append(Paragraph("🚨 Sprawdzenie list sankcyjnych", styles["H2"]))
        
        for i, sanction in enumerate(sanctions, 1):
            story.append(Paragraph(f"<b>Dopasowanie {i}: {sanction['source']}</b>", styles["Meta"]))
            
            # Podstawowe informacje
            sanction_data = [
                ("Źródło", sanction.get('source', 'Brak')),
                ("Nazwa", sanction.get('name', 'Brak')),
                ("Powód dopasowania", sanction.get('reason', 'Brak')),
                ("Data umieszczenia", sanction.get('date', 'Brak')),
                ("Status", sanction.get('status', 'Brak'))
            ]
            
            # Dodaj dodatkowe pola w zależności od źródła
            if sanction.get('source') == 'MF' and sanction.get('nip'):
                sanction_data.append(("NIP", sanction.get('nip', 'Brak')))
            elif sanction.get('source') == 'MSWiA' and sanction.get('citizenship'):
                sanction_data.append(("Obywatelstwo", sanction.get('citizenship', 'Brak')))
            elif sanction.get('source') == 'UE' and sanction.get('country'):
                sanction_data.append(("Kraj", sanction.get('country', 'Brak')))
            
            # Usuń puste wartości
            sanction_data = [(k, v) for k, v in sanction_data if v != "Brak"]
            
            if sanction_data:
                story.append(create_key_value_table(sanction_data, zebra=True))
            
            # Decyzja/Uzasadnienie
            decision = sanction.get('decision', '')
            if decision:
                # Bezpiecznie konwertuj decision na string (obsługa Timestamp objects)
                try:
                    if hasattr(decision, 'strftime'):
                        decision_str = str(decision)
                    else:
                        decision_str = str(decision)
                except Exception:
                    decision_str = str(decision) if decision else ""
                
                if decision_str:
                    story.append(Paragraph("Decyzja/Uzasadnienie:", styles["Meta"]))
                    story.append(Paragraph(decision_str, styles["Value"]))
            
            if i < len(sanctions):  # Dodaj odstęp między dopasowaniami (oprócz ostatniego)
                story.append(Spacer(1, 6))
    else:
        # Dodaj informację o braku dopasowań
        story.append(Spacer(1, 10))
        story.append(Paragraph("✅ Sprawdzenie list sankcyjnych", styles["H2"]))
        story.append(Paragraph("Brak dopasowań na listach sankcyjnych MF, MSWiA i UE", styles["Meta"]))

    # Render z nagłówkiem/stopką
    def on_page(canvas, doc_):
        _header_footer(canvas, doc_, font_name)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

# ---------- Helpers ----------

def sanitize_filename(s: str) -> str:
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    s = s.strip("_") or "raport"
    return s[:80]  # skróć bardzo długie

def generate_pdf_from_xml_bytes(xml_bytes: bytes, out_dir: str, default_nip: str = "unknown") -> str:
    logger = get_logger()
    data = parse_crbr_xml(xml_bytes)
    nip = data.get("podmiot", {}).get("nip") or default_nip
    ident = data.get("meta", {}).get("id_wniosku") or "brak_id"
    fname = f"crbr_{sanitize_filename(nip)}_{sanitize_filename(ident)}.pdf"
    out_path = os.path.join(out_dir, fname)
    os.makedirs(out_dir, exist_ok=True)
    
    # Sprawdź sankcje przed renderowaniem PDF
    sanctions_data = check_contractor_sanctions(data)
    if sanctions_data:
        data["sankcje"] = sanctions_data
        logger.info(f"Znaleziono {len(sanctions_data)} dopasowań sankcyjnych dla NIP: {nip}")
    
    render_pdf(data, out_path)
    log_pdf_generation(nip, out_path, logger)
    return out_path

def generate_pdf_from_xml_bytes_with_sanctions_info(xml_bytes: bytes, out_dir: str, default_nip: str = "unknown") -> tuple:
    """
    Generuje PDF i zwraca informację o sankcjach
    
    Returns:
        tuple: (pdf_path, has_sanctions, sanctions_count)
    """
    logger = get_logger()
    data = parse_crbr_xml(xml_bytes)
    nip = data.get("podmiot", {}).get("nip") or default_nip
    ident = data.get("meta", {}).get("id_wniosku") or "brak_id"
    fname = f"crbr_{sanitize_filename(nip)}_{sanitize_filename(ident)}.pdf"
    out_path = os.path.join(out_dir, fname)
    os.makedirs(out_dir, exist_ok=True)
    
    # Sprawdź sankcje przed renderowaniem PDF
    sanctions_data = check_contractor_sanctions(data)
    has_sanctions = sanctions_data is not None and len(sanctions_data) > 0
    sanctions_count = len(sanctions_data) if sanctions_data else 0
    
    if sanctions_data:
        data["sankcje"] = sanctions_data
        logger.info(f"Znaleziono {len(sanctions_data)} dopasowań sankcyjnych dla NIP: {nip}")
    
    render_pdf(data, out_path)
    log_pdf_generation(nip, out_path, logger)
    return out_path, has_sanctions, sanctions_count

def _is_valid_nip(nip: str) -> bool:
    """Sprawdza czy NIP jest poprawny (format + suma kontrolna)"""
    from utils.nip_validator import validate_nip
    is_valid, _ = validate_nip(nip)
    return is_valid

def bulk_from_csv(csv_path: str, out_dir: str, pause_sec: float = 0.6, timeout: int = 30) -> List[str]:
    logger = get_logger()
    logger.info(f"Rozpoczynanie przetwarzania CSV: {csv_path}")
    
    df = pd.read_csv(csv_path, dtype=str, encoding=get_csv_encoding())
    if "nip" not in df.columns:
        error_msg = "CSV musi zawierać kolumnę 'nip'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Wczytano {len(df)} wierszy z CSV")
    
    df["nip"] = df["nip"].fillna("").str.replace(r"\D", "", regex=True).str.strip()
    valid_nips = df[df["nip"].map(_is_valid_nip)]
    
    logger.info(f"Znaleziono {len(valid_nips)} poprawnych NIP-ów")
    
    generated = []
    for i, nip in enumerate(valid_nips["nip"], 1):
        try:
            logger.info(f"Przetwarzanie NIP {i}/{len(valid_nips)}: {nip}")
            soap = fetch_xml_by_nip(nip, timeout=timeout)
            inner = extract_inner_xml_from_soap(soap)
            pdf_path = generate_pdf_from_xml_bytes(inner, out_dir, default_nip=nip)
            generated.append(pdf_path)
            time.sleep(pause_sec)
        except Exception as e:
            log_error(nip, e, logger)
    
    logger.info(f"Zakończono przetwarzanie. Wygenerowano {len(generated)} PDF-ów")
    return generated

# ---------- CLI ----------

def main():
    setup_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="ścieżka do CSV z kolumną 'nip'")
    ap.add_argument("--nip", help="pojedynczy NIP do pobrania")
    ap.add_argument("--xml", help="lokalny raport XML (z portalu lub wnętrze SOAP)")
    ap.add_argument("--out", required=True, help="katalog wyjściowy na PDF-y")
    ap.add_argument("--timeout", type=int, default=30, help="timeout na zapytanie SOAP (sekundy)")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="poziom logowania")
    ap.add_argument("--log-file", help="plik logów (opcjonalny)")
    args = ap.parse_args()
    
    # Konfiguracja logowania
    logger = setup_logging(
        level=args.log_level,
        log_file=args.log_file,
        console_output=True
    )
    logger.info("Aplikacja SancCheck uruchomiona")

    os.makedirs(args.out, exist_ok=True)
    generated = []

    if args.xml:
        logger.info(f"Przetwarzanie pliku XML: {args.xml}")
        with open(args.xml, "rb") as f:
            xml_bytes = f.read()
        pdf_path = generate_pdf_from_xml_bytes(xml_bytes, args.out)
        generated.append(pdf_path)

    if args.nip:
        from utils.nip_validator import validate_nip
        is_valid, error_msg = validate_nip(args.nip)
        if not is_valid:
            logger.error(f"Niepoprawny NIP: {error_msg}")
            sys.exit(2)
        soap = fetch_xml_by_nip(args.nip, timeout=args.timeout)
        inner = extract_inner_xml_from_soap(soap)
        pdf_path = generate_pdf_from_xml_bytes(inner, args.out, default_nip=args.nip)
        generated.append(pdf_path)

    if args.csv:
        generated.extend(bulk_from_csv(args.csv, args.out, timeout=args.timeout))

    if not generated:
        logger.error("Nie podano --xml, --nip ani --csv. Nic do zrobienia.")
        sys.exit(2)

    logger.info(f"Wygenerowano {len(generated)} plików PDF")
    print("Wygenerowane pliki:")
    for p in generated:
        print(p)

if __name__ == "__main__":
    main()
