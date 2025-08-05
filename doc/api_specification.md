# UMAMI - API Specification (Swagger/OpenAPI)

**Version:** 1.0.0
**Last Updated:** 2025-07-30

## Introduzione

Questa è la documentazione delle API REST per il sistema gestionale UMAMI. Le API sono progettate per essere RESTful e utilizzano JSON per la comunicazione.

**Base URL:** `/api/v1`

---

## Autenticazione

Le API utilizzeranno un sistema di autenticazione basato su token (es. JWT). Ogni richiesta protetta dovrà includere il token nell'header `Authorization`.

`Authorization: Bearer <token>`

---

## Risorse Principali

- **Anagrafiche**: `Associati`, `Fornitori`, `ChiaviElettroniche`
- **Servizi**: `ServiziFisici`, `ServiziPrestazionali`, `PrezziServizi`
- **Contabilità**: `Fatture`, `Pagamenti`
- **Reporting**: `Report`

---

## 1. Associati

Gestione dell'anagrafica dei soci, dei gruppi familiari e dei tesseramenti.

### `GET /associati`

Recupera una lista di tutti i soci con filtri e paginazione.

- **Query Parameters:**
  - `limit` (integer, default: 20): Numero di risultati per pagina.
  - `offset` (integer, default: 0): Offset per la paginazione.
  - `search` (string): Cerca per nome, cognome, email o codice fiscale.
  - `stato` (string): Filtra per stato (`Attivo`, `Sospeso`, `Scaduto`, `Cessato`).
  - `tesserato_fiv` (boolean): Filtra per soci con tesseramento FIV.

- **Success Response (200 OK):**
  ```json
  {
    "count": 1,
    "results": [
      {
        "id_associato": 1,
        "nome": "Mario",
        "cognome": "Rossi",
        "codice_fiscale": "RSSMRA80A01H501A",
        "stato_associato": "Attivo",
        "fk_associato_riferimento": null
      }
    ]
  }
  ```

### `POST /associati`

Crea un nuovo socio.

- **Request Body:**
  ```json
  {
    "nome": "Mario",
    "cognome": "Rossi",
    "codice_fiscale": "RSSMRA80A01H501A",
    "data_nascita": "1980-01-01",
    "indirizzo": "Via Roma 1, Milano",
    "email": "mario.rossi@email.com",
    "telefono": "3331112233",
    "data_iscrizione": "2024-01-15",
    "stato_associato": "Attivo",
    "fk_associato_riferimento": null // ID del socio pagante, se parte di un gruppo
  }
  ```

- **Success Response (201 Created):**
  - Ritorna l'oggetto del socio creato con il suo `id_associato`.

### `GET /associati/{id}`

Recupera i dettagli di un singolo socio. Ritorna anche se presenti i tesseramenti FIV, le chiavi elettroniche e le assegnazioni ai servizi fisici e prestazionali con le relative fatture e pagamenti.

- **Success Response (200 OK):**
  - Ritorna l'oggetto completo del socio con le relative relazioni.

### `PUT /associati/{id}`

Aggiorna i dati di un socio.

- **Request Body:**
  - Oggetto JSON con i campi da aggiornare.
- **Success Response (200 OK):**
  - Ritorna l'oggetto del socio aggiornato.

### `POST /associati/{id}/tesseramento-fiv`

Aggiunge o aggiorna il tesseramento FIV per un socio.

- **Request Body:**
  ```json
  {
    "numero_tessera_fiv": "FIV12345",
    "data_tesseramento_fiv": "2024-01-20",
    "scadenza_certificato_medico": "2025-06-30",
    "stato_tesseramento": "Attivo"
  }
  ```
- **Success Response (200 OK):**
  - Ritorna l'oggetto del tesseramento creato/aggiornato.

---

## 2. Fornitori

Gestione dell'anagrafica dei fornitori per la fatturazione passiva.

### `GET /fornitori`

Recupera una lista di tutti i fornitori con filtri e paginazione.

- **Query Parameters:**
  - `limit` (integer, default: 20): Numero di risultati per pagina.
  - `offset` (integer, default: 0): Offset per la paginazione.
  - `search` (string): Cerca per ragione sociale, partita IVA o codice fiscale.
  - `attivo` (boolean): Filtra per fornitori attivi.

- **Success Response (200 OK):**
  ```json
  {
    "count": 1,
    "results": [
      {
        "id_fornitore": 1,
        "ragione_sociale": "Forniture Nautiche SRL",
        "partita_iva": "12345678901",
        "codice_fiscale": "12345678901",
        "indirizzo": "Via del Porto 15, Genova",
        "email": "info@forniturenautiche.it",
        "telefono": "0105551234"
      }
    ]
  }
  ```

