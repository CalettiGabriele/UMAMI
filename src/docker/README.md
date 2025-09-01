# UMAMI Docker Configuration

Configurazione Docker completa per il sistema UMAMI con separazione backend/frontend, inizializzazione automatica del database e supporto per sviluppo e produzione.

## Struttura

```
src/docker/
├── Dockerfile.backend          # Multi-stage backend (FastAPI)
├── Dockerfile.frontend         # Multi-stage frontend (Gradio)
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── nginx.conf                  # Nginx reverse proxy config
├── init-db.sh                 # Script inizializzazione database automatica
├── .dockerignore              # Ottimizzazione build
└── README.md                  # Questa documentazione
```
## 🗄️ Gestione Automatica Database

Il sistema UMAMI include l'**inizializzazione automatica del database** tramite lo script `init-db.sh`:

### ✅ Comportamento Automatico

- **Al primo avvio**: Se il database non esiste, viene creato automaticamente con tutte le tabelle vuote
- **Avvii successivi**: Se il database esiste già, viene utilizzato senza modifiche
- **Database corrotto**: Se il database è presente ma corrotto, viene ricreato automaticamente

### 📋 Processo di Inizializzazione

1. **Controllo esistenza**: Verifica se `/app/data/umami.db` esiste
2. **Validazione database**: Se esiste, controlla che sia valido e contenga tabelle
3. **Creazione automatica**: Se mancante o corrotto, esegue `db_build.py` per creare il database
4. **Avvio servizio**: Procede con l'avvio del backend FastAPI

### 🔍 Log di Inizializzazione

Durante l'avvio del container backend, vedrai i log dell'inizializzazione:

```bash
=== UMAMI Database Initialization ===
Database path: /app/data/umami.db
⚠ Database non presente, inizializzazione in corso...
🔨 Creazione database in corso...
✓ Database inizializzato con successo!
✓ Tabelle create: 12
  - Associati
  - Fornitori
  - ServiziFisici
  - [...]
✓ Inizializzazione database completata
```

## 🚀 Quick Start

### 1. Prerequisiti

Assicurati di avere installato:
- **Docker** (versione 20.10+)
- **Docker Compose** (versione 2.0+)

```bash
# Verifica installazione
docker --version
docker compose version
```

### 2. Avvio Completo

```bash
# Naviga nella directory docker
cd /path/to/UMAMI/src/docker/

# Avvia tutti i servizi (prima volta con build)
docker compose up --build

# Oppure in background (modalità detached)
docker compose up --build -d
```

### 3. Verifica Stato Container

```bash
# Controlla lo stato dei container
docker compose ps

# Output atteso:
# NAME             STATUS                    PORTS
# umami-backend    Up (healthy)              0.0.0.0:8003->8003/tcp
# umami-frontend   Up                        0.0.0.0:7860->7860/tcp
```

## 🌐 Accesso ai Servizi

### 📍 Accesso Locale (dalla stessa macchina)

- **🖥️ Frontend UMAMI**: http://localhost:7860
- **⚙️ Backend API**: http://localhost:8003
- **📚 Documentazione API**: http://localhost:8003/docs
- **📖 ReDoc API**: http://localhost:8003/redoc
- **💚 Health Check**: http://localhost:8003/health

### 🌍 Accesso da Rete Locale (altre macchine)

I servizi sono configurati per essere **accessibili da qualsiasi dispositivo sulla stessa rete**:

```bash
# Trova l'IP della macchina host
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1
# Esempio output: 192.168.1.100
```

**Da qualsiasi dispositivo sulla rete:**
- **🖥️ Frontend UMAMI**: http://192.168.1.100:7860
- **⚙️ Backend API**: http://192.168.1.100:8003
- **📚 Documentazione API**: http://192.168.1.100:8003/docs

### 📱 Dispositivi Supportati

L'interfaccia è **responsive** e funziona su:
- 💻 Desktop (Windows, Mac, Linux)
- 📱 Smartphone (iOS, Android)
- 📟 Tablet (iPad, Android)

## 🔧 Gestione Container

### Comandi Base

