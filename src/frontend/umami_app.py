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
    
    def load_data(search_val, stato_val, fiv_val):
        try:
            df = api_client.get_associati(search=search_val, stato=stato_val, tesserato_fiv=fiv_val if fiv_val else None)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_data, [search, stato, tesserato_fiv], associati_table)
    return associati_table

def scheda_associato_ui():
    """Scheda dettaglio associato"""
    gr.Markdown("### 📋 Scheda Associato")
    
    associato_id = gr.Number(label="ID Associato", precision=0)
    load_btn = gr.Button("📥 Carica", variant="primary")
    
    with gr.Group():
        gr.Markdown("#### 📝 Dati Anagrafici")
        with gr.Row():
            nome = gr.Textbox(label="Nome")
            cognome = gr.Textbox(label="Cognome")
            cf = gr.Textbox(label="Codice Fiscale")
        with gr.Row():
            email = gr.Textbox(label="Email")
            telefono = gr.Textbox(label="Telefono")
            stato_assoc = gr.Dropdown(label="Stato", choices=STATO_ASSOCIATO_CHOICES)
    
    with gr.Group():
        gr.Markdown("#### ⛵ Tessera FIV")
        tessera_info = gr.JSON(label="Dati FIV")
    
    with gr.Group():
        gr.Markdown("#### 🔑 Chiave Elettronica")
        chiave_info = gr.JSON(label="Dati Chiave")
    
    def load_associato(aid):
        if not aid:
            return [""] * 6 + [None, None]
        try:
            data = api_client.get_associato(int(aid))
            if data:
                return [
                    safe_get(data, 'nome'), safe_get(data, 'cognome'), safe_get(data, 'codice_fiscale'),
                    safe_get(data, 'email'), safe_get(data, 'telefono'), safe_get(data, 'stato_associato'),
                    data.get('tesseramento_fiv', {}), data.get('chiave_elettronica', {})
                ]
        except Exception as e:
            gr.Warning(f"Errore: {e}")
        return [""] * 6 + [None, None]
    
    load_btn.click(load_associato, [associato_id], [nome, cognome, cf, email, telefono, stato_assoc, tessera_info, chiave_info])

def elenco_fornitori_ui():
    """Elenco Fornitori"""
    gr.Markdown("### 🏢 Gestione Fornitori")
    
    with gr.Row():
        search = gr.Textbox(label="🔍 Cerca", placeholder="Ragione Sociale, P.IVA...")
        refresh_btn = gr.Button("🔄 Aggiorna")
        nuovo_btn = gr.Button("➕ Nuovo Fornitore", variant="primary")
    
    fornitori_table = gr.DataFrame(interactive=False)
    
    def load_fornitori(search_val):
        try:
            df = api_client.get_fornitori(search=search_val)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            gr.Warning(f"Errore: {e}")
            return pd.DataFrame()
    
    refresh_btn.click(load_fornitori, [search], fornitori_table)
    return fornitori_table

def scheda_fornitore_ui():
    """Scheda dettaglio fornitore"""
    gr.Markdown("### 📄 Scheda Fornitore")
    
    fornitore_id = gr.Number(label="ID Fornitore", precision=0)
    load_btn = gr.Button("📥 Carica", variant="primary")
    
    with gr.Group():
        gr.Markdown("#### 🏢 Dati Aziendali")
        with gr.Row():
            ragione_sociale = gr.Textbox(label="Ragione Sociale")
            partita_iva = gr.Textbox(label="Partita IVA")

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
    with gr.Blocks(title="UMAMI - Gestione ASD", theme=gr.themes.Soft()) as app:
        gr.Markdown("""
        # 🏄‍♂️ UMAMI - Sistema di Gestione ASD
        ### Gestione completa per Associazioni Sportive Dilettantistiche
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
        server_port=7860,
        show_error=True,
        share=False
    )
