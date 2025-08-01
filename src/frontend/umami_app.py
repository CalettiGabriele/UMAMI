import gradio as gr
import pandas as pd
import api_client
from datetime import datetime

# --- Constants ---
STATO_ASSOCIATO_CHOICES = ["Attivo", "Sospeso", "Scaduto", "Cessato"]
STATO_SERVIZIO_CHOICES = ["Disponibile", "In manutenzione", "Ritirato"]
TIPO_SERVIZIO_CHOICES = ["Deriva", "Catamarano", "Windsurf", "Wingfoil", "SUP", "Canoa"]

# --- Helper Functions ---
def handle_api_response(response, success_message, failure_message):
    if response:
        gr.Info(success_message)
        return True
    else:
        gr.Warning(failure_message)
        return False

# --- UI Modules ---

# ------------------
# --- ASSOCIATI UI ---
# ------------------
def create_associati_ui():
    with gr.Column():
        gr.Markdown("### Gestione Associati")
        with gr.Row():
            search_bar = gr.Textbox(label="Cerca Associato", placeholder="Nome, Cognome, CF...")
            stato_dd = gr.Dropdown(label="Stato", choices=[""] + STATO_ASSOCIATO_CHOICES, value="")
            refresh_btn = gr.Button("🔄 Aggiorna")
        
        associati_df = gr.DataFrame(interactive=False, headers=["ID", "Nome", "Cognome", "Codice Fiscale", "Stato"])

        with gr.Accordion("Aggiungi / Modifica Associato", open=False):
            with gr.Row():
                id_associato = gr.Textbox(label="ID Associato", interactive=False)
                nome = gr.Textbox(label="Nome")
                cognome = gr.Textbox(label="Cognome")
            with gr.Row():
                codice_fiscale = gr.Textbox(label="Codice Fiscale")
                data_nascita = gr.Textbox(label="Data Nascita", placeholder="YYYY-MM-DD")
            with gr.Row():
                indirizzo = gr.Textbox(label="Indirizzo")
                email = gr.Textbox(label="Email")
                telefono = gr.Textbox(label="Telefono")
            with gr.Row():
                data_iscrizione = gr.Textbox(label="Data Iscrizione", placeholder="YYYY-MM-DD", value=datetime.now().strftime('%Y-%m-%d'))
                stato_associato = gr.Dropdown(label="Stato Associato", choices=STATO_ASSOCIATO_CHOICES, value="Attivo")
                fk_associato_riferimento = gr.Textbox(label="ID Associato Riferimento (Capofamiglia)")

            with gr.Row():
                save_btn = gr.Button("Salva")
                clear_btn = gr.Button("Pulisci Form")

    form_outputs = [id_associato, nome, cognome, codice_fiscale, data_nascita, indirizzo, email, telefono, data_iscrizione, stato_associato, fk_associato_riferimento]

    def update_associati_table(search, stato):
        df = api_client.get_associati(search=search, stato=stato)
        if not df.empty:
            return df[['id_associato', 'nome', 'cognome', 'codice_fiscale', 'stato_associato']]
        return pd.DataFrame()

    def on_select_associato(evt: gr.SelectData, df):
        if evt.index is None:
            return [None] * 11
        selected_id = df.iloc[evt.index[0]]['id_associato']
        associato_data = api_client.get_associato(selected_id)
        if associato_data:
            return (
                associato_data.get('id_associato'),
                associato_data.get('nome'),
                associato_data.get('cognome'),
                associato_data.get('codice_fiscale'),
                associato_data.get('data_nascita', '').split('T')[0] if associato_data.get('data_nascita') else '',
                associato_data.get('indirizzo'),
                associato_data.get('email'),
                associato_data.get('telefono'),
                associato_data.get('data_iscrizione', '').split('T')[0] if associato_data.get('data_iscrizione') else '',
                associato_data.get('stato_associato'),
                associato_data.get('fk_associato_riferimento')
            )
        return [None] * 11

    def save_associato(id_val, nome_val, cognome_val, cf_val, dob_val, indirizzo_val, email_val, tel_val, data_isc_val, stato_val, fk_ref_val):
        data = {
            "nome": nome_val, "cognome": cognome_val, "codice_fiscale": cf_val,
            "data_nascita": dob_val if dob_val else None,
            "indirizzo": indirizzo_val, "email": email_val, "telefono": tel_val,
            "data_iscrizione": data_isc_val if data_isc_val else None,
            "stato_associato": stato_val,
            "fk_associato_riferimento": int(fk_ref_val) if fk_ref_val else None
        }
        if id_val:
            response = api_client.update_associato(id_val, data)
            handle_api_response(response, f"Associato {nome_val} {cognome_val} aggiornato!", "Errore durante l'aggiornamento.")
        else:
            response = api_client.create_associato(data)
            handle_api_response(response, f"Associato {nome_val} {cognome_val} creato!", "Errore durante la creazione.")
        return update_associati_table("", ""), *([None]*len(form_outputs))

    refresh_btn.click(update_associati_table, inputs=[search_bar, stato_dd], outputs=associati_df)
    search_bar.submit(update_associati_table, inputs=[search_bar, stato_dd], outputs=associati_df)
    stato_dd.change(update_associati_table, inputs=[search_bar, stato_dd], outputs=associati_df)
    associati_df.select(on_select_associato, inputs=[associati_df], outputs=form_outputs)
    save_btn.click(save_associato, inputs=form_outputs, outputs=[associati_df] + form_outputs)
    clear_btn.click(lambda: [None]*len(form_outputs), outputs=form_outputs)

    return associati_df, update_associati_table

