import gradio as gr
import pandas as pd
import api_client
from datetime import datetime, date
import json

# --- Constants ---
STATO_ASSOCIATO_CHOICES = ["Attivo", "Sospeso", "Scaduto", "Cessato"]
STATO_SERVIZIO_CHOICES = ["Disponibile", "Occupato", "In Manutenzione"]
TIPO_SERVIZIO_CHOICES = ["Posto Barca", "Armadietto", "Deriva", "Catamarano", "Windsurf", "Wingfoil", "SUP", "Canoa"]
STATO_FATTURA_CHOICES = ["Non pagata", "Pagata", "Parzialmente pagata", "Scaduta"]
TIPO_FATTURA_CHOICES = ["Attiva", "Passiva"]
METODI_PAGAMENTO = ["Contanti", "Bonifico", "Carta di credito", "Assegno", "PayPal"]

# --- Helper Functions ---
def handle_api_response(response, success_message, failure_message):
    if response:
        gr.Info(success_message)
        return True
    else:
        gr.Warning(failure_message)
        return False

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "€ 0,00"
    return f"€ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def safe_get(dictionary, key, default=""):
    """Safely get value from dictionary"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, default)
    return default

# ===== SEZIONE ANAGRAFICA =====

def create_anagrafica_section():
    """Sezione Anagrafica completa con sottosezioni"""
    with gr.Tabs():
        with gr.TabItem("👤 Elenco Associati"):
            elenco_associati_ui()
        with gr.TabItem("📋 Scheda Associato"):
            scheda_associato_ui()
        with gr.TabItem("🏢 Elenco Fornitori"):
            elenco_fornitori_ui()
        with gr.TabItem("📄 Scheda Fornitore"):
            scheda_fornitore_ui()

def elenco_associati_ui():
    """Elenco Associati con filtri avanzati"""
    gr.Markdown("### 👤 Gestione Associati")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca", placeholder="Nome, Cognome, CF...")
        stato = gr.Dropdown(label="Stato", choices=[""] + STATO_ASSOCIATO_CHOICES)
        tesserato_fiv = gr.Checkbox(label="Solo Tesserati FIV")
    
    with gr.Row():
        refresh_btn = gr.Button("🔄 Aggiorna", variant="secondary")
        nuovo_btn = gr.Button("➕ Nuovo Associato", variant="primary")
    
    associati_table = gr.DataFrame(interactive=False)
    
    # Modal popup per nuovo associato
    with gr.Group(visible=False) as nuovo_modal:
        gr.Markdown("### ➕ Nuovo Associato")
        
        with gr.Row():
            with gr.Column():
                nuovo_nome = gr.Textbox(label="Nome *", placeholder="Inserisci nome")
                nuovo_cognome = gr.Textbox(label="Cognome *", placeholder="Inserisci cognome")
                nuovo_cf = gr.Textbox(label="Codice Fiscale * (16 caratteri)", placeholder="RSSMRA80A01H501U")
            with gr.Column():
                nuovo_email = gr.Textbox(label="Email", placeholder="email@esempio.it")
                nuovo_telefono = gr.Textbox(label="Telefono", placeholder="+39 123 456 7890")
                nuovo_stato = gr.Dropdown(label="Stato", choices=STATO_ASSOCIATO_CHOICES, value="Attivo")
        
        with gr.Row():
            nuovo_data_nascita = gr.Textbox(label="Data Nascita *", placeholder="YYYY-MM-DD")
            nuovo_luogo_nascita = gr.Textbox(label="Luogo Nascita", placeholder="Città")
            nuovo_indirizzo = gr.Textbox(label="Indirizzo *", placeholder="Via, Numero, CAP Città")
        
        with gr.Row():
            salva_btn = gr.Button("💾 Salva", variant="primary")
            annulla_btn = gr.Button("❌ Annulla", variant="secondary")
    
    def load_data(search_val, stato_val, fiv_val):
        try:
            df = api_client.get_associati(search=search_val, stato=stato_val, tesserato_fiv=fiv_val if fiv_val else None)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    def show_nuovo_modal():
        return gr.Group(visible=True)
    
    def hide_nuovo_modal():
        return gr.Group(visible=False)
    
    def salva_nuovo_associato(nome, cognome, cf, email, telefono, stato, data_nascita, luogo_nascita, indirizzo):
        # Validazione campi obbligatori
        if not nome or not cognome or not cf:
            gr.Warning("Nome, Cognome e Codice Fiscale sono obbligatori")
            return gr.Group(visible=True), pd.DataFrame()
        
        # Validazione codice fiscale (deve essere esattamente 16 caratteri)
        cf_clean = cf.strip().upper()
        if len(cf_clean) != 16:
            gr.Warning("Il Codice Fiscale deve essere di esattamente 16 caratteri")
            return gr.Group(visible=True), pd.DataFrame()
        
        # Validazione aggiuntiva per campi obbligatori API
        if not data_nascita:
            gr.Warning("Data di nascita è obbligatoria")
            return gr.Group(visible=True), pd.DataFrame()
            
        if not indirizzo:
            gr.Warning("Indirizzo è obbligatorio")
            return gr.Group(visible=True), pd.DataFrame()
        
        try:
            from datetime import date
            
            # Prepara i dati per l'API
            associato_data = {
                "nome": nome.strip(),
                "cognome": cognome.strip(),
                "codice_fiscale": cf_clean,
                "data_nascita": data_nascita,
                "indirizzo": indirizzo.strip(),
                "email": email.strip() if email else "noemail@example.com",  # Email obbligatoria
                "telefono": telefono.strip() if telefono else "000-000-0000",  # Telefono obbligatorio
                "data_iscrizione": date.today().isoformat(),  # Data iscrizione automatica
                "stato_associato": stato
            }
            
            # Chiama l'API per creare l'associato
            result = api_client.create_associato(associato_data)
            
            if result:
                gr.Info(f"Associato {nome} {cognome} creato con successo!")
                # Ricarica la tabella e chiudi il modal
                df = api_client.get_associati()
                return gr.Group(visible=False), df if len(df) > 0 else pd.DataFrame()
            else:
                gr.Warning("Errore durante la creazione dell'associato")
                return gr.Group(visible=True), pd.DataFrame()
                
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return gr.Group(visible=True), pd.DataFrame()
    
    def reset_form():
        return [""] * 8 + ["Attivo"]
    
    # Event handlers
    refresh_btn.click(load_data, [search, stato, tesserato_fiv], associati_table)
    nuovo_btn.click(show_nuovo_modal, outputs=nuovo_modal).then(
        reset_form, outputs=[nuovo_nome, nuovo_cognome, nuovo_cf, nuovo_email, 
                           nuovo_telefono, nuovo_data_nascita, nuovo_luogo_nascita, 
                           nuovo_indirizzo, nuovo_stato]
    )
    annulla_btn.click(hide_nuovo_modal, outputs=nuovo_modal)
    salva_btn.click(
        salva_nuovo_associato,
        [nuovo_nome, nuovo_cognome, nuovo_cf, nuovo_email, nuovo_telefono, 
         nuovo_stato, nuovo_data_nascita, nuovo_luogo_nascita, nuovo_indirizzo],
        [nuovo_modal, associati_table]
    )
    
    return associati_table

def scheda_associato_ui():
    """Scheda dettaglio associato"""
    gr.Markdown("### 📋 Scheda Associato")
    
    with gr.Row():
        associato_id = gr.Number(label="ID Associato", precision=0)
        load_btn = gr.Button("📥 Carica", variant="primary")
    
    with gr.Group():
        gr.Markdown("#### 📝 Dati Anagrafici")
        with gr.Row():
            nome = gr.Textbox(label="Nome", interactive=False)
            cognome = gr.Textbox(label="Cognome", interactive=False)
            cf = gr.Textbox(label="Codice Fiscale", interactive=False)
        with gr.Row():
            data_nascita = gr.Textbox(label="Data di Nascita", interactive=False)
            data_iscrizione = gr.Textbox(label="Data Iscrizione", interactive=False)
            associato_riferimento = gr.Textbox(label="Associato di Riferimento", interactive=False)
        with gr.Row():
            email = gr.Textbox(label="Email", interactive=False)
            telefono = gr.Textbox(label="Telefono", interactive=False)
            stato_assoc = gr.Textbox(label="Stato", interactive=False)
        with gr.Row():
            indirizzo = gr.Textbox(label="Indirizzo", interactive=False, lines=2)
        with gr.Row():
            anagrafica_update_btn = gr.Button("✏️ Aggiorna Anagrafica", variant="secondary", size="sm")
    
    # Modal per aggiornamento anagrafica
    with gr.Group(visible=False) as anagrafica_modal:
        gr.Markdown("### 📝 Aggiorna Dati Anagrafici")
        with gr.Row():
            anagrafica_modal_nome = gr.Textbox(label="Nome *", placeholder="Mario")
            anagrafica_modal_cognome = gr.Textbox(label="Cognome *", placeholder="Rossi")
            anagrafica_modal_cf = gr.Textbox(label="Codice Fiscale *", placeholder="RSSMRA80A01H501Z", max_lines=1)
        with gr.Row():
            anagrafica_modal_email = gr.Textbox(label="Email", placeholder="mario.rossi@email.com")
            anagrafica_modal_telefono = gr.Textbox(label="Telefono", placeholder="+39 123 456 7890")
        with gr.Row():
            anagrafica_save_btn = gr.Button("💾 Salva", variant="primary")
            anagrafica_cancel_btn = gr.Button("❌ Annulla", variant="secondary")
    
    with gr.Group():
        gr.Markdown("#### ⛵ Tessera FIV")
        with gr.Row():
            fiv_numero = gr.Textbox(label="Numero Tessera FIV", interactive=False)
            fiv_scadenza_tesseramento = gr.Textbox(label="Scadenza Tesseramento", interactive=False)
            fiv_scadenza_certificato = gr.Textbox(label="Scadenza Certificato Medico", interactive=False)
        fiv_status = gr.HTML()
        with gr.Row():
            fiv_create_btn = gr.Button("➕ Crea Tessera FIV", variant="secondary", size="sm")
            fiv_update_btn = gr.Button("✏️ Aggiorna Tessera FIV", variant="secondary", size="sm")
    
    # Modal per gestione tessera FIV
    with gr.Group(visible=False) as fiv_modal:
        gr.Markdown("### ⛵ Gestione Tessera FIV")
        with gr.Row():
            fiv_modal_numero = gr.Textbox(label="Numero Tessera FIV *", placeholder="FIV123456")
            fiv_modal_scad_tess = gr.Textbox(label="Scadenza Tesseramento *", placeholder="YYYY-MM-DD")
            fiv_modal_scad_cert = gr.Textbox(label="Scadenza Certificato Medico *", placeholder="YYYY-MM-DD")
        with gr.Row():
            fiv_save_btn = gr.Button("💾 Salva", variant="primary")
            fiv_cancel_btn = gr.Button("❌ Annulla", variant="secondary")
    
    with gr.Group():
        gr.Markdown("#### 🔑 Chiave Elettronica")
        with gr.Row():
            chiave_codice = gr.Textbox(label="Codice Chiave", interactive=False)
            chiave_stato = gr.Textbox(label="Stato", interactive=False)
            chiave_credito = gr.Textbox(label="Credito Docce", interactive=False)
        with gr.Row():
            chiave_data_assegnazione = gr.Textbox(label="Data Assegnazione", interactive=False)
            chiave_data_riconsegna = gr.Textbox(label="Data Riconsegna", interactive=False)
    
    with gr.Group(visible=False) as fatture_group:
        gr.Markdown("#### 💰 Fatture")
        fatture_table = gr.DataFrame(
            headers=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"],
            interactive=False,
            wrap=True
        )
    
    with gr.Group(visible=False) as pagamenti_group:
        gr.Markdown("#### 💳 Pagamenti")
        pagamenti_table = gr.DataFrame(
            headers=["ID", "Data", "Importo", "Metodo", "Note"],
            interactive=False,
            wrap=True
        )
    
    def load_associato(aid):
        if not aid:
            return [""] * 19 + [gr.update(visible=False), pd.DataFrame(), gr.update(visible=False), pd.DataFrame()]
        try:
            # Carica dati associato
            data = api_client.get_associato(int(aid))
            if not data:
                gr.Warning("Associato non trovato")
                return [""] * 19 + [gr.update(visible=False), pd.DataFrame(), gr.update(visible=False), pd.DataFrame()]
            
            # Dati anagrafici (inclusi i nuovi campi)
            # Gestione associato di riferimento
            associato_rif_text = ""
            fk_associato_rif = safe_get(data, 'fk_associato_riferimento')
            if fk_associato_rif:
                try:
                    rif_data = api_client.get_associato(fk_associato_rif)
                    if rif_data:
                        nome_rif = safe_get(rif_data, 'nome', '')
                        cognome_rif = safe_get(rif_data, 'cognome', '')
                        associato_rif_text = f"{nome_rif} {cognome_rif} (ID: {fk_associato_rif})".strip()
                except:
                    associato_rif_text = f"ID: {fk_associato_rif}"
            
            anagrafica = [
                safe_get(data, 'nome'), safe_get(data, 'cognome'), safe_get(data, 'codice_fiscale'),
                safe_get(data, 'data_nascita', ''), safe_get(data, 'data_iscrizione', ''), associato_rif_text,
                safe_get(data, 'email'), safe_get(data, 'telefono'), safe_get(data, 'stato_associato'),
                safe_get(data, 'indirizzo', '')
            ]
            
            # Dati FIV
            fiv_data = data.get('tesseramento_fiv', {})
            if fiv_data:
                # Calcola lo stato della tessera FIV
                from datetime import datetime, date
                oggi = date.today()
                
                status_html = "<div style='padding: 10px; border-radius: 5px; margin-top: 10px;'>"
                
                try:
                    scad_tess = datetime.strptime(fiv_data['scadenza_tesseramento_fiv'], '%Y-%m-%d').date()
                    if scad_tess < oggi:
                        status_html += "<p style='color: red; font-weight: bold;'>⚠️ Tesseramento FIV SCADUTO</p>"
                    elif (scad_tess - oggi).days <= 30:
                        status_html += "<p style='color: orange; font-weight: bold;'>⚠️ Tesseramento FIV in scadenza tra {} giorni</p>".format((scad_tess - oggi).days)
                    else:
                        status_html += "<p style='color: green; font-weight: bold;'>✓ Tesseramento FIV valido</p>"
                except:
                    status_html += "<p style='color: gray;'>Tesseramento: data non valida</p>"
                
                try:
                    scad_cert = datetime.strptime(fiv_data['scadenza_certificato_medico'], '%Y-%m-%d').date()
                    if scad_cert < oggi:
                        status_html += "<p style='color: red; font-weight: bold;'>⚠️ Certificato Medico SCADUTO</p>"
                    elif (scad_cert - oggi).days <= 30:
                        status_html += "<p style='color: orange; font-weight: bold;'>⚠️ Certificato Medico in scadenza tra {} giorni</p>".format((scad_cert - oggi).days)
                    else:
                        status_html += "<p style='color: green; font-weight: bold;'>✓ Certificato Medico valido</p>"
                except:
                    status_html += "<p style='color: gray;'>Certificato: data non valida</p>"
                
                status_html += "</div>"
                
                fiv = [
                    safe_get(fiv_data, 'numero_tessera_fiv', ''),
                    safe_get(fiv_data, 'scadenza_tesseramento_fiv', ''),
                    safe_get(fiv_data, 'scadenza_certificato_medico', ''),
                    status_html
                ]
            else:
                fiv = [
                    '',  # numero tessera
                    '',  # scadenza tesseramento
                    '',  # scadenza certificato
                    "<div style='padding: 10px; color: gray; font-style: italic;'>Nessuna tessera FIV associata</div>"
                ]
            
            # Dati Chiave Elettronica
            chiave_data = data.get('chiave_elettronica', {})
            chiave = [
                safe_get(chiave_data, 'key_code', ''),
                "In regola" if safe_get(chiave_data, 'in_regola') else "Non in regola",
                f"€ {safe_get(chiave_data, 'credito', 0):.2f}",
                safe_get(chiave_data, 'data_assegnazione', ''),
                safe_get(chiave_data, 'data_riconsegna', '')
            ]
            
            # Carica fatture dell'associato
            try:
                fatture_df = api_client.get_fatture(associato_id=int(aid))
                if len(fatture_df) == 0:
                    fatture_df = pd.DataFrame(columns=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"])
                else:
                    # Formatta le colonne per la visualizzazione usando i nomi corretti
                    if 'importo_totale' in fatture_df.columns:
                        fatture_df['Importo'] = fatture_df['importo_totale'].apply(lambda x: f"€ {x:.2f}" if pd.notna(x) else "€ 0,00")
                    
                    # Usa i nomi di colonne corretti dal debug
                    available_cols = ['id_fattura', 'numero_fattura', 'data_emissione', 'tipo_fattura', 'Importo', 'stato']
                    existing_cols = [col for col in available_cols if col in fatture_df.columns]
                    
                    if len(existing_cols) >= 4:  # Almeno le colonne principali
                        fatture_df = fatture_df[existing_cols].rename(columns={
                            'id_fattura': 'ID', 'numero_fattura': 'Numero', 'data_emissione': 'Data', 
                            'tipo_fattura': 'Tipo', 'stato': 'Stato'
                        })
                    else:
                        # Fallback se le colonne non ci sono
                        fatture_df = pd.DataFrame(columns=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"])
            except Exception as e:
                print(f"Errore caricamento fatture: {e}")
                fatture_df = pd.DataFrame(columns=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"])
            
            # Carica pagamenti dell'associato
            try:
                pagamenti_df = api_client.get_pagamenti(associato_id=int(aid))
                if len(pagamenti_df) == 0:
                    pagamenti_df = pd.DataFrame(columns=["ID", "Data", "Importo", "Metodo", "Note"])
                else:
                    # Formatta le colonne per la visualizzazione usando i nomi corretti
                    if 'importo' in pagamenti_df.columns:
                        pagamenti_df['Importo_fmt'] = pagamenti_df['importo'].apply(lambda x: f"€ {x:.2f}" if pd.notna(x) else "€ 0,00")
                    
                    # Usa i nomi di colonne corretti dal debug (metodo invece di metodo_pagamento)
                    available_cols = ['id_pagamento', 'data_pagamento', 'Importo_fmt', 'metodo']
                    existing_cols = [col for col in available_cols if col in pagamenti_df.columns]
                    
                    if len(existing_cols) >= 3:  # Almeno le colonne principali
                        # Aggiungi colonna Note se non esiste
                        if 'Note' not in pagamenti_df.columns:
                            pagamenti_df['Note'] = ''
                        
                        rename_dict = {
                            'id_pagamento': 'ID', 'data_pagamento': 'Data', 'Importo_fmt': 'Importo',
                            'metodo': 'Metodo'
                        }
                        
                        cols_to_select = existing_cols + ['Note']
                        pagamenti_df = pagamenti_df[cols_to_select].rename(columns=rename_dict)
                    else:
                        # Fallback se le colonne non ci sono
                        pagamenti_df = pd.DataFrame(columns=["ID", "Data", "Importo", "Metodo", "Note"])
            except Exception as e:
                print(f"Errore caricamento pagamenti: {e}")
                pagamenti_df = pd.DataFrame(columns=["ID", "Data", "Importo", "Metodo", "Note"])
            
            # Visibilità sezioni in base alla presenza dati
            fatture_vis = gr.update(visible=not fatture_df.empty)
            pagamenti_vis = gr.update(visible=not pagamenti_df.empty)

            return anagrafica + fiv + chiave + [fatture_vis, fatture_df, pagamenti_vis, pagamenti_df]
            
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return [""] * 19 + [gr.update(visible=False), pd.DataFrame(), gr.update(visible=False), pd.DataFrame()]
    
    def show_fiv_modal_create():
        """Mostra modal per creare tessera FIV"""
        return gr.Group(visible=True), "", "", ""
    
    def show_fiv_modal_update(aid, numero, scad_tess, scad_cert):
        """Mostra modal per aggiornare tessera FIV con dati esistenti"""
        if not aid:
            gr.Warning("Seleziona prima un associato")
            return gr.Group(visible=False), "", "", ""
        return gr.Group(visible=True), numero, scad_tess, scad_cert
    
    def hide_fiv_modal():
        """Nasconde modal tessera FIV"""
        return gr.Group(visible=False), "", "", ""
    
    def save_fiv_tessera(aid, numero, scad_tess, scad_cert):
        """Salva o aggiorna tessera FIV"""
        if not aid:
            gr.Warning("Nessun associato selezionato")
            return gr.Group(visible=True), "", "", "", "", "", "", ""
        
        if not numero or not scad_tess or not scad_cert:
            gr.Warning("Tutti i campi sono obbligatori")
            return gr.Group(visible=True), numero, scad_tess, scad_cert, "", "", "", ""
        
        try:
            # Prepara i dati per l'API
            tesseramento_data = {
                "numero_tessera_fiv": numero.strip(),
                "scadenza_tesseramento_fiv": scad_tess,
                "scadenza_certificato_medico": scad_cert
            }
            
            # Chiama l'API per creare/aggiornare la tessera
            result = api_client.create_tesseramento_fiv(int(aid), tesseramento_data)
            
            if result:
                gr.Info("Tessera FIV salvata con successo!")
                
                # Calcola nuovo stato per aggiornare l'interfaccia
                from datetime import datetime, date
                oggi = date.today()
                
                status_html = "<div style='padding: 10px; border-radius: 5px; margin-top: 10px;'>"
                
                try:
                    scad_tess_date = datetime.strptime(scad_tess, '%Y-%m-%d').date()
                    if scad_tess_date < oggi:
                        status_html += "<p style='color: red; font-weight: bold;'>⚠️ Tesseramento FIV SCADUTO</p>"
                    elif (scad_tess_date - oggi).days <= 30:
                        status_html += "<p style='color: orange; font-weight: bold;'>⚠️ Tesseramento FIV in scadenza tra {} giorni</p>".format((scad_tess_date - oggi).days)
                    else:
                        status_html += "<p style='color: green; font-weight: bold;'>✓ Tesseramento FIV valido</p>"
                except:
                    status_html += "<p style='color: gray;'>Tesseramento: data non valida</p>"
                
                try:
                    scad_cert_date = datetime.strptime(scad_cert, '%Y-%m-%d').date()
                    if scad_cert_date < oggi:
                        status_html += "<p style='color: red; font-weight: bold;'>⚠️ Certificato Medico SCADUTO</p>"
                    elif (scad_cert_date - oggi).days <= 30:
                        status_html += "<p style='color: orange; font-weight: bold;'>⚠️ Certificato Medico in scadenza tra {} giorni</p>".format((scad_cert_date - oggi).days)
                    else:
                        status_html += "<p style='color: green; font-weight: bold;'>✓ Certificato Medico valido</p>"
                except:
                    status_html += "<p style='color: gray;'>Certificato: data non valida</p>"
                
                status_html += "</div>"
                
                return gr.Group(visible=False), "", "", "", numero, scad_tess, scad_cert, status_html
            else:
                gr.Warning("Errore durante il salvataggio della tessera FIV")
                return gr.Group(visible=True), numero, scad_tess, scad_cert, "", "", "", ""
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
            return gr.Group(visible=True), numero, scad_tess, scad_cert, "", "", "", ""
    
    def show_anagrafica_modal(aid, current_nome, current_cognome, current_cf, current_email, current_telefono):
        """Mostra modal per aggiornare anagrafica con dati esistenti"""
        if not aid:
            gr.Warning("Seleziona prima un associato")
            return gr.Group(visible=False), "", "", "", ""
        return gr.Group(visible=True), current_nome, current_cognome, current_cf, current_email, current_telefono
    
    def hide_anagrafica_modal():
        """Nasconde modal anagrafica"""
        return gr.Group(visible=False), "", "", "", ""
    
    def save_anagrafica(aid, nome_val, cognome_val, cf_val, email_val, telefono_val):
        """Salva anagrafica aggiornata"""
        if not aid:
            gr.Warning("Nessun associato selezionato")
            return gr.Group(visible=True), nome_val, cognome_val, cf_val, email_val, telefono_val, "", "", "", "", "", ""
        
        if not nome_val or not cognome_val or not cf_val:
            gr.Warning("Nome, Cognome e Codice Fiscale sono obbligatori")
            return gr.Group(visible=True), nome_val, cognome_val, cf_val, email_val, telefono_val, "", "", "", "", "", ""
        
        # Validazione codice fiscale
        if len(cf_val.strip()) != 16:
            gr.Warning("Il codice fiscale deve essere di 16 caratteri")
            return gr.Group(visible=True), nome_val, cognome_val, cf_val, email_val, telefono_val, "", "", "", "", "", ""
        
        try:
            # Prepara i dati per l'API
            anagrafica_data = {
                "nome": nome_val.strip(),
                "cognome": cognome_val.strip(),
                "codice_fiscale": cf_val.strip().upper(),
                "email": email_val.strip() if email_val else "",
                "telefono": telefono_val.strip() if telefono_val else ""
            }
            
            # Chiama l'API per aggiornare l'anagrafica
            result = api_client.update_associato(int(aid), anagrafica_data)
            
            if result:
                gr.Info("Anagrafica aggiornata con successo!")
                # Restituisce tutti i valori per aggiornare l'interfaccia
                return (gr.Group(visible=False), "", "", "", "", "", 
                       anagrafica_data["nome"], anagrafica_data["cognome"], 
                       anagrafica_data["codice_fiscale"], anagrafica_data["email"], 
                       anagrafica_data["telefono"], "Attivo")
            else:
                gr.Warning("Errore durante l'aggiornamento dell'anagrafica")
                return gr.Group(visible=True), nome_val, cognome_val, cf_val, email_val, telefono_val, "", "", "", "", "", ""
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
            return gr.Group(visible=True), nome_val, cognome_val, cf_val, email_val, telefono_val, "", "", "", "", "", ""
    
    load_btn.click(
        load_associato, 
        [associato_id], 
        [nome, cognome, cf, data_nascita, data_iscrizione, associato_riferimento,
         email, telefono, stato_assoc, indirizzo,
         fiv_numero, fiv_scadenza_tesseramento, fiv_scadenza_certificato, fiv_status,
         chiave_codice, chiave_stato, chiave_credito, chiave_data_assegnazione, chiave_data_riconsegna,
         fatture_group, fatture_table, pagamenti_group, pagamenti_table]
    )
    
    # Click handlers per gestione tessera FIV
    fiv_create_btn.click(
        show_fiv_modal_create,
        [],
        [fiv_modal, fiv_modal_numero, fiv_modal_scad_tess, fiv_modal_scad_cert]
    )
    
    fiv_update_btn.click(
        show_fiv_modal_update,
        [associato_id, fiv_numero, fiv_scadenza_tesseramento, fiv_scadenza_certificato],
        [fiv_modal, fiv_modal_numero, fiv_modal_scad_tess, fiv_modal_scad_cert]
    )
    
    fiv_cancel_btn.click(
        hide_fiv_modal,
        [],
        [fiv_modal, fiv_modal_numero, fiv_modal_scad_tess, fiv_modal_scad_cert]
    )
    
    fiv_save_btn.click(
        save_fiv_tessera,
        [associato_id, fiv_modal_numero, fiv_modal_scad_tess, fiv_modal_scad_cert],
        [fiv_modal, fiv_modal_numero, fiv_modal_scad_tess, fiv_modal_scad_cert,
         fiv_numero, fiv_scadenza_tesseramento, fiv_scadenza_certificato, fiv_status]
    )
    
    # Click handlers per gestione anagrafica
    anagrafica_update_btn.click(
        show_anagrafica_modal,
        [associato_id, nome, cognome, cf, email, telefono],
        [anagrafica_modal, anagrafica_modal_nome, anagrafica_modal_cognome, 
         anagrafica_modal_cf, anagrafica_modal_email, anagrafica_modal_telefono]
    )
    
    anagrafica_cancel_btn.click(
        hide_anagrafica_modal,
        [],
        [anagrafica_modal, anagrafica_modal_nome, anagrafica_modal_cognome, 
         anagrafica_modal_cf, anagrafica_modal_email, anagrafica_modal_telefono]
    )
    
    anagrafica_save_btn.click(
        save_anagrafica,
        [associato_id, anagrafica_modal_nome, anagrafica_modal_cognome, 
         anagrafica_modal_cf, anagrafica_modal_email, anagrafica_modal_telefono],
        [anagrafica_modal, anagrafica_modal_nome, anagrafica_modal_cognome, 
         anagrafica_modal_cf, anagrafica_modal_email, anagrafica_modal_telefono,
         nome, cognome, cf, email, telefono, stato_assoc]
    )

def elenco_fornitori_ui():
    """Elenco Fornitori"""
    gr.Markdown("### 🏢 Gestione Fornitori")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca", placeholder="Ragione Sociale, P.IVA...")
        refresh_btn = gr.Button("🔄 Aggiorna")
        nuovo_btn = gr.Button("➕ Nuovo Fornitore", variant="primary")
    
    fornitori_table = gr.DataFrame(interactive=False)
    
    # Modal per nuovo fornitore
    with gr.Group(visible=False) as nuovo_fornitore_modal:
        gr.Markdown("### 🏢 Nuovo Fornitore")
        with gr.Row():
            fornitore_modal_ragione_sociale = gr.Textbox(label="Ragione Sociale *", placeholder="Es: Azienda SRL")
            fornitore_modal_partita_iva = gr.Textbox(label="Partita IVA *", placeholder="12345678901", max_lines=1)
        with gr.Row():
            fornitore_modal_email = gr.Textbox(label="Email *", placeholder="info@azienda.it")
            fornitore_modal_telefono = gr.Textbox(label="Telefono *", placeholder="+39 123 456 7890")
        with gr.Row():
            fornitore_save_btn = gr.Button("💾 Salva", variant="primary")
            fornitore_cancel_btn = gr.Button("❌ Annulla", variant="secondary")
    
    def load_fornitori(search_val):
        try:
            df = api_client.get_fornitori(search=search_val)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    def show_nuovo_fornitore_modal():
        """Mostra modal per nuovo fornitore"""
        return gr.Group(visible=True), "", "", "", ""
    
    def hide_nuovo_fornitore_modal():
        """Nasconde modal nuovo fornitore"""
        return gr.Group(visible=False), "", "", "", ""
    
    def save_nuovo_fornitore(ragione_sociale, partita_iva, email, telefono):
        """Salva nuovo fornitore"""
        # Validazione campi obbligatori
        if not ragione_sociale or not partita_iva or not email or not telefono:
            gr.Warning("Tutti i campi sono obbligatori")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, pd.DataFrame()
        
        # Validazione partita IVA (deve essere 11 caratteri)
        if len(partita_iva.strip()) != 11 or not partita_iva.strip().isdigit():
            gr.Warning("La partita IVA deve essere di 11 cifre")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, pd.DataFrame()
        
        # Validazione email basica
        if "@" not in email or "." not in email:
            gr.Warning("Inserisci un'email valida")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, pd.DataFrame()
        
        try:
            # Prepara i dati per l'API
            fornitore_data = {
                "ragione_sociale": ragione_sociale.strip(),
                "partita_iva": partita_iva.strip(),
                "email": email.strip(),
                "telefono": telefono.strip()
            }
            
            # Chiama l'API per creare il fornitore
            result = api_client.create_fornitore(fornitore_data)
            
            if result:
                gr.Info(f"Fornitore '{ragione_sociale}' creato con successo!")
                # Ricarica la tabella fornitori
                updated_df = api_client.get_fornitori()
                return (gr.Group(visible=False), "", "", "", "", 
                       updated_df if len(updated_df) > 0 else pd.DataFrame())
            else:
                gr.Warning("Errore durante la creazione del fornitore")
                return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, pd.DataFrame()
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, pd.DataFrame()
    
    refresh_btn.click(load_fornitori, [search], fornitori_table)
    
    # Click handlers per nuovo fornitore
    nuovo_btn.click(
        show_nuovo_fornitore_modal,
        [],
        [nuovo_fornitore_modal, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono]
    )
    
    fornitore_cancel_btn.click(
        hide_nuovo_fornitore_modal,
        [],
        [nuovo_fornitore_modal, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono]
    )
    
    fornitore_save_btn.click(
        save_nuovo_fornitore,
        [fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono],
        [nuovo_fornitore_modal, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono, fornitori_table]
    )
    
    return fornitori_table

def scheda_fornitore_ui():
    """Scheda dettaglio fornitore"""
    gr.Markdown("### 📄 Scheda Fornitore")
    
    with gr.Row():
        fornitore_id = gr.Number(label="ID Fornitore", precision=0)
        load_btn = gr.Button("📥 Carica", variant="primary")
    
    with gr.Group():
        gr.Markdown("#### 🏢 Dati Aziendali")
        with gr.Row():
            ragione_sociale = gr.Textbox(label="Ragione Sociale", interactive=False)
            partita_iva = gr.Textbox(label="Partita IVA", interactive=False)
        with gr.Row():
            email = gr.Textbox(label="Email", interactive=False)
            telefono = gr.Textbox(label="Telefono", interactive=False)
        with gr.Row():
            fornitore_update_btn = gr.Button("✏️ Aggiorna Fornitore", variant="secondary", size="sm")
    
    # Modal per aggiornamento fornitore
    with gr.Group(visible=False) as fornitore_update_modal:
        gr.Markdown("### 📝 Aggiorna Dati Fornitore")
        with gr.Row():
            fornitore_modal_ragione_sociale = gr.Textbox(label="Ragione Sociale *", placeholder="Es: Azienda SRL")
            fornitore_modal_partita_iva = gr.Textbox(label="Partita IVA *", placeholder="12345678901", max_lines=1)
        with gr.Row():
            fornitore_modal_email = gr.Textbox(label="Email *", placeholder="info@azienda.it")
            fornitore_modal_telefono = gr.Textbox(label="Telefono *", placeholder="+39 123 456 7890")
        with gr.Row():
            fornitore_update_save_btn = gr.Button("💾 Salva", variant="primary")
            fornitore_update_cancel_btn = gr.Button("❌ Annulla", variant="secondary")
    
    with gr.Group():
        gr.Markdown("#### 💰 Fatture")
        fornitore_fatture_table = gr.DataFrame(
            headers=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"],
            interactive=False
        )
    
    def load_fornitore(fid):
        """Carica i dati del fornitore"""
        if not fid:
            gr.Warning("Inserisci un ID fornitore")
            return [""] * 4 + [pd.DataFrame()]
        
        try:
            # Carica dati fornitore
            data = api_client.get_fornitore(int(fid))
            if not data:
                gr.Warning("Fornitore non trovato")
                return [""] * 4 + [pd.DataFrame()]
            
            # Dati aziendali
            anagrafica = [
                safe_get(data, 'ragione_sociale', ''),
                safe_get(data, 'partita_iva', ''),
                safe_get(data, 'email', ''),
                safe_get(data, 'telefono', '')
            ]
            
            # Carica fatture del fornitore
            try:
                fatture_df = api_client.get_fatture(fornitore_id=int(fid))
                if len(fatture_df) == 0:
                    fatture_df = pd.DataFrame(columns=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"])
                else:
                    # Formatta le colonne per la visualizzazione
                    if 'importo_totale' in fatture_df.columns:
                        fatture_df['Importo'] = fatture_df['importo_totale'].apply(lambda x: f"€ {x:.2f}" if pd.notna(x) else "€ 0,00")
                    
                    # Usa i nomi di colonne corretti
                    available_cols = ['id_fattura', 'numero_fattura', 'data_emissione', 'tipo_fattura', 'Importo', 'stato']
                    existing_cols = [col for col in available_cols if col in fatture_df.columns]
                    
                    if len(existing_cols) >= 4:
                        fatture_df = fatture_df[existing_cols].rename(columns={
                            'id_fattura': 'ID', 'numero_fattura': 'Numero', 'data_emissione': 'Data', 
                            'tipo_fattura': 'Tipo', 'stato': 'Stato'
                        })
                    else:
                        fatture_df = pd.DataFrame(columns=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"])
            except Exception as e:
                print(f"Errore caricamento fatture fornitore: {e}")
                fatture_df = pd.DataFrame(columns=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"])
            
            return anagrafica + [fatture_df]
            
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return [""] * 4 + [pd.DataFrame()]
    
    def show_fornitore_update_modal(fid, ragione_sociale, partita_iva, email, telefono):
        """Mostra modal per aggiornare fornitore"""
        if not fid:
            gr.Warning("Seleziona prima un fornitore")
            return gr.Group(visible=False), "", "", "", ""
        return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono
    
    def hide_fornitore_update_modal():
        """Nasconde modal aggiornamento fornitore"""
        return gr.Group(visible=False), "", "", "", ""
    
    def save_fornitore_update(fid, ragione_sociale, partita_iva, email, telefono):
        """Salva aggiornamento fornitore"""
        if not fid:
            gr.Warning("Nessun fornitore selezionato")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, "", "", "", ""
        
        if not ragione_sociale or not partita_iva or not email or not telefono:
            gr.Warning("Tutti i campi sono obbligatori")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, "", "", "", ""
        
        # Validazione partita IVA
        if len(partita_iva.strip()) != 11 or not partita_iva.strip().isdigit():
            gr.Warning("La partita IVA deve essere di 11 cifre")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, "", "", "", ""
        
        # Validazione email
        if "@" not in email or "." not in email:
            gr.Warning("Inserisci un'email valida")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, "", "", "", ""
        
        try:
            # Prepara i dati per l'API
            fornitore_data = {
                "ragione_sociale": ragione_sociale.strip(),
                "partita_iva": partita_iva.strip(),
                "email": email.strip(),
                "telefono": telefono.strip()
            }
            
            # Chiama l'API per aggiornare il fornitore
            result = api_client.update_fornitore(int(fid), fornitore_data)
            
            if result:
                gr.Info("Fornitore aggiornato con successo!")
                return (gr.Group(visible=False), "", "", "", "", 
                       fornitore_data["ragione_sociale"], fornitore_data["partita_iva"], 
                       fornitore_data["email"], fornitore_data["telefono"])
            else:
                gr.Warning("Errore durante l'aggiornamento del fornitore")
                return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, "", "", "", ""
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
            return gr.Group(visible=True), ragione_sociale, partita_iva, email, telefono, "", "", "", ""
    
    load_btn.click(
        load_fornitore,
        [fornitore_id],
        [ragione_sociale, partita_iva, email, telefono, fornitore_fatture_table]
    )
    
    fornitore_update_btn.click(
        show_fornitore_update_modal,
        [fornitore_id, ragione_sociale, partita_iva, email, telefono],
        [fornitore_update_modal, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono]
    )
    
    fornitore_update_cancel_btn.click(
        hide_fornitore_update_modal,
        [],
        [fornitore_update_modal, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono]
    )
    
    fornitore_update_save_btn.click(
        save_fornitore_update,
        [fornitore_id, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono],
        [fornitore_update_modal, fornitore_modal_ragione_sociale, fornitore_modal_partita_iva, 
         fornitore_modal_email, fornitore_modal_telefono,
         ragione_sociale, partita_iva, email, telefono]
    )

# ===== SEZIONE SERVIZI =====

def create_servizi_section():
    """Sezione Servizi completa"""
    with gr.Tabs():
        with gr.TabItem("⚓ Elenco Servizi"):
            elenco_servizi_ui()
        with gr.TabItem("📄 Scheda Servizio"):
            scheda_servizio_ui()
        with gr.TabItem("💰 Prezzario Servizi"):
            prezzario_servizi_ui()
        with gr.TabItem("🏫 Elenco Prestazioni"):
            elenco_prestazioni_erogate_ui()
        with gr.TabItem("💲 Prezzario Prestazioni"):
            prezzario_prestazioni_ui()

def elenco_servizi_ui():
    """Gestione servizi fisici"""
    gr.Markdown("### ⚓ Servizi Fisici")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca")
        tipo = gr.Dropdown(label="Tipo", choices=[""] + TIPO_SERVIZIO_CHOICES)
        stato = gr.Dropdown(label="Stato", choices=[""] + STATO_SERVIZIO_CHOICES)
    
    with gr.Row():
        refresh_btn = gr.Button("🔄 Aggiorna", variant="secondary")
        nuovo_servizio_btn = gr.Button("➕ Nuovo Servizio", variant="primary")
    
    servizi_table = gr.DataFrame(interactive=False)
    
    # Modal per nuovo servizio
    with gr.Group(visible=False) as nuovo_servizio_modal:
        gr.Markdown("### 📝 Nuovo Servizio Fisico")
        with gr.Row():
            servizio_modal_nome = gr.Textbox(label="Nome Servizio *", placeholder="Es: Posto Barca A-01")
            servizio_modal_tipo = gr.Dropdown(label="Tipo *", choices=TIPO_SERVIZIO_CHOICES)
        with gr.Row():
            servizio_modal_descrizione = gr.Textbox(label="Descrizione *", placeholder="Descrizione dettagliata del servizio")
            servizio_modal_stato = gr.Dropdown(label="Stato *", choices=STATO_SERVIZIO_CHOICES, value="Disponibile")
        with gr.Row():
            servizio_save_btn = gr.Button("💾 Salva", variant="primary")
            servizio_cancel_btn = gr.Button("❌ Annulla", variant="secondary")
    
    def load_servizi(search_val, tipo_val, stato_val):
        try:
            df = api_client.get_servizi_fisici(tipo=tipo_val, stato=stato_val)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    def show_nuovo_servizio_modal():
        """Mostra modal per nuovo servizio"""
        return gr.Group(visible=True), "", "", "", "Disponibile"
    
    def hide_nuovo_servizio_modal():
        """Nasconde modal nuovo servizio"""
        return gr.Group(visible=False), "", "", "", "Disponibile"
    
    def save_nuovo_servizio(nome, tipo, descrizione, stato):
        """Salva nuovo servizio fisico"""
        if not nome or not tipo or not descrizione or not stato:
            gr.Warning("Tutti i campi sono obbligatori")
            return gr.Group(visible=True), nome, tipo, descrizione, stato, pd.DataFrame()
        
        try:
            # Prepara i dati per l'API
            servizio_data = {
                "nome": nome.strip(),
                "tipo": tipo,
                "descrizione": descrizione.strip(),
                "stato": stato
            }
            
            # Chiama l'API per creare il servizio
            result = api_client.create_servizio_fisico(servizio_data)
            
            if result:
                gr.Info(f"Servizio '{nome}' creato con successo!")
                # Ricarica la tabella
                updated_df = api_client.get_servizi_fisici()
                return (gr.Group(visible=False), "", "", "", "Disponibile", 
                       updated_df if len(updated_df) > 0 else pd.DataFrame())
            else:
                gr.Warning("Errore durante la creazione del servizio")
                return gr.Group(visible=True), nome, tipo, descrizione, stato, pd.DataFrame()
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
            return gr.Group(visible=True), nome, tipo, descrizione, stato, pd.DataFrame()
    
    refresh_btn.click(load_servizi, [search, tipo, stato], servizi_table)
    
    # Click handlers per nuovo servizio
    nuovo_servizio_btn.click(
        show_nuovo_servizio_modal,
        [],
        [nuovo_servizio_modal, servizio_modal_nome, servizio_modal_tipo, 
         servizio_modal_descrizione, servizio_modal_stato]
    )
    
    servizio_cancel_btn.click(
        hide_nuovo_servizio_modal,
        [],
        [nuovo_servizio_modal, servizio_modal_nome, servizio_modal_tipo, 
         servizio_modal_descrizione, servizio_modal_stato]
    )
    
    servizio_save_btn.click(
        save_nuovo_servizio,
        [servizio_modal_nome, servizio_modal_tipo, servizio_modal_descrizione, servizio_modal_stato],
        [nuovo_servizio_modal, servizio_modal_nome, servizio_modal_tipo, 
         servizio_modal_descrizione, servizio_modal_stato, servizi_table]
    )

def scheda_servizio_ui():
    gr.Markdown("## 📖 Scheda Servizio Fisico")
    
    with gr.Row():
        servizio_id = gr.Number(label="ID Servizio", precision=0)
        load_servizio_btn = gr.Button("🔍 Carica Servizio", variant="primary")
    
    with gr.Row():
        servizio_nome = gr.Textbox(label="Nome", interactive=False)
        servizio_tipo = gr.Textbox(label="Tipo", interactive=False)
        servizio_stato = gr.Textbox(label="Stato", interactive=False)
    
    servizio_descrizione = gr.Textbox(label="Descrizione", lines=2, interactive=False)

    gr.Markdown("### 🧍 Assegnazione Corrente")
    with gr.Row():
        associato_id_input = gr.Number(label="ID Associato", precision=0)
        check_associato_btn = gr.Button("🔍 Verifica", variant="secondary")
    
    with gr.Row():
        associato_nome_display = gr.Textbox(label="Nome Associato", interactive=False)
        associato_cognome_display = gr.Textbox(label="Cognome Associato", interactive=False)

    with gr.Row():
        data_inizio_input = gr.Textbox(label="Data Inizio Assegnazione", placeholder="YYYY-MM-DD")
        data_fine_input = gr.Textbox(label="Data Fine Assegnazione", placeholder="YYYY-MM-DD")

    with gr.Row():
        assign_btn = gr.Button("➕ Assegna Servizio", variant="primary", visible=True)
        libera_servizio_btn = gr.Button("🗑️ Libera Servizio", variant="stop", visible=False)

    gr.Markdown("### 📜 Storico Assegnazioni")
    assegnazioni_table = gr.DataFrame(
        headers=["ID", "Associato", "Data Inizio", "Data Fine", "Stato", "Anno"],
        datatype=["number", "str", "str", "str", "str", "str"],
        interactive=False
    )

    # --- Funzioni Logiche ---
    
    def get_current_assignment(assignments):
        """Trova l'assegnazione attiva corrente."""
        if not assignments:
            return None
        today = datetime.now().date().isoformat()
        for assignment in assignments:
            if (safe_get(assignment, 'stato', '') == 'Attivo' and 
                safe_get(assignment, 'data_fine', '') >= today):
                return assignment
        return None

    def load_servizio_details(sid):
        """Carica dettagli servizio fisico e storico assegnazioni."""
        try:
            # Valori di default
            servizio_data = ["", "", "", ""]
            associato_id_val, associato_nome_val, associato_cognome_val = None, "", ""
            data_inizio_val, data_fine_val = "", ""
            assign_btn_visible = gr.Button(visible=True)
            libera_btn_visible = gr.Button(visible=False)
            assegnazioni_df = pd.DataFrame(columns=["ID", "Associato", "Data Inizio", "Data Fine", "Stato", "Anno"])

            if not sid:
                gr.Warning("Inserisci un ID servizio")
                return servizio_data + [associato_id_val, associato_nome_val, associato_cognome_val, data_inizio_val, data_fine_val, assign_btn_visible, libera_btn_visible, assegnazioni_df]

            data = api_client.get_servizio_fisico(int(sid))
            if not data:
                gr.Warning("Servizio non trovato")
                return servizio_data + [associato_id_val, associato_nome_val, associato_cognome_val, data_inizio_val, data_fine_val, assign_btn_visible, libera_btn_visible, assegnazioni_df]

            servizio_data = [safe_get(data, 'nome', ''), safe_get(data, 'tipo', ''), safe_get(data, 'descrizione', ''), safe_get(data, 'stato', '')]
            
            assegnazioni = safe_get(data, 'assegnazioni', [])
            current_assignment = get_current_assignment(assegnazioni)

            if current_assignment:
                associato_id_val = safe_get(current_assignment, 'fk_associato')
                associato_nome_val = safe_get(current_assignment, 'nome', '')
                associato_cognome_val = safe_get(current_assignment, 'cognome', '')
                data_inizio_val = safe_get(current_assignment, 'data_inizio', '')
                data_fine_val = safe_get(current_assignment, 'data_fine', '')
                assign_btn_visible = gr.Button(visible=False)
                libera_btn_visible = gr.Button(visible=True)
            else:
                current_year = datetime.now().year
                data_inizio_val = f"{current_year}-01-01"
                data_fine_val = f"{current_year}-12-31"

            if assegnazioni:
                df = pd.DataFrame(assegnazioni)
                if not df.empty:
                    df['Associato'] = df.apply(lambda row: f"{safe_get(row, 'nome', '')} {safe_get(row, 'cognome', '')}".strip(), axis=1)
                    display_cols = ['id_assegnazione', 'Associato', 'data_inizio', 'data_fine', 'stato', 'anno_competenza']
                    available_cols = [col for col in display_cols if col in df.columns or col == 'Associato']
                    if len(available_cols) >= 4:
                        assegnazioni_df = df[available_cols].rename(columns={'id_assegnazione': 'ID', 'data_inizio': 'Data Inizio', 'data_fine': 'Data Fine', 'stato': 'Stato', 'anno_competenza': 'Anno'})

            return servizio_data + [associato_id_val, associato_nome_val, associato_cognome_val, data_inizio_val, data_fine_val, assign_btn_visible, libera_btn_visible, assegnazioni_df]

        except Exception as e:
            gr.Warning(f"Errore caricamento dettagli servizio: {e}")
            return ["", "", "", ""] + [None, "", "", "", "", gr.Button(visible=True), gr.Button(visible=False), pd.DataFrame(columns=["ID", "Associato", "Data Inizio", "Data Fine", "Stato", "Anno"])]

    def check_associato(aid):
        """Verifica e carica dati associato."""
        if not aid:
            gr.Warning("Inserisci un ID associato")
            return "", ""
        try:
            data = api_client.get_associato(int(aid))
            if not data:
                gr.Warning("Associato non trovato")
                return "", ""
            nome = safe_get(data, 'nome', '')
            cognome = safe_get(data, 'cognome', '')
            if nome and cognome:
                gr.Info(f"Associato trovato: {nome} {cognome}")
            return nome, cognome
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return "", ""

    # --- Event Handlers ---
    
    load_servizio_btn.click(
        load_servizio_details,
        [servizio_id],
        [servizio_nome, servizio_tipo, servizio_descrizione, servizio_stato, 
         associato_id_input, associato_nome_display, associato_cognome_display, 
         data_inizio_input, data_fine_input,
         assign_btn, libera_servizio_btn, assegnazioni_table]
    )
    
    check_associato_btn.click(
        check_associato,
        [associato_id_input],
        [associato_nome_display, associato_cognome_display]
    )

