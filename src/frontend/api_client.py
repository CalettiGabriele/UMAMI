import requests
import pandas as pd
import gradio as gr

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8001"

# --- Generic API Request Function ---
def _request(method, endpoint, params=None, json=None):
    try:
        response = requests.request(method, f"{BASE_URL}{endpoint}", params=params, json=json)
        response.raise_for_status()
        if response.status_code == 204:  # No Content
            return True
        return response.json()
    except requests.exceptions.RequestException as e:
        gr.Warning(f"API Error: {e}")
        return None

# --- Associati ---
def get_associati(search="", stato="", tesserato_fiv=None):
    params = {}
    if search: params['search'] = search
    if stato: params['stato'] = stato
    if tesserato_fiv is not None: params['tesserato_fiv'] = tesserato_fiv
    data = _request("GET", "/associati", params=params)
    return pd.DataFrame(data['results']) if data and 'results' in data else pd.DataFrame()

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
    return pd.DataFrame(data['results']) if data and 'results' in data else pd.DataFrame()

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
    return pd.DataFrame(data['results']) if data and 'results' in data else pd.DataFrame()

def create_servizio_fisico(servizio_data):
    return _request("POST", "/servizi-fisici", json=servizio_data)

# --- Report ---
def get_report_soci_morosi(giorni_scadenza=0, importo_minimo=None, include_sospesi=False):
    params = {
        'giorni_scadenza': giorni_scadenza,
        'include_sospesi': include_sospesi
    }
    if importo_minimo is not None:
        params['importo_minimo'] = importo_minimo
    data = _request("GET", "/report/soci-morosi", params=params)
    return pd.DataFrame(data['results']) if data and 'results' in data else pd.DataFrame()

def get_report_tesserati_fiv(stato_tesseramento=""):
    params = {'stato_tesseramento': stato_tesseramento} if stato_tesseramento else {}
    data = _request("GET", "/report/tesserati-fiv", params=params)
    return pd.DataFrame(data['results']) if data and 'results' in data else pd.DataFrame()

def get_report_certificati_in_scadenza(giorni=30):
    params = {'giorni_alla_scadenza': giorni}
    data = _request("GET", "/report/certificati-in-scadenza", params=params)
    return pd.DataFrame(data['results']) if data and 'results' in data else pd.DataFrame()
