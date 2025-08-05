# UMAMI - Specifica UI/UX Frontend

**Version:** 2.0.0  
**Last Updated:** 2025-08-05

## Introduzione

Questo documento descrive l'architettura dell'interfaccia utente del sistema gestionale UMAMI, definendo le pagine, le funzionalità e i flussi di navigazione del frontend. Il sistema è progettato per gestire efficacemente un'associazione sportiva dilettantistica attraverso un'interfaccia web intuitiva e funzionale.

## Principi di Design

### Utenti Target
- **Segreteria**: Gestione quotidiana associati, servizi, pagamenti
- **Amministrazione**: Controllo finanziario, report, configurazioni
- **Istruttori**: Gestione corsi e prestazioni
- **Soci**: Consultazione dati personali e servizi (futuro)

### Principi Guida
- **Semplicità**: Interfaccia intuitiva per utenti non tecnici
- **Efficienza**: Riduzione dei click e dei passaggi per operazioni comuni
- **Consistenza**: Pattern di interazione uniformi in tutto il sistema
- **Accessibilità**: Supporto per diversi dispositivi e capacità
- **Feedback**: Conferme chiare per ogni azione critica

## Architettura dell'Interfaccia

### Layout Principale
```
┌─────────────────────────────────────────────────────┐
│ Header: Logo UMAMI | Navigazione | Utente | Logout  │
├─────────────────────────────────────────────────────┤
│ Sidebar Navigation                │ Area Contenuto  │
│ • Anagrafica                      │                 │
│   - Elenco Associati              │                 │
│   - Scheda Associato              │                 │
│   - Elenco Fornitori              │                 │
│   - Scheda Fornitore              │                 │
│ • Servizi                         │                 │
│   - Elenco Servizi                │                 │
│   - Scheda Servizio               │                 │
│   - Prezzario Servizi             │                 │
│   - Elenco Prestazioni            │                 │
│ • Contabilità                     │                 │
│   - Elenco Fatture                │                 │
│   - Scheda Fattura                │                 │
│   - Elenco Pagamenti              │                 │
│ • Report                          │                 │
│   - Bilancio Economico            │                 │
│   - Soci Morosi                   │                 │
└─────────────────────────────────────────────────────┘
```

### Componenti Ricorrenti

**Elementi dell'Interfaccia**:
- **Header Pagina**: Titolo "Gestione Associati" + Pulsante "Nuovo Associato"
- **Barra Filtri**:
  - Campo ricerca testuale (Nome, Cognome, Codice Fiscale)
  - Dropdown "Stato" (Attivo, Sospeso, Scaduto, Cessato)
  - Checkbox "Solo Tesserati FIV"
  - Pulsante "Filtra" e "Reset"
- **Tabella Risultati**:
  - Colonne: ID, Nome, Cognome, Codice Fiscale, Stato, Data Iscrizione
  - Ordinamento per colonna
  - Paginazione (20 record per pagina)
  - Click su riga → Apertura Scheda Associato
- **Azioni Bulk**: Selezione multipla per operazioni di massa

**Funzionalità**:
- Ricerca in tempo reale durante digitazione
- Filtri combinabili e persistenti nella sessione
- Export elenco in Excel/CSV
- Indicatori visivi per stato associato (colori/icone)

#### 1.2 Scheda Associato
**URL**: `/anagrafica/associati/{id}`  
**Descrizione**: Visualizzazione dettagliata e modifica dati associato

**Layout a Sezioni**:

**Sezione 1: Dati Anagrafici**
- Nome, Cognome, Codice Fiscale
- Data di Nascita, Luogo di Nascita
- Indirizzo Completo
- Email, Telefono
- Data Iscrizione, Stato Associato
- Associato di Riferimento (per gruppi familiari)

**Sezione 2: Tessera FIV**
- Numero Tessera FIV
- Data Rilascio, Data Scadenza
- Stato Tesseramento
- Certificato Medico (data scadenza)
- Pulsante "Rinnova Tessera"

**Sezione 3: Chiave Elettronica**
- Codice Chiave
- Stato (Attiva/Disattiva)
- Crediti Docce Disponibili
- Storico Ricariche
- Pulsante "Ricarica Crediti"

**Sezione 4: Servizi Assegnati**
- Tabella servizi fisici attivi
- Periodo di assegnazione
- Stato servizio
- Pulsante "Assegna Nuovo Servizio"

**Sezione 5: Prestazioni/Corsi**
- Lista iscrizioni a corsi/eventi
- Stato iscrizione
- Date e orari
- Pulsante "Nuova Iscrizione"

