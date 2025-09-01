#!/bin/bash
"""
Script di inizializzazione database per container Docker UMAMI
Esegue l'inizializzazione del database solo se non è già presente
"""

set -e

# Configurazione paths
DATABASE_PATH="${DATABASE_PATH:-/app/data/umami.db}"
DATABASE_DIR=$(dirname "$DATABASE_PATH")
SCHEMA_PATH="/app/src/database/database_schema.json"
BUILD_SCRIPT="/app/src/database/db_build.py"

echo "=== UMAMI Database Initialization ==="
echo "Database path: $DATABASE_PATH"
echo "Database directory: $DATABASE_DIR"

# Crea la directory del database se non esiste
mkdir -p "$DATABASE_DIR"

# Controlla se il database esiste già
if [ -f "$DATABASE_PATH" ]; then
    echo "✓ Database già presente: $DATABASE_PATH"
    echo "✓ Saltando inizializzazione database"
    
    # Verifica che il database sia valido
    if python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DATABASE_PATH')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
    tables = cursor.fetchall()
    conn.close()
    if len(tables) > 0:
        print('✓ Database valido con {} tabelle'.format(len(tables)))
        exit(0)
    else:
        print('⚠ Database vuoto, richiede inizializzazione')
        exit(1)
except Exception as e:
    print('✗ Database corrotto:', e)
    exit(1)
"; then
        echo "✓ Database verificato e funzionante"
    else
        echo "⚠ Database presente ma non valido, rimuovo e ricreo..."
        rm -f "$DATABASE_PATH"
    fi
fi

# Se arriviamo qui, il database non esiste o è corrotto
if [ ! -f "$DATABASE_PATH" ]; then
    echo "⚠ Database non presente, inizializzazione in corso..."
    
    # Verifica che i file necessari esistano
    if [ ! -f "$SCHEMA_PATH" ]; then
        echo "✗ Errore: Schema database non trovato: $SCHEMA_PATH"
        exit 1
    fi
    
    if [ ! -f "$BUILD_SCRIPT" ]; then
        echo "✗ Errore: Script build database non trovato: $BUILD_SCRIPT"
        exit 1
    fi
    
    # Esegue la creazione del database
    echo "🔨 Creazione database in corso..."
    cd /app/src/database
    
    # Modifica temporaneamente il db_build.py per usare il percorso corretto
    if python3 -c "
import sys
sys.path.append('/app/src/database')
from db_build import DatabaseBuilder
import os

# Usa il percorso del database dalla variabile d'ambiente
db_path = os.environ.get('DATABASE_PATH', '/app/data/umami.db')
data_dir = os.path.dirname(db_path)
db_name = os.path.basename(db_path)

print(f'Creazione database: {db_path}')

# Crea il builder con il percorso corretto
builder = DatabaseBuilder(config_file='database_schema.json', data_dir=data_dir)
builder.db_path = db_path

# Carica configurazione e crea database
if builder.load_config():
    os.makedirs(data_dir, exist_ok=True)
    if builder.create_database():
        if builder.verify_database():
            print('✓ Database creato e verificato con successo')
            exit(0)
        else:
            print('✗ Errore nella verifica del database')
            exit(1)
    else:
        print('✗ Errore nella creazione del database')
        exit(1)
else:
    print('✗ Errore nel caricamento della configurazione')
    exit(1)
"; then
        echo "✓ Database inizializzato con successo!"
        
        # Verifica finale
        if [ -f "$DATABASE_PATH" ]; then
            echo "✓ Database creato: $DATABASE_PATH"
            
            # Mostra statistiche database
            python3 -c "
import sqlite3
conn = sqlite3.connect('$DATABASE_PATH')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
tables = cursor.fetchall()
print('✓ Tabelle create: {}'.format(len(tables)))
for table in tables:
    print('  - {}'.format(table[0]))
conn.close()
"
        else
            echo "✗ Errore: Database non creato correttamente"
            exit 1
        fi
    else
        echo "✗ Errore durante la creazione del database"
        exit 1
    fi
fi

echo "✓ Inizializzazione database completata"
echo "=================================="