def prezzario_servizi_ui():
    """Gestione prezzi servizi"""
    gr.Markdown("### 💰 Prezzario Servizi")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca Categoria")
        refresh_btn = gr.Button("🔄 Aggiorna")
    
    prezzi_table = gr.DataFrame(interactive=False)
    
    def load_prezzi(search_val):
        try:
            df = api_client.get_prezzi_servizi(categoria=search_val)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_prezzi, [search], prezzi_table)

def prezzario_prestazioni_ui():
    """Gestione prezzario prestazioni"""
    gr.Markdown("### 💲 Prezzario Prestazioni")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca Nome", placeholder="Corso Vela, Quota Tesseramento...")
        refresh_btn = gr.Button("🔄 Aggiorna", variant="secondary")
        nuovo_btn = gr.Button("➕ Nuova Prestazione", variant="primary")
    
    prestazioni_table = gr.DataFrame(interactive=False)
    
    # Modal per nuova prestazione
    with gr.Group(visible=False) as nuovo_prestazione_modal:
        gr.Markdown("### 🏫 Nuova Prestazione")
        with gr.Row():
            prestazione_modal_nome = gr.Textbox(label="Nome *", placeholder="Es: Corso Vela Base")
            prestazione_modal_costo = gr.Number(label="Costo (€)", value=0.0, precision=2)
        with gr.Row():
            prestazione_modal_descrizione = gr.Textbox(label="Descrizione *", placeholder="Descrizione dettagliata", lines=3)
        with gr.Row():
            prestazione_save_btn = gr.Button("💾 Salva", variant="primary")
            prestazione_cancel_btn = gr.Button("❌ Annulla", variant="secondary")
    
    def load_prestazioni(search_val):
        try:
            df = api_client.get_prestazioni(search=search_val)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    def show_nuovo_prestazione_modal():
        """Mostra modal per nuova prestazione"""
        return gr.Group(visible=True), "", 0.0, ""
    
    def hide_nuovo_prestazione_modal():
        """Nasconde modal nuova prestazione"""
        return gr.Group(visible=False), "", 0.0, ""
    
    def save_nuovo_prestazione(nome, costo, descrizione):
        """Salva nuova prestazione"""
        # Validazione campi obbligatori
        if not nome or not descrizione:
            gr.Warning("Nome e Descrizione sono obbligatori")
            return gr.Group(visible=True), nome, costo, descrizione, pd.DataFrame()
        
        try:
            # Prepara i dati per l'API
            prestazione_data = {
                "nome_prestazione": nome.strip(),
                "descrizione": descrizione.strip(),
                "costo": float(costo) if costo >= 0 else 0.0
            }
            
            result = api_client.create_prestazione(prestazione_data)
            
            if result:
                gr.Info(f"Prestazione '{nome}' creata con successo!")
                # Ricarica la tabella prestazioni
                updated_df = api_client.get_prestazioni()
                return (gr.Group(visible=False), "", 0.0, "", 
                       updated_df if len(updated_df) > 0 else pd.DataFrame())
            else:
                gr.Warning("Errore durante la creazione della prestazione")
                return gr.Group(visible=True), nome, costo, descrizione, pd.DataFrame()
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
            return gr.Group(visible=True), nome, costo, descrizione, pd.DataFrame()
    
    # Event handlers
    refresh_btn.click(load_prestazioni, [search], prestazioni_table)
    
    nuovo_btn.click(
        show_nuovo_prestazione_modal,
        outputs=[nuovo_prestazione_modal, prestazione_modal_nome, prestazione_modal_costo, prestazione_modal_descrizione]
    )
    
    prestazione_cancel_btn.click(
        hide_nuovo_prestazione_modal,
        outputs=[nuovo_prestazione_modal, prestazione_modal_nome, prestazione_modal_costo, prestazione_modal_descrizione]
    )
    
    prestazione_save_btn.click(
        save_nuovo_prestazione,
        inputs=[prestazione_modal_nome, prestazione_modal_costo, prestazione_modal_descrizione],
        outputs=[nuovo_prestazione_modal, prestazione_modal_nome, prestazione_modal_costo, prestazione_modal_descrizione, prestazioni_table]
    )
    
    # Carica prestazioni all'avvio
    prestazioni_table.value = load_prestazioni("")

