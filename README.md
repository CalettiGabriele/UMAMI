# UMAMI - Sistema Gestionale ASD

**UMAMI** è un sistema completo per la gestione di Associazioni Sportive Dilettantistiche, sviluppato con tecnologie moderne e architettura modulare.

## 🚀 Caratteristiche Principali

- **Gestione Associati**: Anagrafica completa con supporto per nuclei familiari
- **Tesseramento FIV**: Integrazione con Federazione Italiana Vela
- **Servizi Fisici**: Gestione posti barca, armadietti, locali
- **Prestazioni**: Corsi, eventi, noleggi
- **Contabilità**: Fatturazione, pagamenti, report finanziari
- **Chiavi Elettroniche**: Sistema accessi e crediti docce
- **API REST**: Interfaccia completa per integrazioni

## 🏗️ Architettura del Sistema

```
UMAMI/
├── src/
│   ├── backend/          # API REST FastAPI
│   └── database/         # Database SQLite e script
├── doc/                  # Documentazione completa
└── README.md            # Questo file
```

## 📋 Prerequisiti

- **Python 3.8+**
- **uv** (gestore pacchetti Python) o **pip**
- **SQLite 3**

## ⚡ Quick Start

### 1. Setup del Database

```bash
# Crea e popola il database
cd src/database
uv run db_build.py
uv run db_test.py
```

### 2. Avvio API Server

```bash
# Installa dipendenze (dalla root del progetto)
uv sync

# Avvia server API
uv run uvicorn src.backend.fastapi_builder:app --reload --host 0.0.0.0 --port 8001
```

### 3. Accesso alla Documentazione API

- **API Swagger**: http://localhost:8001/docs
- **API ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

## 🗄️ Database

### Struttura

Il database SQLite è organizzato in **12 tabelle** suddivise in 3 aree:

#### 📋 Area Anagrafiche
- **Associati**: Soci con gestione legami familiari
- **ChiaviElettroniche**: Accessi e crediti docce
- **TessereFIV**: Tesseramento Federazione Italiana Vela
- **Fornitori**: Anagrafica fornitori

#### 🏢 Area Servizi
- **ServiziFisici**: Posti barca, armadietti, locali
- **PrezziServizi**: Prezzario con validità temporale
- **Prestazioni**: Corsi, eventi, noleggi

#### 💰 Area Contabile
- **AssegnazioniServiziFisici**: Assegnazioni per periodo
- **ErogazioniPrestazioni**: Registro prestazioni
- **Fatture**: Documenti contabili
- **DettagliFatture**: Righe di dettaglio
- **Pagamenti**: Movimenti di cassa

### Gestione Database

```bash
# Crea database
cd src/database
uv run db_build.py

# Popola con dati di test
uv run db_test.py

# Accesso diretto
sqlite3 data/umami.db
```

## 🔌 API REST

### Endpoints Principali

#### Associati
- `GET /associati` - Lista con filtri e paginazione
- `POST /associati` - Crea nuovo associato
- `GET /associati/{id}` - Dettagli associato
- `PUT /associati/{id}` - Aggiorna associato
- `POST /associati/{id}/tesseramento-fiv` - Gestione tesseramento

#### Fornitori
- `GET /fornitori` - Lista fornitori
- `POST /fornitori` - Crea fornitore
- `PUT /fornitori/{id}` - Aggiorna fornitore
- `DELETE /fornitori/{id}` - Elimina fornitore

#### Chiavi Elettroniche
- `GET /associati/{id}/chiave-elettronica` - Dettagli chiave
- `POST /associati/{id}/chiave-elettronica` - Crea/aggiorna
- `POST /associati/{id}/chiave-elettronica/ricarica` - Ricarica crediti

#### Report
- `GET /report/soci-morosi` - Soci con fatture non pagate
- `GET /report/tesserati-fiv` - Report tesserati FIV
- `GET /report/certificati-in-scadenza` - Certificati in scadenza

### Esempi di Utilizzo

