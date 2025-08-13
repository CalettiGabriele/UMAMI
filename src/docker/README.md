# Docker Setup per UMAMI

Questa cartella contiene i file Docker per eseguire il sistema UMAMI in container separati per backend e frontend.

## Struttura File

- `Dockerfile.backend`: Container per le API FastAPI (porta 8003)
- `Dockerfile.frontend`: Container per l'interfaccia Gradio (porta 7860)
- `docker-compose.yml`: Orchestrazione completa del sistema
- `.dockerignore`: File da escludere durante il build
- `README.md`: Questa documentazione

## Quick Start

### Avvio Completo con Docker Compose

```bash
# Dalla directory src/docker/
docker-compose up --build

# In background
docker-compose up -d --build
```

### Accesso ai Servizi

- **Backend API**: http://localhost:8003
  - Documentazione Swagger: http://localhost:8003/docs
  - ReDoc: http://localhost:8003/redoc
  - Health Check: http://localhost:8003/health

- **Frontend Interface**: http://localhost:7860

### Comandi Utili

```bash
# Visualizza i log
docker-compose logs -f

# Visualizza solo i log del backend
docker-compose logs -f backend

# Visualizza solo i log del frontend
docker-compose logs -f frontend

# Ferma i servizi
docker-compose down

# Ferma e rimuove i volumi (ATTENZIONE: cancella il database!)
docker-compose down -v

# Ricostruisci solo un servizio
docker-compose build backend
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