```bash
# Visualizza i log in tempo reale
docker compose logs -f

# Log specifici per servizio
docker compose logs -f backend
docker compose logs -f frontend

# Ferma i servizi
docker compose down

# Riavvia i servizi
docker compose restart

# Ricostruisci e riavvia
docker compose up --build -d
```

### Gestione Database

```bash
# Backup del database (il volume persiste automaticamente)
docker compose exec backend ls -la /app/data/

# Ferma SENZA perdere dati
docker compose down

# Ferma e CANCELLA tutti i dati (ATTENZIONE!)
docker compose down -v
```

### Debug e Troubleshooting

```bash
# Accedi al container backend
docker compose exec backend bash

# Accedi al container frontend  
docker compose exec frontend bash

# Verifica health check
docker compose exec backend curl http://localhost:8003/health

# Ricostruisci solo un servizio
docker compose build backend
docker compose up -d backend
```

## 📊 Monitoraggio

### Health Checks

Il backend include health check automatici:
- **Intervallo**: 30 secondi
- **Timeout**: 10 secondi
- **Retry**: 3 tentativi

```bash
# Verifica stato health check
docker compose ps
# Cerca "healthy" nella colonna STATUS
```

### Log Monitoring

```bash
# Tutti i log con timestamp
docker compose logs -f -t

# Solo errori
docker compose logs -f | grep -i error

# Log delle ultime 50 righe
docker compose logs --tail=50
```

## 🔒 Sicurezza e Rete

### Configurazione Rete

- **Backend**: Ascolta su `0.0.0.0:8003` (tutte le interfacce)
- **Frontend**: Ascolta su `0.0.0.0:7860` (tutte le interfacce)
- **Database**: Volume Docker persistente e sicuro

### Firewall

Assicurati che le porte siano aperte:
```bash
# Su macOS
sudo pfctl -f /etc/pf.conf

# Su Linux (ufw)
sudo ufw allow 7860
sudo ufw allow 8003
```

### Accesso Esterno

Per accesso da internet (NON raccomandato per produzione):
```bash
# Usa la configurazione produzione con nginx
docker compose -f docker-compose.prod.yml up --build -d
```

## 🗄️ Gestione Database Avanzata

Per operazioni avanzate sul database, utilizza lo script `manage-db.sh`:

### 📋 Comandi Disponibili

```bash
# Mostra stato database e statistiche
./manage-db.sh status

# Ricrea database da zero (ATTENZIONE: cancella tutti i dati)
./manage-db.sh reset

# Crea backup del database
./manage-db.sh backup

# Ripristina database da backup
./manage-db.sh restore

# Mostra log di inizializzazione
./manage-db.sh logs

# Apre shell nel container backend
./manage-db.sh shell
```

### 💾 Backup e Ripristino

```bash
# Backup automatico con timestamp
./manage-db.sh backup
# Crea: ./backups/umami_backup_20240901_1110.db

# Ripristino da backup
./manage-db.sh restore
# Mostra lista backup disponibili e permette selezione
```

### 🔄 Reset Database

```bash
# Reset completo (richiede conferma)
./manage-db.sh reset
# ⚠️ ATTENZIONE: Cancella tutti i dati esistenti!
```

## 🛠️ Sviluppo

### Modalità Development

```bash
# Avvia con reload automatico
docker compose up --build

# I container sono configurati per:
# - Backend: auto-reload su cambio codice
# - Frontend: riavvio automatico
# - Volume bind per sviluppo live
```

### Personalizzazione

Modifica `docker-compose.yml` per:
- Cambiare porte esposte
- Aggiungere variabili d'ambiente
- Configurare volumi aggiuntivi
- Personalizzare network settings

## ❓ Troubleshooting

### Problemi Comuni

**Container non si avvia:**
```bash
# Controlla i log
docker compose logs backend
docker compose logs frontend

# Verifica porte libere
lsof -i :8003
lsof -i :7860
```

**Database non trovato:**
```bash
# Verifica volume
docker volume ls | grep umami
docker volume inspect docker_umami_data
```

**Accesso rete non funziona:**
```bash
# Verifica binding porte
docker compose ps
# Deve mostrare 0.0.0.0:porta->porta/tcp

# Testa connettività
curl http://localhost:8003/health
```

