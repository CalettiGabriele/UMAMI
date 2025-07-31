#!/usr/bin/env python3
"""
Database Builder per UMAMI - Sistema Gestionale ASD
Questo script crea il database SQLite basato sulla configurazione JSON
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime


class DatabaseBuilder:
    """Classe per la costruzione del database UMAMI"""
    
    def __init__(self, config_file="database_schema.json", data_dir="data"):
        """
        Inizializza il builder del database
        
        Args:
            config_file (str): Path al file di configurazione JSON
            data_dir (str): Directory dove creare il database
        """
        self.script_dir = Path(__file__).parent
        self.config_file = self.script_dir / config_file
        self.data_dir = self.script_dir / data_dir
        self.config = None
        self.db_path = None
        
    def load_config(self):
        """Carica la configurazione dal file JSON"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✓ Configurazione caricata da: {self.config_file}")
            return True
        except FileNotFoundError:
            print(f"✗ Errore: File di configurazione non trovato: {self.config_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"✗ Errore nel parsing JSON: {e}")
            return False
    
    def create_data_directory(self):
        """Crea la directory data se non esiste"""
        self.data_dir.mkdir(exist_ok=True)
        print(f"✓ Directory data verificata: {self.data_dir}")
    
    def build_create_table_sql(self, table_name, table_config):
        """
        Costruisce l'SQL per la creazione di una tabella
        
        Args:
            table_name (str): Nome della tabella
            table_config (dict): Configurazione della tabella
            
        Returns:
            str: Statement SQL CREATE TABLE
        """
        columns = []
        
        for column_name, column_config in table_config['columns'].items():
            column_def = f"{column_name} {column_config['type']}"
            
            # Aggiungi constraints se presenti
            if 'constraints' in column_config:
                for constraint in column_config['constraints']:
                    column_def += f" {constraint}"
            
            # Aggiungi default se presente
            if 'default' in column_config:
                column_def += f" DEFAULT {column_config['default']}"
            
            # Aggiungi NOT NULL se non è nullable (default è NOT NULL)
            if column_config.get('nullable', False) is False and 'NOT NULL' not in column_def:
                if 'PRIMARY KEY' not in column_def:  # PRIMARY KEY implica NOT NULL
                    column_def += " NOT NULL"
            
            columns.append(column_def)
        
        sql = f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(f"    {col}" for col in columns)
        sql += "\n);"
        
        return sql
    
    def create_database(self):
        """Crea il database e tutte le tabelle"""
        if not self.config:
            print("✗ Errore: Configurazione non caricata")
            return False
        
        # Determina il path del database
        db_name = self.config.get('database_name', 'umami.db')
        self.db_path = self.data_dir / db_name
        
        # Backup del database esistente se presente
        if self.db_path.exists():
            backup_path = self.data_dir / f"{db_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(self.db_path, backup_path)
            print(f"✓ Database esistente salvato come backup: {backup_path}")
        
        try:
            # Connessione al database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Abilita le foreign keys
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            print(f"✓ Database creato: {self.db_path}")
            
            # Ordine di creazione delle tabelle per rispettare le foreign keys
            table_order = [
                'Associati',
                'ChiaviElettroniche', 
                'TessereFIV',
                'Fornitori',
                'ServiziFisici',
                'PrezziServizi',
                'Prestazioni',
                'AssegnazioniServiziFisici',
                'ErogazioniPrestazioni',
                'Fatture',
                'DettagliFatture',
                'Pagamenti'
            ]
            
            # Crea le tabelle nell'ordine corretto
            for table_name in table_order:
                if table_name in self.config['tables']:
                    table_config = self.config['tables'][table_name]
                    sql = self.build_create_table_sql(table_name, table_config)
                    
                    print(f"Creando tabella: {table_name}")
                    print(f"SQL: {sql}\n")
                    
                    cursor.execute(sql)
                    print(f"✓ Tabella {table_name} creata con successo")
                else:
                    print(f"⚠ Tabella {table_name} non trovata nella configurazione")
            
            # Commit delle modifiche
            conn.commit()
            
            # Verifica delle tabelle create
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"\n✓ Database creato con successo!")
            print(f"✓ Tabelle create: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Chiudi la connessione
            conn.close()
            
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Errore SQLite: {e}")
            return False
        except Exception as e:
            print(f"✗ Errore generico: {e}")
            return False
    
    def verify_database(self):
        """Verifica l'integrità del database creato"""
        if not self.db_path or not self.db_path.exists():
            print("✗ Database non trovato per la verifica")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print("\n=== VERIFICA DATABASE ===")
            
            # Verifica foreign keys
            cursor.execute("PRAGMA foreign_key_check;")
            fk_errors = cursor.fetchall()
            
            if fk_errors:
                print("✗ Errori nelle foreign keys:")
                for error in fk_errors:
                    print(f"  {error}")
                return False
            else:
                print("✓ Foreign keys verificate correttamente")
            
            # Verifica struttura tabelle
            for table_name in self.config['tables'].keys():
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                
                if columns:
                    print(f"✓ Tabella {table_name}: {len(columns)} colonne")
                else:
                    print(f"✗ Tabella {table_name} non trovata o vuota")
                    return False
            
            conn.close()
            print("✓ Verifica database completata con successo")
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Errore durante la verifica: {e}")
            return False
    
    def print_summary(self):
        """Stampa un riassunto delle operazioni"""
        print("\n" + "="*50)
        print("RIEPILOGO CREAZIONE DATABASE UMAMI")
        print("="*50)
        print(f"Database: {self.db_path}")
        print(f"Configurazione: {self.config_file}")
        
        if self.config:
            print(f"Tabelle configurate: {len(self.config['tables'])}")
            for table_name, table_config in self.config['tables'].items():
                columns_count = len(table_config['columns'])
                description = table_config.get('description', 'Nessuna descrizione')
                print(f"  - {table_name}: {columns_count} colonne - {description}")
        
        print("\nPer utilizzare il database:")
        print(f"  sqlite3 {self.db_path}")
        print("\nPer visualizzare le tabelle:")
        print("  .tables")
        print("\nPer visualizzare la struttura di una tabella:")
        print("  .schema nome_tabella")


def main():
    """Funzione principale"""
    print("UMAMI Database Builder")
    print("=====================")
    print(f"Avvio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Inizializza il builder
    builder = DatabaseBuilder()
    
    # Carica la configurazione
    if not builder.load_config():
        sys.exit(1)
    
    # Crea la directory data
    builder.create_data_directory()
    
    # Crea il database
    if not builder.create_database():
        print("✗ Creazione database fallita")
        sys.exit(1)
    
    # Verifica il database
    if not builder.verify_database():
        print("✗ Verifica database fallita")
        sys.exit(1)
    
    # Stampa il riassunto
    builder.print_summary()
    
    print(f"\n✓ Operazione completata con successo alle {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
