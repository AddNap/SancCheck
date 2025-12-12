#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty test pól
"""

from lxml import etree

def test_fields():
    """Test pól"""
    print("Test pól...")
    
    try:
        # Wczytaj XML z poprzedniego debug
        with open("debug_inner_xml.xml", "rb") as f:
            xml_bytes = f.read()
        
        print(f"XML wczytany: {len(xml_bytes)} bajtów")
        
        # Parsuj XML
        root = etree.fromstring(xml_bytes)
        print("✓ XML sparsowany")
        
        # Sprawdź wszystkie elementy
        print("\n🔍 Wszystkie elementy w XML:")
        all_elements = set()
        for elem in root.iter():
            if elem.tag:
                # Usuń namespace
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                all_elements.add(tag_name)
        
        for elem_name in sorted(all_elements):
            print(f"  - {elem_name}")
        
        # Sprawdź konkretne pola
        print(f"\n📋 Konkretne pola:")
        fields_to_check = [
            "Nazwa", "NIP", "KRS", "KodFormyOrganizacyjnej", "OpisFormyOrganizacyjnej",
            "KodPocztowy", "Miejscowosc", "Ulica", "NrDomu", "NrLokalu",
            "Wojewodztwo", "Powiat", "Gmina",
            "PierwszeImie", "Nazwisko", "PESEL"
        ]
        
        for field in fields_to_check:
            try:
                results = root.xpath(f".//*[local-name()='{field}']/text()")
                if results:
                    print(f"  {field}: '{results[0]}'")
                else:
                    print(f"  {field}: BRAK")
            except Exception as e:
                print(f"  {field}: BŁĄD - {e}")
        
    except Exception as e:
        print(f"✗ Błąd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fields()
    input("\nNaciśnij Enter...")
