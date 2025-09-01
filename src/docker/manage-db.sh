#!/bin/bash
"""
Script di gestione database per UMAMI Docker
Permette operazioni manuali sul database del container
"""

set -e

CONTAINER_NAME="umami-backend"
DATABASE_PATH="/app/data/umami.db"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_usage() {
    echo "Gestione Database UMAMI Docker"
    echo ""
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandi disponibili:"
    echo "  status     - Mostra stato database e container"
    echo "  reset      - Ricrea il database da zero (ATTENZIONE: cancella tutti i dati)"
    echo "  backup     - Crea backup del database"
    echo "  restore    - Ripristina database da backup"
    echo "  logs       - Mostra log di inizializzazione database"
    echo "  shell      - Apre shell nel container backend"
    echo ""
    echo "Esempi:"
    echo "  $0 status"
    echo "  $0 reset"
    echo "  $0 backup"
}

check_container() {
    if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}✗ Container ${CONTAINER_NAME} non in esecuzione${NC}"
        echo "Avvia il sistema con: docker compose up -d"
        exit 1
    fi
    echo -e "${GREEN}✓ Container ${CONTAINER_NAME} attivo${NC}"
}

show_status() {
    echo -e "${BLUE}=== STATO DATABASE UMAMI ===${NC}"
    
    check_container
    
    # Verifica esistenza database
    if docker exec $CONTAINER_NAME test -f $DATABASE_PATH; then
        echo -e "${GREEN}✓ Database presente: ${DATABASE_PATH}${NC}"
        
        # Mostra statistiche database
        docker exec $CONTAINER_NAME python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DATABASE_PATH')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\";')
    tables = cursor.fetchall()
    print('✓ Tabelle: {}'.format(len(tables)))
    for table in tables:
        cursor.execute('SELECT COUNT(*) FROM {}'.format(table[0]))
        count = cursor.fetchone()[0]
        print('  - {}: {} record'.format(table[0], count))
    conn.close()
except Exception as e:
    print('✗ Errore database:', e)
"
    else
        echo -e "${YELLOW}⚠ Database non presente${NC}"
    fi
    
    # Mostra info container
    echo ""
    echo -e "${BLUE}=== INFO CONTAINER ===${NC}"
    docker exec $CONTAINER_NAME df -h /app/data
}

reset_database() {
    echo -e "${YELLOW}⚠ ATTENZIONE: Questa operazione cancellerà TUTTI i dati del database!${NC}"
    read -p "Sei sicuro di voler continuare? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Operazione annullata"
        exit 0
    fi
    
    check_container
    
    echo -e "${BLUE}🔨 Ricreazione database in corso...${NC}"
    
    # Rimuovi database esistente
    docker exec $CONTAINER_NAME rm -f $DATABASE_PATH
    
    # Esegui script di inizializzazione
    docker exec $CONTAINER_NAME ./init-db.sh
    
    echo -e "${GREEN}✓ Database ricreato con successo${NC}"
}

backup_database() {
    check_container
    
    if ! docker exec $CONTAINER_NAME test -f $DATABASE_PATH; then
        echo -e "${RED}✗ Database non presente, impossibile fare backup${NC}"
        exit 1
    fi
    
    BACKUP_NAME="umami_backup_$(date +%Y%m%d_%H%M%S).db"
    BACKUP_PATH="./backups/$BACKUP_NAME"
    
    mkdir -p ./backups
    
    echo -e "${BLUE}💾 Creazione backup: ${BACKUP_NAME}${NC}"
    docker cp $CONTAINER_NAME:$DATABASE_PATH $BACKUP_PATH
    
    echo -e "${GREEN}✓ Backup creato: ${BACKUP_PATH}${NC}"
    ls -lh $BACKUP_PATH
}

restore_database() {
    echo "Backup disponibili:"
    if [ -d "./backups" ]; then
        ls -la ./backups/*.db 2>/dev/null || echo "Nessun backup trovato"
    else
        echo "Directory backups non trovata"
        exit 1
    fi
    
    read -p "Inserisci il nome del file di backup: " backup_file
    
    if [ ! -f "./backups/$backup_file" ]; then
        echo -e "${RED}✗ File backup non trovato: ./backups/$backup_file${NC}"
        exit 1
    fi
    
    check_container
    
    echo -e "${YELLOW}⚠ ATTENZIONE: Questa operazione sostituirà il database corrente!${NC}"
    read -p "Continuare? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Operazione annullata"
        exit 0
    fi
    
    echo -e "${BLUE}📥 Ripristino backup: ${backup_file}${NC}"
    docker cp "./backups/$backup_file" $CONTAINER_NAME:$DATABASE_PATH
    
    echo -e "${GREEN}✓ Database ripristinato con successo${NC}"
}

show_logs() {
    check_container
    echo -e "${BLUE}=== LOG INIZIALIZZAZIONE DATABASE ===${NC}"
    docker logs $CONTAINER_NAME 2>&1 | grep -A 20 -B 5 "UMAMI Database Initialization" || echo "Nessun log di inizializzazione trovato"
}

open_shell() {
    check_container
    echo -e "${BLUE}🐚 Apertura shell nel container ${CONTAINER_NAME}${NC}"
    docker exec -it $CONTAINER_NAME /bin/bash
}

# Main
case "${1:-}" in
    status)
        show_status
        ;;
    reset)
        reset_database
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