#### Creare un Associato
```bash
curl -X POST "http://localhost:8001/associati" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Mario",
    "cognome": "Rossi",
    "codice_fiscale": "RSSMRA80A01H501Z",
    "data_nascita": "1980-01-01",
    "indirizzo": "Via Roma 1, Milano",
    "email": "mario.rossi@email.com",
    "telefono": "3331234567",
    "data_iscrizione": "2024-01-15",
    "stato_associato": "Attivo"
  }'
```

#### Ricerca Associati
```bash
curl "http://localhost:8001/associati?search=mario&stato=Attivo&limit=10"
```

#### Report Soci Morosi
```bash
curl "http://localhost:8001/report/soci-morosi?giorni_scadenza=30&importo_minimo=100"
```

## 🛠️ Sviluppo

### Struttura del Codice

- **`pyproject.toml`** - Configurazione progetto e dipendenze
- **`src/backend/fastapi_builder.py`** - Definizione endpoint FastAPI
- **`src/backend/api_functions.py`** - Business logic e accesso database
- **`src/database/db_build.py`** - Creazione database
- **`src/database/db_test.py`** - Popolamento dati di test
- **`src/database/database_schema.json`** - Schema database

### Setup Ambiente di Sviluppo

```bash
# Installa dipendenze
uv sync

# Avvia server in modalità sviluppo
uv run uvicorn src.backend.fastapi_builder:app --reload --port 8001
```

### Modifica Schema Database

1. Modifica `src/database/database_schema.json`
2. Esegui `uv run src/database/db_build.py`
3. Testa con `uv run src/database/db_test.py`

### Gestione Errori API

- **404 Not Found** - Risorsa non trovata
- **400 Bad Request** - Dati non validi
- **500 Internal Server Error** - Errori database/server
- **422 Unprocessable Entity** - Errori validazione

## 📊 Query Utili

```sql
-- Soci attivi
SELECT * FROM Associati WHERE stato_associato = 'Attivo';

-- Tesserati FIV
SELECT a.*, t.numero_tessera_fiv 
FROM Associati a 
JOIN TessereFIV t ON a.id_associato = t.fk_associato;

-- Certificati in scadenza (30 giorni)
SELECT a.nome, a.cognome, t.scadenza_certificato_medico
FROM Associati a 
JOIN TessereFIV t ON a.id_associato = t.fk_associato 
WHERE t.scadenza_certificato_medico BETWEEN date('now') AND date('now', '+30 days');

-- Fatture non pagate
SELECT * FROM Fatture WHERE stato IN ('Emessa', 'Scaduta');
```

## 🔒 Sicurezza

⚠️ **Nota**: Implementazione attuale per sviluppo/testing.

Per produzione implementare:
- Autenticazione JWT
- Rate limiting
- CORS appropriato
- HTTPS
- Logging di sicurezza
- Validazione input avanzata

## 📚 Documentazione

- **`doc/database_structure.md`** - Struttura dettagliata database
- **`doc/api_specification.md`** - Specifica completa API
- **API Docs**: http://localhost:8001/docs (quando server attivo)

## 🤝 Contribuire

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/nuova-funzionalita`)
3. Commit modifiche (`git commit -am 'Aggiunge nuova funzionalità'`)
4. Push branch (`git push origin feature/nuova-funzionalita`)
5. Crea Pull Request

## 📝 Changelog

### v1.0.0 (2024)
- ✅ Database SQLite completo (12 tabelle)
- ✅ API REST FastAPI con tutti gli endpoint
- ✅ Documentazione API automatica
- ✅ Sistema di gestione associati e fornitori
- ✅ Gestione tesseramento FIV
- ✅ Sistema chiavi elettroniche
- ✅ Report avanzati
- ✅ Validazione dati con Pydantic

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT.

## 🆘 Supporto

Per problemi, bug o richieste di funzionalità:
1. Controlla la documentazione in `doc/`
2. Verifica gli issue esistenti
3. Crea un nuovo issue con dettagli completi

---

**UMAMI** - *Sistema Gestionale ASD completo e moderno* 🏆