# -------------------
# --- FORNITORI UI ---
# -------------------
def create_fornitori_ui():
    with gr.Column():
        gr.Markdown("### Gestione Fornitori")
        with gr.Row():
            search_bar = gr.Textbox(label="Cerca Fornitore", placeholder="Ragione Sociale, P.IVA...")
            refresh_btn = gr.Button("🔄 Aggiorna")
        fornitori_df = gr.DataFrame(interactive=False)

        with gr.Accordion("Aggiungi / Modifica Fornitore", open=False):
            with gr.Row():
                id_fornitore = gr.Textbox(label="ID Fornitore", interactive=False)
                ragione_sociale = gr.Textbox(label="Ragione Sociale")
                partita_iva = gr.Textbox(label="Partita IVA")
            with gr.Row():
                save_btn = gr.Button("Salva")
                clear_btn = gr.Button("Pulisci Form")
                delete_btn = gr.Button("Elimina", variant="stop")
    
    form_outputs = [id_fornitore, ragione_sociale, partita_iva]

    def update_fornitori_table(search):
        return api_client.get_fornitori(search=search)

    def on_select_fornitore(evt: gr.SelectData, df):
        selected_row = df.iloc[evt.index[0]]
        return selected_row.get('id_fornitore'), selected_row.get('ragione_sociale'), selected_row.get('partita_iva')

    def save_fornitore(id_val, rs_val, piva_val):
        data = {"ragione_sociale": rs_val, "partita_iva": piva_val}
        if id_val:
            response = api_client.update_fornitore(id_val, data)
            handle_api_response(response, "Fornitore aggiornato!", "Errore aggiornamento.")
        else:
            response = api_client.create_fornitore(data)
            handle_api_response(response, "Fornitore creato!", "Errore creazione.")
        return update_fornitori_table(""), *([None]*len(form_outputs))

    def delete_fornitore(id_val):
        if id_val:
            response = api_client.delete_fornitore(id_val)
            handle_api_response(response, "Fornitore eliminato!", "Errore eliminazione.")
        return update_fornitori_table(""), *([None]*len(form_outputs))

    refresh_btn.click(update_fornitori_table, inputs=[search_bar], outputs=fornitori_df)
    search_bar.submit(update_fornitori_table, inputs=[search_bar], outputs=fornitori_df)
    fornitori_df.select(on_select_fornitore, inputs=[fornitori_df], outputs=form_outputs)
    save_btn.click(save_fornitore, inputs=form_outputs, outputs=[fornitori_df] + form_outputs)
    clear_btn.click(lambda: [None]*len(form_outputs), outputs=form_outputs)
    delete_btn.click(delete_fornitore, inputs=[id_fornitore], outputs=[fornitori_df] + form_outputs)

    return fornitori_df, update_fornitori_table