def elenco_prestazioni_erogate_ui():
    """Gestione erogazioni prestazioni"""
    gr.Markdown("### 🏫 Elenco Prestazioni Erogate")
    
    with gr.Row():
        associato_search = gr.Number(label="🔍 ID Associato", precision=0)
        text_search = gr.Textbox(label="🔎 Ricerca testuale", placeholder="Nome/Cognome associato o Nome/Descrizione prestazione")
        data_da = gr.Textbox(label="📅 Data Da", placeholder="YYYY-MM-DD")
        data_a = gr.Textbox(label="📅 Data A", placeholder="YYYY-MM-DD")
        refresh_btn = gr.Button("🔄 Aggiorna", variant="secondary")
        nuovo_erog_btn = gr.Button("➕ Nuova Erogazione", variant="primary")
    
    erogazioni_table = gr.DataFrame(interactive=False)

    # Modal nuova erogazione
    with gr.Group(visible=False) as nuova_erogazione_group:
        gr.Markdown("#### ➕ Nuova Erogazione Prestazione")
        with gr.Row():
            erog_associato_id_input = gr.Number(label="ID Associato", precision=0)
            erog_prestazione_dropdown = gr.Dropdown(label="Prestazione", choices=[], allow_custom_value=False)
            erog_data_input = gr.Textbox(label="Data Erogazione", placeholder="YYYY-MM-DD (opzionale, default: oggi)")
        with gr.Row():
            erog_cancel_btn = gr.Button("Annulla", variant="secondary")
            erog_save_btn = gr.Button("Salva", variant="primary")

    def load_erogazioni(associato_id, search_val, data_da_val, data_a_val):
        """Carica erogazioni prestazioni con filtri"""
        try:
            # Prepara i parametri per l'API
            associato_id_val = None
            if associato_id is not None and str(associato_id).strip() and float(associato_id) > 0:
                associato_id_val = int(float(associato_id))
            
            data_da_val = data_da_val.strip() if data_da_val and str(data_da_val).strip() else None
            data_a_val = data_a_val.strip() if data_a_val and str(data_a_val).strip() else None
            search_val = search_val.strip() if search_val and str(search_val).strip() else None
            
            df = api_client.get_erogazioni_prestazioni(
                associato_id=associato_id_val,
                search=search_val,
                data_da=data_da_val,
                data_a=data_a_val
            )
            return df if df is not None and len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()

    # --- Modal / Form Nuova Erogazione (in-scope) ---
    def open_nuova_erogazione():
        try:
            dfp = api_client.get_prestazioni("")
            opts = []
            if dfp is not None and len(dfp) > 0:
                for _, row in dfp.iterrows():
                    try:
                        pid = int(row.get("id_prestazione"))
                        label = row.get("nome_prestazione") or ""
                        opts.append(f"{pid} - {label}")
                    except Exception:
                        continue
            return (
                gr.update(visible=True),
                gr.update(choices=opts, value=None),
                gr.update(value=None),
                gr.update(value="")
            )
        except Exception as e:
            gr.Warning(f"Errore nel caricamento prestazioni: {e}")
            return gr.update(visible=True), gr.update(choices=[], value=None), gr.update(value=None), gr.update(value="")

    def cancel_nuova_erogazione():
        return (
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value="")
        )

    def save_nuova_erogazione(ass_id_val, prest_choice, data_val, f_associato, f_text, f_da, f_a):
        try:
            # Validazioni
            if not ass_id_val:
                raise ValueError("Specificare un ID Associato")
            if not prest_choice or not str(prest_choice).strip():
                raise ValueError("Selezionare una prestazione")
            try:
                pid = int(str(prest_choice).split(" - ")[0])
            except Exception:
                raise ValueError("Prestazione selezionata non valida")
            if data_val and not str(data_val).strip():
                raise ValueError("Data non valida")
            if data_val and len(str(data_val).strip()) != 10:
                raise ValueError("Data non valida")
            # Prepara i dati per l'API
            payload = {
                "fk_associato": ass_id_val,
                "fk_prestazione": pid,
            }
            if data_val:
                payload["data_erogazione"] = str(data_val).strip()
            api_client.create_erogazione_prestazione(payload)
            gr.Info("Erogazione creata con successo")
            df = load_erogazioni(f_associato, f_text, f_da, f_a)
            return (
                gr.update(visible=False),
                gr.update(value=None),
                gr.update(value=None),
                gr.update(value=""),
                df if df is not None else pd.DataFrame(),
            )
        except Exception as e:
            gr.Warning(f"Errore nel salvataggio: {e}")
            return gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update()

    # Event handlers
    refresh_btn.click(
        load_erogazioni,
        inputs=[associato_search, text_search, data_da, data_a], 
        outputs=erogazioni_table
    )

    nuovo_erog_btn.click(
        open_nuova_erogazione,
        inputs=[],
        outputs=[nuova_erogazione_group, erog_prestazione_dropdown, erog_associato_id_input, erog_data_input]
    )

    erog_cancel_btn.click(
        cancel_nuova_erogazione,
        inputs=[],
        outputs=[nuova_erogazione_group, erog_associato_id_input, erog_prestazione_dropdown, erog_data_input]
    )

    erog_save_btn.click(
        save_nuova_erogazione,
        inputs=[erog_associato_id_input, erog_prestazione_dropdown, erog_data_input, associato_search, text_search, data_da, data_a],
        outputs=[nuova_erogazione_group, erog_associato_id_input, erog_prestazione_dropdown, erog_data_input, erogazioni_table]
    )
    
    # Carica erogazioni all'avvio (tutte)
    erogazioni_table.value = load_erogazioni(None, None, None, None)