**Sezione 6: Situazione Pagamenti**
- Fatture emesse (pagate/non pagate)
- Importo totale dovuto
- Ultimo pagamento
- Link a "Dettaglio Contabilità"

**Controlli Pagina**:
- Pulsante "Modifica" (attiva modalità editing)
- Pulsante "Salva" / "Annulla" (in modalità editing)
- Pulsante "Elimina" (con conferma)
- Breadcrumb di navigazione

#### 1.3 Elenco Fornitori
**URL**: `/anagrafica/fornitori`  
**Descrizione**: Gestione fornitori dell'associazione

**Elementi dell'Interfaccia**:
- **Header**: "Gestione Fornitori" + Pulsante "Nuovo Fornitore"
- **Barra Filtri**:
  - Campo ricerca (Ragione Sociale, Partita IVA)
  - Pulsante "Filtra" e "Reset"
- **Tabella**:
  - Colonne: ID, Ragione Sociale, Partita IVA, Data Inserimento
  - Click su riga → Scheda Fornitore
- **Azioni**: Modifica, Elimina (con controllo vincoli)

#### 1.4 Scheda Fornitore
**URL**: `/anagrafica/fornitori/{id}`  
**Descrizione**: Dettagli e modifica dati fornitore

**Sezioni**:

**Sezione 1: Dati Aziendali**
- Ragione Sociale
- Partita IVA
- Codice Fiscale (se diverso da P.IVA)
- Indirizzo Sede Legale

**Sezione 2: Contatti**
- Email
- Telefono
- Fax
- Referente

**Sezione 3: Dati Contabili**
- Codice Fornitore
- Modalità Pagamento Preferita
- Giorni Pagamento
- Note

**Sezione 4: Storico Fatture**
- Tabella fatture ricevute
- Importi e date
- Stato pagamento
- Link a dettaglio fattura

### 2. SEZIONE SERVIZI

#### 2.1 Elenco Servizi
**URL**: `/servizi/elenco`  
**Descrizione**: Gestione servizi fisici (barche, attrezzature)

**Elementi dell'Interfaccia**:
- **Header**: "Gestione Servizi Fisici" + Pulsante "Nuovo Servizio"
- **Filtri**:
  - Dropdown "Tipo" (Deriva, Catamarano, Windsurf, etc.)
  - Dropdown "Stato" (Disponibile, In Manutenzione, Ritirato)
  - Campo ricerca nome
- **Tabella**:
  - Colonne: ID, Nome, Tipo, Stato, Note, Ultimo Utilizzo
  - Indicatori visivi per stato
  - Click su riga → Scheda Servizio

#### 2.2 Scheda Servizio
**URL**: `/servizi/dettaglio/{id}`  
**Descrizione**: Dettagli servizio e storico assegnazioni

**Sezioni**:

**Sezione 1: Dati Servizio**
- Nome Identificativo
- Tipo Servizio
- Stato Attuale
- Note Tecniche
- Data Acquisto/Dismissione

**Sezione 2: Storico Assegnazioni**
- Tabella assegnazioni per anno
- Colonne: Anno, Associato, Periodo, Durata
- Filtri per anno e associato
- Visualizzazione calendario occupazione

**Sezione 3: Manutenzioni**
- Registro interventi
- Date e descrizioni
- Costi sostenuti
- Prossima manutenzione programmata

**Sezione 4: Assegnazione Corrente**
- Associato assegnatario
- Periodo assegnazione
- Pulsanti "Modifica Assegnazione" / "Termina Assegnazione"

#### 2.3 Prezzario Servizi
**URL**: `/servizi/prezzi`  
**Descrizione**: Gestione prezzi per categorie di servizi

**Elementi dell'Interfaccia**:
- **Header**: "Prezzario Servizi" + Pulsante "Nuovo Prezzo"
- **Tabella Prezzi**:
  - Colonne: Categoria Servizio, Prezzo, Validità Dal, Validità Al
  - Modifica inline dei prezzi
  - Storico variazioni prezzi
- **Form Nuovo Prezzo**:
  - Categoria servizio
  - Importo
  - Periodo di validità
  - Note

#### 2.4 Elenco Prestazioni
**URL**: `/servizi/prestazioni`  
**Descrizione**: Gestione corsi, eventi e prestazioni

**Elementi dell'Interfaccia**:
- **Header**: "Gestione Prestazioni" + Pulsante "Nuova Prestazione"
- **Filtri**:
  - Tipo prestazione
  - Stato (Programmata, In Corso, Conclusa)
  - Periodo
