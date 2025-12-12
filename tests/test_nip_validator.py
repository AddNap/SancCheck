# -*- coding: utf-8 -*-
"""
Testy jednostkowe dla walidatora NIP
"""

import unittest
from nip_validator import validate_nip, format_nip, clean_nip, _check_nip_checksum


class TestNIPValidator(unittest.TestCase):
    """Testy dla walidatora NIP"""
    
    def test_valid_nips(self):
        """Test poprawnych NIP-ów"""
        valid_nips = [
            "1234563218",  # Przykładowy poprawny NIP
            "7393873360",  # NIP z przykładu
            "123-456-32-18",
            "123 456 32 18",
            "123.456.32.18"
        ]
        
        for nip in valid_nips:
            with self.subTest(nip=nip):
                is_valid, error = validate_nip(nip)
                self.assertTrue(is_valid, f"NIP {nip} powinien być poprawny: {error}")
    
    def test_invalid_nips(self):
        """Test niepoprawnych NIP-ów"""
        invalid_cases = [
            ("1234563219", "błędna suma kontrolna"),
            ("123456321", "za krótki"),
            ("12345632180", "za długi"),
            ("123456321a", "zawiera literę"),
            ("", "pusty"),
            ("0000000001", "błędna suma kontrolna")
        ]
        
        for nip, reason in invalid_cases:
            with self.subTest(nip=nip, reason=reason):
                is_valid, error = validate_nip(nip)
                self.assertFalse(is_valid, f"NIP {nip} powinien być niepoprawny ({reason})")
                self.assertTrue(error, "Powinien być komunikat błędu")
    
    def test_format_nip(self):
        """Test formatowania NIP"""
        test_cases = [
            ("1234563218", "123-456-32-18"),
            ("7393873360", "739-387-33-60"),
            ("123-456-32-18", "123-456-32-18"),
            ("123 456 32 18", "123-456-32-18"),
        ]
        
        for input_nip, expected in test_cases:
            with self.subTest(input=input_nip):
                result = format_nip(input_nip)
                self.assertEqual(result, expected)
    
    def test_clean_nip(self):
        """Test czyszczenia NIP"""
        test_cases = [
            ("123-456-32-18", "1234563218"),
            ("123 456 32 18", "1234563218"),
            ("123.456.32.18", "1234563218"),
            ("1234563218", "1234563218"),
        ]
        
        for input_nip, expected in test_cases:
            with self.subTest(input=input_nip):
                result = clean_nip(input_nip)
                self.assertEqual(result, expected)
    
    def test_checksum_calculation(self):
        """Test obliczania sumy kontrolnej"""
        # Test poprawnych sum kontrolnych
        valid_checksums = [
            "1234563218",
            "7393873360",
        ]
        
        for nip in valid_checksums:
            with self.subTest(nip=nip):
                self.assertTrue(_check_nip_checksum(nip), f"Suma kontrolna dla {nip} powinna być poprawna")
        
        # Test niepoprawnych sum kontrolnych
        invalid_checksums = [
            "1234563219",  # Błędna ostatnia cyfra
            "1234563210",  # Błędna ostatnia cyfra
        ]
        
        for nip in invalid_checksums:
            with self.subTest(nip=nip):
                self.assertFalse(_check_nip_checksum(nip), f"Suma kontrolna dla {nip} powinna być niepoprawna")


if __name__ == "__main__":
    unittest.main()