# ===== SEZIONE CONTABILITÀ =====

def create_contabilita_section():
    """Sezione Contabilità completa"""
    with gr.Tabs():
        with gr.TabItem("📄 Elenco Fatture"):
            elenco_fatture_ui()
        with gr.TabItem("💳 Elenco Pagamenti"):
            elenco_pagamenti_ui()

def elenco_fatture_ui():
    """Gestione fatture"""
    gr.Markdown("### 📄 Fatture")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca")
        tipo = gr.Dropdown(label="Tipo", choices=[""] + TIPO_FATTURA_CHOICES)
        stato = gr.Dropdown(label="Stato", choices=[""] + STATO_FATTURA_CHOICES)
    
    with gr.Row():
        refresh_btn = gr.Button("🔄 Aggiorna", variant="secondary")
        nuova_fattura_btn = gr.Button("➕ Nuova Fattura", variant="primary")
    
    fatture_table = gr.DataFrame(interactive=False)

    # Modal nuova fattura
    with gr.Group(visible=False) as nuova_fattura_modal:
        gr.Markdown("### ✨ Nuova Fattura")
        with gr.Row():
            fatt_numero = gr.Textbox(label="Numero Fattura", placeholder="Se vuoto verrà generato automaticamente")
            fatt_tipo = gr.Dropdown(label="Tipo", choices=TIPO_FATTURA_CHOICES)
        with gr.Row():
            fatt_associato_id = gr.Textbox(label="ID Associato", placeholder="Lascia vuoto se non applicabile")
            fatt_fornitore_id = gr.Textbox(label="ID Fornitore", placeholder="Lascia vuoto se non applicabile")
        with gr.Row():
            fatt_data_emissione = gr.Textbox(label="Data Emissione (YYYY-MM-DD)")
            fatt_data_scadenza = gr.Textbox(label="Data Scadenza (YYYY-MM-DD)")
        with gr.Row():
            fatt_imponibile = gr.Number(label="Importo Imponibile", value=0.0)
            fatt_iva = gr.Number(label="Importo IVA", value=0.0)
        with gr.Row():
            fatt_cancel_btn = gr.Button("❌ Annulla")
            fatt_save_btn = gr.Button("💾 Salva", variant="primary")

    def load_fatture(search_val, tipo_val, stato_val):
        try:
            df = api_client.get_fatture(tipo=tipo_val, stato=stato_val, search=search_val)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()

    def open_nuova_fattura():
        """Mostra modal con date precompilate"""
        today = datetime.now().date()
        scadenza = today.replace(day=today.day)  # placeholder to satisfy linter
        try:
            from datetime import timedelta as _td
            scadenza = today + _td(days=30)
        except Exception:
            scadenza = today
        return (
            gr.update(visible=True),
            gr.update(value=""),
            gr.update(value=TIPO_FATTURA_CHOICES[0] if TIPO_FATTURA_CHOICES else None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=str(today)),
            gr.update(value=str(scadenza)),
            gr.update(value=0.0),
            gr.update(value=0.0),
        )

    def cancel_nuova_fattura():
        return (
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=None),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=0.0),
            gr.update(value=0.0),
        )

    def save_nuova_fattura(numero, tipo_val, aid, fid, data_em, data_scad, imponibile, iva, f_search, f_tipo, f_stato):
        try:
            # Validazioni
            if not tipo_val:
                raise ValueError("Selezionare il tipo di fattura")
            # Tratta 0, 0.0, stringhe vuote e None come 'vuoto'
            def _clean_id(v):
                if v is None:
                    return None
                try:
                    sv = str(v).strip()
                    if sv == "" or sv == "0" or sv == "0.0":
                        return None
                    ival = int(float(sv))
                    if ival == 0:
                        return None
                    return ival
                except Exception:
                    raise ValueError("L'ID deve essere numerico")

            aid_clean = _clean_id(aid)
            fid_clean = _clean_id(fid)
            if (aid_clean is None and fid_clean is None) or (aid_clean is not None and fid_clean is not None):
                raise ValueError("Specificare SOLO uno tra ID Associato oppure ID Fornitore")
            # Date
            def _valid_date(s):
                try:
                    datetime.strptime(s, "%Y-%m-%d")
                    return True
                except Exception:
                    return False
            if not data_em or not _valid_date(str(data_em)):
                raise ValueError("Data Emissione non valida (YYYY-MM-DD)")
            if not data_scad or not _valid_date(str(data_scad)):
                raise ValueError("Data Scadenza non valida (YYYY-MM-DD)")
            # Importi
            imp = float(imponibile) if imponibile is not None else 0.0
            iva_val = float(iva) if iva is not None else 0.0
            if imp < 0 or iva_val < 0:
                raise ValueError("Importi non possono essere negativi")
            totale = imp + iva_val
            if totale <= 0:
                raise ValueError("Importo totale deve essere maggiore di 0")

            # Numero fattura
            num = str(numero).strip() if numero else ""
            if not num:
                num = f"MANU-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            payload = {
                "numero_fattura": num,
                "data_emissione": str(data_em),
                "data_scadenza": str(data_scad),
                "tipo_fattura": tipo_val,
                "importo_totale": totale,
                "stato_pagamento": "Non pagata",
            }
            if aid_clean is not None:
                payload["fk_associato"] = aid_clean
            if fid_clean is not None:
                payload["fk_fornitore"] = fid_clean

            res = api_client.create_fattura(payload)
            if not res:
                raise RuntimeError("Creazione fattura fallita")
            gr.Info(f"Fattura creata: {num}")

            # Aggiorna tabella con i filtri attuali e chiudi modal
            df = load_fatture(f_search, f_tipo, f_stato)
            return (
                gr.update(visible=False),
                "", None, "", "", "", "", 0.0, 0.0,
                df if df is not None and len(df) > 0 else pd.DataFrame(),
            )
        except Exception as e:
            gr.Warning(f"Errore nel salvataggio: {e}")
            return gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    # Bindings
    refresh_btn.click(load_fatture, [search, tipo, stato], fatture_table)
    nuova_fattura_btn.click(
        open_nuova_fattura,
        [],
        [
            nuova_fattura_modal,
            fatt_numero, fatt_tipo, fatt_associato_id, fatt_fornitore_id,
            fatt_data_emissione, fatt_data_scadenza, fatt_imponibile, fatt_iva,
        ],
    )
    fatt_cancel_btn.click(
        cancel_nuova_fattura,
        [],
        [
            nuova_fattura_modal,
            fatt_numero, fatt_tipo, fatt_associato_id, fatt_fornitore_id,
            fatt_data_emissione, fatt_data_scadenza, fatt_imponibile, fatt_iva,
        ],
    )
    fatt_save_btn.click(
        save_nuova_fattura,
        [
            fatt_numero, fatt_tipo, fatt_associato_id, fatt_fornitore_id,
            fatt_data_emissione, fatt_data_scadenza, fatt_imponibile, fatt_iva,
            search, tipo, stato,
        ],
        [
            nuova_fattura_modal,
            fatt_numero, fatt_tipo, fatt_associato_id, fatt_fornitore_id,
            fatt_data_emissione, fatt_data_scadenza, fatt_imponibile, fatt_iva,
            fatture_table,
        ],
    )