- **Tabella**:
  - Colonne: Nome, Tipo, Istruttore, Date, Iscritti/Max, Stato
  - Click su riga → Dettaglio prestazione

**Sezione Dettaglio Prestazione**:
- Dati prestazione (nome, descrizione, date)
- Lista iscritti con stato pagamento
- Pulsanti gestione (Aggiungi Iscritto, Modifica, Chiudi)

### 3. SEZIONE CONTABILITÀ

#### 3.1 Elenco Fatture
**URL**: `/contabilita/fatture`  
**Descrizione**: Gestione fatture attive e passive

**Elementi dell'Interfaccia**:
- **Header**: "Gestione Fatture" + Pulsante "Nuova Fattura"
- **Filtri**:
  - Tipo (Attive/Passive)
  - Stato (Emessa, Pagata, Scaduta)
  - Periodo emissione
  - Cliente/Fornitore
- **Tabella**:
  - Colonne: Numero, Data, Cliente/Fornitore, Importo, Stato, Scadenza
  - Indicatori visivi per fatture scadute
  - Click su riga → Scheda Fattura

#### 3.2 Scheda Fattura
**URL**: `/contabilita/fatture/{id}`  
**Descrizione**: Dettagli fattura e gestione pagamenti

**Sezioni**:

**Sezione 1: Dati Fattura**
- Numero e Data Fattura
- Cliente/Fornitore
- Importo Totale
- Data Scadenza
- Stato Pagamento

**Sezione 2: Dettagli Fattura**
- Tabella righe fattura
- Descrizione, Quantità, Prezzo, Totale
- Calcolo IVA e totali

**Sezione 3: Pagamenti**
- Storico pagamenti ricevuti/effettuati
- Importo residuo
- Pulsante "Registra Pagamento"

**Sezione 4: Documenti**
- PDF fattura
- Ricevute pagamento
- Documenti allegati

#### 3.3 Elenco Pagamenti
**URL**: `/contabilita/pagamenti`  
**Descrizione**: Registro movimenti di cassa

**Elementi dell'Interfaccia**:
- **Header**: "Registro Pagamenti" + Pulsante "Nuovo Pagamento"
- **Filtri**:
  - Tipo (Entrata/Uscita)
  - Metodo pagamento
  - Periodo
  - Importo min/max
- **Tabella**:
  - Colonne: Data, Tipo, Descrizione, Importo, Metodo, Fattura Collegata
  - Totali per periodo
  - Export per contabilità

### 4. SEZIONE REPORT

#### 4.1 Bilancio Economico
**URL**: `/report/bilancio`  
**Descrizione**: Report economico dell'associazione

**Elementi dell'Interfaccia**:
- **Filtri Periodo**:
  - Selezione anno
  - Confronto con anno precedente
  - Filtro per mese

**Sezioni Report**:

**Sezione 1: Riepilogo Generale**
- Totale Entrate
- Totale Uscite
- Saldo Netto
- Grafici trend mensili

**Sezione 2: Dettaglio Entrate**
- Quote associative
- Servizi fisici
- Prestazioni/Corsi
- Altre entrate
- Breakdown per categoria

**Sezione 3: Dettaglio Uscite**
- Fornitori
- Manutenzioni
- Utenze
- Altre spese
- Breakdown per categoria

**Controlli Export**:
- Pulsante "Scarica PDF"
- Pulsante "Scarica Excel"
- Opzioni stampa

#### 4.2 Soci Morosi
**URL**: `/report/morosi`  
**Descrizione**: Elenco soci con pagamenti in ritardo

**Elementi dell'Interfaccia**:
- **Filtri**:
  - Giorni di ritardo minimi
  - Importo minimo dovuto
  - Includi soci sospesi
  - Stato associato

**Tabella Risultati**:
- Colonne: Nome, Cognome, Importo Dovuto, Giorni Ritardo, Ultima Fattura
- Ordinamento per importo/giorni
- Totale crediti
- Numero soci coinvolti

**Azioni**:
- Export elenco per solleciti
- Invio email automatiche
- Stampa lettere di sollecito
- Aggiornamento stato soci

## Flussi di Navigazione

### Navigazione Principale
- **Sidebar Sempre Visibile**: Menu principale con sezioni collassabili
- **Breadcrumb**: Percorso di navigazione in ogni pagina
- **Ricerca Globale**: Barra ricerca associati sempre accessibile
- **Shortcuts Tastiera**: Combinazioni rapide per azioni frequenti

