# **Documentazione Database \- UMAMI**

## **1\. Introduzione e Filosofia del Progetto**

Questo documento descrive la struttura e le logiche del database progettato per il software gestionale di un'associazione sportiva dilettantistica (ASD).

La scelta è ricaduta su un modello di database **relazionale (SQL)**, come PostgreSQL o SQLite. Questa decisione è motivata dalla natura intrinsecamente relazionale dei dati (soci, servizi, fatture, pagamenti) e dalla necessità di garantire la massima **integrità, coerenza e affidabilità delle transazioni (proprietà ACID)**, specialmente per la gestione contabile.

Lo schema è progettato per essere **flessibile e scalabile**. Include la gestione dei legami familiari direttamente nella tabella dei soci e separa i dati specifici del tesseramento FIV (Federazione Italiana Vela) in una tabella dedicata, per una maggiore chiarezza e normalizzazione.

## **2\. Schema delle Tabelle**

Il database è organizzato in tre aree logiche principali: **Anagrafiche**, **Servizi** e **Contabilità**.

### **Area Anagrafiche**

Contiene le entità principali con cui l'associazione interagisce.

#### **Associati**

Tabella madre che censisce tutti i soci dell'associazione e gestisce i legami familiari. Contiene solo i dati anagrafici essenziali.

| Campo                      | Tipo    | Note                      | Descrizione                                                                                                                            |
| -------------------------- | ------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| id\_associato              | INT     | PK, AUTO\_INCREMENT       | Identificativo unico del socio                                                                                                         |
| fk\_associato\_riferimento | INT     | FK -> Associati, NULLABLE | Chiave auto-referenziante. Se valorizzato, punta all'id\_associato del membro che paga per questo socio. Se NULL, il socio paga per sé |
| nome                       | VARCHAR |                           | Nome di battesimo del socio                                                                                                            |
| cognome                    | VARCHAR |                           | Cognome del socio                                                                                                                      |
| codice\_fiscale            | VARCHAR | UNIQUE                    | Codice Fiscale                                                                                                                         |
| data\_nascita              | DATE    |                           | Data di nascita                                                                                                                        |
| indirizzo                  | VARCHAR |                           | Indirizzo di residenza completo                                                                                                        |
| email                      | VARCHAR |                           | Indirizzo email                                                                                                                        |
| telefono                   | VARCHAR |                           | Numero di telefono                                                                                                                     |
| data\_iscrizione           | DATE    |                           | Data di prima iscrizione all'associazione                                                                                              |
| stato\_associato           | ENUM    |                           | Stato attuale del socio ('Attivo', 'Sospeso', 'Scaduto', 'Cessato')                                                                    |

#### ChiaviElettroniche

Contiene i dati operativi per l'accesso ai locali e ai crediti per le docce.

| Campo        | Tipo    | Note                | Descrizione                                                                                 |
| ------------ | ------- | ------------------- | ------------------------------------------------------------------------------------------- |
| fk_associato | INT     | PK, FK -> Associati | Collega questi dati ad un unico socio. Agisce sia da chiave primaria che da chiave esterna. |
| key_code     | VARCHAR | UNIQUE              | Codice univoco associato alla chiave/badge elettronico dell'associato                       |
| in_regola    | BOOL    |                     | Valore che consente l'accesso solo se l'associato è in regola con i pagamenti               |
| credito      | DECIMAL | DEFAULT 0.00        | Saldo del credito residuo del socioper l'utilizzo delle docce                               |

#### **TessereFIV**

Contiene i dati aggiuntivi solo per i soci tesserati FIV.  

| Campo                         | Tipo    | Note                 | Descrizione                                                                               |
| ----------------------------- | ------- | -------------------- | ----------------------------------------------------------------------------------------- |
| fk\_associato                 | INT     | PK, FK \-> Associati | Collega questi dati a un unico socio. Agisce sia da Chiave Primaria che da Chiave Esterna |
| numero\_tessera\_fiv          | VARCHAR | UNIQUE               | Il numero di tessera ufficiale rilasciato dalla FIV                                       |
| scadenza\_tesseramento\_fiv   | DATE    |                      | Data di scadenza del tesseramento FIV                                                     |
| scadenza\_certificato\_medico | DATE    |                      | Data di scadenza del certificato medico (agonistico/non agonistico)                       |




#### **Fornitori**

Anagrafica delle entità da cui l'associazione acquista beni o servizi.

| Campo            | Tipo    | Note                | Descrizione                                |
| ---------------- | ------- | ------------------- | ------------------------------------------ |
| id\_fornitore    | INT     | PK, AUTO\_INCREMENT | Identificativo unico del fornitore         |
| ragione\_sociale | VARCHAR |                     |                                            |
| partita\_iva     | VARCHAR | UNIQUE              | Partita IVA o Codice Fiscale del fornitore |
| email            | VARCHAR |                     | Email di contatto del fornitore            |
| telefono         | VARCHAR |                     | Telefono di contatto del fornitore         |