### `POST /fornitori`

Crea un nuovo fornitore.

- **Request Body:**
  ```json
  {
    "ragione_sociale": "Forniture Nautiche SRL",
    "partita_iva": "12345678901",
    "codice_fiscale": "12345678901",
    "indirizzo": "Via del Porto 15, Genova",
    "email": "info@forniturenautiche.it",
    "telefono": "0105551234"
  }
  ```

- **Success Response (201 Created):**
  - Ritorna l'oggetto del fornitore creato con il suo `id_fornitore`.

### `GET /fornitori/{id}`

Recupera i dettagli di un singolo fornitore. Ritorna anche se presenti le fatture e i pagamenti.

- **Success Response (200 OK):**
  - Ritorna l'oggetto completo del fornitore con le relative relazioni.

### `PUT /fornitori/{id}`

Aggiorna i dati di un fornitore.

- **Request Body:**
  - Oggetto JSON con i campi da aggiornare.
- **Success Response (200 OK):**
  - Ritorna l'oggetto del fornitore aggiornato.

### `DELETE /fornitori/{id}`

Elimina un fornitore (solo se non ha fatture associate).

- **Success Response (204 No Content)**

---

## 3. Chiavi Elettroniche

Gestione delle chiavi di accesso e crediti docce per i soci.

### `GET /associati/{id}/chiave-elettronica`

Recupera i dati della chiave elettronica di un socio.

- **Success Response (200 OK):**
  ```json
  {
    "fk_associato": 1,
    "numero_chiave": "KEY001",
    "crediti_docce": 10,
    "data_ultima_ricarica": "2024-07-15",
    "stato_chiave": "Attiva"
  }
  ```

### `POST /associati/{id}/chiave-elettronica`

Crea o aggiorna la chiave elettronica per un socio.

- **Request Body:**
  ```json
  {
    "numero_chiave": "KEY001",
    "crediti_docce": 10,
    "stato_chiave": "Attiva"
  }
  ```

- **Success Response (201 Created):**
  - Ritorna l'oggetto della chiave elettronica creata/aggiornata.

### `POST /associati/{id}/chiave-elettronica/ricarica-crediti`

Ricarica i crediti docce per la chiave elettronica di un socio.

- **Request Body:**
  ```json
  {
    "crediti_da_aggiungere": 5
  }
  ```

- **Success Response (200 OK):**
  - Ritorna l'oggetto della chiave elettronica aggiornata.

---

## 4. Servizi

Gestione del catalogo servizi (fisici e prestazionali) e delle assegnazioni.

### `GET /servizi-fisici`

Recupera la lista dei servizi fisici (es. posti barca, armadietti) con costi e assegnazioni (id, nome e cognome del socio). Se non c'è assegnazione, il campo `fk_associato` sarà null.

- **Query Parameters:**
  - `stato` (string): Filtra per stato (`Disponibile`, `Occupato`, `In Manutenzione`).
  - `tipo` (string): Filtra per tipo di servizio.

- **Success Response (200 OK):**
  ```json
  {
    "count": 2,
    "results": [
      {
        "id_servizio_fisico": 1,
        "nome": "Posto Barca A1",
        "descrizione": "Posto barca per imbarcazioni fino a 8 metri",
        "tipo": "Posto Barca",
        "stato": "Disponibile"
      },
      {
        "id_servizio_fisico": 2,
        "nome": "Armadietto 15",
        "descrizione": "Armadietto spogliatoio",
        "tipo": "Armadietto",
        "stato": "Occupato"
      }
    ]
  }
  ```

### `POST /servizi-fisici`

Crea un nuovo servizio fisico.

- **Request Body:**
  ```json
  {
    "nome": "Posto Barca B5",
    "descrizione": "Posto barca per imbarcazioni fino a 10 metri",
    "tipo": "Posto Barca",
    "stato": "Disponibile"
  }
  ```

- **Success Response (201 Created):**
  - Ritorna l'oggetto del servizio fisico creato.

### `GET /servizi-fisici/{id}`

Recupera i dettagli di un singolo servizio fisico. Ritorna anche le assegnazioni storiche con id, nome e cognome del socio per ogni anno.

### `PUT /servizi-fisici/{id}`

Aggiorna i dati di un servizio fisico.

### `POST /servizi-fisici/{id}/assegnazioni`

Assegna un servizio fisico a un socio.

- **Request Body:**
  ```json
  {
    "fk_associato": 1,
    "data_inizio": "2024-01-01",
    "data_fine": "2024-12-31",
    "stato": "Attivo"
  }
  ```
