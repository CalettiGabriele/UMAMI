# UMAMI - Specifica UI/UX e Flussi di Lavoro

**Version:** 1.0.0  
**Last Updated:** 2025-08-01

## Introduzione

Questo documento descrive l'architettura dell'interfaccia utente e i flussi di lavoro per il sistema gestionale UMAMI. L'analisi si concentra sui processi operativi e sui percorsi utente necessari per gestire efficacemente un'associazione sportiva dilettantistica.

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
│ • Dashboard                       │                 │
│ • Associati                       │                 │
│ • Servizi                         │                 │
│ • Contabilità                     │                 │
│ • Report                          │                 │
│ • Configurazioni                  │                 │
└─────────────────────────────────────────────────────┘
```

### Componenti Ricorrenti
- **Tabelle con Filtri**: Liste paginabili con ricerca e filtri avanzati
- **Form Modali**: Creazione/modifica rapida senza cambio pagina
- **Card Informative**: Visualizzazione riassuntiva di dati complessi
- **Wizard Multi-step**: Processi complessi suddivisi in passaggi
- **Dashboard Widget**: Metriche e KPI in tempo reale

## Flussi di Lavoro Principali

### 1. Gestione Associati

#### 1.1 Iscrizione Nuovo Socio
**Attori**: Segreteria  
**Frequenza**: Quotidiana  
**Complessità**: Media

**Flusso Standard**:
1. **Accesso Sezione Associati**
   - Click su "Associati" nella sidebar
   - Visualizzazione lista associati esistenti

2. **Avvio Creazione**
   - Click su "Nuovo Associato" (CTA prominente)
   - Apertura form di inserimento

3. **Inserimento Dati Anagrafici**
   - Form con validazione in tempo reale
   - Campi obbligatori evidenziati
   - Controllo codice fiscale duplicato

4. **Gestione Gruppo Familiare** (opzionale)
   - Toggle "Parte di gruppo familiare"
   - Ricerca e selezione socio pagante
   - Visualizzazione membri gruppo esistente

5. **Conferma e Salvataggio**
   - Riepilogo dati inseriti
   - Conferma creazione
   - Redirect a scheda associato creato

**Varianti del Flusso**:
- **Socio Minorenne**: Richiesta obbligatoria socio pagante
- **Dati Incompleti**: Salvataggio bozza con promemoria
- **Socio Esistente**: Avviso duplicato con opzione merge

#### 1.2 Tesseramento FIV
**Attori**: Segreteria  
**Frequenza**: Stagionale  
**Complessità**: Bassa

**Flusso**:
1. **Accesso Scheda Associato**
   - Ricerca associato (nome/codice fiscale)
   - Click su risultato ricerca

2. **Sezione Tesseramento**
   - Tab "Tesseramento FIV" nella scheda
   - Visualizzazione stato attuale

3. **Inserimento/Aggiornamento Dati**
   - Form con campi specifici FIV
   - Validazione numero tessera
   - Calcolo automatico scadenze

4. **Conferma**
   - Salvataggio immediato
   - Aggiornamento stato visivo
   - Notifica successo

#### 1.3 Gestione Chiavi Elettroniche
**Attori**: Segreteria  
**Frequenza**: Occasionale  
**Complessità**: Bassa

**Flusso**:
1. **Accesso da Scheda Associato**
   - Tab "Chiave Elettronica"
   - Visualizzazione stato attuale

2. **Configurazione Chiave**
   - Inserimento codice chiave
   - Impostazione stato (attiva/disattiva)
   - Gestione crediti docce

3. **Ricarica Crediti** (sub-flusso)
   - Click "Ricarica Crediti"
   - Inserimento importo
   - Conferma transazione
   - Aggiornamento saldo

### 2. Gestione Servizi

#### 2.1 Assegnazione Servizio Fisico
**Attori**: Segreteria  
**Frequenza**: Quotidiana  
**Complessità**: Media

**Flusso**:
1. **Visualizzazione Servizi Disponibili**
   - Sezione "Servizi Fisici"
   - Griglia con stato visivo (disponibile/occupato/manutenzione)
   - Filtri per tipo servizio

2. **Selezione Servizio**
   - Click su servizio disponibile
   - Apertura dettagli servizio

3. **Assegnazione a Socio**
   - Click "Assegna"
   - Ricerca socio destinatario
   - Selezione periodo validità

4. **Configurazione Assegnazione**
   - Definizione anno competenza
   - Conferma prezzo applicato
   - Note aggiuntive (opzionale)

5. **Conferma**
   - Riepilogo assegnazione
   - Salvataggio
   - Aggiornamento stato servizio

#### 2.2 Iscrizione a Prestazione
**Attori**: Segreteria, Istruttori  
**Frequenza**: Quotidiana  
**Complessità**: Bassa

**Flusso**:
1. **Selezione Prestazione**
   - Sezione "Prestazioni"
   - Lista corsi/eventi disponibili
   - Visualizzazione posti disponibili

2. **Iscrizione Socio**
   - Click "Iscriviti" su prestazione
   - Ricerca e selezione socio
   - Verifica prerequisiti (età, livello, etc.)

3. **Conferma Iscrizione**
   - Riepilogo prestazione e costi
   - Conferma iscrizione
   - Aggiornamento posti disponibili

### 3. Gestione Contabile

#### 3.1 Generazione Fatture Periodiche
**Attori**: Amministrazione  
**Frequenza**: Mensile/Trimestrale  
**Complessità**: Alta

**Flusso**:
1. **Accesso Generazione Fatture**
   - Sezione "Contabilità" > "Genera Fatture"
   - Selezione periodo fatturazione

2. **Configurazione Parametri**
   - Selezione servizi da fatturare
   - Filtri per tipo socio/servizio
   - Anteprima importi

3. **Revisione Pre-generazione**
   - Lista associati da fatturare
   - Dettaglio servizi per associato
   - Possibilità esclusioni manuali

4. **Generazione Batch**
   - Avvio processo generazione
   - Progress bar con stato
   - Log operazioni

5. **Revisione Post-generazione**
   - Riepilogo fatture create
   - Gestione errori/eccezioni
   - Invio automatico (opzionale)

#### 3.2 Registrazione Pagamento
**Attori**: Segreteria, Amministrazione  
**Frequenza**: Quotidiana  
**Complessità**: Bassa

**Flusso**:
1. **Identificazione Fattura**
   - Ricerca per numero fattura/socio
   - Visualizzazione fatture non pagate
   - Selezione fattura target

2. **Inserimento Pagamento**
   - Form pagamento con dati fattura
   - Selezione metodo pagamento
   - Inserimento data e importo

3. **Riconciliazione**
   - Verifica corrispondenza importi
   - Gestione pagamenti parziali
   - Note aggiuntive

4. **Conferma**
   - Salvataggio pagamento
   - Aggiornamento stato fattura
   - Generazione ricevuta (opzionale)

### 4. Reporting e Monitoraggio

#### 4.1 Report Soci Morosi
**Attori**: Amministrazione  
**Frequenza**: Settimanale  
**Complessità**: Bassa

**Flusso**:
1. **Accesso Report**
   - Sezione "Report" > "Soci Morosi"
   - Configurazione parametri filtro

2. **Personalizzazione Criteri**
   - Giorni di scadenza minima
   - Importo minimo dovuto
   - Inclusione soci sospesi

3. **Generazione Report**
   - Elaborazione dati
   - Visualizzazione risultati tabellari
   - Metriche aggregate (totale crediti, numero soci)

4. **Azioni Conseguenti**
   - Export per solleciti
   - Invio comunicazioni
   - Aggiornamento stati soci

#### 4.2 Monitoraggio Certificati Medici
**Attori**: Segreteria  
**Frequenza**: Mensile  
**Complessità**: Bassa

**Flusso**:
1. **Dashboard Scadenze**
   - Widget certificati in scadenza
   - Indicatori visivi per urgenza
   - Filtro per giorni alla scadenza

2. **Dettaglio Scadenze**
   - Lista soci con certificati in scadenza
   - Ordinamento per data scadenza
   - Informazioni contatto

3. **Azioni di Follow-up**
   - Invio promemoria automatici
   - Registrazione comunicazioni
   - Aggiornamento stati tesseramento

## Pattern di Interazione

### Ricerca e Filtri
- **Ricerca Globale**: Barra ricerca sempre visibile per associati
- **Filtri Contestuali**: Filtri specifici per ogni sezione
- **Ricerca Incrementale**: Risultati in tempo reale durante digitazione
- **Filtri Salvati**: Possibilità salvare combinazioni filtri frequenti

### Gestione Errori
- **Validazione Preventiva**: Controlli in tempo reale sui form
- **Messaggi Chiari**: Spiegazione errori in linguaggio comprensibile
- **Recupero Graceful**: Possibilità correzione senza perdita dati
- **Conferme Critiche**: Dialog di conferma per azioni irreversibili

### Feedback Utente
- **Loading States**: Indicatori progresso per operazioni lunghe
- **Notifiche Toast**: Conferme successo/errore non invasive
- **Stati Visivi**: Indicatori chiari per stati record (attivo/sospeso/scaduto)
- **Breadcrumb**: Navigazione contestuale sempre visibile

## Responsive Design

### Breakpoint Principali
- **Desktop**: ≥1200px - Layout completo con sidebar
- **Tablet**: 768px-1199px - Sidebar collassabile, layout adattivo
- **Mobile**: <768px - Navigazione mobile, layout verticale

### Priorità Mobile
- **Ricerca Rapida**: Accesso immediato a ricerca associati
- **Azioni Critiche**: Registrazione pagamenti, iscrizioni urgenti
- **Consultazione**: Visualizzazione dati associato, servizi
- **Notifiche**: Alert per scadenze e azioni richieste

## Accessibilità

### Standard di Conformità
- **WCAG 2.1 AA**: Conformità standard internazionali
- **Navigazione Tastiera**: Tutti gli elementi accessibili via tastiera
- **Screen Reader**: Supporto completo per lettori schermo
- **Contrasto**: Rapporti colore conformi alle linee guida

### Considerazioni Specifiche
- **Etichette Descrittive**: Label chiare per tutti i form
- **Struttura Semantica**: HTML semantico per navigazione assistita
- **Focus Management**: Gestione focus per modali e wizard
- **Testi Alternativi**: Descrizioni per elementi grafici e icone

## Metriche di Successo

### KPI Usabilità
- **Task Completion Rate**: >95% per operazioni principali
- **Time on Task**: <2 minuti per iscrizione nuovo socio
- **Error Rate**: <5% errori utente su form critici
- **User Satisfaction**: Score >4/5 su questionari usabilità

### Metriche Performance
- **Page Load Time**: <2 secondi per pagine principali
- **Time to Interactive**: <3 secondi su connessioni 3G
- **Core Web Vitals**: Conformità standard Google
- **Uptime**: >99.5% disponibilità sistema

## Considerazioni Future

### Evoluzione Funzionale
- **App Mobile Nativa**: Per soci e istruttori
- **Integrazione Pagamenti**: Gateway pagamento online
- **Comunicazioni Automatiche**: SMS/Email per scadenze
- **Dashboard Soci**: Area riservata per consultazione dati

### Scalabilità
- **Multi-tenant**: Supporto multiple associazioni
- **Personalizzazione**: Temi e configurazioni per associazione
- **Integrazione Esterna**: API per sistemi federali/regionali
- **Analytics Avanzate**: Business intelligence e predittive

---

*Questo documento rappresenta la base per lo sviluppo dell'interfaccia utente del sistema UMAMI. Deve essere aggiornato iterativamente basandosi sui feedback degli utenti e sui test di usabilità.*