### **Area Servizi**

Contiene il catalogo di tutti i servizi, fisici e prestazionali, offerti dall'associazione.

#### **Servizi**

Catalogo delle risorse/servizi tangibili e univoci (es. posti barca, armadietti).

| Campo        | Tipo | Note                | Descrizione                                                                                                                        |
| ------------ | ---- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| id\_servizio | INT  | PK, AUTO\_INCREMENT | ID unico del servizio                                                                                                             |
| fk\_prezzo   | INT  | FK -> PrezziServizi | Prezzo associato al servizio (1 prezzo -> N servizi)                                                                              |
| descrizione  | TEXT |                     | Dettagli sulla risorsa/servizio                                                                                                   |
| stato        | ENUM |                     | Stato attuale del servizio ('Disponibile', 'Occupato', 'In Manutenzione')                                                         |

#### PrezziServizi

Prezzario dei servizi. Un record di prezzo può essere associato a più servizi.

| Campo               | Tipo    | Note                | Descrizione                                            |
| ------------------- | ------- | ------------------- | ------------------------------------------------------ |
| id\_prezzo          | INT     | PK, AUTO\_INCREMENT | ID univoco del prezzo                                  |
| categoria\_servizio | VARCHAR |                     | Etichetta umana per la categoria del servizio (es. "Posto Barca A", "Armadietto") |
| costo               | DECIMAL |                     | Prezzo di listino                                      |

#### **Prestazioni**

Catalogo di tutti i servizi non tangibili (corsi, noleggi, quote, eventi).

| Campo                       | Tipo    | Note                | Descrizione                               |
| --------------------------- | ------- | ------------------- | ----------------------------------------- |
| id\_prestazione             | INT     | PK, AUTO\_INCREMENT | ID unico del servizio                     |
| nome\_prestazione           | VARCHAR |                     | Nome del servizio ('Corso Vela', 'Quota') |
| descrizione                 | TEXT    |                     | Dettagli sul servizio                     |
| costo                       | DECIMAL |                     | Prezzo di listino della prestazione       |

### **Area Contabile**

Tabelle che gestiscono i flussi finanziari e legano i soci ai servizi.

#### **AssegnazioniServizi**

Tabella ponte che collega un socio a un servizio per un periodo.

| Campo            | Tipo | Note              | Descrizione                                     |
| ---------------- | ---- | ----------------- | ----------------------------------------------- |
| id\_assegnazione | INT  | PK, AUTO\_INCREMENT | ID unico dell'assegnazione                      |
| fk\_associato    | INT  | FK -> Associati   | Il socio a cui è assegnata la risorsa           |
| fk\_servizio     | INT  | FK -> Servizi     | Il servizio assegnato                           |
| anno\_competenza | YEAR |                   | Anno di validità dell'assegnazione (per rinnovi |
| data\_inizio     | DATE |                   | Data di inizio dell'assegnazione                |

#### **ErogazioniPrestazioni**

Tabella ponte che registra l'iscrizione/fruizione di un servizio prestazionale da parte di un socio.

| Campo            | Tipo     | Note                | Descrizione                         |
| ---------------- | -------- | ------------------- | ----------------------------------- |
| id\_erogazione   | INT      | PK, AUTO\_INCREMENT | ID unico dell'erogazione/iscrizione |
| fk\_associato    | INT      | FK -> Associati    | Il socio che fruisce del servizio   |
| fk_prestazione   | INT      | FK -> prestazioni   | La prestazione erogato              |
| data\_erogazione | DATETIME |                     | Data dell'iscrizione                |

#### **Fatture**

Registro centrale di tutti i documenti contabili, sia in entrata (attivi) che in uscita (passivi).

| Campo                                   | Tipo    | Note                              | Descrizione                                                                             |
| --------------------------------------- | ------- | --------------------------------- | --------------------------------------------------------------------------------------- |
| id\_fattura                             | INT     | PK, AUTO\_INCREMENT               | ID unico della fattura                                                                  |
| numero\_fattura                         | VARCHAR | UNIQUE                            | Numero del documento (progressivo per fatture attive, del fornitore per quelle passive) |
| data\_emissione                         | DATE    |                                   |                                                                                         |
| data\_scadenza                          | DATE    |                                   |                                                                                         |
| importo\_imponibile                     | DECIMAL |                                   |                                                                                         |
| importo\_iva                            | DECIMAL |                                   |                                                                                         |
| importo\_totale                         | DECIMAL |                                   |                                                                                         |
| tipo                                    | ENUM    | 'Entrata', 'Uscita'               |                                                                                         |
| stato                                   | ENUM    |                                   | Stato del pagamento ('Emessa', 'Pagata', 'Pagata Parzialmente', 'Stornata')             |
| fk\_associato                           | INT     | FK -> Associati, NULLABLE         |                                                                                         |
| fk\_fornitore                           | INT     | FK -> Fornitori, NULLABLE        |                                                                                         |
| categoria                                | ENUM    | NULLABLE                          | Categoria di bilancio (era in DettagliFattura)                                          |
| gruppo                                   | ENUM    | NULLABLE                          | Gruppo di bilancio (era in DettagliFattura)                                             |
| settore                                  | ENUM    | NULLABLE                          | Settore di bilancio (era in DettagliFattura)                                            |
| descrizione                               | TEXT    | NULLABLE                          | Descrizione della voce (era in DettagliFattura)                                         |
| fk\_assegnazione\_servizio              | INT     | FK -> AssegnazioniServizi, NULLABLE | Link di tracciabilità al servizio fatturato (era in DettagliFattura)                    |
| fk\_erogazione\_prestazione | INT     | FK -> ErogazioniPrestazioni, NULLABLE | Link di tracciabilità al servizio prestazionale fatturato (era in DettagliFattura)      |