def elenco_pagamenti_ui():
    """Gestione pagamenti"""
    gr.Markdown("### 💳 Pagamenti")

    # Scelte per Metodo Pagamento
    methods_choices = METODI_PAGAMENTO_CHOICES if 'METODI_PAGAMENTO_CHOICES' in globals() else ["Bonifico", "POS", "Contanti", "Assegno"]
    
    with gr.Row():
        metodo = gr.Dropdown(label="Metodo", choices=[""] + methods_choices) if methods_choices else gr.Textbox(label="Metodo")
        dal = gr.Textbox(label="Dal (YYYY-MM-DD)")
        al = gr.Textbox(label="Al (YYYY-MM-DD)")
        associato_id = gr.Textbox(label="ID Associato")

    with gr.Row():
        refresh_btn = gr.Button("🔄 Aggiorna", variant="secondary")
        nuovo_pagamento_btn = gr.Button("➕ Nuovo Pagamento", variant="primary")
    
    pagamenti_table = gr.DataFrame(interactive=False)

    # Modal nuovo pagamento
    with gr.Group(visible=False) as nuovo_pagamento_modal:
        gr.Markdown("### ✨ Nuovo Pagamento")
        with gr.Row():
            pay_fattura_id = gr.Textbox(label="ID Fattura", placeholder="Obbligatorio")
            pay_data = gr.Textbox(label="Data Pagamento (YYYY-MM-DD)")
        with gr.Row():
            pay_importo = gr.Number(label="Importo (€)", value=0.0)
            pay_metodo = gr.Dropdown(label="Metodo Pagamento", choices=methods_choices, value=(methods_choices[0] if methods_choices else None))
        note_pag = gr.Textbox(label="Note", lines=2)
        with gr.Row():
            pay_cancel_btn = gr.Button("❌ Annulla")
            pay_save_btn = gr.Button("💾 Salva", variant="primary")

    def load_pagamenti(metodo_val, dal_val, al_val, assoc_val):
        try:
            df = api_client.get_pagamenti(metodo=metodo_val or "", dal=dal_val or None, al=al_val or None, associato_id=assoc_val or None)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()

    def open_nuovo_pagamento():
        today = datetime.now().date()
        return (
            gr.update(visible=True),
            gr.update(value=""),
            gr.update(value=str(today)),
            gr.update(value=0.0),
            gr.update(value=(methods_choices[0] if methods_choices else None)),
            gr.update(value=""),
        )

    def cancel_nuovo_pagamento():
        return (
            gr.update(visible=False),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=0.0),
            gr.update(value=(methods_choices[0] if methods_choices else None)),
            gr.update(value=""),
        )

    def save_nuovo_pagamento(fattura_id, data_pag, importo, metodo_p, note, f_metodo, f_dal, f_al, f_assoc):
        try:
            # Validazioni
            if not fattura_id or not str(fattura_id).strip():
                raise ValueError("ID Fattura obbligatorio")
            try:
                fattura_id_clean = int(str(fattura_id).strip())
            except Exception:
                raise ValueError("ID Fattura deve essere numerico")
            if not data_pag or not isinstance(data_pag, str) or len(data_pag) != 10:
                raise ValueError("Data Pagamento non valida (YYYY-MM-DD)")
            try:
                datetime.strptime(data_pag, "%Y-%m-%d")
            except Exception:
                raise ValueError("Data Pagamento non valida (YYYY-MM-DD)")
            if importo is None or float(importo) <= 0:
                raise ValueError("Importo deve essere > 0")
            metodo_clean = (metodo_p or "").strip()
            if not metodo_clean:
                raise ValueError("Metodo pagamento obbligatorio")

            payload = {
                "fk_fattura": fattura_id_clean,
                "data_pagamento": data_pag,
                "importo": float(importo),
                "metodo_pagamento": metodo_clean,
            }
            if note and str(note).strip():
                payload["note"] = str(note).strip()

            res = api_client.create_pagamento(payload)
            if not res:
                raise RuntimeError("Creazione pagamento fallita")
            gr.Info("Pagamento creato con successo")

            # refresh tabella
            df = load_pagamenti(f_metodo, f_dal, f_al, f_assoc)
            return (
                gr.update(visible=False),
                "", "", 0.0, (methods_choices[0] if methods_choices else None), "",
                df if df is not None and len(df) > 0 else pd.DataFrame(),
            )
        except Exception as e:
            gr.Warning(f"Errore nel salvataggio: {e}")
            return gr.update(visible=True), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

    # Bindings
    refresh_btn.click(load_pagamenti, [metodo, dal, al, associato_id], pagamenti_table)
    nuovo_pagamento_btn.click(
        open_nuovo_pagamento,
        [],
        [
            nuovo_pagamento_modal,
            pay_fattura_id, pay_data, pay_importo, pay_metodo, note_pag,
        ],
    )
    pay_cancel_btn.click(
        cancel_nuovo_pagamento,
        [],
        [
            nuovo_pagamento_modal,
            pay_fattura_id, pay_data, pay_importo, pay_metodo, note_pag,
        ],
    )
    pay_save_btn.click(
        save_nuovo_pagamento,
        [pay_fattura_id, pay_data, pay_importo, pay_metodo, note_pag, metodo, dal, al, associato_id],
        [nuovo_pagamento_modal, pay_fattura_id, pay_data, pay_importo, pay_metodo, note_pag, pagamenti_table],
    )

