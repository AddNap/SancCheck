# -*- coding: utf-8 -*-
"""
Testy jednostkowe dla parsowania XML CRBR
"""

import unittest
from lxml import etree
from crbr_bulk_to_pdf import parse_crbr_xml


class TestCRBRParsing(unittest.TestCase):
    """Testy dla parsowania XML CRBR"""
    
    def setUp(self):
        """Przygotowanie danych testowych"""
        self.sample_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <PobierzInformacjeOSpolkachIBeneficjentachOdpowiedzDane>
            <IdentyfikatorWniosku>TEST123456789</IdentyfikatorWniosku>
            <DataICzasZlozeniaWniosku>2023-01-01T12:00:00</DataICzasZlozeniaWniosku>
            <DataICzasUdostepnieniaWniosku>2023-01-01T12:01:00</DataICzasUdostepnieniaWniosku>
            <DataOd>2023-01-01</DataOd>
            <DataDo>2023-12-31</DataDo>
            
            <ListaInformacjiOSpolkachIBeneficjentach>
                <SpolkaIBeneficjenci>
                    <Nazwa>TEST SPÓŁKA Z O.O.</Nazwa>
                    <NIP>1234567890</NIP>
                    <KRS>0000123456</KRS>
                    <KodFormyOrganizacyjnej>130</KodFormyOrganizacyjnej>
                    <OpisFormyOrganizacyjnej>Spółka z ograniczoną odpowiedzialnością</OpisFormyOrganizacyjnej>
                    <KodPocztowy>00-001</KodPocztowy>
                    <Miejscowosc>Warszawa</Miejscowosc>
                    <Ulica>Testowa</Ulica>
                    <NrDomu>1</NrDomu>
                    <NrLokalu>2</NrLokalu>
                    <Teryt>
                        <Wojewodztwo>MAZOWIECKIE</Wojewodztwo>
                        <Powiat>WARSZAWSKI</Powiat>
                        <Gmina>WARSZAWA</Gmina>
                    </Teryt>
                    
                    <ListaBeneficjentowRzeczywistych>
                        <BeneficjentRzeczywisty>
                            <PierwszeImie>Jan</PierwszeImie>
                            <KolejneImiona>Marian</KolejneImiona>
                            <Nazwisko>Kowalski</Nazwisko>
                            <PESEL>12345678901</PESEL>
                            <Obywatelstwo>
                                <Nazwa>POLSKA</Nazwa>
                            </Obywatelstwo>
                            <KrajZamieszkania>
                                <Nazwa>POLSKA</Nazwa>
                            </KrajZamieszkania>
                            <ListaInformacjiOUdzialach>
                                <InformacjaOUdzialach>
                                    <InneUprawnienia>
                                        <RodzajInnychUprawnien>wspólnik</RodzajInnychUprawnien>
                                    </InneUprawnienia>
                                </InformacjaOUdzialach>
                            </ListaInformacjiOUdzialach>
                        </BeneficjentRzeczywisty>
                    </ListaBeneficjentowRzeczywistych>
                    
                    <ListaReprezentantow>
                        <Reprezentant>
                            <PierwszeImie>Anna</PierwszeImie>
                            <Nazwisko>Nowak</Nazwisko>
                            <PESEL>98765432109</PESEL>
                            <ListaFunkcjiZglaszajacego>
                                <Funkcja>
                                    <Opis>prezes zarządu</Opis>
                                </Funkcja>
                            </ListaFunkcjiZglaszajacego>
                        </Reprezentant>
                    </ListaReprezentantow>
                </SpolkaIBeneficjenci>
            </ListaInformacjiOSpolkachIBeneficjentach>
        </PobierzInformacjeOSpolkachIBeneficjentachOdpowiedzDane>"""
    
    def test_parse_meta_data(self):
        """Test parsowania metadanych"""
        data = parse_crbr_xml(self.sample_xml)
        
        self.assertIn("meta", data)
        meta = data["meta"]
        
        self.assertEqual(meta["id_wniosku"], "TEST123456789")
        self.assertEqual(meta["data_zlozenia"], "2023-01-01T12:00:00")
        self.assertEqual(meta["data_udostepnienia"], "2023-01-01T12:01:00")
        self.assertEqual(meta["data_od"], "2023-01-01")
        self.assertEqual(meta["data_do"], "2023-12-31")
    
    def test_parse_company_data(self):
        """Test parsowania danych spółki"""
        data = parse_crbr_xml(self.sample_xml)
        
        self.assertIn("podmiot", data)
        podmiot = data["podmiot"]
        
        self.assertEqual(podmiot["nazwa"], "TEST SPÓŁKA Z O.O.")
        self.assertEqual(podmiot["nip"], "1234567890")
        self.assertEqual(podmiot["krs"], "0000123456")
        self.assertEqual(podmiot["forma"], "130 - Spółka z ograniczoną odpowiedzialnością")
        
        # Test adresu
        self.assertIn("adres", podmiot)
        adres = podmiot["adres"]
        self.assertEqual(adres["miejscowosc"], "Warszawa")
        self.assertEqual(adres["ulica"], "Testowa")
        self.assertEqual(adres["nr_domu"], "1")
        self.assertEqual(adres["nr_lokalu"], "2")
        self.assertEqual(adres["kod_pocztowy"], "00-001")
        self.assertEqual(adres["wojewodztwo"], "MAZOWIECKIE")
        self.assertEqual(adres["powiat"], "WARSZAWSKI")
        self.assertEqual(adres["gmina"], "WARSZAWA")
    
    def test_parse_beneficiaries(self):
        """Test parsowania beneficjentów"""
        data = parse_crbr_xml(self.sample_xml)
        
        self.assertIn("beneficjenci", data)
        beneficjenci = data["beneficjenci"]
        
        self.assertEqual(len(beneficjenci), 1)
        
        beneficjent = beneficjenci[0]
        self.assertEqual(beneficjent["imie"], "Jan")
        self.assertEqual(beneficjent["imiona_kolejne"], "Marian")
        self.assertEqual(beneficjent["nazwisko"], "Kowalski")
        self.assertEqual(beneficjent["pesel"], "12345678901")
        self.assertEqual(beneficjent["obywatelstwo"], "POLSKA")
        self.assertEqual(beneficjent["panstwo_zamieszkania"], "POLSKA")
        
        # Test uprawnień
        self.assertIn("uprawnienia", beneficjent)
        uprawnienia = beneficjent["uprawnienia"]
        self.assertEqual(len(uprawnienia), 1)
        self.assertEqual(uprawnienia[0], "wspólnik")
    
    def test_parse_declarant(self):
        """Test parsowania zgłaszającego"""
        data = parse_crbr_xml(self.sample_xml)
        
        self.assertIn("zglaszajacy", data)
        zglaszajacy = data["zglaszajacy"]
        
        self.assertEqual(zglaszajacy["imie"], "Anna")
        self.assertEqual(zglaszajacy["nazwisko"], "Nowak")
        self.assertEqual(zglaszajacy["pesel"], "98765432109")
        self.assertEqual(zglaszajacy["funkcja"], "prezes zarządu")
    
    def test_empty_xml(self):
        """Test parsowania pustego XML"""
        empty_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <PobierzInformacjeOSpolkachIBeneficjentachOdpowiedzDane>
        </PobierzInformacjeOSpolkachIBeneficjentachOdpowiedzDane>"""
        
        data = parse_crbr_xml(empty_xml)
        
        # Sprawdź czy struktura jest poprawna
        self.assertIn("meta", data)
        self.assertIn("podmiot", data)
        self.assertIn("beneficjenci", data)
        self.assertIn("zglaszajacy", data)
        
        # Sprawdź czy listy są puste
        self.assertEqual(len(data["beneficjenci"]), 0)
        self.assertEqual(data["zglaszajacy"], {})


if __name__ == "__main__":
    unittest.main()