<!-- Sezione DettagliFattura rimossa: ora ogni fattura rappresenta una singola voce e contiene i campi prima presenti nelle righe di dettaglio. -->

#### **Pagamenti**

Registro di tutti i movimenti di cassa/banca.

| Campo           | Tipo    | Note                                     | Descrizione                                  |
| --------------- | ------- | ---------------------------------------- | -------------------------------------------- |
| id\_pagamento   | INT     | PK, AUTO\_INCREMENT                      | ID unico del movimento                       |
| data\_pagamento | DATE    |                                          | Data effettiva del movimento di denaro       |
| importo         | DECIMAL |                                          | Importo del movimento                        |
| metodo          | ENUM    | 'Bonifico', 'POS', 'Contanti', 'Assegno' |                                              |
| fk\_fattura     | INT     | FK \-> Fatture                           | La fattura che questo pagamento sta saldando |
| tipo            | ENUM    | 'Entrata', 'Uscita'                      | Specifica se il denaro è entrato o uscito    |

## **3\. Flussi Operativi e Logiche di Implementazione**

### **3.1. Gestione Anagrafica e Tesseramento FIV**

**Caso d'uso: Un nuovo socio si iscrive e si tessera anche alla FIV.**

1. **Iscrizione Base**: Viene creato un nuovo record in Associati con i dati anagrafici del socio.  
2. **Tesseramento FIV**: Se il socio richiede il tesseramento FIV, l'operatore crea un record collegato nella tabella DatiTesseramentoFIV.  
   * fk\_associato: L'id\_associato del socio appena creato.  
   * Vengono inseriti numero\_tessera\_fiv, data\_tesseramento\_fiv, e la scadenza\_certificato\_medico.  
3. **Controllo Certificato Medico**: Un processo automatico deve controllare la tabella DatiTesseramentoFIV per le scadenze dei certificati. Se un certificato scade, il sistema può inviare notifiche e, se necessario, aggiornare lo stato\_tesseramento del socio in Associati a 'Sospeso', poiché il tesseramento FIV potrebbe non essere più valido.

L'iscrizione a corsi agonistici o a regate (servizi in ServiziPrestazionali) può ora avere come pre-requisito la presenza di un record valido in DatiTesseramentoFIV per quel socio.

### **3.2. Gestione Gruppi Familiari e Fatturazione Consolidata**

La logica rimane invariata, basandosi sul campo fk\_associato\_pagante nella tabella Associati. Il sistema raggruppa i servizi per pagante finale e crea fatture consolidate.

**Esempio**: Se "Laura Verdi" (figlia) si iscrive a un corso che richiede tesseramento FIV, il costo del corso e del tesseramento verranno fatturati in un unico documento (tabella `Fatture`) intestato a suo padre "Giovanni Verdi", con descrizione e importi aggregati.

### **3.3. Ciclo di Fatturazione Attiva (Socio Singolo)**

Il flusso per un socio che paga per sé (fk\_associato\_pagante è NULL) rimane invariato.

### **3.4. Ciclo di Fatturazione Passiva (Verso i Fornitori)**

Questo flusso rimane completamente invariato.

### **3.5. Logiche di Reporting**

Le logiche esistenti rimangono valide. Si aggiungono nuove possibilità:

* **Elenco Tesserati FIV**: SELECT \* FROM Associati A JOIN DatiTesseramentoFIV F ON A.id\_associato \= F.fk\_associato.  
* **Elenco Certificati Medici in Scadenza**: SELECT \* FROM Associati A JOIN DatiTesseramentoFIV F ON A.id\_associato \= F.fk\_associato WHERE F.scadenza\_certificato\_medico BETWEEN CURDATE() AND CURDATE() \+ INTERVAL 30 DAY.  
* **Composizione Gruppo Familiare**: La query rimane la stessa: SELECT \* FROM Associati WHERE fk\_associato\_pagante \= \[ID del pagante\] OR id\_associato \= \[ID del pagante\].