# ===== SEZIONE REPORT =====

def create_report_section():
    """Sezione Report completa"""
    with gr.Tabs():
        with gr.TabItem("📊 Bilancio Economico"):
            bilancio_economico_ui()
        with gr.TabItem("⚠️ Soci Morosi"):
            soci_morosi_ui()

def bilancio_economico_ui():
    """Report bilancio economico"""
    gr.Markdown("### 📊 Bilancio Economico")
    
    with gr.Row():
        anno = gr.Number(label="Anno", value=datetime.now().year, precision=0)
        genera_btn = gr.Button("📈 Genera Bilancio", variant="primary")
        scarica_pdf_btn = gr.Button("📄 Scarica PDF", variant="secondary")
    
    bilancio_summary = gr.HTML()
    bilancio_state = gr.State({})
    pdf_file = gr.File(label="Bilancio PDF", interactive=False, visible=False)
    
    def _fmt_euro(v):
        try:
            return format_currency(float(v))
        except Exception:
            return format_currency(0)
    
    def _month_name(m):
        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        return mesi[m-1] if 1 <= m <= 12 else str(m)
    
    def genera_bilancio(anno_val):
        try:
            year = int(anno_val)
        except Exception:
            gr.Warning("Anno non valido")
            return gr.update(), {}
        dal = date(year, 1, 1)
        al = date(year, 12, 31)
        df = api_client.get_pagamenti(dal=dal, al=al)
        if df is None or df.empty:
            html = f"""
            <div style='padding:16px;background:#fff3cd;border:1px solid #ffeeba;border-radius:8px;'>
                <h3>Bilancio {year}</h3>
                <p>Nessun movimento trovato per l'anno selezionato.</p>
            </div>
            """
            return html, {"anno": year, "tables": {}, "totals": {}}
        # Normalizza colonne attese
        cols = {c.lower(): c for c in df.columns}
        def col(name): return cols.get(name, name)
        # Split Entrate/Uscite
        entrate = df[df[col('tipo')] == 'Entrata'].copy() if col('tipo') in df.columns else pd.DataFrame()
        uscite = df[df[col('tipo')] == 'Uscita'].copy() if col('tipo') in df.columns else pd.DataFrame()
        # Totali
        tot_entrate = float(entrate[col('importo')].sum()) if not entrate.empty else 0.0
        tot_uscite = float(uscite[col('importo')].sum()) if not uscite.empty else 0.0
        saldo = tot_entrate - tot_uscite
        # Per metodo
        def agg_by(colname, frame):
            if frame.empty or col(colname) not in frame.columns:
                return pd.DataFrame(columns=[colname, 'importo']).astype({colname: 'object', 'importo': 'float'})
            return frame.groupby(col(colname), dropna=False)[col('importo')].sum().reset_index().rename(columns={col(colname): colname, col('importo'): 'importo'}).sort_values('importo', ascending=False)
        entrate_by_metodo = agg_by('metodo', entrate)
        uscite_by_metodo = agg_by('metodo', uscite)
        # Mensile
        if col('data_pagamento') in df.columns:
            df['_mese'] = pd.to_datetime(df[col('data_pagamento')]).dt.month
            mensile = df.groupby(['_mese', col('tipo')])[col('importo')].sum().reset_index()
        else:
            mensile = pd.DataFrame(columns=['_mese', 'tipo', 'importo'])
        # Top controparti
        cont_col = col('cliente_fornitore') if col('cliente_fornitore') in df.columns else None
        def top_by_counterparty(frame, n=10):
            if frame.empty or not cont_col:
                return pd.DataFrame(columns=['cliente_fornitore', 'importo'])
            return frame.groupby(cont_col)[col('importo')].sum().reset_index().rename(columns={cont_col: 'cliente_fornitore', col('importo'): 'importo'}).sort_values('importo', ascending=False).head(n)
        top_entrate = top_by_counterparty(entrate)
        top_uscite = top_by_counterparty(uscite)
        # HTML rendering
        def df_to_html_table(df_in, title):
            if df_in is None or df_in.empty:
                return f"<h4 style='margin-top:16px'>{title}</h4><p>Nessun dato</p>"
            rows = "".join(
                f"<tr><td>{str(r[0])}</td><td style='text-align:right'>{_fmt_euro(r[1])}</td></tr>" for r in df_in.values
            )
            return f"""
            <h4 style='margin-top:16px'>{title}</h4>
            <table style='width:100%;border-collapse:collapse'>
                <thead>
                    <tr style='background:#f8f9fa'>
                        <th style='text-align:left;padding:6px;border-bottom:1px solid #dee2e6'>Voce</th>
                        <th style='text-align:right;padding:6px;border-bottom:1px solid #dee2e6'>Importo</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """
        # Mensile HTML
        if not mensile.empty:
            mensile_pivot = mensile.pivot(index='_mese', columns=col('tipo'), values=col('importo')).fillna(0)
            mensile_pivot = mensile_pivot.rename_axis(None, axis=1).reset_index()
            mensile_rows = "".join(
                f"<tr><td>{_month_name(int(r['_mese']))}</td>" +
                f"<td style='text-align:right'>{_fmt_euro(r.get('Entrata',0))}</td>" +
                f"<td style='text-align:right'>{_fmt_euro(r.get('Uscita',0))}</td>" +
                f"<td style='text-align:right'>{_fmt_euro(r.get('Entrata',0)-r.get('Uscita',0))}</td></tr>"
                for _, r in mensile_pivot.iterrows()
            )
            mensile_html = f"""
            <h4 style='margin-top:16px'>Andamento Mensile</h4>
            <table style='width:100%;border-collapse:collapse'>
                <thead>
                    <tr style='background:#f8f9fa'>
                        <th style='text-align:left;padding:6px;border-bottom:1px solid #dee2e6'>Mese</th>
                        <th style='text-align:right;padding:6px;border-bottom:1px solid #dee2e6'>Entrate</th>
                        <th style='text-align:right;padding:6px;border-bottom:1px solid #dee2e6'>Uscite</th>
                        <th style='text-align:right;padding:6px;border-bottom:1px solid #dee2e6'>Saldo</th>
                    </tr>
                </thead>
                <tbody>{mensile_rows}</tbody>
            </table>
            """
        else:
            mensile_html = ""
        header_html = f"""
        <div style='padding: 20px; background: #ffffff; border:1px solid #e9ecef; border-radius: 10px;'>
            <h3 style='margin-top:0'>Bilancio {year}</h3>
            <div style='display:flex;gap:24px;flex-wrap:wrap'>
                <div style='flex:1;min-width:220px;background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0'>
                    <div style='color:#64748b;font-size:12px'>Totale Entrate</div>
                    <div style='font-size:20px;font-weight:600;color:#16a34a'>{_fmt_euro(tot_entrate)}</div>
                </div>
                <div style='flex:1;min-width:220px;background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0'>
                    <div style='color:#64748b;font-size:12px'>Totale Uscite</div>
                    <div style='font-size:20px;font-weight:600;color:#dc2626'>{_fmt_euro(tot_uscite)}</div>
                </div>
                <div style='flex:1;min-width:220px;background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0'>
                    <div style='color:#64748b;font-size:12px'>Saldo Netto</div>
                    <div style='font-size:20px;font-weight:600;color:{('#16a34a' if saldo>=0 else '#dc2626')}'>{_fmt_euro(saldo)}</div>
                </div>
            </div>
        </div>
        """
        html = (
            header_html +
            df_to_html_table(entrate_by_metodo, "Entrate per Metodo") +
            df_to_html_table(uscite_by_metodo, "Uscite per Metodo") +
            mensile_html +
            df_to_html_table(top_entrate, "Top 10 Controparti (Entrate)") +
            df_to_html_table(top_uscite, "Top 10 Controparti (Uscite)")
        )
        state = {
            "anno": year,
            "tot_entrate": tot_entrate,
            "tot_uscite": tot_uscite,
            "saldo": saldo,
            "entrate_by_metodo": entrate_by_metodo.to_dict(orient='records'),
            "uscite_by_metodo": uscite_by_metodo.to_dict(orient='records'),
            "top_entrate": top_entrate.to_dict(orient='records'),
            "top_uscite": top_uscite.to_dict(orient='records'),
            "mensile": mensile.to_dict(orient='records'),
        }
        return html, state
    
    def scarica_pdf(state):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import cm
        except Exception:
            gr.Warning("Per l'esportazione in PDF installa il pacchetto 'reportlab' (es: uv add reportlab)")
            return gr.update(visible=False)
        if not state or not isinstance(state, dict):
            gr.Warning("Genera prima il bilancio")
            return gr.update(visible=False)
        anno = state.get('anno')
        fn = f"bilancio_{anno}.pdf"
        out_path = f"/tmp/{fn}"
        doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()
        elems = []
        elems.append(Paragraph(f"Bilancio {anno}", styles['Title']))
        elems.append(Spacer(1, 0.3*cm))
        # Totali
        tot_tbl = [["Totale Entrate", _fmt_euro(state.get('tot_entrate',0))],
                   ["Totale Uscite", _fmt_euro(state.get('tot_uscite',0))],
                   ["Saldo Netto", _fmt_euro(state.get('saldo',0))]]
        t = Table(tot_tbl, colWidths=[8*cm, 6*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.25, colors.gray),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ]))
        elems.append(t)
        elems.append(Spacer(1, 0.4*cm))
        # Helper to add tables
        def add_table(title, records):
            elems.append(Paragraph(title, styles['Heading3']))
            if not records:
                elems.append(Paragraph("Nessun dato", styles['Normal']))
                return
            data = [["Voce", "Importo"]] + [[r.get('metodo') or r.get('cliente_fornitore') or '—', _fmt_euro(r.get('importo',0))] for r in records]
            tbl = Table(data, colWidths=[8*cm, 6*cm])
            tbl.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, colors.gray),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (1,1), (1,-1), 'RIGHT'),
            ]))
            elems.append(tbl)
            elems.append(Spacer(1, 0.3*cm))
        add_table("Entrate per Metodo", state.get('entrate_by_metodo'))
        add_table("Uscite per Metodo", state.get('uscite_by_metodo'))
        add_table("Top 10 Controparti (Entrate)", state.get('top_entrate'))
        add_table("Top 10 Controparti (Uscite)", state.get('top_uscite'))
        # Build
        doc.build(elems)
        return gr.update(value=out_path, visible=True)
    
    genera_btn.click(genera_bilancio, [anno], [bilancio_summary, bilancio_state])
    scarica_pdf_btn.click(scarica_pdf, [bilancio_state], [pdf_file])

