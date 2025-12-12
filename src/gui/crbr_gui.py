#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SancCheck GUI - Interfejs graficzny dla aplikacji SancCheck

GUI umożliwia:
- Dodawanie NIP-ów do listy weryfikacji
- Import NIP-ów z pliku CSV
- Generowanie raportów PDF dla wybranych NIP-ów
- Weryfikacja list sankcyjnych
- Śledzenie postępu operacji
- Podgląd wyników

Autor: (C) 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from typing import List, Dict, Any
import queue
import time

# Import funkcji z oryginalnego skryptu
from ..core.crbr_bulk_to_pdf import (
    fetch_xml_by_nip, 
    extract_inner_xml_from_soap, 
    generate_pdf_from_xml_bytes,
    parse_crbr_xml
)

class CRBRGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SancCheck - Weryfikacja sankcji CRBR")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Kolejka do komunikacji między wątkami
        self.queue = queue.Queue()
        
        # Lista NIP-ów do weryfikacji
        self.nip_list = []
        
        # Status operacji
        self.is_processing = False
        
        self.setup_ui()
        self.check_queue()
        
    def setup_ui(self):
        """Konfiguracja interfejsu użytkownika"""
        
        # Główny frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguracja grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Tytuł
        title_label = ttk.Label(main_frame, text="SancCheck - Weryfikacja sankcji CRBR", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Sekcja dodawania NIP-ów
        self.setup_nip_section(main_frame)
        
        # Sekcja listy NIP-ów
        self.setup_list_section(main_frame)
        
        # Sekcja operacji
        self.setup_operations_section(main_frame)
        
        # Sekcja logów
        self.setup_logs_section(main_frame)
        
    def setup_nip_section(self, parent):
        """Sekcja dodawania NIP-ów"""
        nip_frame = ttk.LabelFrame(parent, text="Dodawanie NIP-ów", padding="10")
        nip_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        nip_frame.columnconfigure(1, weight=1)
        
        # Pole NIP
        ttk.Label(nip_frame, text="NIP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.nip_entry = ttk.Entry(nip_frame, width=15)
        self.nip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.nip_entry.bind('<Return>', lambda e: self.add_nip())
        
        # Przycisk dodaj
        self.add_btn = ttk.Button(nip_frame, text="Dodaj NIP", command=self.add_nip)
        self.add_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Przycisk import CSV
        self.import_btn = ttk.Button(nip_frame, text="Import CSV", command=self.import_csv)
        self.import_btn.grid(row=0, column=3)
        
    def setup_list_section(self, parent):
        """Sekcja listy NIP-ów"""
        list_frame = ttk.LabelFrame(parent, text="Lista NIP-ów do weryfikacji", padding="10")
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Treeview dla listy NIP-ów
        columns = ('nip', 'status', 'file')
        self.nip_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        # Konfiguracja kolumn
        self.nip_tree.heading('nip', text='NIP')
        self.nip_tree.heading('status', text='Status')
        self.nip_tree.heading('file', text='Plik PDF')
        
        self.nip_tree.column('nip', width=120)
        self.nip_tree.column('status', width=100)
        self.nip_tree.column('file', width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.nip_tree.yview)
        self.nip_tree.configure(yscrollcommand=scrollbar.set)
        
        self.nip_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Przyciski zarządzania listą
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Usuń zaznaczone", command=self.remove_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Wyczyść listę", command=self.clear_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="Eksport do CSV", command=self.export_csv).pack(side=tk.LEFT)
        
    def setup_operations_section(self, parent):
        """Sekcja operacji"""
        ops_frame = ttk.LabelFrame(parent, text="Operacje", padding="10")
        ops_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Katalog wyjściowy
        ttk.Label(ops_frame, text="Katalog wyjściowy:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.output_dir_var = tk.StringVar(value="output_pdfs")
        self.output_entry = ttk.Entry(ops_frame, textvariable=self.output_dir_var, width=30)
        self.output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.browse_btn = ttk.Button(ops_frame, text="Przeglądaj", command=self.browse_output_dir)
        self.browse_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Timeout
        ttk.Label(ops_frame, text="Timeout (s):").grid(row=0, column=3, sticky=tk.W, padx=(10, 5))
        self.timeout_var = tk.StringVar(value="45")
        self.timeout_entry = ttk.Entry(ops_frame, textvariable=self.timeout_var, width=8)
        self.timeout_entry.grid(row=0, column=4)
        
        ops_frame.columnconfigure(1, weight=1)
        
        # Przyciski operacji
        btn_frame = ttk.Frame(ops_frame)
        btn_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0))
        
        self.process_btn = ttk.Button(btn_frame, text="Generuj raporty PDF", 
                                     command=self.start_processing, style="Accent.TButton")
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(btn_frame, text="Zatrzymaj", command=self.stop_processing, 
                                  state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(ops_frame, variable=self.progress_var, 
                                           maximum=100, length=300)
        self.progress_bar.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_logs_section(self, parent):
        """Sekcja logów"""
        logs_frame = ttk.LabelFrame(parent, text="Logi operacji", padding="10")
        logs_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Przycisk czyszczenia logów
        ttk.Button(logs_frame, text="Wyczyść logi", command=self.clear_logs).grid(row=1, column=0, pady=(5, 0))
        
    def log_message(self, message: str):
        """Dodaje wiadomość do logów"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_logs(self):
        """Czyści logi"""
        self.log_text.delete(1.0, tk.END)
        
    def add_nip(self):
        """Dodaje NIP do listy"""
        nip = self.nip_entry.get().strip()
        if not nip:
            messagebox.showwarning("Ostrzeżenie", "Wprowadź NIP")
            return
            
        # Walidacja NIP (tylko cyfry)
        if not nip.isdigit() or len(nip) != 10:
            messagebox.showerror("Błąd", "NIP musi składać się z 10 cyfr")
            return
            
        if nip in self.nip_list:
            messagebox.showwarning("Ostrzeżenie", "Ten NIP już jest na liście")
            return
            
        self.nip_list.append(nip)
        self.nip_tree.insert('', tk.END, values=(nip, "Oczekuje", ""))
        self.nip_entry.delete(0, tk.END)
        self.log_message(f"Dodano NIP: {nip}")
        
    def remove_selected(self):
        """Usuwa zaznaczone NIP-y z listy"""
        selected = self.nip_tree.selection()
        if not selected:
            messagebox.showwarning("Ostrzeżenie", "Zaznacz NIP-y do usunięcia")
            return
            
        for item in selected:
            nip = self.nip_tree.item(item)['values'][0]
            self.nip_list.remove(nip)
            self.nip_tree.delete(item)
            self.log_message(f"Usunięto NIP: {nip}")
            
    def clear_list(self):
        """Czyści całą listę NIP-ów"""
        if not self.nip_list:
            return
            
        if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz wyczyścić całą listę?"):
            self.nip_list.clear()
            for item in self.nip_tree.get_children():
                self.nip_tree.delete(item)
            self.log_message("Wyczyszczono listę NIP-ów")
            
    def import_csv(self):
        """Importuje NIP-y z pliku CSV"""
        file_path = filedialog.askopenfilename(
            title="Wybierz plik CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            import pandas as pd
            from utf8_config import get_csv_encoding
            df = pd.read_csv(file_path, dtype=str, encoding=get_csv_encoding())
            
            if 'nip' not in df.columns:
                messagebox.showerror("Błąd", "Plik CSV musi zawierać kolumnę 'nip'")
                return
                
            imported_count = 0
            for nip in df['nip']:
                nip = str(nip).strip()
                # Usuń wszystkie znaki niebędące cyframi
                nip = ''.join(filter(str.isdigit, nip))
                
                if len(nip) == 10 and nip not in self.nip_list:
                    self.nip_list.append(nip)
                    self.nip_tree.insert('', tk.END, values=(nip, "Oczekuje", ""))
                    imported_count += 1
                    
            self.log_message(f"Zaimportowano {imported_count} NIP-ów z pliku {os.path.basename(file_path)}")
            messagebox.showinfo("Sukces", f"Zaimportowano {imported_count} NIP-ów")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas importu CSV: {str(e)}")
            
    def export_csv(self):
        """Eksportuje listę NIP-ów do CSV"""
        if not self.nip_list:
            messagebox.showwarning("Ostrzeżenie", "Lista NIP-ów jest pusta")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Zapisz plik CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            import pandas as pd
            from utf8_config import get_csv_encoding
            df = pd.DataFrame({'nip': self.nip_list})
            df.to_csv(file_path, index=False, encoding=get_csv_encoding())
            self.log_message(f"Eksportowano {len(self.nip_list)} NIP-ów do pliku {os.path.basename(file_path)}")
            messagebox.showinfo("Sukces", f"Eksportowano {len(self.nip_list)} NIP-ów")
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas eksportu: {str(e)}")
            
    def browse_output_dir(self):
        """Wybieranie katalogu wyjściowego"""
        directory = filedialog.askdirectory(title="Wybierz katalog wyjściowy")
        if directory:
            self.output_dir_var.set(directory)
            
    def start_processing(self):
        """Rozpoczyna przetwarzanie NIP-ów"""
        if not self.nip_list:
            messagebox.showwarning("Ostrzeżenie", "Lista NIP-ów jest pusta")
            return
            
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showerror("Błąd", "Wybierz katalog wyjściowy")
            return
            
        try:
            timeout = int(self.timeout_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Timeout musi być liczbą")
            return
            
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        
        # Uruchom przetwarzanie w osobnym wątku
        thread = threading.Thread(target=self.process_nips, args=(output_dir, timeout))
        thread.daemon = True
        thread.start()
        
    def stop_processing(self):
        """Zatrzymuje przetwarzanie"""
        self.is_processing = False
        self.log_message("Zatrzymywanie przetwarzania...")
        
    def process_nips(self, output_dir: str, timeout: int):
        """Przetwarza NIP-y w osobnym wątku"""
        total_nips = len(self.nip_list)
        processed = 0
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for i, nip in enumerate(self.nip_list):
                if not self.is_processing:
                    break
                    
                # Aktualizuj status w GUI
                self.queue.put(('update_status', nip, "Przetwarzanie..."))
                
                try:
                    # Pobierz dane z CRBR
                    self.queue.put(('log', f"Pobieranie danych dla NIP: {nip}"))
                    soap_xml = fetch_xml_by_nip(nip, timeout=timeout)
                    inner_xml = extract_inner_xml_from_soap(soap_xml)
                    
                    # Wygeneruj PDF
                    pdf_path = generate_pdf_from_xml_bytes(inner_xml, output_dir, default_nip=nip)
                    
                    # Aktualizuj status
                    self.queue.put(('update_status', nip, "Gotowe", os.path.basename(pdf_path)))
                    self.queue.put(('log', f"Wygenerowano PDF: {os.path.basename(pdf_path)}"))
                    
                except Exception as e:
                    error_msg = str(e)
                    self.queue.put(('update_status', nip, "Błąd", ""))
                    self.queue.put(('log', f"Błąd dla NIP {nip}: {error_msg}"))
                    
                processed += 1
                progress = (processed / total_nips) * 100
                self.queue.put(('update_progress', progress))
                
                # Krótka pauza między zapytaniami
                if self.is_processing and i < total_nips - 1:
                    time.sleep(0.5)
                    
        except Exception as e:
            self.queue.put(('log', f"Błąd ogólny: {str(e)}"))
            
        finally:
            self.queue.put(('processing_complete',))
            
    def update_status(self, nip: str, status: str, file: str = ""):
        """Aktualizuje status NIP-u w liście"""
        for item in self.nip_tree.get_children():
            values = self.nip_tree.item(item)['values']
            if values[0] == nip:
                self.nip_tree.item(item, values=(nip, status, file))
                break
                
    def update_progress(self, value: float):
        """Aktualizuje pasek postępu"""
        self.progress_var.set(value)
        
    def check_queue(self):
        """Sprawdza kolejkę komunikatów z wątku"""
        try:
            while True:
                message = self.queue.get_nowait()
                msg_type = message[0]
                
                if msg_type == 'log':
                    self.log_message(message[1])
                elif msg_type == 'update_status':
                    self.update_status(message[1], message[2], message[3] if len(message) > 3 else "")
                elif msg_type == 'update_progress':
                    self.update_progress(message[1])
                elif msg_type == 'processing_complete':
                    self.is_processing = False
                    self.process_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    self.log_message("Przetwarzanie zakończone")
                    
        except queue.Empty:
            pass
            
        # Sprawdź ponownie za 100ms
        self.root.after(100, self.check_queue)

def main():
    """Główna funkcja aplikacji"""
    # Ustawienia UTF-8
    from utf8_config import setup_utf8
    setup_utf8()
    
    root = tk.Tk()
    
    # Styl
    style = ttk.Style()
    style.theme_use('clam')
    
    # Ustawienia stylu
    style.configure("Accent.TButton", foreground="white", background="#0078d4")
    
    app = CRBRGUI(root)
    
    # Obsługa zamknięcia aplikacji
    def on_closing():
        if app.is_processing:
            if messagebox.askokcancel("Zamknij", "Przetwarzanie w toku. Czy na pewno chcesz zamknąć aplikację?"):
                app.is_processing = False
                root.destroy()
        else:
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    main()
