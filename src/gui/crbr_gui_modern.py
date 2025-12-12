# -*- coding: utf-8 -*-
"""
SancCheck GUI - Nowoczesna wersja z ttkbootstrap
Aplikacja do weryfikacji sankcji w danych CRBR
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import threading
from io import StringIO
import os
import sys
import subprocess
import webbrowser
from datetime import datetime, date
from typing import List, Dict, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
import json
from urllib3.util.retry import Retry

# Dodaj ścieżki do sys.path aby móc importować nasze moduły
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(src_dir)

# Dodaj ścieżki do sys.path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import naszych modułów
from core.crbr_bulk_to_pdf import bulk_from_csv, generate_pdf_from_xml_bytes, generate_pdf_from_xml_bytes_with_sanctions_info, fetch_xml_by_nip, extract_inner_xml_from_soap
from utils.nip_validator import validate_nip, format_nip
from utils.logger_config import setup_logging, get_logger
from utils.utf8_config import setup_utf8, get_csv_encoding


class ModernCRBRGUI:
    """Nowoczesny interfejs GUI dla aplikacji SancCheck"""
    
    def __init__(self):
        # Konfiguracja UTF-8
        setup_utf8()
        
        # Konfiguracja logowania
        self.logger = setup_logging(level="INFO", console_output=False)
        
        # Domyślny motyw
        self.current_theme = "flatly"
        
        # Tworzenie głównego okna z motywem i obsługą drag and drop
        self.root = self.create_main_window()
        
        # Kolory akcentu (Office/Windows style)
        self.accent_color = "#0078D4"
        self.success_color = "#107C10"
        self.danger_color = "#D13438"
        self.warning_color = "#FF8C00"
        self.sanctions_hover_color = "#FF6B35"  # Intensywny pomarańczowy dla hover sankcji
        
        # Zmienne
        self.nip_list = []
        self.generated_files = []
        self.is_processing = False
        self.stop_processing = False
        
        # Słownik do przechowywania pełnych ścieżek PDF (klucz: formatted_id, wartość: pełna_ścieżka)
        self.pdf_paths = {}
        
        # Zmienna do przechowywania aktualnie hoverowanego elementu
        self.hovered_item = None
        
        # Zmienne dla zakresu dat
        today = date.today()
        self.date_from = today
        self.date_to = today
        
        # Słowa kluczowe sugerujące wykluczenie z postępowania (art. 7 ust. 1 ustawy o przeciwdziałaniu wspieraniu agresji na Ukrainę)
        self.exclusion_keywords = [
            "Rosja", "Rosyjska"
        ]
        
        # Sesja HTTP z retry i timeout
        self.session = self.create_http_session()
        self.executor = None
        
        # Tworzenie interfejsu
        self.create_widgets()
        self.setup_layout()
        
        # Konfiguracja logowania do GUI
        self.setup_gui_logging()
        
        # Wczytaj słowa kluczowe z pliku
        self.load_exclusion_keywords_from_file()
    
    def create_main_window(self):
        """Tworzy główne okno z obsługą drag and drop"""
        try:
            # Próbuj użyć TkinterDnD dla drag and drop
            from tkinterdnd2 import TkinterDnD
            
            # Utwórz okno z TkinterDnD
            root = TkinterDnD.Tk()
            root.title("SancCheck - Weryfikacja sankcji CRBR")
            root.geometry("1200x800")
            root.minsize(800, 600)
            
            # Zastosuj motyw ttkbootstrap
            style = ttk_bs.Style(theme=self.current_theme)
            
            # Log message będzie dodane później w setup_drag_and_drop
            return root
            
        except ImportError:
            # Fallback na zwykłe okno ttkbootstrap
            root = ttk_bs.Window(themename=self.current_theme)
            root.title("SancCheck - Weryfikacja sankcji CRBR")
            root.geometry("1200x800")
            root.minsize(800, 600)
            
            # Log message będzie dodane później w setup_drag_and_drop
            return root
    
    def create_http_session(self):
        """Tworzy sesję HTTP z retry i timeout"""
        session = requests.Session()
        
        # Konfiguracja retry
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Timeout
        session.timeout = 30
        
        return session
    
    def create_widgets(self):
        """Tworzy wszystkie widgety"""
        
        # Główny pasek narzędzi
        self.create_toolbar()
        
        # Główny kontener z podziałem poziomym
        self.create_main_paned()
        
        # Lewa strona - lista NIP-ów
        self.create_nip_panel()
        
        # Prawa strona - logi
        self.create_log_panel()
        
        # Pasek statusu
        self.create_status_bar()
        
        # Skróty klawiszowe
        self.setup_keyboard_shortcuts()
    
    def setup_keyboard_shortcuts(self):
        """Konfiguruje skróty klawiszowe"""
        # Ctrl+V - Wklej ze schowka
        self.root.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        self.root.bind('<Control-V>', lambda e: self.paste_from_clipboard())
        
        # Ctrl+Shift+V - Wklej ze schowka (alternatywny)
        self.root.bind('<Control-Shift-V>', lambda e: self.paste_from_clipboard())
        
        # Fokus na głównym oknie dla skrótów
        self.root.focus_set()
    
    def create_toolbar(self):
        """Tworzy górny pasek narzędzi w układzie rzędów"""
        # Główny kontener dla toolbaru
        self.toolbar_container = ttk_bs.Frame(self.root)
        self.toolbar_container.pack(fill=X, padx=5, pady=5)
        
        # RZĄD 1: Import i dodawanie danych
        self.toolbar_row1 = ttk_bs.Frame(self.toolbar_container)
        self.toolbar_row1.pack(fill=X, pady=2)
        
        # Etykieta sekcji
        ttk_bs.Label(self.toolbar_row1, text="📋 Dane:", font=('Arial', 9, 'bold')).pack(side=LEFT, padx=(0, 10))
        
        # Przycisk Import CSV
        self.btn_import_csv = ttk_bs.Button(
            self.toolbar_row1,
            text="📁 Import CSV/Excel",
            command=self.import_csv,
            bootstyle="info",
            width=18,
            compound="center"
        )
        self.btn_import_csv.pack(side=LEFT, padx=2)
        
        # Przycisk Dodaj NIP/PESEL/REGON
        self.btn_add_nip = ttk_bs.Button(
            self.toolbar_row1,
            text="➕ Dodaj NIP/PESEL/REGON",
            command=self.add_identifier_dialog,
            bootstyle="primary",
            width=25,
            compound="center"
        )
        self.btn_add_nip.pack(side=LEFT, padx=2)
        
        # Przycisk Wklej
        self.btn_paste = ttk_bs.Button(
            self.toolbar_row1,
            text="📋 Wklej",
            command=self.paste_from_clipboard,
            bootstyle="info",
            width=12,
            compound="center"
        )
        self.btn_paste.pack(side=LEFT, padx=2)
        
        # Przycisk Wyczyść
        self.btn_clear = ttk_bs.Button(
            self.toolbar_row1,
            text="🗑️ Wyczyść",
            command=self.clear_all,
            bootstyle="secondary",
            width=15,
            compound="center"
        )
        self.btn_clear.pack(side=LEFT, padx=2)
        
        # Separator między rzędami
        ttk_bs.Separator(self.toolbar_container, orient=HORIZONTAL).pack(fill=X, pady=5)
        
        # RZĄD 2: Zakres dat i ustawienia
        self.toolbar_row2 = ttk_bs.Frame(self.toolbar_container)
        self.toolbar_row2.pack(fill=X, pady=2)
        
        # Etykieta sekcji
        ttk_bs.Label(self.toolbar_row2, text="⚙️ Ustawienia:", font=('Arial', 9, 'bold')).pack(side=LEFT, padx=(0, 10))
        
        # Sekcja zakresu dat
        self.create_date_range_section()
        
        # Przycisk Motywy
        self.btn_themes = ttk_bs.Button(
            self.toolbar_row2,
            text="🎨 Motywy",
            command=self.show_theme_menu,
            bootstyle="secondary",
            width=15,
            compound="center"
        )
        self.btn_themes.pack(side=LEFT, padx=2)
        
        # Separator między rzędami
        ttk_bs.Separator(self.toolbar_container, orient=HORIZONTAL).pack(fill=X, pady=5)
        
        # RZĄD 3: Generowanie i eksport
        self.toolbar_row3 = ttk_bs.Frame(self.toolbar_container)
        self.toolbar_row3.pack(fill=X, pady=2)
        
        # Etykieta sekcji
        ttk_bs.Label(self.toolbar_row3, text="▶️ Generowanie:", font=('Arial', 9, 'bold')).pack(side=LEFT, padx=(0, 10))
        
        # Przycisk Generuj
        self.btn_generate = ttk_bs.Button(
            self.toolbar_row3,
            text="▶️ Generuj PDF",
            command=self.start_generation,
            bootstyle="success",
            width=18,
            compound="center"
        )
        self.btn_generate.pack(side=LEFT, padx=2)
        
        # Przycisk Stop
        self.btn_stop = ttk_bs.Button(
            self.toolbar_row3,
            text="⏹️ Stop",
            command=self.stop_generation,
            bootstyle="danger",
            width=12,
            state=DISABLED,
            compound="center"
        )
        self.btn_stop.pack(side=LEFT, padx=2)
        
        # Przycisk Eksport
        self.btn_export = ttk_bs.Button(
            self.toolbar_row3,
            text="💾 Eksport",
            command=self.export_results,
            bootstyle="warning",
            width=15,
            compound="center"
        )
        self.btn_export.pack(side=LEFT, padx=2)
        
        # Separator między rzędami
        ttk_bs.Separator(self.toolbar_container, orient=HORIZONTAL).pack(fill=X, pady=5)
        
        # RZĄD 4: Sankcje i postęp
        self.toolbar_row4 = ttk_bs.Frame(self.toolbar_container)
        self.toolbar_row4.pack(fill=X, pady=2)
        
        # Etykieta sekcji
        ttk_bs.Label(self.toolbar_row4, text="🚨 Sankcje:", font=('Arial', 9, 'bold')).pack(side=LEFT, padx=(0, 10))
        
        # Przycisk Aktualizuj listy sankcyjne
        self.btn_update_sanctions = ttk_bs.Button(
            self.toolbar_row4,
            text="🔄 Aktualizuj listy sankcyjne",
            command=self.update_sanctions_lists,
            bootstyle="warning",
            width=25,
            compound="center"
        )
        self.btn_update_sanctions.pack(side=LEFT, padx=2)
        
        # Pasek postępu
        self.progress = ttk_bs.Progressbar(
            self.toolbar_row4,
            mode='determinate',
            bootstyle="info-striped",
            length=200
        )
        self.progress.pack(side=RIGHT, padx=10)
    
    def create_date_range_section(self):
        """Tworzy sekcję z zakresem dat"""
        # Ramka dla zakresu dat
        self.date_frame = ttk_bs.Frame(self.toolbar_row2)
        self.date_frame.pack(side=LEFT, padx=5)
        
        # Etykieta "Od:"
        self.lbl_date_from = ttk_bs.Label(
            self.date_frame,
            text="Od:",
            font=('Arial', 9, 'bold')
        )
        self.lbl_date_from.pack(side=LEFT, padx=(0, 2))
        
        # Pole daty "od"
        self.date_from_var = tk.StringVar(value=self.date_from.strftime("%Y-%m-%d"))
        self.entry_date_from = ttk_bs.Entry(
            self.date_frame,
            textvariable=self.date_from_var,
            width=12,
            font=('Arial', 9)
        )
        self.entry_date_from.pack(side=LEFT, padx=2)
        
        # Etykieta "Do:"
        self.lbl_date_to = ttk_bs.Label(
            self.date_frame,
            text="Do:",
            font=('Arial', 9, 'bold')
        )
        self.lbl_date_to.pack(side=LEFT, padx=(5, 2))
        
        # Pole daty "do"
        self.date_to_var = tk.StringVar(value=self.date_to.strftime("%Y-%m-%d"))
        self.entry_date_to = ttk_bs.Entry(
            self.date_frame,
            textvariable=self.date_to_var,
            width=12,
            font=('Arial', 9)
        )
        self.entry_date_to.pack(side=LEFT, padx=2)
        
        # Przycisk "Dzisiaj"
        self.btn_today = ttk_bs.Button(
            self.date_frame,
            text="📅 Dzisiaj",
            command=self.set_today_dates,
            bootstyle="info-outline",
            width=10
        )
        self.btn_today.pack(side=LEFT, padx=(5, 0))
        
        # Bind dla walidacji dat
        self.entry_date_from.bind('<FocusOut>', self.validate_date_from)
        self.entry_date_to.bind('<FocusOut>', self.validate_date_to)
    
    def set_today_dates(self):
        """Ustawia daty na dzisiaj"""
        today = date.today()
        self.date_from = today
        self.date_to = today
        self.date_from_var.set(today.strftime("%Y-%m-%d"))
        self.date_to_var.set(today.strftime("%Y-%m-%d"))
        self.log_message("Ustawiono daty na dzisiaj")
    
    def validate_date_from(self, event=None):
        """Waliduje datę 'od'"""
        try:
            date_str = self.date_from_var.get()
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.date_from = parsed_date
            self.log_message(f"Ustawiono datę od: {parsed_date}")
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD")
            self.date_from_var.set(self.date_from.strftime("%Y-%m-%d"))
    
    def validate_date_to(self, event=None):
        """Waliduje datę 'do'"""
        try:
            date_str = self.date_to_var.get()
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            self.date_to = parsed_date
            self.log_message(f"Ustawiono datę do: {parsed_date}")
        except ValueError:
            messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD")
            self.date_to_var.set(self.date_to.strftime("%Y-%m-%d"))
    
    def get_date_range(self):
        """Zwraca zakres dat jako tuple (od, do)"""
        return self.date_from, self.date_to
    
    def check_exclusion_keywords(self, text_content):
        """
        Sprawdza czy w tekście są słowa sugerujące wykluczenie z postępowania
        na mocy art. 7 ust. 1 ustawy o przeciwdziałaniu wspieraniu agresji na Ukrainę
        
        Args:
            text_content (str): Tekst do sprawdzenia
            
        Returns:
            tuple: (has_exclusion_keywords, found_keywords, warning_message)
        """
        if not text_content:
            return False, [], ""
        
        # Konwertuj tekst na małe litery dla porównania
        text_lower = text_content.lower()
        found_keywords = []
        
        # Sprawdź każde słowo kluczowe
        for keyword in self.exclusion_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            warning_message = (
                f"⚠️ UWAGA: Znaleziono słowa sugerujące wykluczenie z postępowania "
                f"na mocy art. 7 ust. 1 ustawy o przeciwdziałaniu wspieraniu agresji na Ukrainę:\n"
                f"Znalezione słowa: {', '.join(found_keywords[:5])}"
                f"{'...' if len(found_keywords) > 5 else ''}"
            )
            return True, found_keywords, warning_message
        
        return False, [], ""
    
    def check_exclusion_in_xml(self, xml_bytes, nip):
        """
        Sprawdza XML pod kątem słów kluczowych sugerujących wykluczenie
        
        Args:
            xml_bytes (bytes): Zawartość XML do sprawdzenia
            nip (str): NIP dla którego sprawdzamy
        """
        try:
            # Konwertuj XML na tekst
            xml_text = xml_bytes.decode('utf-8', errors='ignore')
            
            # Sprawdź słowa kluczowe
            has_exclusion, found_keywords, warning_message = self.check_exclusion_keywords(xml_text)
            
            if has_exclusion:
                # Loguj ostrzeżenie
                self.log_message(f"⚠️ UWAGA dla NIP {format_nip(nip)}: {warning_message}", "WARNING")
                
                # Dodaj szczegółowe informacje o znalezionych słowach
                if found_keywords:
                    self.log_message(f"Znalezione słowa kluczowe: {', '.join(found_keywords)}", "WARNING")
                
                # Można tutaj dodać dodatkowe akcje, np. zapis do pliku z ostrzeżeniami
                self.save_exclusion_warning(nip, found_keywords, xml_text)
                
        except Exception as e:
            self.log_message(f"Błąd podczas sprawdzania słów kluczowych dla NIP {format_nip(nip)}: {e}", "ERROR")
    
    def save_exclusion_warning(self, nip, found_keywords, xml_content):
        """
        Zapisuje ostrzeżenie o wykluczeniu do pliku
        
        Args:
            nip (str): NIP
            found_keywords (list): Lista znalezionych słów kluczowych
            xml_content (str): Zawartość XML
        """
        try:
            # Utwórz katalog dla ostrzeżeń jeśli nie istnieje
            warnings_dir = "exclusion_warnings"
            if not os.path.exists(warnings_dir):
                os.makedirs(warnings_dir)
            
            # Nazwa pliku z ostrzeżeniem
            warning_file = os.path.join(warnings_dir, f"warning_{format_nip(nip)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            # Zawartość pliku ostrzeżenia
            warning_content = f"""
