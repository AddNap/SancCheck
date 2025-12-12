"""
Pomocnicze funkcje do parsowania XML CRBR
"""

from typing import Dict, Any, List, Optional
from lxml import etree


def get_text_by_local_name(root, tag_name: str) -> str:
    """
    Pobiera tekst z elementu XML na podstawie nazwy lokalnej (ignoruje namespace)
    
    Args:
        root: Element XML
        tag_name: Nazwa tagu do wyszukania
        
    Returns:
        Tekst z elementu lub pusty string
    """
    try:
        results = root.xpath(f".//*[local-name()='{tag_name}']/text()")
        return results[0].strip() if results else ""
    except Exception as e:
        print(f"Błąd w get_text_by_local_name dla '{tag_name}': {e}")
        return ""


def find_application_id(root) -> str:
    """
    Znajduje identyfikator wniosku w różnych możliwych formatach
    
    Args:
        root: Element XML root
        
    Returns:
        Identyfikator wniosku lub pusty string
    """
    # Lista możliwych nazw identyfikatora
    id_names = [
        "identyfikatorZlozonegoWniosku",
        "IdentyfikatorWniosku", 
        "identyfikatorWniosku",
        "IdentyfikatorZlozonegoWniosku"
    ]
    
    # Najpierw spróbuj standardowego findtext
    for id_name in id_names:
        id_value = (root.findtext(f".//{id_name}") or "").strip()
        if id_value:
            return id_value
    
    # Jeśli nie znaleziono, użyj xpath z local-name
    for id_name in id_names:
        try:
            results = root.xpath(f".//*[local-name()='{id_name}']/text()")
            if results:
                return results[0].strip()
        except:
            pass
    
    return ""


def extract_meta_data(root) -> Dict[str, str]:
    """
    Wyciąga metadane z XML
    
    Args:
        root: Element XML root
        
    Returns:
        Słownik z metadanymi
    """
    return {
        "id_wniosku": find_application_id(root),
        "data_udostepnienia": get_text_by_local_name(root, "DataICzasUdostepnieniaWniosku"),
        "data_zlozenia": get_text_by_local_name(root, "DataICzasZlozeniaWniosku"),
        "data_od": get_text_by_local_name(root, "DataPoczatkuPrezentacjiZgloszenia"),
        "data_do": get_text_by_local_name(root, "DataKoncaPrezentacjiZgloszenia"),
    }


def extract_entity_data(root) -> Dict[str, Any]:
    """
    Wyciąga dane podmiotu z XML
    
    Args:
        root: Element XML root
        
    Returns:
        Słownik z danymi podmiotu
    """
    podmiot = {
        "nazwa": get_text_by_local_name(root, "Nazwa"),
        "nip": get_text_by_local_name(root, "NIP"),
        "krs": get_text_by_local_name(root, "KRS"),
        "forma": get_text_by_local_name(root, "OpisFormyOrganizacyjnej"),
    }
    
    adres = {
        "wojewodztwo": get_text_by_local_name(root, "Wojewodztwo"),
        "powiat": get_text_by_local_name(root, "Powiat"),
        "gmina": get_text_by_local_name(root, "Gmina"),
        "miejscowosc": get_text_by_local_name(root, "Miejscowosc"),
        "ulica": get_text_by_local_name(root, "Ulica"),
        "nr_domu": get_text_by_local_name(root, "NrDomu"),
        "nr_lokalu": get_text_by_local_name(root, "NrLokalu"),
        "kod_pocztowy": get_text_by_local_name(root, "KodPocztowy"),
    }
    
    podmiot["adres"] = adres
    return podmiot