# ----------------
# --- CHIAVI UI ---
# ----------------
def create_chiavi_ui():
    with gr.Column():
        gr.Markdown("### Gestione Chiavi Elettroniche")
        with gr.Row():
            associati_list = gr.Dropdown(label="Seleziona Associato")
            refresh_associati_btn = gr.Button("🔄")
        
        chiave_info = gr.JSON(label="Dati Chiave Elettronica")
        
        with gr.Accordion("Crea/Aggiorna Chiave", open=False):
            with gr.Row():
                key_code = gr.Textbox(label="Codice Chiave (es. A01)")
                in_regola = gr.Checkbox(label="In Regola", value=True)
                save_chiave_btn = gr.Button("Salva Chiave")
        
        with gr.Accordion("Ricarica Crediti Docce", open=False):
            with gr.Row():
                crediti_input = gr.Number(label="Aggiungi Crediti", value=0, minimum=1)
                ricarica_btn = gr.Button("Ricarica Crediti")

    def load_associati_choices():
        df = api_client.get_associati()
        if not df.empty:
            choices = [f"{row['id_associato']} - {row['nome']} {row['cognome']}" for _, row in df.iterrows()]
            return gr.Dropdown(choices=choices, value=None)
        return gr.Dropdown(choices=[], value=None)

    def get_chiave_info(associato_choice):
        if not associato_choice: return None, ""
        associato_id = int(associato_choice.split(' - ')[0])
        data = api_client.get_chiave_elettronica(associato_id)
        return data, data.get('key_code', '') if data else ''

    def save_chiave(associato_choice, code, in_regola_val):
        if not associato_choice: return None
        associato_id = int(associato_choice.split(' - ')[0])
        data = {"key_code": code, "in_regola": in_regola_val}
        response = api_client.create_or_update_chiave(associato_id, data)
        handle_api_response(response, "Chiave salvata!", "Errore salvataggio chiave.")
        return get_chiave_info(associato_choice)[0]

    def ricarica(associato_choice, crediti):
        if not associato_choice or not crediti or crediti <= 0: return None
        associato_id = int(associato_choice.split(' - ')[0])
        response = api_client.ricarica_crediti(associato_id, crediti)
        handle_api_response(response, "Crediti ricaricati!", "Errore ricarica.")
        return get_chiave_info(associato_choice)[0]

    refresh_associati_btn.click(load_associati_choices, outputs=associati_list)
    associati_list.change(get_chiave_info, inputs=associati_list, outputs=[chiave_info, key_code])
    save_chiave_btn.click(save_chiave, inputs=[associati_list, key_code, in_regola], outputs=chiave_info)
    ricarica_btn.click(ricarica, inputs=[associati_list, crediti_input], outputs=chiave_info)
    
    return associati_list, load_associati_choices

# -----------------
# --- SERVIZI UI ---
# -----------------
def create_servizi_ui():
    with gr.Column():
        gr.Markdown("### Gestione Servizi Fisici")
        with gr.Row():
            tipo_dd = gr.Dropdown(label="Tipo", choices=[""] + TIPO_SERVIZIO_CHOICES, value="")
            stato_dd = gr.Dropdown(label="Stato", choices=[""] + STATO_SERVIZIO_CHOICES, value="")
            refresh_btn = gr.Button("🔄 Aggiorna")
        servizi_df = gr.DataFrame(interactive=False)

        with gr.Accordion("Aggiungi Servizio Fisico", open=False):
            with gr.Row():
                nome = gr.Textbox(label="Nome (es. Laser #12345)")
                tipo_servizio = gr.Dropdown(label="Tipo Servizio", choices=TIPO_SERVIZIO_CHOICES)
                stato_servizio = gr.Dropdown(label="Stato", choices=STATO_SERVIZIO_CHOICES, value="Disponibile")
            with gr.Row():
                note = gr.Textbox(label="Note")
                save_btn = gr.Button("Salva Servizio")

    def update_servizi_table(tipo, stato):
        return api_client.get_servizi_fisici(tipo=tipo, stato=stato)

    def save_servizio(nome_val, tipo_val, stato_val, note_val):
        data = {"nome": nome_val, "tipo": tipo_val, "stato": stato_val, "note": note_val}
        response = api_client.create_servizio_fisico(data)
        handle_api_response(response, "Servizio creato!", "Errore creazione servizio.")
        return update_servizi_table("", "")

    refresh_btn.click(update_servizi_table, inputs=[tipo_dd, stato_dd], outputs=servizi_df)
    tipo_dd.change(update_servizi_table, inputs=[tipo_dd, stato_dd], outputs=servizi_df)
    stato_dd.change(update_servizi_table, inputs=[tipo_dd, stato_dd], outputs=servizi_df)
    save_btn.click(save_servizio, inputs=[nome, tipo_servizio, stato_servizio, note], outputs=servizi_df)

    return servizi_df, update_servizi_table

