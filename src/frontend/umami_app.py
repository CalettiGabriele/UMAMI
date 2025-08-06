import gradio as gr
import pandas as pd
import api_client
from datetime import datetime, date
import json

# --- Constants ---
STATO_ASSOCIATO_CHOICES = ["Attivo", "Sospeso", "Scaduto", "Cessato"]
STATO_SERVIZIO_CHOICES = ["Disponibile", "In manutenzione", "Ritirato"]
TIPO_SERVIZIO_CHOICES = ["Deriva", "Catamarano", "Windsurf", "Wingfoil", "SUP", "Canoa"]
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
            return df if not df.empty else pd.DataFrame()
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
                return gr.Group(visible=False), df if not df.empty else pd.DataFrame()
            else:
                gr.Warning("Errore durante la creazione dell'associato")
                return gr.Group(visible=True), pd.DataFrame()
                
        except Exception as e:
            gr.Warning(f"Errore: {str(e)}")
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
            email = gr.Textbox(label="Email", interactive=False)
            telefono = gr.Textbox(label="Telefono", interactive=False)
            stato_assoc = gr.Textbox(label="Stato", interactive=False)
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
    
    with gr.Group():
        gr.Markdown("#### 💰 Fatture")
        fatture_table = gr.DataFrame(
            headers=["ID", "Numero", "Data", "Tipo", "Importo", "Stato"],
            interactive=False,
            wrap=True
        )
    
    with gr.Group():
        gr.Markdown("#### 💳 Pagamenti")
        pagamenti_table = gr.DataFrame(
            headers=["ID", "Data", "Importo", "Metodo", "Note"],
            interactive=False,
            wrap=True
        )
    
    def load_associato(aid):
        if not aid:
            return [""] * 13 + [pd.DataFrame(), pd.DataFrame()]
        try:
            # Carica dati associato
            data = api_client.get_associato(int(aid))
            if not data:
                gr.Warning("Associato non trovato")
                return [""] * 15 + [pd.DataFrame(), pd.DataFrame()]
            
            # Dati anagrafici
            anagrafica = [
                safe_get(data, 'nome'), safe_get(data, 'cognome'), safe_get(data, 'codice_fiscale'),
                safe_get(data, 'email'), safe_get(data, 'telefono'), safe_get(data, 'stato_associato')
            ]
            
            # Dati FIV
            fiv_data = data.get('tesseramento_fiv', {})
            if fiv_data:
                # Calcola lo stato della tessera FIV
                from datetime import datetime, date
                oggi = date.today()
                scadenza_tesseramento = fiv_data.get('scadenza_tesseramento_fiv')
                scadenza_certificato = fiv_data.get('scadenza_certificato_medico')
                
                status_html = "<div style='padding: 10px; border-radius: 5px; margin-top: 10px;'>"
                
                # Controlla stato tesseramento
                if scadenza_tesseramento:
                    try:
                        scad_tess = datetime.strptime(scadenza_tesseramento, '%Y-%m-%d').date()
                        if scad_tess < oggi:
                            status_html += "<p style='color: red; font-weight: bold;'>⚠️ Tesseramento FIV SCADUTO</p>"
                        elif (scad_tess - oggi).days <= 30:
                            status_html += "<p style='color: orange; font-weight: bold;'>⚠️ Tesseramento FIV in scadenza tra {} giorni</p>".format((scad_tess - oggi).days)
                        else:
                            status_html += "<p style='color: green; font-weight: bold;'>✓ Tesseramento FIV valido</p>"
                    except:
                        status_html += "<p style='color: gray;'>Tesseramento: data non valida</p>"
                
                # Controlla stato certificato medico
                if scadenza_certificato:
                    try:
                        scad_cert = datetime.strptime(scadenza_certificato, '%Y-%m-%d').date()
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
                if fatture_df.empty:
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
                if pagamenti_df.empty:
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
            
            return anagrafica + fiv + chiave + [fatture_df, pagamenti_df]
            
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return [""] * 13 + [pd.DataFrame(), pd.DataFrame()]
    
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
            return gr.Group(visible=False), "", "", "", "", ""
        return gr.Group(visible=True), current_nome, current_cognome, current_cf, current_email, current_telefono
    
    def hide_anagrafica_modal():
        """Nasconde modal anagrafica"""
        return gr.Group(visible=False), "", "", "", "", ""
    
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
        [nome, cognome, cf, email, telefono, stato_assoc,
         fiv_numero, fiv_scadenza_tesseramento, fiv_scadenza_certificato, fiv_status,
         chiave_codice, chiave_stato, chiave_credito, chiave_data_assegnazione, chiave_data_riconsegna,
         fatture_table, pagamenti_table]
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
            return df if not df.empty else pd.DataFrame()
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
                       updated_df if not updated_df.empty else pd.DataFrame())
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
                if fatture_df.empty:
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
        with gr.TabItem("💰 Prezzario Servizi"):
            prezzario_servizi_ui()
        with gr.TabItem("🏫 Elenco Prestazioni"):
            elenco_prestazioni_ui()