### Reset Completo

```bash
# Ferma tutto e cancella dati
docker compose down -v

# Rimuovi immagini
docker rmi docker-backend docker-frontend

# Riavvia da zero
docker compose up --build -d
```

## 📈 Produzione

Per deployment in produzione, usa:
```bash
# Configurazione produzione con nginx
docker compose -f docker-compose.prod.yml up --build -d

# Include:
# - Nginx reverse proxy
# - SSL/TLS termination
# - Rate limiting
# - Security headers
```

---

## 🎯 Riepilogo Comandi Essenziali

```bash
# 1. Prima volta - Avvia tutto
cd src/docker/
docker compose up --build -d

# 2. Verifica stato
docker compose ps

# 3. Accedi all'app
# Locale: http://localhost:7860
# Rete: http://[IP-MACCHINA]:7860

# 4. Ferma tutto
docker compose down

# 5. Riavvia
docker compose up -d
```

🎉 **Il sistema UMAMI è ora accessibile da tutta la rete locale!**
docker-compose build frontend
```

## Build Singoli Container

### Backend

```bash
# Dalla directory root del progetto
docker build -f src/docker/Dockerfile.backend -t umami-backend .

# Esegui il container
docker run -p 8003:8003 -v umami_data:/app/data umami-backend
```

### Frontend

```bash
# Dalla directory root del progetto
docker build -f src/docker/Dockerfile.frontend -t umami-frontend .

# Esegui il container (assicurati che il backend sia in esecuzione)
docker run -p 7860:7860 -e BACKEND_URL=http://localhost:8003 umami-frontend
```

## Persistenza Dati

Il database SQLite viene salvato in un volume Docker chiamato `umami_data` che persiste tra i riavvii dei container.

### Backup del Database

```bash
# Copia il database dal volume
docker run --rm -v umami_data:/data -v $(pwd):/backup alpine cp /data/umami.db /backup/umami_backup.db
```

### Ripristino del Database

```bash
# Ripristina il database nel volume
docker run --rm -v umami_data:/data -v $(pwd):/backup alpine cp /backup/umami_backup.db /data/umami.db
```

## Configurazione

### Variabili d'Ambiente

**Backend:**
- `DATABASE_PATH`: Percorso del database SQLite (default: `/app/data/umami.db`)
- `PYTHONPATH`: Path Python (default: `/app`)

**Frontend:**
- `BACKEND_URL`: URL del backend (default: `http://backend:8003`)
- `PYTHONPATH`: Path Python (default: `/app`)

### Personalizzazione Porte

Per cambiare le porte, modifica il file `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8003"  # Cambia la porta esterna
  frontend:
    ports:
      - "8000:7860"  # Cambia la porta esterna
```

## Troubleshooting

### Container non si avvia

```bash
# Controlla i log per errori
docker-compose logs backend
docker-compose logs frontend

# Verifica lo stato dei container
docker-compose ps
```

### Problemi di connessione Frontend → Backend

1. Verifica che il backend sia in esecuzione: `curl http://localhost:8003/health`
2. Controlla la variabile `BACKEND_URL` nel frontend
3. Assicurati che i container siano nella stessa rete Docker

### Reset Completo

```bash
# Ferma tutto e rimuovi volumi
docker-compose down -v

# Rimuovi le immagini
docker rmi umami-backend umami-frontend

# Ricostruisci tutto
docker-compose up --build
```

## Sviluppo

Per lo sviluppo, puoi montare il codice sorgente come volume per vedere le modifiche in tempo reale:

```yaml
# Aggiungi al docker-compose.yml
volumes:
  - ../../src/backend:/app/src/backend
  - ../../src/frontend:/app/src/frontend
```

## Produzione

Per l'ambiente di produzione:

1. Rimuovi `--reload` dal comando uvicorn nel Dockerfile.backend
2. Usa immagini multi-stage per ridurre le dimensioni
3. Configura un reverse proxy (nginx) davanti ai container
4. Usa variabili d'ambiente per le configurazioni sensibili
5. Implementa backup automatici del database