### Pattern di Interazione Ricorrenti

#### Gestione Liste
1. **Caricamento Pagina**: Visualizzazione lista con filtri di default
2. **Applicazione Filtri**: Aggiornamento in tempo reale dei risultati
3. **Selezione Record**: Click su riga per apertura dettaglio
4. **Azioni Bulk**: Selezione multipla per operazioni di massa
5. **Paginazione**: Controlli per navigazione tra pagine

#### Gestione Schede Dettaglio
1. **Visualizzazione**: Dati organizzati in sezioni logiche
2. **Modalità Modifica**: Attivazione editing con pulsante "Modifica"
3. **Validazione**: Controlli in tempo reale durante inserimento
4. **Salvataggio**: Conferma modifiche con feedback visivo
5. **Navigazione**: Possibilità di passare tra record correlati

#### Gestione Form
1. **Validazione Preventiva**: Controlli durante digitazione
2. **Campi Obbligatori**: Evidenziazione visiva chiara
3. **Suggerimenti**: Tooltip e placeholder informativi
4. **Salvataggio Automatico**: Bozze per form complessi
5. **Conferme**: Dialog per azioni irreversibili

## Elementi UI Ricorrenti

### Componenti Standard

#### Tabelle Dati
- **Header Fisso**: Intestazioni sempre visibili durante scroll
- **Ordinamento**: Click su colonna per ordinamento ascendente/discendente
- **Filtri Colonna**: Filtri specifici per ogni colonna
- **Azioni Riga**: Menu contestuale per ogni record
- **Selezione Multipla**: Checkbox per operazioni bulk

#### Form di Input
- **Layout Responsive**: Adattamento automatico a dimensione schermo
- **Validazione Real-time**: Feedback immediato su errori
- **Campi Dipendenti**: Aggiornamento automatico campi correlati
- **Salvataggio Progressivo**: Salvataggio automatico bozze
- **Reset Intelligente**: Ripristino valori precedenti

#### Modali e Dialog
- **Overlay Scuro**: Background semi-trasparente
- **Chiusura Multipla**: ESC, click esterno, pulsante X
- **Focus Management**: Gestione automatica focus
- **Dimensioni Adattive**: Ridimensionamento per contenuto
- **Animazioni Fluide**: Transizioni smooth per apertura/chiusura

### Stati Visivi

#### Indicatori di Stato
- **Colori Semantici**: Verde (attivo), Rosso (scaduto), Giallo (attenzione)
- **Icone Descrittive**: Simboli universalmente riconoscibili
- **Badge Numerici**: Contatori per elementi in attesa
- **Progress Bar**: Indicatori di completamento processi
- **Loading Spinner**: Feedback per operazioni in corso

#### Feedback Utente
- **Toast Notifications**: Messaggi temporanei non invasivi
- **Alert Banner**: Avvisi persistenti per situazioni critiche
- **Inline Messages**: Feedback contestuale nei form
- **Status Bar**: Informazioni di stato sempre visibili
- **Confirmation Dialog**: Conferme per azioni critiche

## Responsive Design

### Breakpoint e Layout

#### Desktop (≥1200px)
- **Sidebar Fissa**: Menu navigazione sempre visibile
- **Layout Multi-colonna**: Sfruttamento spazio orizzontale
- **Tabelle Complete**: Visualizzazione tutte le colonne
- **Modali Centrate**: Dialog al centro schermo
- **Tooltip Hover**: Informazioni aggiuntive al passaggio mouse

#### Tablet (768px-1199px)
- **Sidebar Collassabile**: Menu nascondibile per spazio
- **Layout Adattivo**: Riorganizzazione elementi
- **Tabelle Scrollabili**: Scroll orizzontale per tabelle larghe
- **Touch Friendly**: Elementi dimensionati per touch
- **Orientamento Adattivo**: Supporto portrait/landscape

#### Mobile (<768px)
- **Menu Hamburger**: Navigazione nascosta in drawer
- **Layout Verticale**: Stack elementi uno sotto l'altro
- **Tabelle Card**: Trasformazione tabelle in card
- **Swipe Gestures**: Navigazione con gesti touch
- **Bottom Navigation**: Menu principale in basso

### Ottimizzazioni Mobile

#### Performance
- **Lazy Loading**: Caricamento progressivo contenuti
- **Image Optimization**: Immagini ottimizzate per dispositivo
- **Caching Intelligente**: Cache locale per dati frequenti
- **Offline Support**: Funzionalità base offline
- **Progressive Web App**: Installazione come app nativa

