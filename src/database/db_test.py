#!/usr/bin/env python3
"""
Script di Popolamento Database per UMAMI

Questo script inserisce dati di test nel database SQLite, coprendo diverse casistiche:
- Gruppi familiari e soci singoli
- Tesseramenti FIV e certificati medici
- Servizi fisici e prestazionali
- Cicli di fatturazione attiva e passiva
- Pagamenti e stati delle fatture
"""

import sqlite3
import sys
from pathlib import Path
from datetime import date, timedelta, datetime

class DatabasePopulator:
    """Popola il database UMAMI con dati di test."""

    def __init__(self, db_name="umami.db"):
        self.script_dir = Path(__file__).parent
        self.db_path = self.script_dir / "data" / db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Stabilisce la connessione al database."""
        if not self.db_path.exists():
            print(f"â— Errore: Database non trovato in {self.db_path}")
            print("Eseguire prima lo script db_build.py per creare il database.")
            return False
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            print(f"âœ“ Connessione al database {self.db_path} stabilita.")
            return True
        except sqlite3.Error as e:
            print(f"â— Errore di connessione SQLite: {e}")
            return False

    def clear_data(self):
        """Pulisce tutti i dati dalle tabelle per un nuovo inserimento."""
        print("\nPulizia dati esistenti...")
        tables = [
            'Pagamenti', 'DettagliFatture', 'Fatture', 'ErogazioniPrestazioni',
            'AssegnazioniServiziFisici', 'PrezziServizi', 'Prestazioni',
            'ServiziFisici', 'Fornitori', 'TessereFIV', 
            'ChiaviElettroniche', 'Associati'
        ]
        try:
            for table in tables:
                self.cursor.execute(f"DELETE FROM {table};")
                self.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
            self.conn.commit()
            print("âœ“ Dati esistenti rimossi con successo.")
        except sqlite3.Error as e:
            print(f"â— Errore durante la pulizia dei dati: {e}")
            self.conn.rollback()

    def populate_associati(self):
        """Popola la tabella Associati."""
        print("\nPopolamento tabella: Associati")
        associati = [
            # Famiglia Rossi (Pagante: Mario)
            (1, None, 'Mario', 'Rossi', 'RSSMRA80A01H501A', '1980-01-01', 'Via Roma 1, Milano', 'mario.rossi@email.com', '3331112233', '2022-01-15', 'Attivo'),
            (2, 1, 'Anna', 'Rossi', 'RSSNNA82C41H501B', '1982-03-01', 'Via Roma 1, Milano', 'anna.rossi@email.com', '3334445566', '2022-01-15', 'Attivo'),
            (3, 1, 'Luca', 'Rossi', 'RSSLCU10A01H501C', '2010-01-01', 'Via Roma 1, Milano', 'luca.rossi@email.com', '3337778899', '2022-01-15', 'Attivo'),
            # Socio singolo
            (4, None, 'Giuseppe', 'Verdi', 'VRDGPP75B02F205Z', '1975-02-02', 'Via Garibaldi 10, Torino', 'giuseppe.verdi@email.com', '3471234567', '2021-05-20', 'Attivo'),
            # Socio sospeso
            (5, None, 'Laura', 'Bianchi', 'BNCLRA90D45L219X', '1990-04-05', 'Corso Vittorio 5, Roma', 'laura.bianchi@email.com', '3289876543', '2023-02-10', 'Sospeso'),
            # Socio scaduto
            (6, None, 'Paolo', 'Neri', 'NRAPLA88E06A944Y', '1988-05-06', 'Piazza Duomo 3, Firenze', 'paolo.neri@email.com', '3391122334', '2020-09-01', 'Scaduto'),
        ]
        try:
            self.cursor.executemany("INSERT INTO Associati VALUES (?,?,?,?,?,?,?,?,?,?,?)", associati)
            print(f"âœ“ {len(associati)} record inseriti in Associati.")
        except sqlite3.Error as e:
            print(f"â— Errore in Associati: {e}")

    def populate_tessere_fiv(self):
        """Popola TessereFIV."""
        print("\nPopolamento tabella: TessereFIV")
        dati_fiv = [
            # Mario Rossi - certificato valido
            (1, 'FIV12345', (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'), (date.today() + timedelta(days=180)).strftime('%Y-%m-%d')),
            # Luca Rossi - certificato in scadenza
            (3, 'FIV67890', (date.today() + timedelta(days=300)).strftime('%Y-%m-%d'), (date.today() + timedelta(days=25)).strftime('%Y-%m-%d')),
            # Giuseppe Verdi - certificato scaduto
            (4, 'FIV54321', (date.today() + timedelta(days=200)).strftime('%Y-%m-%d'), (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')),
        ]
        try:
            self.cursor.executemany("INSERT INTO TessereFIV VALUES (?,?,?,?)", dati_fiv)
            print(f"âœ“ {len(dati_fiv)} record inseriti in TessereFIV.")
        except sqlite3.Error as e:
            print(f"â— Errore in TessereFIV: {e}")

    def populate_chiavi_elettroniche(self):
        """Popola ChiaviElettroniche."""
        print("\nPopolamento tabella: ChiaviElettroniche")
        chiavi = [
            (1, 'KEY001', True, 15.50),  # Mario Rossi
            (3, 'KEY003', True, 8.00),   # Luca Rossi
            (4, 'KEY004', False, 0.00),  # Giuseppe Verdi - non in regola
        ]
        try:
            self.cursor.executemany("INSERT INTO ChiaviElettroniche VALUES (?,?,?,?)", chiavi)
            print(f"✓ {len(chiavi)} record inseriti in ChiaviElettroniche.")
        except sqlite3.Error as e:
            print(f"✗ Errore in ChiaviElettroniche: {e}")

    def populate_fornitori(self):
        """Popola la tabella Fornitori."""
        print("\nPopolamento tabella: Fornitori")
        fornitori = [
            (1, 'Sail & Fun S.r.l.', '01234567890', 'info@sailfun.it', '010123456'),
            (2, 'Pulizie Veloci S.p.A.', '09876543210', 'amministrazione@pulizieveloci.it', '029876543'),
        ]
        try:
            self.cursor.executemany("INSERT INTO Fornitori VALUES (?,?,?,?,?)", fornitori)
            print(f"âœ“ {len(fornitori)} record inseriti in Fornitori.")
        except sqlite3.Error as e:
            print(f"â— Errore in Fornitori: {e}")

    def populate_servizi(self):
        """Popola ServiziFisici, PrezziServizi, Prestazioni."""
        print("\nPopolamento tabelle Servizi...")
        servizi_fisici = [
            (1, 'Posto Barca A-01', 'Posto barca fino a 8m', 'Posto Barca', 'Occupato'),
            (2, 'Posto Barca B-12', 'Posto barca fino a 12m', 'Posto Barca', 'Disponibile'),
            (3, 'Armadietto N-5', 'Armadietto spogliatoio maschile', 'Armadietto', 'Occupato'),
            (4, 'Armadietto F-8', 'Armadietto spogliatoio femminile', 'Armadietto', 'In Manutenzione'),
        ]
        prezzi_servizi = [
            (1, 2500.00),
            (2, 4000.00),
            (3, 150.00),
        ]
        prestazioni = [
            (1, 'Corso Vela Base', 'Corso di 5 lezioni su deriva', 350.00),
            (2, 'Regata Sociale Estiva', 'Iscrizione alla regata di club', 50.00),
            (3, 'Quota Tesseramento FIV', 'Tesseramento annuale alla Federazione Italiana Vela', 30.00),
        ]
        try:
            self.cursor.executemany("INSERT INTO ServiziFisici VALUES (?,?,?,?,?)", servizi_fisici)
            self.cursor.executemany("INSERT INTO PrezziServizi VALUES (?,?)", prezzi_servizi)
            self.cursor.executemany("INSERT INTO Prestazioni VALUES (?,?,?,?)", prestazioni)
            print(f"✓ {len(servizi_fisici)} ServiziFisici, {len(prezzi_servizi)} PrezziServizi, {len(prestazioni)} Prestazioni inseriti.")
        except sqlite3.Error as e:
            print(f"✗ Errore nelle tabelle Servizi: {e}")

    def populate_assegnazioni_e_erogazioni(self):
        """Popola AssegnazioniServiziFisici e ErogazioniPrestazioni."""
        print("\nPopolamento Assegnazioni e Erogazioni...")
        assegnazioni = [
            (1, 4, 1, 2024, '2024-01-01', '2024-12-31', 'Attivo'), # Verdi, Posto Barca A-01
            (2, 1, 3, 2024, '2024-01-01', '2024-12-31', 'Attivo'), # M. Rossi, Armadietto N-5
        ]
        erogazioni = [
            (1, 3, 1, datetime(2024, 6, 10, 14, 0).strftime('%Y-%m-%d %H:%M:%S')), # L. Rossi, Corso Vela
            (2, 1, 2, datetime(2024, 7, 20, 10, 0).strftime('%Y-%m-%d %H:%M:%S')), # M. Rossi, Regata
            (3, 3, 3, datetime(2024, 1, 20, 9, 0).strftime('%Y-%m-%d %H:%M:%S')),  # L. Rossi, Tesseramento FIV
        ]
        try:
            self.cursor.executemany("INSERT INTO AssegnazioniServiziFisici VALUES (?,?,?,?,?,?,?)", assegnazioni)
            self.cursor.executemany("INSERT INTO ErogazioniPrestazioni VALUES (?,?,?,?)", erogazioni)
            print(f"âœ“ {len(assegnazioni)} Assegnazioni e {len(erogazioni)} Erogazioni inserite.")
        except sqlite3.Error as e:
            print(f"â— Errore in Assegnazioni/Erogazioni: {e}")

    def populate_fatture_e_pagamenti(self):
        """Popola Fatture, DettagliFatture, Pagamenti."""
        print("\nPopolamento ciclo contabile...")
        fatture = [
            # Fattura ATTIVA a G. Verdi (pagata)
            (1, 'ATT-2024-001', '2024-01-10', '2024-02-10', 4, None, 'Attiva', 2500.00, 550.00, 3050.00, 'Pagata'),
            # Fattura ATTIVA a M. Rossi (famiglia, emessa)
            (2, 'ATT-2024-002', '2024-06-15', '2024-07-15', 1, None, 'Attiva', 580.00, 127.60, 707.60, 'Emessa'),
            # Fattura PASSIVA da Sail & Fun (scaduta)
            (3, 'PASS-2024-SF-10', '2024-03-01', '2024-03-31', None, 1, 'Passiva', 1200.00, 264.00, 1464.00, 'Scaduta'),
        ]
        dettagli = [
            # Dettagli per fattura 1 (Verdi)
            (1, 1, 'Canone annuale Posto Barca A-01', 1, 2500.00, 2500.00, 1, None),
            # Dettagli per fattura 2 (Rossi)
            (2, 2, 'Iscrizione Corso Vela Base - Luca Rossi', 1, 350.00, 350.00, None, 1),
            (3, 2, 'Iscrizione Regata Sociale Estiva - Mario Rossi', 1, 50.00, 50.00, None, 2),
            (4, 2, 'Canone annuale Armadietto N-5 - Mario Rossi', 1, 150.00, 150.00, 2, None),
            (5, 2, 'Quota Tesseramento FIV - Luca Rossi', 1, 30.00, 30.00, None, 3),
            # Dettagli per fattura 3 (Passiva)
            (6, 3, 'Fornitura materiale di consumo', 1, 1200.00, 1200.00, None, None),
        ]
        pagamenti = [
            # Pagamento per fattura 1 (Verdi)
            (1, '2024-02-05', 3050.00, 'Bonifico', 1, 'Entrata'),
        ]
        try:
            self.cursor.executemany("INSERT INTO Fatture VALUES (?,?,?,?,?,?,?,?,?,?,?)", fatture)
            self.cursor.executemany("INSERT INTO DettagliFatture VALUES (?,?,?,?,?,?,?,?)", dettagli)
            self.cursor.executemany("INSERT INTO Pagamenti VALUES (?,?,?,?,?,?)", pagamenti)
            print(f"âœ“ {len(fatture)} Fatture, {len(dettagli)} Dettagli, {len(pagamenti)} Pagamenti inseriti.")
        except sqlite3.Error as e:
            print(f"â— Errore nel ciclo contabile: {e}")

    def close(self):
        """Chiude la connessione al database."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print("\nâœ“ Connessione al database chiusa.")

    def run(self):
        """Esegue il processo di popolamento completo."""
        if not self.connect():
            return

        self.clear_data()
        self.populate_associati()
        self.populate_tessere_fiv()
        self.populate_chiavi_elettroniche()
        self.populate_fornitori()
        self.populate_servizi()
        self.populate_assegnazioni_e_erogazioni()
        self.populate_fatture_e_pagamenti()
        self.close()
        
        print("\n" + "="*50)
        print("POPOLAMENTO DATABASE COMPLETATO CON SUCCESSO")
        print("="*50)
        print(f"Database {self.db_path.name} ora contiene dati di test.")

def main():
    """Funzione principale."""
    populator = DatabasePopulator()
    populator.run()

if __name__ == "__main__":
    main()