- **Success Response (201 Created):**
  - Ritorna l'oggetto dell'assegnazione.

### `GET /servizi-prestazionali`

Recupera la lista dei servizi prestazionali (es. corsi, eventi).

- **Query Parameters:**
  - `tipo` (string): Filtra per tipo di servizio.
  - `attivo` (boolean): Filtra per servizi attivi.

- **Success Response (200 OK):**
  ```json
  {
    "count": 2,
    "results": [
      {
        "id_servizio_prestazionale": 1,
        "nome": "Corso di Vela Base",
        "descrizione": "Corso introduttivo alla vela per principianti",
        "tipo": "Corso",
        "durata_ore": 20,
        "max_partecipanti": 8
      },
      {
        "id_servizio_prestazionale": 2,
        "nome": "Regata Sociale Estiva",
        "descrizione": "Regata sociale per tutti i soci",
        "tipo": "Evento",
        "durata_ore": 4,
        "max_partecipanti": 50
      }
    ]
  }
  ```

### `POST /servizi-prestazionali`

Crea un nuovo servizio prestazionale.

- **Request Body:**
  ```json
  {
    "nome": "Corso di Vela Avanzato",
    "descrizione": "Corso avanzato per velisti esperti",
    "tipo": "Corso",
    "durata_ore": 30,
    "max_partecipanti": 6
  }
  ```

- **Success Response (201 Created):**
  - Ritorna l'oggetto del servizio prestazionale creato.

### `GET /servizi-prestazionali/{id}`

Recupera i dettagli di un singolo servizio prestazionale.

### `PUT /servizi-prestazionali/{id}`

Aggiorna i dati di un servizio prestazionale.

### `GET /servizi-prestazionali/{id}/erogazioni`

Recupera tutte le erogazioni per un servizio prestazionale.

- **Query Parameters:**
  - `data_da` (date): Filtra erogazioni dalla data specificata.
  - `data_a` (date): Filtra erogazioni fino alla data specificata.

### `POST /servizi-prestazionali/{id}/erogazioni`

Iscrive un socio a un servizio prestazionale.

- **Request Body:**
  ```json
  {
    "fk_associato": 3,
    "data_erogazione": "2024-06-10T14:00:00"
  }
  ```
- **Success Response (201 Created):**
  - Ritorna l'oggetto dell'erogazione.

---

## 5. Prezzi Servizi

Gestione del prezzario per i servizi fisici.

### `GET /prezzi-servizi`

Recupera la lista dei prezzi per i servizi fisici.

- **Query Parameters:**
  - `fk_servizio_fisico` (integer): Filtra per servizio fisico specifico.
  - `attivo` (boolean): Filtra per prezzi attivi.

- **Success Response (200 OK):**
  ```json
  {
    "count": 2,
    "results": [
      {
        "id_prezzo": 1,
        "fk_servizio_fisico": 1,
        "nome_servizio": "Posto Barca A1",
        "prezzo_mensile": 150.00,
        "prezzo_annuale": 1500.00,
        "data_validita_inizio": "2024-01-01",
        "data_validita_fine": "2024-12-31"
      }
    ]
  }
  ```

### `POST /prezzi-servizi`

Crea un nuovo prezzo per un servizio fisico.

- **Request Body:**
  ```json
  {
    "fk_servizio_fisico": 1,
    "prezzo_mensile": 150.00,
    "prezzo_annuale": 1500.00,
    "data_validita_inizio": "2024-01-01",
    "data_validita_fine": "2024-12-31"
  }
  ```

- **Success Response (201 Created):**
  - Ritorna l'oggetto del prezzo creato.

### `GET /prezzi-servizi/{id}`

Recupera i dettagli di un singolo prezzo.

### `PUT /prezzi-servizi/{id}`

Aggiorna un prezzo esistente.

### `DELETE /prezzi-servizi/{id}`

Elimina un prezzo (solo se non è utilizzato in fatture).

---

## 6. Fatture

Gestione del ciclo di fatturazione attivo e passivo.

### `GET /fatture`

Recupera una lista di fatture.

- **Query Parameters:**
  - `tipo_fattura` (string): `Attiva` o `Passiva`.
  - `stato` (string): `Emessa`, `Pagata`, `Scaduta`, `Annullata`.
  - `fk_associato` (integer): ID del socio.
  - `fk_fornitore` (integer): ID del fornitore.

### `POST /fatture/genera-attive`

Genera automaticamente le fatture attive per i soci in base ai servizi assegnati in un dato periodo.