OSTRZEŻENIE O WYKLUCZENIU Z POSTĘPOWANIA
========================================

NIP: {format_nip(nip)}
Data sprawdzenia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Ustawa: art. 7 ust. 1 ustawy z dnia 13 kwietnia 2022 r. o szczególnych rozwiązaniach 
        w zakresie przeciwdziałania wspieraniu agresji na Ukrainę

ZNALEZIONE SŁOWA KLUCZOWE:
{', '.join(found_keywords)}

UWAGA: Ten raport zawiera słowa sugerujące możliwość wykluczenia z postępowania
na mocy ww. ustawy. Wymaga dodatkowej weryfikacji.

========================================
ZAWARTOŚĆ XML (fragment):
========================================
{xml_content[:2000]}{'...' if len(xml_content) > 2000 else ''}
"""
            
            # Zapisz plik
            with open(warning_file, 'w', encoding='utf-8') as f:
                f.write(warning_content)
            
            self.log_message(f"Zapisano ostrzeżenie do pliku: {warning_file}", "INFO")
            
        except Exception as e:
            self.log_message(f"Błąd podczas zapisywania ostrzeżenia: {e}", "ERROR")
    
    def create_main_paned(self):
        """Tworzy główny kontener z podziałem pionowym"""
        self.main_paned = ttk_bs.PanedWindow(self.root, orient=VERTICAL)
        self.main_paned.pack(fill=BOTH, expand=True, padx=5, pady=5)
    
    def create_nip_panel(self):
        """Tworzy panel z listą NIP-ów"""
        # Kontener dla górnej części
        self.nip_frame = ttk_bs.LabelFrame(self.main_paned, text="📋 Lista identyfikatorów", padding=10)
        self.main_paned.add(self.nip_frame, weight=2)
        
        # Treeview dla listy identyfikatorów
        columns = ('Identyfikator', 'Typ', 'Status', 'Plik PDF')
        self.nip_tree = ttk_bs.Treeview(self.nip_frame, columns=columns, show='headings', height=15)
        
        # Konfiguracja kolumn
        self.nip_tree.heading('Identyfikator', text='Identyfikator')
        self.nip_tree.heading('Typ', text='Typ')
        self.nip_tree.heading('Status', text='Status')
        self.nip_tree.heading('Plik PDF', text='Plik PDF')
        
        self.nip_tree.column('Identyfikator', width=150)
        self.nip_tree.column('Typ', width=80)
        self.nip_tree.column('Status', width=100)
        self.nip_tree.column('Plik PDF', width=200)
        
        # Scrollbar dla treeview
        nip_scrollbar = ttk_bs.Scrollbar(self.nip_frame, orient=VERTICAL, command=self.nip_tree.yview)
        self.nip_tree.configure(yscrollcommand=nip_scrollbar.set)
        
        # Konfiguracja tagów kolorów
        self.nip_tree.tag_configure('sanctions_found', background=self.warning_color, foreground='white')
        self.nip_tree.tag_configure('sanctions_found_hover', background=self.sanctions_hover_color, foreground='white')
        self.nip_tree.tag_configure('normal', background='')
        
        # Pakowanie
        self.nip_tree.pack(side=LEFT, fill=BOTH, expand=True)
        nip_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Bind dla dwukliku
        self.nip_tree.bind('<Double-1>', self.on_double_click)
        
        # Bind dla hover efektów
        self.nip_tree.bind('<Motion>', self.on_mouse_motion)
        self.nip_tree.bind('<Leave>', self.on_mouse_leave)
        
        # Obsługa drag and drop będzie skonfigurowana na końcu create_widgets
        
        # Panel przycisków dla NIP-ów
        self.nip_buttons_frame = ttk_bs.Frame(self.nip_frame)
        self.nip_buttons_frame.pack(fill=X, pady=(10, 0))
        
        self.btn_remove_nip = ttk_bs.Button(
            self.nip_buttons_frame,
            text="🗑️ Usuń zaznaczone",
            command=self.remove_selected_nips,
            bootstyle="danger-outline",
            width=25,
            compound="left"
        )
        self.btn_remove_nip.pack(fill=X, pady=(0, 5))
        
        self.btn_validate_nips = ttk_bs.Button(
            self.nip_buttons_frame,
            text="✅ Waliduj NIP-y",
            command=self.validate_all_nips,
            bootstyle="info-outline",
            width=25,
            compound="left"
        )
        self.btn_validate_nips.pack(fill=X, pady=(0, 0))
    
    def create_log_panel(self):
        """Tworzy panel z logami"""
        # Kontener dla dolnej części
        self.log_frame = ttk_bs.LabelFrame(self.main_paned, text="📝 Logi", padding=10)
        self.main_paned.add(self.log_frame, weight=1)
        
        # Text widget dla logów
        self.log_text = tk.Text(
            self.log_frame,
            height=8,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f8f9fa',
            fg='#212529'
        )
        
        # Scrollbar dla logów
        log_scrollbar = ttk_bs.Scrollbar(self.log_frame, orient=VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Pakowanie
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        log_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Panel przycisków dla logów
        self.log_buttons_frame = ttk_bs.Frame(self.log_frame)
        self.log_buttons_frame.pack(fill=X, pady=(10, 0))
        
        self.btn_clear_logs = ttk_bs.Button(
            self.log_buttons_frame,
            text="🗑️ Wyczyść logi",
            command=self.clear_logs,
            bootstyle="secondary-outline",
            width=25,
            compound="left"
        )
        self.btn_clear_logs.pack(fill=X, pady=(0, 5))
        
        self.btn_save_logs = ttk_bs.Button(
            self.log_buttons_frame,
            text="💾 Zapisz logi",
            command=self.save_logs,
            bootstyle="info-outline",
            width=25,
            compound="left"
        )
        self.btn_save_logs.pack(fill=X, pady=(0, 0))
    
    def create_status_bar(self):
        """Tworzy pasek statusu"""
        self.status_frame = ttk_bs.Frame(self.root)
        self.status_frame.pack(fill=X, side=BOTTOM)
        
        self.status_label = ttk_bs.Label(
            self.status_frame,
            text="Gotowy do pracy",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=LEFT, fill=X, expand=True, padx=5, pady=2)
        
        # Licznik identyfikatorów
        self.nip_count_label = ttk_bs.Label(
            self.status_frame,
            text="Identyfikatory: 0",
            relief=tk.SUNKEN
        )
        self.nip_count_label.pack(side=RIGHT, padx=5, pady=2)
    
    def setup_layout(self):
        """Konfiguruje układ widgetów"""
        # Ustawienie proporcji podziału (2:1 - lista NIP-ów większa, logi mniejsze)
        self.main_paned.pane(self.nip_frame, weight=2)
        self.main_paned.pane(self.log_frame, weight=1)
        
        # Tooltips
        self.create_tooltips()
        
        # Konfiguracja drag and drop na końcu (po utworzeniu wszystkich widgetów)
        self.setup_drag_and_drop()
    
    def create_tooltips(self):
        """Tworzy tooltips dla przycisków"""
        # Tooltips dla przycisków w toolbarze
        self.create_tooltip(self.btn_import_csv, "Importuj NIP-y z pliku CSV, XLS, XLSX")
        self.create_tooltip(self.btn_add_nip, "Dodaj NIP, PESEL lub REGON do listy")
        self.create_tooltip(self.btn_paste, "Wklej NIP-y ze schowka (Excel, tabelki)")
        self.create_tooltip(self.btn_today, "Ustaw daty na dzisiaj")
        self.create_tooltip(self.btn_themes, "Zmień motyw aplikacji")
        self.create_tooltip(self.btn_generate, "Rozpocznij generowanie PDF-ów")
        self.create_tooltip(self.btn_stop, "Zatrzymaj generowanie PDF-ów")
        self.create_tooltip(self.btn_export, "Eksportuj wyniki do pliku")
        self.create_tooltip(self.btn_update_sanctions, "Aktualizuj listy wykluczonych podmiotów i osób")
        self.create_tooltip(self.btn_clear, "Wyczyść całą listę NIP-ów")
        
        # Tooltips dla przycisków w panelach
        self.create_tooltip(self.btn_remove_nip, "Usuń zaznaczone NIP-y z listy")
        self.create_tooltip(self.btn_validate_nips, "Sprawdź poprawność wszystkich NIP-ów")
        self.create_tooltip(self.btn_clear_logs, "Wyczyść wszystkie logi")
        self.create_tooltip(self.btn_save_logs, "Zapisz logi do pliku")
    
    def create_tooltip(self, widget, text):
        """Tworzy tooltip dla widgetu"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk_bs.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def setup_gui_logging(self):
        """Konfiguruje logowanie do GUI"""
        import logging
        
        # Dodaj handler dla GUI
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                try:
                    message = self.format(record)
                    self.text_widget.insert(tk.END, message + "\n")
                    self.text_widget.see(tk.END)
                    self.text_widget.update_idletasks()
                except Exception:
                    self.handleError(record)
        
        # Dodaj handler do loggera
        gui_handler = GUILogHandler(self.log_text)
        gui_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')
        gui_handler.setFormatter(formatter)
        self.logger.addHandler(gui_handler)
    
    def log_message(self, message, level="INFO"):
        """Dodaje wiadomość do logów"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()
    
    def update_status(self, message):
        """Aktualizuje pasek statusu"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def update_nip_count(self):
        """Aktualizuje licznik identyfikatorów"""
        count = len(self.nip_list)
        self.nip_count_label.config(text=f"Identyfikatory: {count}")
    
    def import_csv(self):
        """Importuje NIP-y z pliku CSV z lepszą obsługą błędów i mapowaniem kolumn"""
        file_path = filedialog.askopenfilename(
            title="Wybierz plik CSV lub Excel",
            filetypes=[
                ("Pliki CSV", "*.csv"), 
                ("Pliki Excel", "*.xlsx *.xls"), 
                ("Pliki CSV", "*.csv"),
                ("Pliki Excel XLSX", "*.xlsx"),
                ("Pliki Excel XLS", "*.xls"),
                ("Wszystkie pliki", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            # Wczytaj plik z różnymi kodowaniami
            df = self.load_csv_with_encoding(file_path)
            
            if df is None or df.empty:
                messagebox.showerror("Błąd", "Plik jest pusty lub nie można go odczytać")
                return
            
            # Znajdź kolumnę z NIP-ami
            nip_column = self.find_nip_column(df)
            
            if nip_column is None:
                # Dialog wyboru kolumny
                nip_column = self.create_column_selection_dialog(df.columns.tolist())
                if not nip_column:
                    return
            
            # Wyciągnij i wyczyść NIP-y
            nips = self.extract_and_clean_nips(df, nip_column)
            
            if not nips:
                messagebox.showwarning("Uwaga", "Nie znaleziono żadnych NIP-ów w wybranej kolumnie")
                return
            
            # Walidacja NIP-ów
            validation_result = self.validate_nips_batch(nips)
            
            # Dodaj poprawne NIP-y do listy
            if validation_result['valid']:
                for nip in validation_result['valid']:
                    if nip not in self.nip_list:
                        self.nip_list.append(nip)
                        self.add_nip_to_tree(nip, "Oczekuje", "", False)
                self.update_nip_count()
            
            # Pokaż szczegółowe wyniki
            self.show_import_results(validation_result, file_path)
            
        except Exception as e:
            error_msg = f"Błąd importu pliku:\n{str(e)}"
            messagebox.showerror("Błąd", error_msg)
            self.log_message(f"Błąd importu: {e}", "ERROR")
    
    def paste_from_clipboard(self):
        """Wkleja NIP-y ze schowka (Excel, tabelki)"""
        try:
            # Pobierz dane ze schowka
            clipboard_data = self.root.clipboard_get()
            
            if not clipboard_data or not clipboard_data.strip():
                messagebox.showwarning("Uwaga", "Schowek jest pusty")
                return
            
            # Parsuj dane ze schowka
            parsed_data = self.parse_clipboard_data(clipboard_data)
            
            if not parsed_data:
                messagebox.showwarning("Uwaga", "Nie znaleziono żadnych identyfikatorów w schowku")
                return
            
            # Walidacja identyfikatorów
            validation_result = self.validate_nips_batch(parsed_data)
            
            # Dodaj poprawne identyfikatory do listy
            added_count = 0
            if validation_result['valid']:
                for identifier in validation_result['valid']:
                    if identifier not in self.nip_list:
                        self.nip_list.append(identifier)
                        self.add_nip_to_tree(identifier, "Oczekuje", "", False)
                        added_count += 1
                self.update_nip_count()
            
            # Pokaż wyniki
            self.show_paste_results(validation_result, added_count)
            
        except tk.TclError:
            messagebox.showwarning("Uwaga", "Schowek jest pusty lub zawiera nieobsługiwane dane")
        except Exception as e:
            error_msg = f"Błąd wklejania ze schowka:\n{str(e)}"
            messagebox.showerror("Błąd", error_msg)
            self.log_message(f"Błąd wklejania: {e}", "ERROR")
    
    def parse_clipboard_data(self, clipboard_data):
        """Parsuje dane ze schowka i wyciąga identyfikatory"""
        identifiers = []
        
        # Podziel na linie
        lines = clipboard_data.strip().split('\n')
        
        for line in lines:
            # Podziel na komórki (tab, średnik, przecinek)
            cells = []
            for separator in ['\t', ';', ',']:
                if separator in line:
                    cells = line.split(separator)
                    break
            
            if not cells:
                # Jeśli nie ma separatorów, traktuj całą linię jako jedną komórkę
                cells = [line.strip()]
            
            for cell in cells:
                cell = cell.strip()
                if not cell:
                    continue
                
                # Usuń cudzysłowy i spacje
                cell = cell.strip('"\' \t')
                
                # Sprawdź różne formaty identyfikatorów
                clean_id = self.extract_identifier_from_cell(cell)
                if clean_id:
                    identifiers.append(clean_id)
        
        return identifiers
    
    def extract_identifier_from_cell(self, cell):
        """Wyciąga identyfikator z komórki w różnych formatach"""
        # Usuń wszystkie znaki niebędące cyframi i myślnikami
        import re
        
        # Sprawdź czy to może być identyfikator (tylko cyfry)
        if cell.isdigit() and len(cell) in [9, 10, 11, 14]:
            return cell
        
        # Sprawdź formaty z myślnikami
        if '-' in cell:
            # Usuń myślniki i sprawdź czy reszta to cyfry
            clean_id = cell.replace('-', '')
            if clean_id.isdigit() and len(clean_id) in [9, 10, 11, 14]:
                return clean_id
        
        # Sprawdź formaty z spacjami (np. "123 456 7890")
        if ' ' in cell:
            clean_id = cell.replace(' ', '')
            if clean_id.isdigit() and len(clean_id) in [9, 10, 11, 14]:
                return clean_id
        
        # Sprawdź formaty z kropkami (np. "123.456.7890")
        if '.' in cell:
            clean_id = cell.replace('.', '')
            if clean_id.isdigit() and len(clean_id) in [9, 10, 11, 14]:
                return clean_id
        
        # Sprawdź formaty mieszane (np. "123-456.7890")
        # Usuń wszystkie znaki niebędące cyframi
        clean_id = re.sub(r'[^\d]', '', cell)
        if clean_id.isdigit() and len(clean_id) in [9, 10, 11, 14]:
            return clean_id
        
        return None
    
    def show_paste_results(self, validation_result, added_count):
        """Pokazuje wyniki wklejania ze schowka"""
        total = len(validation_result['valid']) + len(validation_result['invalid'])
        valid = len(validation_result['valid'])
        invalid = len(validation_result['invalid'])
        
        message = f"Wklejanie ze schowka zakończone:\n\n"
        message += f"• Znaleziono: {total} identyfikatorów\n"
        message += f"• Poprawne: {valid}\n"
        message += f"• Niepoprawne: {invalid}\n"
        message += f"• Dodano do listy: {added_count}"
        
        if validation_result['invalid']:
            message += f"\n\nNiepoprawne identyfikatory:\n"
            for invalid_id in validation_result['invalid'][:5]:  # Pokaż max 5
                message += f"• {invalid_id}\n"
            if len(validation_result['invalid']) > 5:
                message += f"... i {len(validation_result['invalid']) - 5} więcej"
        
        if added_count > 0:
            messagebox.showinfo("Wklejanie zakończone", message)
            self.log_message(f"Wklejono {added_count} identyfikatorów ze schowka", "INFO")
        else:
            messagebox.showwarning("Wklejanie zakończone", message)
    
    def load_csv_with_encoding(self, file_path):
        """Wczytuje plik CSV lub Excel z różnymi kodowaniami"""
        # Obsługa plików Excel
        if file_path.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(file_path)
                self.log_message(f"Wczytano plik Excel: {os.path.basename(file_path)}")
                return df
            except Exception as e:
                self.log_message(f"Błąd wczytywania pliku Excel: {e}", "ERROR")
                return None
        
        # Obsługa plików CSV z różnymi kodowaniami
        encodings = ['utf-8', 'utf-8-sig', 'cp1250', 'iso-8859-2', 'windows-1250']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                self.log_message(f"Wczytano plik CSV z kodowaniem: {encoding}")
                return df
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.log_message(f"Błąd wczytywania z kodowaniem {encoding}: {e}", "WARNING")
                continue
        
        raise Exception("Nie można wczytać pliku z żadnym z obsługiwanych kodowań")
    
    def find_nip_column(self, df):
        """Znajduje kolumnę z NIP-ami"""
        # Lista możliwych nazw kolumn
        possible_names = [
            'nip', 'NIP', 'Nip', 'numer_nip', 'numer_NIP', 'tax_id', 'tax_ID',
            'nip_number', 'NIP_NUMBER', 'tax_number', 'TAX_NUMBER',
            'numer_podatkowy', 'NUMER_PODATKOWY', 'id_podatkowy', 'ID_PODATKOWY'
        ]
        
        # Sprawdź dokładne dopasowania
        for name in possible_names:
            if name in df.columns:
                return name
        
        # Sprawdź częściowe dopasowania (case-insensitive)
        df_columns_lower = [col.lower() for col in df.columns]
        for name in possible_names:
            name_lower = name.lower()
            for i, col_lower in enumerate(df_columns_lower):
                if name_lower in col_lower or col_lower in name_lower:
                    return df.columns[i]
        
        return None
    
    def extract_and_clean_nips(self, df, column_name):
        """Wyciąga i czyści NIP-y z kolumny"""
        try:
            # Wyciągnij wartości z kolumny
            values = df[column_name].dropna().astype(str)
            
            # Wyczyść NIP-y (usuń spacje, myślniki, inne znaki)
            cleaned_nips = []
            for value in values:
                # Usuń wszystkie znaki niebędące cyframi
                clean_value = ''.join(filter(str.isdigit, str(value)))
                
                # Sprawdź czy ma 10 cyfr
                if len(clean_value) == 10:
                    cleaned_nips.append(clean_value)
                elif len(clean_value) > 0:
                    # Loguj NIP-y które nie mają 10 cyfr
                    self.log_message(f"Pominięto NIP o nieprawidłowej długości: {value} (ma {len(clean_value)} cyfr)", "WARNING")
            
            return cleaned_nips
            
        except Exception as e:
            raise Exception(f"Błąd wyciągania NIP-ów z kolumny '{column_name}': {e}")
    
    def validate_nips_batch(self, nips):
        """Waliduje listę NIP-ów"""
        valid_nips = []
        invalid_nips = []
        duplicate_nips = []
        
        seen_nips = set()
        
        for nip in nips:
            # Sprawdź duplikaty
            if nip in seen_nips:
                duplicate_nips.append(nip)
                continue
            
            seen_nips.add(nip)
            
            # Walidacja NIP
            is_valid, error = validate_nip(nip)
            if is_valid:
                valid_nips.append(nip)
            else:
                invalid_nips.append((nip, error))
        
        return {
            'valid': valid_nips,
            'invalid': invalid_nips,
            'duplicates': duplicate_nips,
            'total': len(nips)
        }
    
    def show_import_results(self, validation_result, file_path):
        """Pokazuje szczegółowe wyniki importu"""
        valid = validation_result['valid']
        invalid = validation_result['invalid']
        duplicates = validation_result['duplicates']
        total = validation_result['total']
        
        # Przygotuj wiadomość
        message_parts = []
        
        if valid:
            message_parts.append(f"✅ Zaimportowano: {len(valid)} poprawnych NIP-ów")
        
        if invalid:
            message_parts.append(f"❌ Odrzucono: {len(invalid)} niepoprawnych NIP-ów")
            # Loguj szczegóły błędów
            for invalid_item in invalid[:5]:  # Pokaż max 5 błędów
                if isinstance(invalid_item, dict):
                    nip = invalid_item['nip']
                    error = invalid_item['error']
                else:
                    # Fallback dla starego formatu (tuple)
                    nip, error = invalid_item
                self.log_message(f"Niepoprawny NIP {format_nip(nip)}: {error}", "WARNING")
        
        if duplicates:
            message_parts.append(f"⚠️ Pominięto: {len(duplicates)} duplikatów")
            self.log_message(f"Duplikaty: {', '.join(duplicates[:5])}", "WARNING")
        
        if not valid:
            messagebox.showwarning("Uwaga", "Nie zaimportowano żadnych poprawnych NIP-ów")
        else:
            messagebox.showinfo("Wyniki importu", "\n".join(message_parts))
        
        # Loguj podsumowanie
        self.log_message(f"Import zakończony: {len(valid)}/{total} NIP-ów z pliku {os.path.basename(file_path)}")
    
    def create_column_selection_dialog(self, columns):
        """Tworzy dialog wyboru kolumny z NIP-ami"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz kolumnę z NIP-ami")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Centrowanie okna
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Ramka główna
        main_frame = ttk_bs.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Etykieta
        ttk_bs.Label(main_frame, text="Wybierz kolumnę zawierającą NIP-y:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Lista kolumn
        listbox_frame = ttk_bs.Frame(main_frame)
        listbox_frame.pack(fill=BOTH, expand=True, pady=10)
        
        listbox = tk.Listbox(listbox_frame, height=8)
        scrollbar = ttk_bs.Scrollbar(listbox_frame, orient=VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Dodaj kolumny do listy
        for col in columns:
            listbox.insert(tk.END, col)
        
        # Wybierz pierwszą kolumnę domyślnie
        if columns:
            listbox.selection_set(0)
        
        # Ramka przycisków
        button_frame = ttk_bs.Frame(main_frame)
        button_frame.pack(pady=20)
        
        selected_column = None
        
        def select_column():
            nonlocal selected_column
            selection = listbox.curselection()
            if selection:
                selected_column = columns[selection[0]]
                dialog.destroy()
            else:
                messagebox.showwarning("Uwaga", "Wybierz kolumnę")
        
        def cancel():
            nonlocal selected_column
            selected_column = None
            dialog.destroy()
        
        ttk_bs.Button(button_frame, text="Wybierz", command=select_column, bootstyle="success").pack(side=LEFT, padx=5)
        ttk_bs.Button(button_frame, text="Anuluj", command=cancel, bootstyle="secondary").pack(side=LEFT, padx=5)
        
        # Bind Enter i double-click
        listbox.bind('<Return>', lambda e: select_column())
        listbox.bind('<Double-Button-1>', lambda e: select_column())
        
        # Focus na listbox
        listbox.focus_set()
        
        # Czekaj na zamknięcie dialogu
        dialog.wait_window()
        
        return selected_column
    
    def add_identifier_dialog(self):
        """Dialog do dodawania NIP/PESEL/REGON"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Dodaj NIP/PESEL/REGON")
        dialog.geometry("450x250")
        dialog.resizable(False, False)
        
        # Centrowanie okna
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Ramka główna
        main_frame = ttk_bs.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Etykieta i pole tekstowe
        ttk_bs.Label(main_frame, text="Wprowadź NIP, PESEL lub REGON:", font=('Arial', 10, 'bold')).pack(pady=5)
        
        identifier_var = tk.StringVar()
        identifier_entry = ttk_bs.Entry(main_frame, textvariable=identifier_var, width=25, font=('Arial', 12))
        identifier_entry.pack(pady=5)
        identifier_entry.focus()
        
        # Etykieta z informacją o rozpoznanym typie
        type_label = ttk_bs.Label(main_frame, text="", font=('Arial', 9), foreground='blue')
        type_label.pack(pady=2)
        
        # Informacja o formatach
        info_text = "NIP: 10 cyfr | PESEL: 11 cyfr | REGON: 9 lub 14 cyfr"
        ttk_bs.Label(main_frame, text=info_text, font=('Arial', 8), foreground='gray').pack(pady=5)
        
        # Przyciski
        button_frame = ttk_bs.Frame(main_frame)
        button_frame.pack(pady=20)
        
        def detect_type(identifier):
            """Rozpoznaje typ identyfikatora na podstawie długości"""
            clean_id = ''.join(filter(str.isdigit, identifier))
            length = len(clean_id)
            
            if length == 10:
                return "NIP", clean_id
            elif length == 11:
                return "PESEL", clean_id
            elif length == 9:
                return "REGON-9", clean_id
            elif length == 14:
                return "REGON-14", clean_id
            else:
                return "Nieznany", clean_id
        
        def update_type_label(*args):
            """Aktualizuje etykietę z typem identyfikatora"""
            identifier = identifier_var.get().strip()
            if identifier:
                id_type, clean_id = detect_type(identifier)
                if id_type != "Nieznany":
                    type_label.config(text=f"Rozpoznano: {id_type}")
                    type_label.config(foreground='green')
                else:
                    clean_id = ''.join(filter(str.isdigit, identifier))
                    if clean_id:
                        type_label.config(text=f"Nieznany typ (długość: {len(clean_id)} cyfr)")
                        type_label.config(foreground='orange')
                    else:
                        type_label.config(text="")
            else:
                type_label.config(text="")
        
        # Bind do aktualizacji etykiety
        identifier_var.trace('w', update_type_label)
        
        def add_identifier():
            identifier = identifier_var.get().strip()
            if not identifier:
                messagebox.showerror("Błąd", "Wprowadź NIP, PESEL lub REGON")
                return
            
            # Rozpoznaj typ
            id_type, clean_id = detect_type(identifier)
            
            if id_type == "Nieznany":
                messagebox.showerror("Błąd", f"Nieznany typ identyfikatora. Długość: {len(clean_id)} cyfr.\nOczekiwane: NIP (10), PESEL (11), REGON (9 lub 14)")
                return
            
            # Walidacja w zależności od typu
            if id_type == "NIP":
                is_valid, error_msg = validate_nip(clean_id)
                if not is_valid:
                    messagebox.showerror("Błąd", f"Niepoprawny NIP: {error_msg}")
                    return
            elif id_type == "PESEL":
                # Podstawowa walidacja PESEL (sprawdzenie długości i cyfr)
                if not clean_id.isdigit() or len(clean_id) != 11:
                    messagebox.showerror("Błąd", "Niepoprawny PESEL")
                    return
            elif id_type.startswith("REGON"):
                # Podstawowa walidacja REGON (sprawdzenie długości i cyfr)
                if not clean_id.isdigit() or len(clean_id) not in [9, 14]:
                    messagebox.showerror("Błąd", "Niepoprawny REGON")
                    return
            
            # Sprawdź czy identyfikator już istnieje
            if clean_id in self.nip_list:
                messagebox.showwarning("Uwaga", f"Ten {id_type} już istnieje na liście")
                return
            
            # Dodaj identyfikator
            self.nip_list.append(clean_id)
            self.add_nip_to_tree(clean_id, "Oczekuje", "", False)
            self.update_nip_count()
            self.log_message(f"Dodano {id_type}: {clean_id}")
            dialog.destroy()
        
        ttk_bs.Button(button_frame, text="Dodaj", command=add_identifier, bootstyle="success").pack(side=LEFT, padx=5)
        ttk_bs.Button(button_frame, text="Anuluj", command=dialog.destroy, bootstyle="secondary").pack(side=LEFT, padx=5)
        
        # Bind Enter
        identifier_entry.bind('<Return>', lambda e: add_identifier())
    
    def add_nip_to_tree(self, identifier, status, pdf_file="", has_sanctions=False):
        """Dodaje identyfikator do treeview"""
        # Określ typ i formatuj identyfikator
        if len(identifier) == 10:
            formatted_id = format_nip(identifier)  # NIP
            id_type = "NIP"
        elif len(identifier) == 11:
            # PESEL - format: XXXXX-XXXXX
            formatted_id = f"{identifier[:6]}-{identifier[6:]}"
            id_type = "PESEL"
        elif len(identifier) == 9:
            # REGON-9 - format: XXX-XXX-XXX
            formatted_id = f"{identifier[:3]}-{identifier[3:6]}-{identifier[6:]}"
            id_type = "REGON-9"
        elif len(identifier) == 14:
            # REGON-14 - format: XXXX-XXXX-XXXXX
            formatted_id = f"{identifier[:4]}-{identifier[4:8]}-{identifier[8:]}"
            id_type = "REGON-14"
        else:
            formatted_id = identifier
            id_type = "Nieznany"
        
        # Wybierz tag na podstawie sankcji
        tag = 'sanctions_found' if has_sanctions else 'normal'
        
        self.nip_tree.insert('', 'end', values=(formatted_id, id_type, status, pdf_file), tags=(tag,))
    
    def remove_selected_nips(self):
        """Usuwa zaznaczone identyfikatory"""
        selected_items = self.nip_tree.selection()
        if not selected_items:
            messagebox.showwarning("Uwaga", "Zaznacz identyfikatory do usunięcia")
            return
        
        # Usuń z listy i treeview
        for item in selected_items:
            values = self.nip_tree.item(item, 'values')
            identifier = values[0].replace('-', '')  # Usuń formatowanie
            if identifier in self.nip_list:
                self.nip_list.remove(identifier)
            self.nip_tree.delete(item)
        
        self.update_nip_count()
        self.log_message(f"Usunięto {len(selected_items)} identyfikatorów")
    
    def validate_all_nips(self):
        """Waliduje wszystkie identyfikatory na liście"""
        invalid_identifiers = []
        for identifier in self.nip_list:
            length = len(identifier)
            is_valid = False
            
            if length == 10:
                # NIP
                is_valid, _ = validate_nip(identifier)
            elif length == 11:
                # PESEL - podstawowa walidacja
                is_valid = identifier.isdigit() and len(identifier) == 11
            elif length in [9, 14]:
                # REGON - podstawowa walidacja
                is_valid = identifier.isdigit() and len(identifier) in [9, 14]
            
            if not is_valid:
                invalid_identifiers.append(identifier)
        
        if invalid_identifiers:
            messagebox.showwarning("Uwaga", f"Znaleziono {len(invalid_identifiers)} niepoprawnych identyfikatorów")
            self.log_message(f"Niepoprawne identyfikatory: {', '.join(invalid_identifiers)}", "WARNING")
        else:
            messagebox.showinfo("Sukces", "Wszystkie identyfikatory są poprawne")
            self.log_message("Wszystkie identyfikatory przeszły walidację")
    
    def start_generation(self):
        """Rozpoczyna generowanie PDF-ów"""
        if not self.nip_list:
            messagebox.showwarning("Uwaga", "Lista NIP-ów jest pusta")
            return
        
        if self.is_processing:
            messagebox.showwarning("Uwaga", "Generowanie już trwa")
            return
        
        # Wybierz katalog wyjściowy
        output_dir = filedialog.askdirectory(title="Wybierz katalog wyjściowy")
        if not output_dir:
            return
        
        # Rozpocznij generowanie z ThreadPoolExecutor
        self.is_processing = True
        self.stop_processing = False
        self.btn_generate.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.progress.config(maximum=len(self.nip_list), value=0)
        
        # Utwórz executor z maksymalnie 3 wątkami
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        thread = threading.Thread(target=self.generate_pdfs_thread, args=(output_dir,))
        thread.daemon = True
        thread.start()
    
    def generate_pdfs_thread(self, output_dir):
        """Wątek generowania PDF-ów z ThreadPoolExecutor"""
        try:
            self.update_status("Generowanie PDF-ów...")
            self.log_message(f"Rozpoczynanie generowania {len(self.nip_list)} PDF-ów")
            
            # Przygotuj zadania
            tasks = []
            for i, nip in enumerate(self.nip_list):
                if self.stop_processing:
                    break
                
                clean_nip = nip.replace('-', '') if nip else ""
                if not clean_nip:
                    continue
                
                task = self.executor.submit(self.process_single_nip, clean_nip, output_dir, i)
                tasks.append((task, nip, i))
            
            # Przetwarzaj wyniki
            completed = 0
            for task, nip, index in tasks:
                if self.stop_processing:
                    self.log_message("Generowanie zatrzymane przez użytkownika", "WARNING")
                    break
                
                try:
                    result = task.result(timeout=60)  # Timeout 60 sekund na zadanie
                    if result:
                        if len(result) == 4:  # Nowy format z informacją o sankcjach
                            pdf_path, success, has_sanctions, sanctions_count = result
                        else:  # Stary format dla kompatybilności
                            pdf_path, success = result
                            has_sanctions = False
                            sanctions_count = 0
                        
                        if success:
                            status_text = "Gotowy"
                            if has_sanctions:
                                status_text += f" (🚨 {sanctions_count} sankcji)"
                            self.root.after(0, self.update_nip_status, nip, status_text, pdf_path, has_sanctions)
                            self.generated_files.append(pdf_path)
                            self.log_message(f"Wygenerowano PDF: {os.path.basename(pdf_path)}")
                        else:
                            self.root.after(0, self.update_nip_status, nip, "Błąd", "", False)
                    else:
                        self.root.after(0, self.update_nip_status, nip, "Błąd", "", False)
                    
                    completed += 1
                    self.root.after(0, self.progress.config, {'value': completed})
                    
                except Exception as e:
                    self.root.after(0, self.update_nip_status, nip, "Błąd", "")
                    self.log_message(f"Błąd dla NIP {format_nip(nip)}: {e}", "ERROR")
                    completed += 1
                    self.root.after(0, self.progress.config, {'value': completed})
            
            if not self.stop_processing:
                self.log_message(f"Zakończono generowanie. Wygenerowano {len(self.generated_files)} PDF-ów")
                self.update_status("Generowanie zakończone")
            
        except Exception as e:
            self.log_message(f"Błąd generowania: {e}", "ERROR")
            self.update_status("Błąd generowania")
        
        finally:
            # Zamknij executor
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None
            
            # Przywróć stan przycisków
            self.root.after(0, self.finish_generation)
    
    def process_single_nip(self, clean_nip, output_dir, index):
        """Przetwarza pojedynczy NIP"""
        try:
            self.log_message(f"Przetwarzanie NIP: {format_nip(clean_nip)}")
            
            # Pobierz dane SOAP używając sesji
            soap = self.fetch_xml_by_nip_with_session(clean_nip)
            inner = extract_inner_xml_from_soap(soap)
            
            # Sprawdź słowa kluczowe sugerujące wykluczenie
            self.check_exclusion_in_xml(inner, clean_nip)
            
            # Wygeneruj PDF z informacją o sankcjach
            pdf_path, has_sanctions, sanctions_count = generate_pdf_from_xml_bytes_with_sanctions_info(inner, output_dir, default_nip=clean_nip)
            
            return pdf_path, True, has_sanctions, sanctions_count
            
        except Exception as e:
            self.log_message(f"Błąd dla NIP {format_nip(clean_nip)}: {e}", "ERROR")
            return None, False
    
    def fetch_xml_by_nip_with_session(self, nip):
        """Pobiera XML używając sesji HTTP"""
        from core.crbr_bulk_to_pdf import build_soap_request_by_nip, CRBR_ENDPOINT, HEADERS
        
        payload = build_soap_request_by_nip(nip)
        
        try:
            response = self.session.post(CRBR_ENDPOINT, data=payload, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Błąd pobierania danych dla NIP {nip}: {e}")
    
    def update_nip_status(self, identifier, status, pdf_file, has_sanctions=False):
        """Aktualizuje status identyfikatora w treeview"""
        # Formatuj identyfikator w zależności od typu
        if len(identifier) == 10:
            formatted_id = format_nip(identifier)  # NIP
            id_type = "NIP"
        elif len(identifier) == 11:
            # PESEL - format: XXXXX-XXXXX
            formatted_id = f"{identifier[:6]}-{identifier[6:]}"
            id_type = "PESEL"
        elif len(identifier) == 9:
            # REGON-9 - format: XXX-XXX-XXX
            formatted_id = f"{identifier[:3]}-{identifier[3:6]}-{identifier[6:]}"
            id_type = "REGON-9"
        elif len(identifier) == 14:
            # REGON-14 - format: XXXX-XXXX-XXXXX
            formatted_id = f"{identifier[:4]}-{identifier[4:8]}-{identifier[8:]}"
            id_type = "REGON-14"
        else:
            formatted_id = identifier
            id_type = "Nieznany"
        
        # Wybierz tag na podstawie sankcji
        tag = 'sanctions_found' if has_sanctions else 'normal'
        
        for item in self.nip_tree.get_children():
            values = self.nip_tree.item(item, 'values')
            if values[0] == formatted_id:
                # Przechowaj pełną ścieżkę w słowniku, ale wyświetl tylko nazwę pliku
                display_file = os.path.basename(pdf_file) if pdf_file else ""
                self.nip_tree.item(item, values=(formatted_id, id_type, status, display_file), tags=(tag,))
                # Przechowaj pełną ścieżkę w słowniku
                if pdf_file:
                    self.pdf_paths[formatted_id] = pdf_file
                break
    
    def stop_generation(self):
        """Zatrzymuje generowanie PDF-ów"""
        self.stop_processing = True
        self.log_message("Zatrzymywanie generowania...", "WARNING")
        self.update_status("Zatrzymywanie...")
        
        # Anuluj wszystkie zadania w executor
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
    
    def finish_generation(self):
        """Kończy generowanie i przywraca stan przycisków"""
        self.is_processing = False
        self.btn_generate.config(state=NORMAL)
        self.btn_stop.config(state=DISABLED)
        self.progress.config(value=0)
    
    def on_double_click(self, event):
        """Obsługuje dwuklik w tabeli"""
        item = self.nip_tree.selection()[0]
        values = self.nip_tree.item(item, 'values')
        
        # Pobierz pełną ścieżkę ze słownika
        formatted_id = values[0]  # formatted_id to pierwsza kolumna
        pdf_file = self.pdf_paths.get(formatted_id, '')
        if not pdf_file:
            # Fallback na starą metodę (dla kompatybilności)
            pdf_file = values[3]
        
        if pdf_file and os.path.exists(pdf_file):
            try:
                # Otwórz PDF w domyślnej przeglądarce
                if sys.platform.startswith('win'):
                    os.startfile(pdf_file)
                elif sys.platform.startswith('darwin'):
                    subprocess.call(['open', pdf_file])
                else:
                    subprocess.call(['xdg-open', pdf_file])
                
                self.log_message(f"Otwarto PDF: {pdf_file}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku: {e}")
        else:
            messagebox.showwarning("Uwaga", "Plik PDF nie istnieje")
    
    def on_mouse_motion(self, event):
        """Obsługuje ruch myszy nad treeview"""
        item = self.nip_tree.identify_row(event.y)
        if item and item != self.hovered_item:
            # Przywróć poprzedni element do normalnego stanu
            if self.hovered_item:
                self.restore_item_style(self.hovered_item)
            
            # Ustaw nowy hoverowany element
            self.hovered_item = item
            self.apply_hover_style(item)
    
    def on_mouse_leave(self, event):
        """Obsługuje opuszczenie myszy z treeview"""
        if self.hovered_item:
            self.restore_item_style(self.hovered_item)
            self.hovered_item = None
    
    def apply_hover_style(self, item):
        """Aplikuje styl hover dla elementu"""
        tags = self.nip_tree.item(item, 'tags')
        if 'sanctions_found' in tags:
            # Dla rekordów z sankcjami użyj specjalnego koloru hover
            self.nip_tree.item(item, tags=('sanctions_found_hover',))
    
    def restore_item_style(self, item):
        """Przywraca oryginalny styl elementu"""
        tags = self.nip_tree.item(item, 'tags')
        if 'sanctions_found_hover' in tags:
            # Przywróć oryginalny tag dla sankcji
            self.nip_tree.item(item, tags=('sanctions_found',))
        elif 'normal' in tags or not tags:
            # Element normalny - nie ma potrzeby zmiany
            pass
    
    def setup_drag_and_drop(self):
        """Konfiguruje obsługę drag and drop dla plików"""
        # Sprawdź czy okno obsługuje drag and drop
        if hasattr(self.root, 'tk') and 'TkinterDnD' in str(type(self.root)):
            try:
                from tkinterdnd2 import DND_FILES
                
                # Rejestruj treeview jako drop target
                self.nip_tree.drop_target_register(DND_FILES)
                self.nip_tree.dnd_bind('<<Drop>>', self.on_file_drop)
                
                # Dodaj wizualną wskazówkę
                self.add_drag_drop_indicator()
                
                self.log_message("Drag & Drop aktywne - przeciągnij pliki CSV/XLS/XLSX na okno")
                return
                
            except Exception as e:
                self.log_message(f"Błąd konfiguracji drag & drop: {e}")
                self.setup_simple_drag_and_drop()
        else:
            # Okno nie obsługuje drag and drop - użyj fallback
            self.log_message("Okno nie obsługuje drag & drop, używam prostej obsługi")
            self.setup_simple_drag_and_drop()
    
    def add_drag_drop_indicator(self):
        """Dodaje wizualną wskazówkę drag and drop"""
        # Dodaj subtelną wskazówkę w etykiecie statusu
        if hasattr(self, 'status_label'):
            original_text = self.status_label.cget('text')
            if "Drag & Drop" not in original_text:
                self.status_label.config(text=f"{original_text} | Drag & Drop: CSV, XLS, XLSX")
    
    def setup_simple_drag_and_drop(self):
        """Prosta implementacja drag and drop używająca tylko tkinter"""
        # Dodaj tooltip do przycisku importu CSV
        if hasattr(self, 'btn_import_csv'):
            self.create_tooltip(
                self.btn_import_csv, 
                "Importuj NIP-y z pliku CSV, XLS, XLSX\nObsługuje również przeciąganie plików"
            )
        
        # Dodaj informację w logu
        self.log_message("💡 Wskazówka: Możesz przeciągnąć pliki CSV, XLS, XLSX na okno aplikacji")
    
    def on_file_drop(self, event):
        """Obsługuje upuszczenie plików"""
        # Debug: sprawdź co otrzymaliśmy
        self.log_message(f"Otrzymane dane drag & drop: {event.data}")
        
        # Poprawne parsowanie ścieżek (obsługa ścieżek ze spacjami)
        files = []
        if event.data:
            # Jeśli dane zawierają nawiasy klamrowe, usuń je
            data = event.data.strip('{}')
            
            # Specjalna obsługa przypadku gdy folder i plik są połączone
            # Przykład: "C:/Users/.../Raport crbr/nipy.csv"
            import re
            
            # Najpierw spróbuj znaleźć pełne ścieżki plików (z rozszerzeniem)
            file_pattern = r'([A-Za-z]:[^}]*?\.(?:csv|xls|xlsx))'
            file_matches = re.findall(file_pattern, data)
            
            if file_matches:
                # Znaleziono pliki - użyj ich
                files = file_matches
                self.log_message(f"Znalezione pliki przez wzorzec: {files}")
            else:
                # Fallback - podziel na części i spróbuj zrekonstruować
                parts = data.split()
                self.log_message(f"Podzielone części: {parts}")
                
                # Spróbuj połączyć części w logiczne ścieżki
                reconstructed_files = []
                current_path = ""
                
                for part in parts:
                    if current_path:
                        # Sprawdź czy dodanie tej części tworzy prawidłową ścieżkę pliku
                        test_path = current_path + " " + part
                        if any(test_path.lower().endswith(ext) for ext in ['.csv', '.xls', '.xlsx']):
                            reconstructed_files.append(test_path)
                            current_path = ""
                        else:
                            current_path = test_path
                    else:
                        if any(part.lower().endswith(ext) for ext in ['.csv', '.xls', '.xlsx']):
                            # To jest już pełna ścieżka pliku
                            reconstructed_files.append(part)
                        else:
                            current_path = part
                
                files = reconstructed_files
                self.log_message(f"Zrekonstruowane pliki: {files}")
        
        self.log_message(f"Znalezione pliki: {files}")
        
        for file_path in files:
            self.process_dropped_file(file_path)
    
    def process_dropped_file(self, file_path):
        """Przetwarza upuszczony plik"""
        try:
            # Debug: sprawdź szczegóły pliku
            self.log_message(f"Przetwarzam ścieżkę: {file_path}")
            self.log_message(f"Typ: {type(file_path)}")
            
            # Sprawdź czy to jest plik czy folder
            if os.path.isdir(file_path):
                self.log_message(f"To jest folder, nie plik: {file_path}")
                messagebox.showwarning(
                    "Nieprawidłowy typ", 
                    f"Przeciągnięto folder zamiast pliku: {os.path.basename(file_path)}\nPrzeciągnij konkretny plik CSV, XLS lub XLSX."
                )
                return
            
            if not os.path.isfile(file_path):
                # Sprawdź czy to względna ścieżka - spróbuj zrekonstruować pełną ścieżkę
                if not os.path.isabs(file_path):
                    # To jest względna ścieżka - spróbuj znaleźć plik w bieżącym katalogu
                    current_dir = os.getcwd()
                    possible_paths = [
                        os.path.join(current_dir, file_path),
                        os.path.join(current_dir, os.path.basename(file_path))
                    ]
                    
                    self.log_message(f"Próbuję znaleźć plik w: {possible_paths}")
                    
                    for possible_path in possible_paths:
                        if os.path.isfile(possible_path):
                            self.log_message(f"Znaleziono plik: {possible_path}")
                            file_path = possible_path
                            break
                    else:
                        self.log_message(f"Nie znaleziono pliku w żadnej lokalizacji")
                        messagebox.showwarning(
                            "Nieprawidłowa ścieżka", 
                            f"Nie można znaleźć pliku: {file_path}\nPrzeciągnij konkretny plik CSV, XLS lub XLSX."
                        )
                        return
                else:
                    self.log_message(f"Ścieżka nie wskazuje na plik: {file_path}")
                    messagebox.showwarning(
                        "Nieprawidłowa ścieżka", 
                        f"Ścieżka nie wskazuje na plik: {file_path}\nPrzeciągnij konkretny plik CSV, XLS lub XLSX."
                    )
                    return
            
            # Sprawdź rozszerzenie pliku
            file_ext = os.path.splitext(file_path)[1].lower()
            self.log_message(f"Rozszerzenie pliku: {file_ext}")
            
            if file_ext in ['.csv', '.xls', '.xlsx']:
                self.log_message(f"Przetwarzam upuszczony plik: {os.path.basename(file_path)}")
                
                # Użyj istniejącej funkcji importu
                if file_ext == '.csv':
                    self.import_from_file(file_path)
                else:
                    self.import_from_excel(file_path)
            else:
                messagebox.showwarning(
                    "Nieobsługiwany format", 
                    f"Plik {os.path.basename(file_path)} ma nieobsługiwany format.\nObsługiwane formaty: CSV, XLS, XLSX"
                )
                
        except Exception as e:
            self.log_message(f"Błąd przetwarzania pliku: {e}", "ERROR")
            messagebox.showerror("Błąd", f"Nie można przetworzyć pliku {file_path}:\n{str(e)}")
    
    def import_from_excel(self, file_path):
        """Importuje dane z pliku Excel (XLS, XLSX)"""
        try:
            import pandas as pd
            
            # Wczytaj plik Excel
            df = pd.read_excel(file_path)
            
            # Konwertuj na format CSV w pamięci
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            csv_content = csv_buffer.getvalue()
            
            # Użyj istniejącej funkcji walidacji
            from utils.nip_validator import validate_nips_from_csv_content
            validation_result = validate_nips_from_csv_content(csv_content)
            
            # Dodaj poprawne NIP-y do listy
            if validation_result['valid']:
                for nip in validation_result['valid']:
                    if nip not in self.nip_list:
                        self.nip_list.append(nip)
                        self.add_nip_to_tree(nip, "Oczekuje", "", False)
                self.update_nip_count()
            
            # Pokaż szczegółowe wyniki
            self.show_import_results(validation_result, file_path)
            
        except Exception as e:
            error_msg = f"Błąd importu pliku Excel:\n{str(e)}"
            messagebox.showerror("Błąd", error_msg)
            self.log_message(error_msg, "ERROR")
    
    def import_from_file(self, file_path):
        """Importuje dane z pliku CSV"""
        try:
            # Użyj istniejącej logiki importu CSV
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            from utils.nip_validator import validate_nips_from_csv_content
            validation_result = validate_nips_from_csv_content(content)
            
            # Dodaj poprawne NIP-y do listy
            if validation_result['valid']:
                for nip in validation_result['valid']:
                    if nip not in self.nip_list:
                        self.nip_list.append(nip)
                        self.add_nip_to_tree(nip, "Oczekuje", "", False)
                self.update_nip_count()
            
            # Pokaż szczegółowe wyniki
            self.show_import_results(validation_result, file_path)
            
        except Exception as e:
            error_msg = f"Błąd importu pliku CSV:\n{str(e)}"
            messagebox.showerror("Błąd", error_msg)
            self.log_message(error_msg, "ERROR")
    
    def export_results(self):
        """Eksportuje wyniki do pliku"""
        if not self.generated_files:
            messagebox.showwarning("Uwaga", "Brak wygenerowanych plików")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Zapisz wyniki",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("SancCheck - Wyniki weryfikacji\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Data generowania: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Liczba wygenerowanych plików: {len(self.generated_files)}\n\n")
                f.write("Lista plików:\n")
                f.write("-" * 30 + "\n")
                for i, file_path in enumerate(self.generated_files, 1):
                    f.write(f"{i:3d}. {os.path.basename(file_path)}\n")
                    f.write(f"     {file_path}\n\n")
            
            self.log_message(f"Wyniki zapisane do: {file_path}")
            messagebox.showinfo("Sukces", f"Wyniki zapisane do:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")
    
    def clear_all(self):
        """Czyści całą listę NIP-ów"""
        if not self.nip_list:
            return
        
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz wyczyścić całą listę NIP-ów?"):
            self.nip_list.clear()
            self.generated_files.clear()
            
            # Wyczyść treeview
            for item in self.nip_tree.get_children():
                self.nip_tree.delete(item)
            
            self.update_nip_count()
            self.log_message("Wyczyszczono całą listę NIP-ów")
    
    def clear_logs(self):
        """Czyści logi"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Logi wyczyszczone")
    
    def save_logs(self):
        """Zapisuje logi do pliku"""
        file_path = filedialog.asksaveasfilename(
            title="Zapisz logi",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            
            self.log_message(f"Logi zapisane do: {file_path}")
            messagebox.showinfo("Sukces", f"Logi zapisane do:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")
    
    def show_theme_menu(self):
        """Pokazuje menu wyboru motywów"""
        # Lista dostępnych motywów z opisami
        themes = [
            ("flatly", "Flatly - Jasny, nowoczesny"),
            ("darkly", "Darkly - Ciemny, elegancki"),
            ("cosmo", "Cosmo - Niebieski, profesjonalny"),
            ("litera", "Litera - Minimalistyczny, czytelny"),
            ("minty", "Minty - Zielony, świeży"),
            ("pulse", "Pulse - Fioletowy, dynamiczny"),
            ("sandstone", "Sandstone - Beżowy, ciepły"),
            ("united", "United - Pomarańczowy, energiczny"),
            ("yeti", "Yeti - Szary, neutralny"),
            ("superhero", "Superhero - Ciemny, niebieski"),
            ("solar", "Solar - Ciemny, żółty"),
            ("vapor", "Vapor - Różowy, futurystyczny")
        ]
        
        # Utwórz okno wyboru motywu
        theme_window = tk.Toplevel(self.root)
        theme_window.title("Wybierz motyw aplikacji")
        theme_window.geometry("400x500")
        theme_window.resizable(False, False)
        theme_window.transient(self.root)
        theme_window.grab_set()
        
        # Centrowanie okna
        theme_window.update_idletasks()
        x = (theme_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (theme_window.winfo_screenheight() // 2) - (500 // 2)
        theme_window.geometry(f"400x500+{x}+{y}")
        
        # Ramka główna
        main_frame = ttk_bs.Frame(theme_window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Tytuł
        title_label = ttk_bs.Label(
            main_frame, 
            text="🎨 Wybierz motyw aplikacji", 
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Aktualny motyw
        current_label = ttk_bs.Label(
            main_frame,
            text=f"Aktualny motyw: {self.current_theme.title()}",
            font=('Arial', 10, 'italic')
        )
        current_label.pack(pady=(0, 15))
        
        # Lista motywów
        listbox_frame = ttk_bs.Frame(main_frame)
        listbox_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        listbox = tk.Listbox(listbox_frame, height=12, font=('Arial', 10))
        scrollbar = ttk_bs.Scrollbar(listbox_frame, orient=VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Dodaj motywy do listy
        for theme_name, theme_desc in themes:
            listbox.insert(tk.END, f"{theme_name.title()} - {theme_desc}")
        
        # Zaznacz aktualny motyw
        for i, (theme_name, _) in enumerate(themes):
            if theme_name == self.current_theme:
                listbox.selection_set(i)
                listbox.see(i)
                break
        
        # Ramka przycisków
        button_frame = ttk_bs.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        def apply_theme():
            selection = listbox.curselection()
            if selection:
                selected_theme = themes[selection[0]][0]
                self.change_theme(selected_theme)
                theme_window.destroy()
            else:
                messagebox.showwarning("Uwaga", "Wybierz motyw")
        
        def preview_theme():
            selection = listbox.curselection()
            if selection:
                selected_theme = themes[selection[0]][0]
                # Podgląd motywu (tymczasowa zmiana)
                self.root.style.theme_use(selected_theme)
                self.log_message(f"Podgląd motywu: {selected_theme}")
        
        ttk_bs.Button(
            button_frame, 
            text="Podgląd", 
            command=preview_theme, 
            bootstyle="info-outline"
        ).pack(side=LEFT, padx=(0, 5))
        
        ttk_bs.Button(
            button_frame, 
            text="Zastosuj", 
            command=apply_theme, 
            bootstyle="success"
        ).pack(side=LEFT, padx=5)
        
        ttk_bs.Button(
            button_frame, 
            text="Anuluj", 
            command=theme_window.destroy, 
            bootstyle="secondary"
        ).pack(side=RIGHT)
        
        # Bind Enter i double-click
        listbox.bind('<Return>', lambda e: apply_theme())
        listbox.bind('<Double-Button-1>', lambda e: apply_theme())
        
        # Focus na listbox
        listbox.focus_set()
    
    def change_theme(self, theme_name):
        """Zmienia motyw aplikacji"""
        try:
            # Zmień motyw
            self.current_theme = theme_name
            self.root.style.theme_use(theme_name)
            
            # Zaktualizuj tytuł okna
            self.root.title(f"SancCheck - Weryfikacja sankcji CRBR ({theme_name.title()})")
            
            # Loguj zmianę
            self.log_message(f"Zmieniono motyw na: {theme_name.title()}")
            
            # Pokaż komunikat
            messagebox.showinfo("Sukces", f"Motyw zmieniony na: {theme_name.title()}")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zmienić motywu: {e}")
            self.log_message(f"Błąd zmiany motywu: {e}", "ERROR")
    
    def update_sanctions_lists(self):
        """Aktualizuje listy wykluczonych podmiotów i osób"""
        try:
            self.log_message("Rozpoczynanie aktualizacji list sankcyjnych...")
            self.update_status("Aktualizacja list sankcyjnych...")
            
            # Wyłącz przycisk podczas aktualizacji
            self.btn_update_sanctions.config(state=DISABLED, text="🔄 Aktualizacja...")
            
            # Uruchom aktualizację w osobnym wątku
            thread = threading.Thread(target=self.update_sanctions_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            self.log_message(f"Błąd uruchamiania aktualizacji list sankcyjnych: {e}", "ERROR")
            self.btn_update_sanctions.config(state=NORMAL, text="🔄 Aktualizuj listy sankcyjne")
    
    def update_sanctions_thread(self):
        """Wątek aktualizacji list sankcyjnych"""
        try:
            # Import funkcji pobierania list sankcyjnych
            from core.download_sanctions import save_sanctions_data
            
            # Pobierz i zapisz dane sankcyjne
            self.log_message("Pobieranie danych z Ministerstwa Finansów...")
            df_mf, df_mswia, df_eu = save_sanctions_data()
            
            # Aktualizuj słowa kluczowe na podstawie pobranych danych
            self.update_exclusion_keywords_from_sanctions(df_mf, df_mswia, df_eu)
            
            # Przywróć stan przycisku
            self.root.after(0, self.finish_sanctions_update, True, "Aktualizacja zakończona pomyślnie")
            
        except Exception as e:
            error_msg = f"Błąd aktualizacji list sankcyjnych: {e}"
            self.log_message(error_msg, "ERROR")
            self.root.after(0, self.finish_sanctions_update, False, error_msg)
    
    def update_exclusion_keywords_from_sanctions(self, df_mf, df_mswia, df_eu):
        """Aktualizuje słowa kluczowe na podstawie pobranych list sankcyjnych i konsoliduje dane do JSON"""
        try:
            new_keywords = set(self.exclusion_keywords)
            
            # Konsoliduj dane sankcyjne do jednego pliku JSON
            consolidated_data = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'sources': {
                        'mf': {'count': 0, 'available': False},
                        'mswia': {'count': 0, 'available': False},
                        'eu': {'count': 0, 'available': False}
                    }
                },
                'sanctions': {
                    'mf': [],
                    'mswia': [],
                    'eu': []
                }
            }
            
            # Przetwórz dane MF
            if df_mf is not None and not df_mf.empty:
                self.log_message(f"Konsolidowanie {len(df_mf)} rekordów z MF...")
                consolidated_data['metadata']['sources']['mf'] = {
                    'count': len(df_mf),
                    'available': True
                }
                
                for _, row in df_mf.iterrows():
                    record = {}
                    for col in df_mf.columns:
                        if pd.notna(row[col]):
                            # Handle pandas Timestamp objects safely
                            value = row[col]
                            if hasattr(value, 'strftime'):
                                record[col] = str(value)
                            else:
                                record[col] = str(value)
                    
                    consolidated_data['sanctions']['mf'].append(record)
                    
                    # Dodaj nazwy do słów kluczowych
                    if 'Nazwa' in record:
                        name = record['Nazwa'].strip()
                        if len(name) > 2:
                            new_keywords.add(name)
                    elif 'Imiona i nazwiska' in record:
                        name = record['Imiona i nazwiska'].strip()
                        if len(name) > 2:
                            new_keywords.add(name)
            
            # Przetwórz dane MSWiA
            if df_mswia is not None and not df_mswia.empty:
                self.log_message(f"Konsolidowanie {len(df_mswia)} rekordów z MSWiA...")
                consolidated_data['metadata']['sources']['mswia'] = {
                    'count': len(df_mswia),
                    'available': True
                }
                
                for _, row in df_mswia.iterrows():
                    record = {}
                    for col in df_mswia.columns:
                        if pd.notna(row[col]):
                            # Handle pandas Timestamp objects safely
                            value = row[col]
                            if hasattr(value, 'strftime'):
                                record[col] = str(value)
                            else:
                                record[col] = str(value)
                    
                    consolidated_data['sanctions']['mswia'].append(record)
                    
                    # Dodaj nazwy do słów kluczowych
                    if 'Imiona i nazwiska' in record:
                        name = record['Imiona i nazwiska'].strip()
                        if len(name) > 2:
                            new_keywords.add(name)
            
            # Przetwórz dane UE
            if df_eu is not None and not df_eu.empty:
                self.log_message(f"Konsolidowanie {len(df_eu)} rekordów z UE...")
                consolidated_data['metadata']['sources']['eu'] = {
                    'count': len(df_eu),
                    'available': True
                }
                
                for _, row in df_eu.iterrows():
                    record = {}
                    for col in df_eu.columns:
                        if pd.notna(row[col]):
                            # Handle pandas Timestamp objects safely
                            value = row[col]
                            if hasattr(value, 'strftime'):
                                record[col] = str(value)
                            else:
                                record[col] = str(value)
                    
                    consolidated_data['sanctions']['eu'].append(record)
                    
                    # Dodaj nazwy do słów kluczowych
                    if 'Name' in record:
                        name = record['Name'].strip()
                        if len(name) > 2:
                            new_keywords.add(name)
            
            # Zapisz skonsolidowane dane do JSON
            self.save_consolidated_sanctions_data(consolidated_data)
            
            # Usuń stare pliki Excel
            self.cleanup_old_sanctions_files()
            
            # Aktualizuj listę słów kluczowych
            old_count = len(self.exclusion_keywords)
            self.exclusion_keywords = list(new_keywords)
            new_count = len(self.exclusion_keywords)
            
            self.log_message(f"Zaktualizowano słowa kluczowe: {old_count} → {new_count} ({new_count - old_count} nowych)")
            
            # Zapisz zaktualizowaną listę do pliku
            self.save_exclusion_keywords_to_file()
            
        except Exception as e:
            self.log_message(f"Błąd aktualizacji słów kluczowych: {e}", "ERROR")
    
    def save_consolidated_sanctions_data(self, consolidated_data):
        """Zapisuje skonsolidowane dane sankcyjne do pliku JSON"""
        try:
            sanctions_dir = os.path.join("data", "sanctions")
            if not os.path.exists(sanctions_dir):
                os.makedirs(sanctions_dir)
            
            json_file = os.path.join(sanctions_dir, "consolidated_sanctions.json")
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, ensure_ascii=False, indent=2)
            
            total_records = (
                consolidated_data['metadata']['sources']['mf']['count'] +
                consolidated_data['metadata']['sources']['mswia']['count'] +
                consolidated_data['metadata']['sources']['eu']['count']
            )
            
            self.log_message(f"Zapisano skonsolidowane dane sankcyjne: {total_records} rekordów do {json_file}")
            
        except Exception as e:
            self.log_message(f"Błąd zapisywania skonsolidowanych danych: {e}", "ERROR")
    
    def cleanup_old_sanctions_files(self):
        """Usuwa stare pliki Excel po konsolidacji do JSON"""
        try:
            sanctions_dir = os.path.join("data", "sanctions")
            if not os.path.exists(sanctions_dir):
                return
            
            import glob
            
            # Znajdź wszystkie pliki Excel
            excel_patterns = [
                os.path.join(sanctions_dir, "mf_sanctions_*.xlsx"),
                os.path.join(sanctions_dir, "mswia_sanctions_*.xlsx"),
                os.path.join(sanctions_dir, "eu_sanctions_*.xlsx")
            ]
            
            deleted_count = 0
            for pattern in excel_patterns:
                files = glob.glob(pattern)
                for file_path in files:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        self.log_message(f"Usunięto stary plik: {os.path.basename(file_path)}")
                    except Exception as e:
                        self.log_message(f"Błąd usuwania pliku {file_path}: {e}", "WARNING")
            
            if deleted_count > 0:
                self.log_message(f"Usunięto {deleted_count} starych plików Excel")
            
        except Exception as e:
            self.log_message(f"Błąd czyszczenia starych plików: {e}", "ERROR")
    
    def save_exclusion_keywords_to_file(self):
        """Zapisuje aktualną listę słów kluczowych do pliku"""
        try:
            keywords_file = os.path.join(project_root, 'config', 'exclusion_keywords.txt')
            with open(keywords_file, 'w', encoding='utf-8') as f:
                f.write("# Lista słów kluczowych sugerujących wykluczenie z postępowania\n")
                f.write("# art. 7 ust. 1 ustawy o przeciwdziałaniu wspieraniu agresji na Ukrainę\n")
                f.write(f"# Zaktualizowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for keyword in sorted(self.exclusion_keywords):
                    f.write(f"{keyword}\n")
            
            self.log_message(f"Zapisano {len(self.exclusion_keywords)} słów kluczowych do pliku: {keywords_file}")
            
        except Exception as e:
            self.log_message(f"Błąd zapisywania słów kluczowych: {e}", "ERROR")
    
    def load_exclusion_keywords_from_file(self):
        """Wczytuje listę słów kluczowych z pliku"""
        try:
            keywords_file = os.path.join(project_root, 'config', 'exclusion_keywords.txt')
            if os.path.exists(keywords_file):
                with open(keywords_file, 'r', encoding='utf-8') as f:
                    keywords = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            keywords.append(line)
                
                if keywords:
                    self.exclusion_keywords = keywords
                    self.log_message(f"Wczytano {len(keywords)} słów kluczowych z pliku")
                else:
                    self.log_message("Plik słów kluczowych jest pusty, używam domyślnych")
            else:
                self.log_message("Brak pliku słów kluczowych, używam domyślnych")
                
        except Exception as e:
            self.log_message(f"Błąd wczytywania słów kluczowych: {e}", "ERROR")
    
    def finish_sanctions_update(self, success, message):
        """Kończy aktualizację list sankcyjnych"""
        self.btn_update_sanctions.config(state=NORMAL, text="🔄 Aktualizuj listy sankcyjne")
        
        if success:
            self.log_message(message, "INFO")
            self.update_status("Gotowy do pracy")
            messagebox.showinfo("Sukces", message)
        else:
            self.log_message(message, "ERROR")
            self.update_status("Błąd aktualizacji")
            messagebox.showerror("Błąd", message)

    
    

    def run(self):
        """Uruchamia aplikację"""
        self.log_message("Aplikacja SancCheck uruchomiona")
        self.root.mainloop()


def main():
    """Główna funkcja"""
    try:
        app = ModernCRBRGUI()
        app.run()
    except Exception as e:
        print(f"Błąd uruchamiania aplikacji: {e}")
        print("Aplikacja będzie kontynuowana bez niektórych funkcji...")
        # Nie kończ aplikacji - pozwól użytkownikowi zobaczyć błąd
        import traceback
        traceback.print_exc()
        input("Naciśnij Enter aby kontynuować...")


if __name__ == "__main__":
    main()
