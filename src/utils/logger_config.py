# -*- coding: utf-8 -*-
"""
Konfiguracja systemu logowania dla aplikacji CRBR
"""

import logging
import sys
import os
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Konfiguruje system logowania.
    
    Args:
        level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ścieżka do pliku logów (opcjonalne)
        console_output: Czy wyświetlać logi w konsoli
        
    Returns:
        logging.Logger: Skonfigurowany logger
    """
    # Utwórz logger
    logger = logging.getLogger("crbr_app")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Usuń istniejące handlery (żeby uniknąć duplikatów)
    logger.handlers.clear()
    
    # Format logów
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler dla konsoli
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler dla pliku
    if log_file:
        # Utwórz katalog jeśli nie istnieje
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # W pliku zapisuj wszystko
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "crbr_app") -> logging.Logger:
    """
    Pobiera logger o podanej nazwie.
    
    Args:
        name: Nazwa loggera
        
    Returns:
        logging.Logger: Logger
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Dekorator do logowania wywołań funkcji.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        logger.debug(f"Wywołanie funkcji: {func.__name__}(args={args}, kwargs={kwargs})")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Funkcja {func.__name__} zakończona pomyślnie")
            return result
        except Exception as e:
            logger.error(f"Błąd w funkcji {func.__name__}: {e}")
            raise
    return wrapper


def log_soap_request(nip: str, endpoint: str, logger: Optional[logging.Logger] = None):
    """
    Loguje żądanie SOAP.
    
    Args:
        nip: NIP dla którego wysyłane jest żądanie
        endpoint: Endpoint SOAP
        logger: Logger (opcjonalny)
    """
    if logger is None:
        logger = get_logger()
    
    logger.info(f"Wysyłanie żądania SOAP dla NIP: {nip}")
    logger.debug(f"Endpoint: {endpoint}")


def log_soap_response(nip: str, status_code: int, response_size: int, logger: Optional[logging.Logger] = None):
    """
    Loguje odpowiedź SOAP.
    
    Args:
        nip: NIP dla którego otrzymano odpowiedź
        status_code: Kod statusu HTTP
        response_size: Rozmiar odpowiedzi w bajtach
        logger: Logger (opcjonalny)
    """
    if logger is None:
        logger = get_logger()
    
    if status_code == 200:
        logger.info(f"Otrzymano odpowiedź SOAP dla NIP {nip} (status: {status_code}, rozmiar: {response_size} bajtów)")
    else:
        logger.warning(f"Błąd SOAP dla NIP {nip} (status: {status_code}, rozmiar: {response_size} bajtów)")


def log_pdf_generation(nip: str, pdf_path: str, logger: Optional[logging.Logger] = None):
    """
    Loguje generowanie PDF.
    
    Args:
        nip: NIP dla którego generowany jest PDF
        pdf_path: Ścieżka do wygenerowanego PDF
        logger: Logger (opcjonalny)
    """
    if logger is None:
        logger = get_logger()
    
    logger.info(f"Wygenerowano PDF dla NIP {nip}: {pdf_path}")


def log_error(nip: str, error: Exception, logger: Optional[logging.Logger] = None):
    """
    Loguje błąd.
    
    Args:
        nip: NIP dla którego wystąpił błąd
        error: Wyjątek
        logger: Logger (opcjonalny)
    """
    if logger is None:
        logger = get_logger()
    
    logger.error(f"Błąd dla NIP {nip}: {error}")


# Przykład użycia
if __name__ == "__main__":
    # Konfiguracja logowania
    logger = setup_logging(
        level="DEBUG",
        log_file="logs/crbr_app.log",
        console_output=True
    )
    
    # Test logowania
    logger.info("Aplikacja SancCheck uruchomiona")
    logger.debug("Tryb debugowania włączony")
    logger.warning("To jest ostrzeżenie")
    logger.error("To jest błąd")
    
    # Test logowania funkcji
    @log_function_call
    def test_function(x, y):
        return x + y
    
    result = test_function(5, 3)
    logger.info(f"Wynik testu: {result}")