# ----------------
# --- REPORT UI ---
# ----------------
def create_report_ui():
    with gr.Tabs():
        with gr.TabItem("Soci Morosi"):
            report_morosi_df = gr.DataFrame()
            with gr.Row():
                giorni_scadenza = gr.Number(label="Giorni di Scadenza Minimi", value=0)
                importo_minimo = gr.Number(label="Importo Minimo Insoluto", value=0)
                include_sospesi = gr.Checkbox(label="Includi Sospesi")
                refresh_morosi_btn = gr.Button("🔄 Aggiorna Report")
        with gr.TabItem("Tesserati FIV"):
            report_fiv_df = gr.DataFrame()
            with gr.Row():
                stato_tesseramento = gr.Dropdown(label="Stato Tesseramento", choices=["", "Da rinnovare", "In corso", "Approvato", "Scaduto"], value="")
                refresh_fiv_btn = gr.Button("🔄 Aggiorna Report")
        with gr.TabItem("Certificati in Scadenza"):
            report_certificati_df = gr.DataFrame()
            with gr.Row():
                giorni_alla_scadenza = gr.Number(label="Giorni alla Scadenza", value=30)
                refresh_certificati_btn = gr.Button("🔄 Aggiorna Report")

    def load_morosi_report(giorni, importo, include):
        return api_client.get_report_soci_morosi(giorni, importo if importo > 0 else None, include)
    def load_fiv_report(stato):
        return api_client.get_report_tesserati_fiv(stato)
    def load_certificati_report(giorni):
        return api_client.get_report_certificati_in_scadenza(giorni)

    refresh_morosi_btn.click(load_morosi_report, inputs=[giorni_scadenza, importo_minimo, include_sospesi], outputs=report_morosi_df)
    refresh_fiv_btn.click(load_fiv_report, inputs=[stato_tesseramento], outputs=report_fiv_df)
    refresh_certificati_btn.click(load_certificati_report, inputs=[giorni_alla_scadenza], outputs=report_certificati_df)

    all_reports = [report_morosi_df, report_fiv_df, report_certificati_df]
    def load_all_reports():
        return load_morosi_report(0, 0, False), load_fiv_report(""), load_certificati_report(30)

    return all_reports, load_all_reports

# --- Main UI Layout ---
def create_ui():
    with gr.Blocks(theme=gr.themes.Soft(), title="UMAMI ASD Management") as app:
        gr.Markdown("# Gestione UMAMI ASD")
        with gr.Tabs():
            with gr.TabItem("🏠 Dashboard"):
                gr.Markdown("## Benvenuti nel sistema di gestione UMAMI.")
                gr.Markdown("Seleziona una sezione dal menu per iniziare.")
            with gr.TabItem("👤 Anagrafiche"):
                with gr.Tabs():
                    with gr.TabItem("Associati"):
                        associati_comp, load_associati_fn = create_associati_ui()
                    with gr.TabItem("Fornitori"):
                        fornitori_comp, load_fornitori_fn = create_fornitori_ui()
                    with gr.TabItem("Chiavi Elettroniche"):
                        chiavi_comp, load_chiavi_fn = create_chiavi_ui()
            with gr.TabItem("⚙️ Servizi"):
                servizi_comp, load_servizi_fn = create_servizi_ui()
            with gr.TabItem("📊 Report"):
                report_comps, load_reports_fn = create_report_ui()

        def on_load():
            load_associati_res = load_associati_fn("", "")
            load_fornitori_res = load_fornitori_fn("")
            load_chiavi_res = load_chiavi_fn()
            load_servizi_res = load_servizi_fn("", "")
            load_reports_res = load_reports_fn()
            return (
                load_associati_res,
                load_fornitori_res,
                load_chiavi_res,
                load_servizi_res,
                *load_reports_res
            )

        app.load(
            on_load, 
            outputs=[
                associati_comp, 
                fornitori_comp, 
                chiavi_comp, 
                servizi_comp,
                *report_comps
            ]
        )

    return app

# --- Main Execution ---
if __name__ == "__main__":
    umami_app = create_ui()
    umami_app.launch()