def extract_beneficiary_data(beneficiary_element) -> Dict[str, Any]:
    """
    Wyciąga dane beneficjenta z elementu XML
    
    Args:
        beneficiary_element: Element XML beneficjenta
        
    Returns:
        Słownik z danymi beneficjenta
    """
    # Obywatelstwo
    obyw = ""
    oby_el = beneficiary_element.xpath(".//*[local-name()='Obywatelstwo']")
    if oby_el:
        obyw = get_text_by_local_name(oby_el[0], "Nazwa")

    # Kraj zamieszkania
    kraj = ""
    kraj_el = beneficiary_element.xpath(".//*[local-name()='KrajZamieszkania']")
    if kraj_el:
        kraj = get_text_by_local_name(kraj_el[0], "Nazwa")

    # Podstawowe dane
    rec = {
        "imie": get_text_by_local_name(beneficiary_element, "PierwszeImie"),
        "imiona_kolejne": get_text_by_local_name(beneficiary_element, "KolejneImiona"),
        "nazwisko": get_text_by_local_name(beneficiary_element, "Nazwisko"),
        "pesel": get_text_by_local_name(beneficiary_element, "PESEL"),
        "obywatelstwo": obyw,
        "panstwo_zamieszkania": kraj,
        "uprawnienia": []
    }

    # Uprawnienia - szczegółowe informacje
    uprawnienia = beneficiary_element.xpath(".//*[local-name()='InformacjaOUdzialach']")
    detailed_entitlements = []
    
    for upr in uprawnienia:
        entitlement_info = {}
        
        # Bezpośrednie uprawnienia właścicielskie
        bezposrednie = upr.xpath(".//*[local-name()='UprawnieniaWlascicielskieBezposrednie']")
        if bezposrednie:
            bezp_elem = bezposrednie[0]
            entitlement_info.update({
                "typ": "Bezpośrednie uprawnienia",
                "kod": get_text_by_local_name(bezp_elem, "KodUprawnienWlascicielskich"),
                "rodzaj": get_text_by_local_name(bezp_elem, "RodzajUprawnienWlascicielskich"),
                "jednostka_miary_kod": get_text_by_local_name(bezp_elem, "KodJednostkiMiary"),
                "jednostka_miary": get_text_by_local_name(bezp_elem, "JednostkaMiary"),
                "ilosc": get_text_by_local_name(bezp_elem, "Ilosc")
            })
            
            # Uprzywilejowania
            uprzyw = bezp_elem.xpath(".//*[local-name()='InformacjaOUprzywilejowaniu']")
            if uprzyw:
                uprz_elem = uprzyw[0]
                entitlement_info.update({
                    "kod_uprzywilejowania": get_text_by_local_name(uprz_elem, "KodUprzywilejowania"),
                    "rodzaj_uprzywilejowania": get_text_by_local_name(uprz_elem, "RodzajUprzywilejowania"),
                    "opis_uprzywilejowania": get_text_by_local_name(uprz_elem, "OpisUprzywilejowania")
                })
        
        # Pośrednie uprawnienia właścicielskie
        posrednie = upr.xpath(".//*[local-name()='UprawnieniaWlascicielskiePosrednie']")
        if posrednie:
            posr_elem = posrednie[0]
            entitlement_info.update({
                "typ": "Pośrednie uprawnienia",
                "kod": get_text_by_local_name(posr_elem, "KodUprawnienWlascicielskich"),
                "rodzaj": get_text_by_local_name(posr_elem, "RodzajUprawnienWlascicielskich"),
                "jednostka_miary_kod": get_text_by_local_name(posr_elem, "KodJednostkiMiary"),
                "jednostka_miary": get_text_by_local_name(posr_elem, "JednostkaMiary"),
                "ilosc": get_text_by_local_name(posr_elem, "Ilosc")
            })
        
        # Inne uprawnienia
        inne = upr.xpath(".//*[local-name()='InneUprawnienia']")
        if inne:
            inne_elem = inne[0]
            # Pobierz opis z RodzajInnychUprawnien/Opis
            rodzaj_elem = inne_elem.xpath(".//*[local-name()='RodzajInnychUprawnien']")
            if rodzaj_elem:
                opis = get_text_by_local_name(rodzaj_elem[0], "Opis")
                kod = get_text_by_local_name(rodzaj_elem[0], "Kod")
            else:
                opis = ""
                kod = ""
            
            entitlement_info.update({
                "typ": "Inne uprawnienia",
                "rodzaj": opis,
                "kod": kod
            })
        
        if entitlement_info:
            detailed_entitlements.append(entitlement_info)
            # Dodaj też do listy uprawnień dla kompatybilności wstecznej
            if entitlement_info.get("rodzaj"):
                rec["uprawnienia"].append(entitlement_info["rodzaj"])
    
    rec["szczegolowe_uprawnienia"] = detailed_entitlements
    
    return rec


def extract_declarant_data(root) -> Dict[str, str]:
    """
    Wyciąga dane zgłaszającego z XML
    
    Args:
        root: Element XML root
        
    Returns:
        Słownik z danymi zgłaszającego
    """
    zglaszajacy = root.xpath(".//*[local-name()='Zglaszajacy']")
    if not zglaszajacy:
        return {}
    
    zg = zglaszajacy[0]
    
    # Funkcja
    funkcja = ""
    lista_funkcji = zg.xpath(".//*[local-name()='ListaFunkcjiZglaszajacego']")
    if lista_funkcji:
        funkcje = lista_funkcji[0].xpath(".//*[local-name()='Funkcja']")
        if funkcje:
            funkcja = get_text_by_local_name(funkcje[0], "Opis")
    
    # Obywatelstwo
    obyw = ""
    oby_el = zg.xpath(".//*[local-name()='Obywatelstwo']")
    if oby_el:
        obyw = get_text_by_local_name(oby_el[0], "Nazwa")

    # Kraj zamieszkania
    kraj = ""
    kraj_el = zg.xpath(".//*[local-name()='KrajZamieszkania']")
    if kraj_el:
        kraj = get_text_by_local_name(kraj_el[0], "Nazwa")

    return {
        "imie": get_text_by_local_name(zg, "PierwszeImie"),
        "imiona_kolejne": get_text_by_local_name(zg, "KolejneImiona"),
        "nazwisko": get_text_by_local_name(zg, "Nazwisko"),
        "pesel": get_text_by_local_name(zg, "PESEL"),
        "data_urodzenia": get_text_by_local_name(zg, "DataUrodzenia"),
        "obywatelstwo": obyw,
        "kraj_zamieszkania": kraj,
        "rodzaj_reprezentacji": get_text_by_local_name(zg, "RodzajReprezentacji"),
        "inne_informacje": get_text_by_local_name(zg, "InneInformacje"),
        "funkcja": funkcja
    }


def parse_crbr_xml_refactored(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Refaktoryzowana funkcja parsowania XML CRBR
    
    Args:
        xml_bytes: Bajty XML do sparsowania
        
    Returns:
        Słownik z danymi CRBR
    """
    root = etree.fromstring(xml_bytes)
    
    # Inicjalizacja struktury danych
    data = {
        "meta": extract_meta_data(root),
        "podmiot": extract_entity_data(root),
        "beneficjenci": [],
        "zglaszajacy": extract_declarant_data(root)
    }
    
    # Beneficjenci
    beneficjenci = root.xpath(".//*[local-name()='BeneficjentRzeczywisty']")
    for b in beneficjenci:
        beneficiary_data = extract_beneficiary_data(b)
        data["beneficjenci"].append(beneficiary_data)
    
    return data