- **Request Body:**
  ```json
  {
    "periodo_inizio": "2024-01-01",
    "periodo_fine": "2024-12-31",
    "data_emissione": "2025-01-15",
    "data_scadenza": "2025-02-15"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "messaggio": "Generazione fatture completata.",
    "fatture_generate": 50,
    "importo_totale": 125000.00
  }
  ```

### `POST /fatture`

Crea una singola fattura (tipicamente passiva o manuale).

- **Request Body:**
  ```json
  {
    "tipo_fattura": "Passiva",
    "fk_fornitore": 1,
    "numero_fattura": "PASS-2024-XYZ",
    "data_emissione": "2024-07-30",
    "importo_imponibile": 100.00,
    "importo_iva": 22.00,
    "importo_totale": 122.00,
    "stato": "Emessa",
    "dettagli": [
      {
        "descrizione": "Materiale di pulizia",
        "quantita": 1,
        "prezzo_unitario": 100.00,
        "importo_totale": 100.00
      }
    ]
  }
  ```
- **Success Response (201 Created):**
  - Ritorna l'oggetto della fattura creata.

### `GET /fatture/{id}`

Recupera i dettagli di una singola fattura, incluse le righe di dettaglio.

### `POST /fatture/{id}/pagamenti`

Registra un pagamento per una fattura.

- **Request Body:**
  ```json
  {
    "data_pagamento": "2024-08-01",
    "importo": 122.00,
    "metodo": "Bonifico",
    "tipo": "Uscita"
  }
  ```
- **Success Response (201 Created):**
  - Ritorna l'oggetto del pagamento. La fattura collegata viene aggiornata a `Pagata`.

---

## 7. Report

Endpoint dedicati per generare report specifici.

### `GET /report/tesserati-fiv`

Genera un report di tutti i soci tesserati FIV.

- **Query Parameters:**
  - `stato_tesseramento` (string): `Attivo`, `Sospeso`, `Scaduto`.

- **Success Response (200 OK):**
  - Array di oggetti con i dettagli dei soci e del loro tesseramento.

### `GET /report/certificati-in-scadenza`

Genera un report dei certificati medici in scadenza.

- **Query Parameters:**
  - `giorni_alla_scadenza` (integer, default: 30): Numero di giorni per considerare un certificato in scadenza.

- **Success Response (200 OK):**
  - Array di oggetti con i dettagli dei soci e la data di scadenza del certificato.

### `GET /report/soci-morosi`

Genera un report dei soci con fatture non pagate (morosi).

- **Query Parameters:**
  - `giorni_scadenza` (integer, default: 0): Filtra fatture scadute da almeno N giorni.
  - `importo_minimo` (decimal): Filtra per importo minimo dovuto.
  - `include_sospesi` (boolean, default: false): Include anche soci con stato "Sospeso".

- **Success Response (200 OK):**
  ```json
  {
    "count": 2,
    "totale_crediti": 1250.00,
    "results": [
      {
        "id_associato": 15,
        "nome": "Marco",
        "cognome": "Bianchi",
        "email": "marco.bianchi@email.com",
        "telefono": "3339998877",
        "stato_associato": "Attivo",
        "fatture_non_pagate": [
          {
            "id_fattura": 123,
            "numero_fattura": "ATT-2024-123",
            "data_emissione": "2024-06-15",
            "data_scadenza": "2024-07-15",
            "importo_totale": 750.00,
            "giorni_scadenza": 16,
            "stato": "Scaduta"
          }
        ],
        "totale_dovuto": 750.00
      },
      {
        "id_associato": 28,
        "nome": "Laura",
        "cognome": "Verdi",
        "email": "laura.verdi@email.com",
        "telefono": "3331234567",
        "stato_associato": "Attivo",
        "fatture_non_pagate": [
          {
            "id_fattura": 145,
            "numero_fattura": "ATT-2024-145",
            "data_emissione": "2024-07-01",
            "data_scadenza": "2024-07-31",
            "importo_totale": 500.00,
            "giorni_scadenza": 0,
            "stato": "Emessa"
          }
        ],
        "totale_dovuto": 500.00
      }
    ]
  }
  ```

### `GET /report/fatturato`

Genera un report sul fatturato per un dato periodo.

- **Query Parameters:**
  - `periodo_inizio` (date, required): Data inizio (es. `2024-01-01`).
  - `periodo_fine` (date, required): Data fine (es. `2024-12-31`).

- **Success Response (200 OK):**
  ```json
  {
    "periodo": "2024-01-01 - 2024-12-31",
    "fatturato_attivo": {
      "imponibile": 150000.00,
      "iva": 33000.00,
      "totale": 183000.00
    },
    "fatturato_passivo": {
      "imponibile": 25000.00,
      "iva": 5500.00,
      "totale": 30500.00
    }
  }
  ```
