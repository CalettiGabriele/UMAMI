# Database UMAMI - Sistema Gestionale ASD

Questo modulo contiene gli strumenti per la creazione e gestione del database SQLite per il sistema gestionale dell'associazione sportiva dilettantistica.

## File Principali

- **`db_build.py`**: Script principale per la creazione del database
- **`database_schema.json`**: Configurazione delle tabelle in formato JSON
- **`data/`**: Directory contenente il database SQLite generato

## Utilizzo

### Creazione del Database

```bash
cd src/database
python3 db_build.py
```

Lo script:
1. Legge la configurazione da `database_schema.json`
2. Crea la directory `data/` se non esiste
3. Genera il database SQLite `data/umami.db`
4. Crea tutte le tabelle nell'ordine corretto per rispettare le foreign keys
5. Verifica l'integrità del database creato

### Modifica della Struttura

Per modificare la struttura del database:

1. Modifica il file `database_schema.json`
2. Esegui nuovamente `python3 db_build.py`
3. Il database esistente verrà automaticamente salvato come backup

### Accesso al Database

```bash
# Accesso diretto con SQLite
sqlite3 data/umami.db

# Visualizza tutte le tabelle
.tables

# Visualizza la struttura di una tabella
.schema Associati

# Esegui una query
SELECT * FROM Associati;
```

## Struttura del Database

Il database è organizzato in tre aree logiche:

### Area Anagrafiche
- **Associati**: Soci dell'associazione con gestione legami familiari
- **ChiaviElettroniche**: Dati operativi per accesso locali e crediti docce
- **DatiTesseramentoFIV**: Dati specifici tesseramento Federazione Italiana Vela
- **Fornitori**: Anagrafica fornitori

### Area Servizi
- **ServiziFisici**: Catalogo risorse fisiche (posti barca, armadietti, etc.)
- **PrezziServizi**: Prezzario servizi fisici con validità temporale
- **ServiziPrestazionali**: Catalogo servizi prestazionali (corsi, eventi, etc.)

### Area Contabile
- **AssegnazioniServiziFisici**: Collegamento soci-servizi fisici per periodo
- **ErogazioniPrestazioni**: Registro prestazioni erogate
- **Fatture**: Registro documenti contabili (attivi e passivi)
- **DettagliFatture**: Righe di dettaglio fatture
- **Pagamenti**: Movimenti di cassa/banca

## Caratteristiche Tecniche

- **Database**: SQLite (compatibile con PostgreSQL per future migrazioni)
- **Integrità referenziale**: Foreign keys abilitate
- **Backup automatico**: Il database esistente viene salvato prima della ricreazione
- **Validazione**: Controlli CHECK per valori enum
- **Configurazione esterna**: Schema definito in JSON per facilità di modifica

## Esempi di Query Utili

```sql
-- Elenco soci attivi
SELECT * FROM Associati WHERE stato_associato = 'Attivo';

-- Soci tesserati FIV
SELECT a.*, d.numero_tessera_fiv, d.data_tesseramento_fiv 
FROM Associati a 
JOIN DatiTesseramentoFIV d ON a.id_associato = d.fk_associato;

-- Certificati medici in scadenza (prossimi 30 giorni)
SELECT a.nome, a.cognome, d.scadenza_certificato_medico
FROM Associati a 
JOIN DatiTesseramentoFIV d ON a.id_associato = d.fk_associato 
WHERE d.scadenza_certificato_medico BETWEEN date('now') AND date('now', '+30 days');

-- Fatture non pagate
SELECT * FROM Fatture WHERE stato = 'Emessa';

-- Composizione gruppo familiare
SELECT * FROM Associati 
WHERE fk_associato_riferimento = [ID_PAGANTE] OR id_associato = [ID_PAGANTE];
```

## Manutenzione

- Il database viene ricreato completamente ad ogni esecuzione di `db_build.py`
- I backup vengono salvati automaticamente con timestamp
- Per modifiche strutturali, aggiornare sempre `database_schema.json`
- Verificare sempre l'integrità dopo le modifiche con il comando di verifica integrato

## Supporto

Per problemi o modifiche alla struttura del database, consultare la documentazione completa in `doc/database_structure.md`.