#### Usabilità
- **Touch Targets**: Elementi touch di almeno 44px
- **Scroll Momentum**: Scroll fluido e naturale
- **Pull to Refresh**: Aggiornamento con gesto pull
- **Haptic Feedback**: Feedback tattile per azioni
- **Voice Input**: Supporto input vocale per ricerche

## Accessibilità e Inclusività

### Standard WCAG 2.1 AA

#### Perceivabilità
- **Contrasto Colori**: Rapporto minimo 4.5:1 per testo normale
- **Testo Ridimensionabile**: Zoom fino al 200% senza perdita funzionalità
- **Contenuto Non-testuale**: Alt text per immagini e icone
- **Sottotitoli**: Per contenuti video/audio
- **Orientamento**: Supporto portrait e landscape

#### Operabilità
- **Navigazione Tastiera**: Tutti gli elementi accessibili via tastiera
- **Nessun Limite Tempo**: O possibilità di estensione
- **Controllo Animazioni**: Possibilità disabilitare animazioni
- **Focus Visibile**: Indicatori chiari per elemento attivo
- **Shortcut Personalizzabili**: Combinazioni tasti configurabili

#### Comprensibilità
- **Linguaggio Semplice**: Terminologia chiara e consistente
- **Etichette Descrittive**: Label significative per form
- **Messaggi Errore**: Spiegazioni chiare e soluzioni
- **Istruzioni**: Guidance per processi complessi
- **Glossario**: Definizioni per termini tecnici

#### Robustezza
- **Markup Semantico**: HTML strutturato correttamente
- **Screen Reader**: Compatibilità con lettori schermo
- **Browser Support**: Funzionamento su browser principali
- **Graceful Degradation**: Funzionalità base anche senza JavaScript
- **API Accessibility**: Supporto tecnologie assistive

## Considerazioni Tecniche

### Performance e Ottimizzazione

#### Metriche Target
- **First Contentful Paint**: <1.5 secondi
- **Largest Contentful Paint**: <2.5 secondi
- **First Input Delay**: <100 millisecondi
- **Cumulative Layout Shift**: <0.1
- **Time to Interactive**: <3 secondi

#### Strategie Ottimizzazione
- **Code Splitting**: Caricamento modulare del codice
- **Tree Shaking**: Eliminazione codice non utilizzato
- **Compression**: Gzip/Brotli per risorse statiche
- **CDN**: Distribuzione contenuti geograficamente
- **Service Workers**: Caching avanzato e offline support

### Sicurezza Frontend

#### Protezione Dati
- **HTTPS Only**: Comunicazioni sempre crittografate
- **CSP Headers**: Content Security Policy restrittive
- **XSS Prevention**: Sanitizzazione input utente
- **CSRF Protection**: Token per form critici
- **Session Management**: Gestione sicura sessioni utente

#### Privacy
- **GDPR Compliance**: Conformità regolamento europeo
- **Cookie Consent**: Gestione consensi cookie
- **Data Minimization**: Raccolta solo dati necessari
- **Right to Erasure**: Possibilità cancellazione dati
- **Audit Trail**: Log delle operazioni sensibili

## Roadmap e Evoluzioni Future

### Fase 1: Core Functionality (Q1 2025)
- ✅ Gestione Anagrafica completa
- ✅ Servizi e Prestazioni base
- ✅ Contabilità essenziale
- ✅ Report fondamentali
- ✅ Responsive design

### Fase 2: Advanced Features (Q2 2025)
- 🔄 Dashboard avanzata con KPI
- 🔄 Workflow automatizzati
- 🔄 Integrazione sistemi pagamento
- 🔄 Notifiche push
- 🔄 Export avanzati

### Fase 3: Mobile & Integration (Q3 2025)
- 📋 App mobile nativa
- 📋 API pubbliche
- 📋 Integrazione sistemi esterni
- 📋 Sincronizzazione offline
- 📋 Geolocalizzazione servizi

### Fase 4: AI & Analytics (Q4 2025)
- 📋 Predizioni e suggerimenti AI
- 📋 Analytics avanzate
- 📋 Chatbot assistenza
- 📋 Automazione processi
- 📋 Business intelligence

---

**Documento Versione 2.0.0**  
*Ultima modifica: 5 Agosto 2025*

*Questo documento definisce l'architettura UI/UX del sistema UMAMI e deve essere utilizzato come riferimento per lo sviluppo frontend. Aggiornamenti e modifiche devono essere documentati e approvati dal team di progetto.*