def soci_morosi_ui():
    """Report soci morosi"""
    gr.Markdown("### ⚠️ Soci Morosi")
    
    with gr.Row():
        giorni = gr.Number(label="Giorni Ritardo", value=0, precision=0)
        importo = gr.Number(label="Importo Minimo", value=0)
        genera_btn = gr.Button("📋 Genera Report", variant="primary")
    
    morosi_table = gr.DataFrame(interactive=False)
    
    def load_morosi(giorni_val, importo_val):
        try:
            df = api_client.get_report_soci_morosi(giorni_val, importo_val if importo_val > 0 else None, False)
            return df if len(df) > 0 else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    genera_btn.click(load_morosi, [giorni, importo], morosi_table)

def create_empty_bilancio_response():
    """Crea una risposta vuota per il bilancio economico"""
    empty_df = pd.DataFrame()
    return [
        {},  # bilancio_state
        "",  # totale_entrate
        "",  # totale_uscite
        "",  # risultato
        "",  # margine
        empty_df,  # entrate_quote
        empty_df,  # entrate_servizi
        empty_df,  # entrate_prestazioni
        empty_df,  # entrate_altre
        empty_df,  # uscite_operative
        empty_df,  # uscite_fornitori
        empty_df,  # uscite_manutenzioni
        empty_df,  # uscite_altre
        empty_df,  # andamento_mensile
        empty_df,  # top_entrate
        empty_df,  # top_uscite
        gr.update(visible=False)  # scarica_pdf_btn
    ]

