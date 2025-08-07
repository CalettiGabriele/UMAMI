import requests
import pandas as pd
import gradio as gr

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8003"

# --- Generic API Request Function ---
def _request(method, endpoint, params=None, json=None):
    try:
        response = requests.request(method, f"{BASE_URL}{endpoint}", params=params, json=json)
        response.raise_for_status()
        if response.status_code == 204:  # No Content
            return True
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        gr.Warning(f"Errore API: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        gr.Warning(f"Errore imprevisto: {str(e)}")
        return None

# --- Associati ---
def get_associati(search="", stato="", tesserato_fiv=None):
    params = {}
    if search: params['search'] = search
    if stato: params['stato'] = stato
    if tesserato_fiv is not None: params['tesserato_fiv'] = tesserato_fiv
    data = _request("GET", "/associati", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def get_associato(associato_id):
    return _request("GET", f"/associati/{associato_id}")

def create_associato(associato_data):
    return _request("POST", "/associati", json=associato_data)

def update_associato(associato_id, associato_data):
    return _request("PUT", f"/associati/{associato_id}", json=associato_data)

def create_tesseramento_fiv(associato_id, tesseramento_data):
    return _request("POST", f"/associati/{associato_id}/tesseramento-fiv", json=tesseramento_data)

# --- Fornitori ---
def get_fornitori(search=""):
    params = {'search': search} if search else {}
    data = _request("GET", "/fornitori", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def get_fornitore(fornitore_id):
    return _request("GET", f"/fornitori/{fornitore_id}")

def create_fornitore(fornitore_data):
    return _request("POST", "/fornitori", json=fornitore_data)

def update_fornitore(fornitore_id, fornitore_data):
    return _request("PUT", f"/fornitori/{fornitore_id}", json=fornitore_data)

def delete_fornitore(fornitore_id):
    return _request("DELETE", f"/fornitori/{fornitore_id}")

# --- Chiavi Elettroniche ---
def get_chiave_elettronica(associato_id):
    return _request("GET", f"/associati/{associato_id}/chiave-elettronica")

def create_or_update_chiave(associato_id, chiave_data):
    return _request("POST", f"/associati/{associato_id}/chiave-elettronica", json=chiave_data)

def ricarica_crediti(associato_id, crediti):
    return _request("POST", f"/associati/{associato_id}/chiave-elettronica/ricarica", json={'crediti_da_aggiungere': crediti})

# --- Servizi Fisici ---
def get_servizi_fisici(tipo="", stato=""):
    params = {}
    if tipo: params['tipo'] = tipo
    if stato: params['stato'] = stato
    data = _request("GET", "/servizi-fisici", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def get_servizio_fisico(servizio_id):
    return _request("GET", f"/servizi-fisici/{servizio_id}")

def create_servizio_fisico(servizio_data):
    return _request("POST", "/servizi-fisici", json=servizio_data)

def update_servizio_fisico(servizio_id, servizio_data):
    return _request("PUT", f"/servizi-fisici/{servizio_id}", json=servizio_data)

def assign_servizio_fisico(servizio_id, assegnazione_data):
    return _request("POST", f"/servizi-fisici/{servizio_id}/assegnazioni", json=assegnazione_data)

def update_assegnazione_servizio_fisico(assegnazione_id, assegnazione_data):
    return _request("PUT", f"/assegnazioni-servizi-fisici/{assegnazione_id}", json=assegnazione_data)

# --- Report ---
def get_report_soci_morosi(giorni_scadenza=0, importo_minimo=None, include_sospesi=False):
    params = {
        'giorni_scadenza': giorni_scadenza,
        'include_sospesi': include_sospesi
    }
    if importo_minimo is not None:
        params['importo_minimo'] = importo_minimo
    data = _request("GET", "/report/soci-morosi", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def get_report_tesserati_fiv(stato_tesseramento=""):
    params = {'stato_tesseramento': stato_tesseramento} if stato_tesseramento else {}
    data = _request("GET", "/report/tesserati-fiv", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def get_report_certificati_in_scadenza(giorni=30):
    params = {'giorni_alla_scadenza': giorni}
    data = _request("GET", "/report/certificati-in-scadenza", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

# --- Prezzi Servizi ---
def get_prezzi_servizi(categoria=""):
    params = {'categoria': categoria} if categoria else {}
    data = _request("GET", "/prezzi-servizi", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def create_prezzo_servizio(prezzo_data):
    return _request("POST", "/prezzi-servizi", json=prezzo_data)

def update_prezzo_servizio(prezzo_id, prezzo_data):
    return _request("PUT", f"/prezzi-servizi/{prezzo_id}", json=prezzo_data)

def delete_prezzo_servizio(prezzo_id):
    return _request("DELETE", f"/prezzi-servizi/{prezzo_id}")

def get_prezzo_servizio(prezzo_id):
    return _request("GET", f"/prezzi-servizi/{prezzo_id}")

# --- Fatture ---
def get_fatture(tipo="", stato="", search="", associato_id=None, fornitore_id=None):
    params = {}
    if tipo: params['tipo'] = tipo
    if stato: params['stato'] = stato
    if search: params['search'] = search
    if associato_id: params['associato_id'] = associato_id
    if fornitore_id: params['fornitore_id'] = fornitore_id
    data = _request("GET", "/fatture", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def create_fattura(fattura_data):
    return _request("POST", "/fatture", json=fattura_data)

def get_fattura(fattura_id):
    return _request("GET", f"/fatture/{fattura_id}")

def update_fattura(fattura_id, fattura_data):
    return _request("PUT", f"/fatture/{fattura_id}", json=fattura_data)

# --- Pagamenti ---
def get_pagamenti(metodo="", dal=None, al=None, associato_id=None):
    params = {}
    if metodo: params['metodo'] = metodo
    if dal: params['dal'] = dal
    if al: params['al'] = al
    if associato_id: params['associato_id'] = associato_id
    data = _request("GET", "/pagamenti", params=params)
    if data and isinstance(data, list):
        return pd.DataFrame(data)
    elif data and 'results' in data:
        return pd.DataFrame(data['results'])
    return pd.DataFrame()

def create_pagamento(pagamento_data):
    return _request("POST", "/pagamenti", json=pagamento_data)

def get_pagamento(pagamento_id):
    return _request("GET", f"/pagamenti/{pagamento_id}")