def elenco_servizi_ui():
    """Gestione servizi fisici"""
    gr.Markdown("### ⚓ Servizi Fisici")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca")
        tipo = gr.Dropdown(label="Tipo", choices=[""] + TIPO_SERVIZIO_CHOICES)
        stato = gr.Dropdown(label="Stato", choices=[""] + STATO_SERVIZIO_CHOICES)
    
    servizi_table = gr.DataFrame(interactive=False)
    refresh_btn = gr.Button("🔄 Aggiorna")
    
    def load_servizi(search_val, tipo_val, stato_val):
        try:
            df = api_client.get_servizi_fisici(tipo=tipo_val, stato=stato_val)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_servizi, [search, tipo, stato], servizi_table)

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
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_prezzi, [search], prezzi_table)

def elenco_prestazioni_ui():
    """Gestione prestazioni"""
    gr.Markdown("### 🏫 Prestazioni")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca")
        refresh_btn = gr.Button("🔄 Aggiorna")
    
    prestazioni_table = gr.DataFrame(interactive=False)
    
    def load_prestazioni(search_val):
        try:
            # Note: This should use prestazioni API when available
            df = pd.DataFrame()  # Placeholder
            return df
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_prestazioni, [search], prestazioni_table)

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
    
    fatture_table = gr.DataFrame(interactive=False)
    refresh_btn = gr.Button("🔄 Aggiorna")
    
    def load_fatture(search_val, tipo_val, stato_val):
        try:
            df = api_client.get_fatture(tipo=tipo_val, stato=stato_val, search=search_val)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_fatture, [search, tipo, stato], fatture_table)

def elenco_pagamenti_ui():
    """Gestione pagamenti"""
    gr.Markdown("### 💳 Pagamenti")
    
    with gr.Row():
        metodo = gr.Dropdown(label="Metodo", choices=[""] + METODI_PAGAMENTO)
        dal = gr.Textbox(label="Dal (YYYY-MM-DD)")
        al = gr.Textbox(label="Al (YYYY-MM-DD)")
    
    pagamenti_table = gr.DataFrame(interactive=False)
    refresh_btn = gr.Button("🔄 Aggiorna")
    
    def load_pagamenti(metodo_val, dal_val, al_val):
        try:
            df = api_client.get_pagamenti(metodo=metodo_val, dal=dal_val, al=al_val)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_pagamenti, [metodo, dal, al], pagamenti_table)

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
    
    bilancio_summary = gr.HTML()
    
    def genera_bilancio(anno_val):
        # Mock bilancio data
        html = f"""
        <div style="padding: 20px; background: #f0f0f0; border-radius: 10px;">
            <h3>Bilancio {anno_val}</h3>
            <p><strong>Totale Entrate:</strong> {format_currency(28000)}</p>
            <p><strong>Totale Uscite:</strong> {format_currency(17000)}</p>
            <p><strong>Saldo Netto:</strong> <span style="color: green;">{format_currency(11000)}</span></p>
        </div>
        """
        return html
    
    genera_btn.click(genera_bilancio, [anno], bilancio_summary)

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
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    genera_btn.click(load_morosi, [giorni, importo], morosi_table)

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
    
    return app

# ===== APP LAUNCH =====

if __name__ == "__main__":
    app = create_main_ui()
    app.launch(
        server_name="127.0.0.1",
        server_port=7861,
        show_error=True,
        share=False
    )