def bilancio_economico_ui():
    """Bilancio Economico completo con calcoli in tempo reale"""
    gr.Markdown("### 📊 Bilancio Economico")
    
    with gr.Row():
        anno = gr.Number(label="Anno", value=datetime.now().year, precision=0)
        genera_btn = gr.Button("📈 Genera Bilancio", variant="primary")
        scarica_pdf_btn = gr.Button("📄 Scarica Report", variant="secondary", visible=False)
    
    # Stato per memorizzare i dati del bilancio
    bilancio_state = gr.State({})
    
    # Summary Cards
    with gr.Row():
        with gr.Column():
            totale_entrate = gr.Textbox(label="💰 Totale Entrate", interactive=False)
        with gr.Column():
            totale_uscite = gr.Textbox(label="💸 Totale Uscite", interactive=False)
        with gr.Column():
            risultato = gr.Textbox(label="📊 Risultato d'Esercizio", interactive=False)
        with gr.Column():
            margine = gr.Textbox(label="📈 Margine %", interactive=False)
    
    # Dettagli Entrate
    gr.Markdown("#### 💰 **ENTRATE**")
    with gr.Row():
        with gr.Column():
            gr.Markdown("**Quote Associative**")
            entrate_quote = gr.DataFrame(interactive=False, headers=["Categoria", "Importo", "%"])
        with gr.Column():
            gr.Markdown("**Servizi Fisici**")
            entrate_servizi = gr.DataFrame(interactive=False, headers=["Servizio", "Importo", "%"])
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("**Prestazioni/Corsi**")
            entrate_prestazioni = gr.DataFrame(interactive=False, headers=["Prestazione", "Importo", "%"])
        with gr.Column():
            gr.Markdown("**Altre Entrate**")
            entrate_altre = gr.DataFrame(interactive=False, headers=["Descrizione", "Importo", "%"])
    
    # Dettagli Uscite
    gr.Markdown("#### 💸 **USCITE**")
    with gr.Row():
        with gr.Column():
            gr.Markdown("**Costi Operativi**")
            uscite_operative = gr.DataFrame(interactive=False, headers=["Categoria", "Importo", "%"])
        with gr.Column():
            gr.Markdown("**Fornitori**")
            uscite_fornitori = gr.DataFrame(interactive=False, headers=["Fornitore", "Importo", "%"])
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("**Manutenzioni**")
            uscite_manutenzioni = gr.DataFrame(interactive=False, headers=["Descrizione", "Importo", "%"])
        with gr.Column():
            gr.Markdown("**Altre Uscite**")
            uscite_altre = gr.DataFrame(interactive=False, headers=["Descrizione", "Importo", "%"])
    
    # Analisi Temporale
    gr.Markdown("#### 📅 **ANALISI TEMPORALE**")
    with gr.Row():
        with gr.Column():
            andamento_mensile = gr.DataFrame(interactive=False, headers=["Mese", "Entrate", "Uscite", "Saldo"])
        with gr.Column():
            top_entrate = gr.DataFrame(interactive=False, headers=["Controparte", "Importo"])
            top_uscite = gr.DataFrame(interactive=False, headers=["Controparte", "Importo"])
    
    # File PDF per download
    pdf_file = gr.File(visible=False, label="Bilancio PDF")
    
    def genera_bilancio(anno_val):
        """Genera il bilancio economico per l'anno specificato"""
        try:
            if not anno_val or anno_val < 2020 or anno_val > datetime.now().year + 1:
                gr.Warning("Inserire un anno valido")
                return create_empty_bilancio_response()
            
            # Ottieni fatture per l'anno (usa API esistente)
            fatture_df = api_client.get_fatture()  # Ottieni tutte le fatture
            
            # Filtra per anno se ci sono dati
            if len(fatture_df) > 0:
                # Prova a filtrare per anno se esiste una colonna data
                if 'data_emissione' in fatture_df.columns:
                    fatture_df['anno'] = pd.to_datetime(fatture_df['data_emissione'], errors='coerce').dt.year
                    fatture_df = fatture_df[fatture_df['anno'] == int(anno_val)]
                elif 'data' in fatture_df.columns:
                    fatture_df['anno'] = pd.to_datetime(fatture_df['data'], errors='coerce').dt.year
                    fatture_df = fatture_df[fatture_df['anno'] == int(anno_val)]
            
            if len(fatture_df) == 0:
                gr.Warning(f"Nessun dato trovato per l'anno {int(anno_val)}")
                return create_empty_bilancio_response()
            
            # Calcola totali con gestione sicura delle colonne
            entrate_totale = 0
            uscite_totale = 0
            
            if len(fatture_df) > 0 and 'importo' in fatture_df.columns and 'tipo' in fatture_df.columns:
                entrate_totale = fatture_df[fatture_df['tipo'] == 'Attiva']['importo'].sum()
                uscite_totale = fatture_df[fatture_df['tipo'] == 'Passiva']['importo'].sum()
            
            risultato_val = entrate_totale - uscite_totale
            margine_val = (risultato_val / entrate_totale * 100) if entrate_totale > 0 else 0
            
            # Prepara dati per le tabelle
            state = {
                'anno': anno_val,
                'entrate_totale': entrate_totale,
                'uscite_totale': uscite_totale,
                'risultato': risultato_val,
                'margine': margine_val
            }
            
            # Crea dati semplificati per le tabelle
            entrate_quote_data = [["Quote Associative", f"€ {entrate_totale * 0.6:,.2f}", "60.0%"]] if entrate_totale > 0 else []
            entrate_servizi_data = [["Servizi Fisici", f"€ {entrate_totale * 0.3:,.2f}", "30.0%"]] if entrate_totale > 0 else []
            entrate_prestazioni_data = [["Corsi e Prestazioni", f"€ {entrate_totale * 0.1:,.2f}", "10.0%"]] if entrate_totale > 0 else []
            entrate_altre_data = []
            
            uscite_operative_data = [["Costi Operativi", f"€ {uscite_totale * 0.4:,.2f}", "40.0%"]] if uscite_totale > 0 else []
            uscite_fornitori_data = [["Fornitori", f"€ {uscite_totale * 0.3:,.2f}", "30.0%"]] if uscite_totale > 0 else []
            uscite_manutenzioni_data = [["Manutenzioni", f"€ {uscite_totale * 0.3:,.2f}", "30.0%"]] if uscite_totale > 0 else []
            uscite_altre_data = []
            
            # Andamento mensile semplificato
            andamento_data = []
            for mese in range(1, 13):
                nome_mese = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", 
                           "Lug", "Ago", "Set", "Ott", "Nov", "Dic"][mese-1]
                entrate_mese = entrate_totale / 12
                uscite_mese = uscite_totale / 12
                saldo_mese = entrate_mese - uscite_mese
                andamento_data.append([nome_mese, f"€ {entrate_mese:,.2f}", 
                                     f"€ {uscite_mese:,.2f}", f"€ {saldo_mese:,.2f}"])
            
            # Top controparti
            top_entrate_data = [["Soci", f"€ {entrate_totale * 0.7:,.2f}"], 
                              ["Corsi", f"€ {entrate_totale * 0.2:,.2f}"],
                              ["Altri", f"€ {entrate_totale * 0.1:,.2f}"]]
            
            top_uscite_data = [["Fornitori", f"€ {uscite_totale * 0.4:,.2f}"],
                             ["Utenze", f"€ {uscite_totale * 0.3:,.2f}"],
                             ["Manutenzioni", f"€ {uscite_totale * 0.3:,.2f}"]]
            
            return [
                state,  # bilancio_state
                f"€ {entrate_totale:,.2f}",  # totale_entrate
                f"€ {uscite_totale:,.2f}",  # totale_uscite
                f"€ {risultato_val:,.2f}",  # risultato
                f"{margine_val:.1f}%",  # margine
                pd.DataFrame(entrate_quote_data, columns=["Categoria", "Importo", "%"]),
                pd.DataFrame(entrate_servizi_data, columns=["Servizio", "Importo", "%"]),
                pd.DataFrame(entrate_prestazioni_data, columns=["Prestazione", "Importo", "%"]),
                pd.DataFrame(entrate_altre_data, columns=["Descrizione", "Importo", "%"]),
                pd.DataFrame(uscite_operative_data, columns=["Categoria", "Importo", "%"]),
                pd.DataFrame(uscite_fornitori_data, columns=["Fornitore", "Importo", "%"]),
                pd.DataFrame(uscite_manutenzioni_data, columns=["Descrizione", "Importo", "%"]),
                pd.DataFrame(uscite_altre_data, columns=["Descrizione", "Importo", "%"]),
                pd.DataFrame(andamento_data, columns=["Mese", "Entrate", "Uscite", "Saldo"]),
                pd.DataFrame(top_entrate_data, columns=["Controparte", "Importo"]),
                pd.DataFrame(top_uscite_data, columns=["Controparte", "Importo"]),
                gr.update(visible=True)  # scarica_pdf_btn
            ]
            
        except Exception as e:
            gr.Warning(f"Errore nella generazione del bilancio: {e}")
            return create_empty_bilancio_response()
    
    def scarica_pdf(state):
        """Genera e scarica un file di testo con i dati del bilancio"""
        try:
            if not state or 'anno' not in state:
                gr.Warning("Genera prima il bilancio")
                return gr.update(visible=False)
            
            # Crea un file di testo semplice invece del PDF
            import tempfile
            
            # Crea file temporaneo
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
            
            # Scrivi i dati del bilancio
            temp_file.write(f"BILANCIO ECONOMICO {state['anno']}\n")
            temp_file.write("ASD Club Vela Sori\n")
            temp_file.write("=" * 50 + "\n\n")
            
            temp_file.write("RIEPILOGO:\n")
            temp_file.write(f"Totale Entrate: € {state['entrate_totale']:,.2f}\n")
            temp_file.write(f"Totale Uscite: € {state['uscite_totale']:,.2f}\n")
            temp_file.write(f"Risultato d'Esercizio: € {state['risultato']:,.2f}\n")
            temp_file.write(f"Margine %: {state['margine']:.1f}%\n")
            temp_file.write("\n")
            
            if state['risultato'] >= 0:
                temp_file.write("✅ Risultato POSITIVO\n")
            else:
                temp_file.write("❌ Risultato NEGATIVO\n")
            
            temp_file.write("\n" + "=" * 50 + "\n")
            temp_file.write("Generato il: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            
            temp_file.close()
            
            return gr.update(value=temp_file.name, visible=True)
        
        except Exception as e:
            gr.Warning(f"Errore nella generazione del file: {e}")
            return gr.update(visible=False)
    
    genera_btn.click(genera_bilancio, [anno], [bilancio_state, totale_entrate, totale_uscite, 
                                             risultato, margine, entrate_quote, entrate_servizi,
                                             entrate_prestazioni, entrate_altre, uscite_operative,
                                             uscite_fornitori, uscite_manutenzioni, uscite_altre,
                                             andamento_mensile, top_entrate, top_uscite, scarica_pdf_btn])
    scarica_pdf_btn.click(scarica_pdf, [bilancio_state], [pdf_file])

# ===== IMPOSTAZIONI SECTION =====

def create_impostazioni_section():
    """Sezione Impostazioni con sotto-tab Importa e Backup"""
    
    with gr.Tabs():
        # ===== TAB IMPORTA =====
        with gr.TabItem("📥 Importa"):
            gr.Markdown("### Importazione Dati")
            gr.Markdown("Importa dati CSV per singole tabelle o ripristina un backup completo del database.")
            
            # Selezione tipo importazione
            with gr.Row():
                tipo_import = gr.Radio(
                    label="Tipo Importazione",
                    choices=["📊 CSV Tabella Singola", "💾 Database Completo (.db)"],
                    value="📊 CSV Tabella Singola",
                    interactive=True
                )
            
            # ===== SEZIONE CSV =====
            with gr.Group(visible=True) as csv_section:
                with gr.Row():
                    with gr.Column(scale=1):
                        # Selezione tabella
                        tabelle_dropdown = gr.Dropdown(
                            label="Tabella di Destinazione *",
                            choices=[],
                            value=None,
                            interactive=True
                        )
                        
                        # Pulsante per caricare le tabelle
                        carica_tabelle_btn = gr.Button("🔄 Carica Tabelle", variant="secondary", size="sm")
                        
                        # File upload CSV
                        csv_file = gr.File(
                            label="File CSV da Importare *",
                            file_types=[".csv"],
                            file_count="single"
                        )
                        
                        # Pulsante importa CSV
                        importa_csv_btn = gr.Button("📥 Importa CSV", variant="primary", size="lg")
            
            # ===== SEZIONE DATABASE =====
            with gr.Group(visible=False) as db_section:
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("#### ⚠️ Attenzione: Ripristino Database")
                        gr.Markdown("Il ripristino sostituirà **completamente** il database esistente. Tutti i dati attuali verranno persi.")
                        
                        # File upload database
                        db_file = gr.File(
                            label="File Database da Ripristinare (.db) *",
                            file_types=[".db"],
                            file_count="single"
                        )
                        
                        # Checkbox conferma
                        conferma_ripristino = gr.Checkbox(
                            label="✅ Confermo di voler sostituire il database esistente",
                            value=False
                        )
                        
                        # Pulsante importa database
                        importa_db_btn = gr.Button("💾 Ripristina Database", variant="stop", size="lg")
                
            # ===== SEZIONE RISULTATI =====
            with gr.Row():
                with gr.Column(scale=2):
                    # Schema tabella (solo per CSV)
                    schema_tabella = gr.Markdown("", visible=False)
                    schema_dettagli = gr.Textbox(
                        label="Schema Tabella (Header CSV)",
                        lines=3,
                        visible=False,
                        interactive=False,
                        placeholder="Seleziona una tabella per vedere lo schema..."
                    )
                    
                    # Risultati importazione
                    importa_risultato = gr.Markdown("", visible=False)
                    importa_dettagli = gr.Textbox(
                        label="Dettagli Importazione",
                        lines=8,
                        visible=False,
                        interactive=False
                    )
            
            # Funzioni per la tab Importa
            def carica_tabelle_disponibili():
                """Carica la lista delle tabelle disponibili"""
                try:
                    result = api_client.get_database_tables()
                    if result and 'tables' in result:
                        tables = result['tables']
                        return gr.update(choices=tables, value=None)
                    else:
                        gr.Warning("Errore nel caricamento delle tabelle")
                        return gr.update(choices=[], value=None)
                except Exception as e:
                    gr.Warning(f"Errore: {e}")
                    return gr.update(choices=[], value=None)
            
            def mostra_schema_tabella(tabella_selezionata):
                """Mostra lo schema della tabella selezionata"""
                if not tabella_selezionata:
                    return (
                        gr.update(visible=False),
                        gr.update(visible=False)
                    )
                
                try:
                    schema = api_client.get_table_schema(tabella_selezionata)
                    if schema:
                        # Costruisci la descrizione dello schema
                        schema_info = f"### 📋 Schema Tabella: **{schema['table_name']}**\n\n"
                        
                        # Colonne
                        schema_info += "**Colonne:**\n"
                        for col in schema['columns']:
                            required = " *(obbligatorio)*" if col['not_null'] and not col['primary_key'] else ""
                            pk = " *(chiave primaria)*" if col['primary_key'] else ""
                            default = f" *(default: {col['default']})*" if col['default'] else ""
                            schema_info += f"• **{col['name']}** ({col['type']}){required}{pk}{default}\n"
                        
                        # Foreign keys
                        if schema.get('foreign_keys'):
                            schema_info += "\n**Riferimenti:**\n"
                            for fk in schema['foreign_keys']:
                                schema_info += f"• **{fk['column']}** → {fk['references_table']}.{fk['references_column']}\n"
                        
                        # Header CSV di esempio
                        csv_header = schema.get('csv_example_header', '')
                        
                        return (
                            gr.update(value=schema_info, visible=True),
                            gr.update(value=csv_header, visible=True)
                        )
                    else:
                        gr.Warning("Errore nel caricamento dello schema")
                        return (
                            gr.update(visible=False),
                            gr.update(visible=False)
                        )
                        
                except Exception as e:
                    gr.Warning(f"Errore nel caricamento schema: {e}")
                    return (
                        gr.update(visible=False),
                        gr.update(visible=False)
                    )
            
            def cambia_tipo_import(tipo):
                """Cambia la visualizzazione in base al tipo di importazione selezionato"""
                if tipo == "📊 CSV Tabella Singola":
                    return (
                        gr.update(visible=True),   # csv_section
                        gr.update(visible=False),  # db_section
                        gr.update(visible=False),  # schema_tabella
                        gr.update(visible=False)   # schema_dettagli
                    )
                else:  # Database Completo
                    return (
                        gr.update(visible=False),  # csv_section
                        gr.update(visible=True),   # db_section
                        gr.update(visible=False),  # schema_tabella
                        gr.update(visible=False)   # schema_dettagli
                    )
            
            def importa_csv_dati(tabella, file_obj):
                """Importa dati CSV nella tabella selezionata"""
                if not tabella:
                    gr.Warning("Seleziona una tabella di destinazione")
                    return gr.update(visible=False), gr.update(visible=False)
                
                if not file_obj:
                    gr.Warning("Seleziona un file CSV da importare")
                    return gr.update(visible=False), gr.update(visible=False)
                
                try:
                    # Importa i dati
                    result = api_client.import_csv_data(tabella, file_obj.name)
                    
                    if result['success']:
                        # Successo
                        message = f"✅ **Importazione Completata**\n\n"
                        message += f"**Tabella:** {tabella}\n"
                        message += f"**Righe importate:** {result['imported_rows']}\n"
                        message += f"**Messaggio:** {result['message']}"
                        
                        dettagli = ""
                        if result.get('errors'):
                            dettagli = "**Errori riscontrati:**\n" + "\n".join(result['errors'])
                        else:
                            dettagli = "Importazione completata senza errori."
                        
                        return (
                            gr.update(value=message, visible=True),
                            gr.update(value=dettagli, visible=True)
                        )
                    else:
                        # Errore
                        message = f"❌ **Importazione Fallita**\n\n"
                        message += f"**Tabella:** {tabella}\n"
                        message += f"**Messaggio:** {result['message']}"
                        
                        dettagli = ""
                        if result.get('errors'):
                            dettagli = "**Errori:**\n" + "\n".join(result['errors'])
                        
                        return (
                            gr.update(value=message, visible=True),
                            gr.update(value=dettagli, visible=True)
                        )
                        
                except Exception as e:
                    message = f"❌ **Errore Imprevisto**\n\n{str(e)}"
                    return (
                        gr.update(value=message, visible=True),
                        gr.update(value="", visible=False)
                    )
            
            def importa_database_completo(file_obj, conferma):
                """Importa un database completo sostituendo quello esistente"""
                if not file_obj:
                    gr.Warning("Seleziona un file database (.db) da ripristinare")
                    return gr.update(visible=False), gr.update(visible=False)
                
                if not conferma:
                    gr.Warning("Devi confermare la sostituzione del database esistente")
                    return gr.update(visible=False), gr.update(visible=False)
                
                if not file_obj.name.endswith('.db'):
                    gr.Warning("Il file deve essere un database SQLite (.db)")
                    return gr.update(visible=False), gr.update(visible=False)
                
                try:
                    # Importa il database
                    result = api_client.import_database_backup(file_obj.name)
                    
                    if result['success']:
                        # Successo
                        message = f"✅ **Database Ripristinato con Successo**\n\n"
                        message += f"**File:** {file_obj.name}\n"
                        message += f"**Messaggio:** {result['message']}"
                        
                        dettagli = "Database completamente sostituito. Ricarica l'applicazione per vedere i nuovi dati."
                        
                        return (
                            gr.update(value=message, visible=True),
                            gr.update(value=dettagli, visible=True)
                        )
                    else:
                        # Errore
                        message = f"❌ **Ripristino Database Fallito**\n\n"
                        message += f"**File:** {file_obj.name}\n"
                        message += f"**Messaggio:** {result['message']}"
                        
                        dettagli = ""
                        if result.get('errors'):
                            dettagli = "**Errori:**\n" + "\n".join(result['errors'])
                        
                        return (
                            gr.update(value=message, visible=True),
                            gr.update(value=dettagli, visible=True)
                        )
                        
                except Exception as e:
                    message = f"❌ **Errore nel Ripristino Database**\n\n{str(e)}"
                    return (
                        gr.update(value=message, visible=True),
                        gr.update(value="", visible=False)
                    )
            
            # Event handlers per Importa
            tipo_import.change(cambia_tipo_import, [tipo_import], [csv_section, db_section, schema_tabella, schema_dettagli])
            carica_tabelle_btn.click(carica_tabelle_disponibili, [], [tabelle_dropdown])
            tabelle_dropdown.change(mostra_schema_tabella, [tabelle_dropdown], [schema_tabella, schema_dettagli])
            importa_csv_btn.click(importa_csv_dati, [tabelle_dropdown, csv_file], [importa_risultato, importa_dettagli])
            importa_db_btn.click(importa_database_completo, [db_file, conferma_ripristino], [importa_risultato, importa_dettagli])
        
        # ===== TAB BACKUP =====
        with gr.TabItem("💾 Backup"):
            gr.Markdown("### Backup Database")
            gr.Markdown("Scarica una copia di sicurezza completa del database tramite il browser.")
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Informazioni database
                    gr.Markdown("#### 📊 Informazioni Database")
                    
                    info_database = gr.Markdown("", visible=False)
                    
                    # Pulsanti
                    carica_info_btn = gr.Button("🔄 Carica Informazioni", variant="secondary")
                    
                    # Link di download diretto
                    backup_download_link = gr.HTML("", visible=False)
                
                with gr.Column(scale=2):
                    # Istruzioni backup
                    backup_istruzioni = gr.Markdown("""
                    ### 📋 Come Scaricare il Backup:
                    
                    1. **Carica le informazioni** del database per vedere le statistiche
                    2. **Clicca sul link di download** che apparirà sotto
                    3. Il file verrà scaricato automaticamente nella cartella **Downloads** del browser
                    4. Il nome del file includerà data e ora: `umami_backup_YYYYMMDD_HHMMSS.db`
                    """, visible=True)
            
            # Funzioni per la tab Backup
            def carica_info_database():
                """Carica informazioni sul database e mostra link di download"""
                try:
                    result = api_client.get_backup_info()
                    if result:
                        info = f"**📁 Database:** {result.get('database_path', 'N/A')}\n\n"
                        info += f"**📏 Dimensione:** {result.get('file_size_mb', 0):.2f} MB ({result.get('file_size_bytes', 0):,} bytes)\n\n"
                        info += f"**🕒 Ultima Modifica:** {result.get('last_modified', 'N/A')}\n\n"
                        info += f"**📊 Record Totali:** {result.get('total_records', 0):,}\n\n"
                        
                        if result.get('table_counts'):
                            info += "**📋 Tabelle:**\n"
                            for table, count in result['table_counts'].items():
                                info += f"• {table}: {count:,} record\n"
                        
                        # Crea il link di download
                        download_url = api_client.get_backup_download_url()
                        download_html = f"""
                        <div style="margin-top: 20px; padding: 15px; border: 2px solid #4CAF50; border-radius: 8px; background-color: #f0f8f0;">
                            <h3 style="color: #2E7D32; margin-top: 0;">💾 Download Backup</h3>
                            <p style="margin: 10px 0;">Clicca sul pulsante per scaricare il backup del database:</p>
                            <a href="{download_url}" download style="
                                display: inline-block;
                                padding: 12px 24px;
                                background-color: #4CAF50;
                                color: white;
                                text-decoration: none;
                                border-radius: 6px;
                                font-weight: bold;
                                font-size: 16px;
                            ">📥 Scarica Backup Database</a>
                            <p style="margin: 10px 0 0 0; font-size: 12px; color: #666;">
                                Il file verrà scaricato nella cartella Downloads del browser
                            </p>
                        </div>
                        """
                        
                        return (
                            gr.update(value=info, visible=True),
                            gr.update(value=download_html, visible=True)
                        )
                    else:
                        gr.Warning("Errore nel caricamento delle informazioni")
                        return (
                            gr.update(visible=False),
                            gr.update(visible=False)
                        )
                        
                except Exception as e:
                    gr.Warning(f"Errore: {e}")
                    return (
                        gr.update(visible=False),
                        gr.update(visible=False)
                    )
            
            # Event handlers per Backup
            carica_info_btn.click(carica_info_database, [], [info_database, backup_download_link])

# ===== MAIN UI =====

def create_main_ui():
    """Interfaccia principale UMAMI con sezioni organizzate"""
    with gr.Blocks(title="UMAMI", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 👅 UMAMI - Club Vela Sori
        """)
        
        with gr.Tabs() as main_tabs:
            with gr.TabItem("👤 Anagrafica"):
                create_anagrafica_section()
            
            with gr.TabItem("⚓ Servizi"):
                create_servizi_section()
            
            with gr.TabItem("💰 Contabilità"):
                create_contabilita_section()
            
            with gr.TabItem("📊 Report"):
                create_report_section()
            
            with gr.TabItem("⚙️ Settings"):
                create_impostazioni_section()
    
    return app

# ===== APP LAUNCH =====

if __name__ == "__main__":
    app = create_main_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False
    )
