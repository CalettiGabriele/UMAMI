#!/usr/bin/env python3
"""
UMAMI FastAPI Application
=========================

API REST per il sistema di gestione ASD UMAMI.
Implementa tutti gli endpoint descritti nella specifica API.
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import logging

# Import delle funzioni di business logic
from .api_functions import (
    # Associati
    get_associati, create_associato, get_associato_by_id, update_associato,
    create_tesseramento_fiv,
    # Fornitori
    get_fornitori, create_fornitore, get_fornitore_by_id, update_fornitore, delete_fornitore,
    # Chiavi Elettroniche
    get_chiave_elettronica, create_or_update_chiave_elettronica, ricarica_crediti_docce,
    # Servizi
    get_servizi_fisici, create_servizio_fisico, get_servizio_fisico_by_id,
    # Report
    get_soci_morosi, get_tesserati_fiv, get_certificati_in_scadenza,
    # Eccezioni
    DatabaseError, NotFoundError
)

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializzazione FastAPI
app = FastAPI(
    title="UMAMI API",
    description="API REST per il sistema di gestione ASD UMAMI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== MODELLI PYDANTIC =====

class AssociatoCreate(BaseModel):
    fk_associato_riferimento: Optional[int] = None
    nome: str = Field(..., min_length=1, max_length=50)
    cognome: str = Field(..., min_length=1, max_length=50)
    codice_fiscale: str = Field(..., min_length=16, max_length=16)
    data_nascita: date
    indirizzo: str = Field(..., max_length=200)
    email: EmailStr
    telefono: str = Field(..., max_length=20)
    data_iscrizione: date
    stato_associato: str = Field(..., pattern="^(Attivo|Sospeso|Cessato)$")

class AssociatoUpdate(BaseModel):
    fk_associato_riferimento: Optional[int] = None
    nome: Optional[str] = Field(None, min_length=1, max_length=50)
    cognome: Optional[str] = Field(None, min_length=1, max_length=50)
    codice_fiscale: Optional[str] = Field(None, min_length=16, max_length=16)
    data_nascita: Optional[date] = None
    indirizzo: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    stato_associato: Optional[str] = Field(None, pattern="^(Attivo|Sospeso|Cessato)$")

class TesseramentoFIVCreate(BaseModel):
    numero_tessera_fiv: str = Field(..., max_length=20)
    scadenza_tesseramento_fiv: date
    scadenza_certificato_medico: date

class FornitoreCreate(BaseModel):
    ragione_sociale: str = Field(..., min_length=1, max_length=100)
    partita_iva: str = Field(..., min_length=11, max_length=11)
    email: EmailStr
    telefono: str = Field(..., max_length=20)

class FornitoreUpdate(BaseModel):
    ragione_sociale: Optional[str] = Field(None, min_length=1, max_length=100)
    partita_iva: Optional[str] = Field(None, min_length=11, max_length=11)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)

class ChiaveElettronicaCreate(BaseModel):
    key_code: str = Field(..., max_length=50)
    in_regola: bool = True
    credito: Optional[float] = Field(0.00, ge=0)

class RicaricaCrediti(BaseModel):
    crediti_da_aggiungere: float = Field(..., gt=0)

class ServizioFisicoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    descrizione: str = Field(..., max_length=500)
    tipo: str = Field(..., max_length=50)
    stato: str = Field(..., pattern="^(Disponibile|Occupato|In Manutenzione)$")

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# ===== EXCEPTION HANDLERS =====

@app.exception_handler(NotFoundError)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not Found", "detail": str(exc)}
    )

@app.exception_handler(DatabaseError)
async def database_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Database Error", "detail": str(exc)}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "detail": str(exc)}
    )

# ===== ENDPOINTS ASSOCIATI =====

@app.get("/associati", summary="Lista associati")
async def list_associati(
    limit: int = Query(20, ge=1, le=100, description="Numero massimo di risultati"),
    offset: int = Query(0, ge=0, description="Offset per paginazione"),
    search: Optional[str] = Query(None, description="Ricerca per nome, cognome, email o codice fiscale"),
    stato: Optional[str] = Query(None, pattern="^(Attivo|Sospeso|Cessato)$", description="Filtra per stato"),
    tesserato_fiv: Optional[bool] = Query(None, description="Filtra per tesseramento FIV")
):
    """Recupera la lista degli associati con filtri e paginazione"""
    try:
        return get_associati(limit=limit, offset=offset, search=search, 
                           stato=stato, tesserato_fiv=tesserato_fiv)
    except Exception as e:
        logger.error(f"Error in list_associati: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/associati", status_code=201, summary="Crea associato")
async def create_associato_endpoint(associato: AssociatoCreate):
    """Crea un nuovo associato"""
    try:
        return create_associato(associato.dict())
    except Exception as e:
        logger.error(f"Error in create_associato: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/associati/{associato_id}", summary="Dettagli associato")
async def get_associato_endpoint(
    associato_id: int = Path(..., description="ID dell'associato")
):
    """Recupera i dettagli di un associato"""
    try:
        return get_associato_by_id(associato_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_associato: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/associati/{associato_id}", summary="Aggiorna associato")
async def update_associato_endpoint(
    associato_id: int = Path(..., description="ID dell'associato"),
    associato: AssociatoUpdate = Body(...)
):
    """Aggiorna i dati di un associato"""
    try:
        # Filtra solo i campi non None
        update_data = {k: v for k, v in associato.dict().items() if v is not None}
        return update_associato(associato_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_associato: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/associati/{associato_id}/tesseramento-fiv", status_code=201, summary="Crea/aggiorna tesseramento FIV")
async def create_tesseramento_fiv_endpoint(
    associato_id: int = Path(..., description="ID dell'associato"),
    tesseramento: TesseramentoFIVCreate = Body(...)
):
    """Crea o aggiorna il tesseramento FIV di un associato"""
    try:
        return create_tesseramento_fiv(associato_id, tesseramento.dict())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_tesseramento_fiv: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS FORNITORI =====

@app.get("/fornitori", summary="Lista fornitori")
async def list_fornitori(
    limit: int = Query(20, ge=1, le=100, description="Numero massimo di risultati"),
    offset: int = Query(0, ge=0, description="Offset per paginazione"),
    search: Optional[str] = Query(None, description="Ricerca per ragione sociale, P.IVA o email"),
    attivo: Optional[bool] = Query(None, description="Filtra per stato attivo")
):
    """Recupera la lista dei fornitori con filtri e paginazione"""
    try:
        return get_fornitori(limit=limit, offset=offset, search=search, attivo=attivo)
    except Exception as e:
        logger.error(f"Error in list_fornitori: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fornitori", status_code=201, summary="Crea fornitore")
async def create_fornitore_endpoint(fornitore: FornitoreCreate):
    """Crea un nuovo fornitore"""
    try:
        return create_fornitore(fornitore.dict())
    except Exception as e:
        logger.error(f"Error in create_fornitore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fornitori/{fornitore_id}", summary="Dettagli fornitore")
async def get_fornitore_endpoint(
    fornitore_id: int = Path(..., description="ID del fornitore")
):
    """Recupera i dettagli di un fornitore"""
    try:
        return get_fornitore_by_id(fornitore_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_fornitore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/fornitori/{fornitore_id}", summary="Aggiorna fornitore")
async def update_fornitore_endpoint(
    fornitore_id: int = Path(..., description="ID del fornitore"),
    fornitore: FornitoreUpdate = Body(...)
):
    """Aggiorna i dati di un fornitore"""
    try:
        update_data = {k: v for k, v in fornitore.dict().items() if v is not None}
        return update_fornitore(fornitore_id, update_data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in update_fornitore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/fornitori/{fornitore_id}", status_code=204, summary="Elimina fornitore")
async def delete_fornitore_endpoint(
    fornitore_id: int = Path(..., description="ID del fornitore")
):
    """Elimina un fornitore (solo se non ha fatture associate)"""
    try:
        delete_fornitore(fornitore_id)
        return {"message": "Fornitore eliminato con successo"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in delete_fornitore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS CHIAVI ELETTRONICHE =====

@app.get("/associati/{associato_id}/chiave-elettronica", summary="Dettagli chiave elettronica")
async def get_chiave_elettronica_endpoint(
    associato_id: int = Path(..., description="ID dell'associato")
):
    """Recupera i dettagli della chiave elettronica di un associato"""
    try:
        return get_chiave_elettronica(associato_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_chiave_elettronica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/associati/{associato_id}/chiave-elettronica", status_code=201, summary="Crea/aggiorna chiave elettronica")
async def create_chiave_elettronica_endpoint(
    associato_id: int = Path(..., description="ID dell'associato"),
    chiave: ChiaveElettronicaCreate = Body(...)
):
    """Crea o aggiorna la chiave elettronica di un associato"""
    try:
        return create_or_update_chiave_elettronica(associato_id, chiave.dict())
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_chiave_elettronica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/associati/{associato_id}/chiave-elettronica/ricarica", summary="Ricarica crediti docce")
async def ricarica_crediti_endpoint(
    associato_id: int = Path(..., description="ID dell'associato"),
    ricarica: RicaricaCrediti = Body(...)
):
    """Ricarica i crediti docce per una chiave elettronica"""
    try:
        return ricarica_crediti_docce(associato_id, ricarica.crediti_da_aggiungere)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in ricarica_crediti: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS SERVIZI FISICI =====

@app.get("/servizi-fisici", summary="Lista servizi fisici")
async def list_servizi_fisici(
    stato: Optional[str] = Query(None, pattern="^(Disponibile|Occupato|In Manutenzione)$", description="Filtra per stato"),
    tipo: Optional[str] = Query(None, description="Filtra per tipo/categoria")
):
    """Recupera la lista dei servizi fisici con filtri"""
    try:
        return get_servizi_fisici(stato=stato, tipo=tipo)
    except Exception as e:
        logger.error(f"Error in list_servizi_fisici: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/servizi-fisici", status_code=201, summary="Crea servizio fisico")
async def create_servizio_fisico_endpoint(servizio: ServizioFisicoCreate):
    """Crea un nuovo servizio fisico"""
    try:
        return create_servizio_fisico(servizio.dict())
    except Exception as e:
        logger.error(f"Error in create_servizio_fisico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/servizi-fisici/{servizio_id}", summary="Dettagli servizio fisico")
async def get_servizio_fisico_endpoint(
    servizio_id: int = Path(..., description="ID del servizio fisico")
):
    """Recupera i dettagli di un servizio fisico"""
    try:
        return get_servizio_fisico_by_id(servizio_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_servizio_fisico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS REPORT =====

@app.get("/report/soci-morosi", summary="Report soci morosi")
async def report_soci_morosi(
    giorni_scadenza: int = Query(0, ge=0, description="Minimo giorni di scadenza"),
    importo_minimo: Optional[float] = Query(None, ge=0, description="Importo minimo dovuto"),
    include_sospesi: bool = Query(False, description="Includi associati sospesi")
):
    """Genera il report dei soci morosi (con fatture non pagate)"""
    try:
        return get_soci_morosi(
            giorni_scadenza=giorni_scadenza,
            importo_minimo=importo_minimo,
            include_sospesi=include_sospesi
        )
    except Exception as e:
        logger.error(f"Error in report_soci_morosi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/tesserati-fiv", summary="Report tesserati FIV")
async def report_tesserati_fiv(
    stato_tesseramento: Optional[str] = Query(None, pattern="^(Attivo|Scaduto)$", description="Filtra per stato tesseramento")
):
    """Genera il report dei tesserati FIV"""
    try:
        results = get_tesserati_fiv(stato_tesseramento=stato_tesseramento)
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in report_tesserati_fiv: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/certificati-in-scadenza", summary="Report certificati medici in scadenza")
async def report_certificati_in_scadenza(
    giorni_alla_scadenza: int = Query(30, ge=1, le=365, description="Giorni alla scadenza")
):
    """Genera il report dei certificati medici in scadenza"""
    try:
        results = get_certificati_in_scadenza(giorni_alla_scadenza=giorni_alla_scadenza)
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in report_certificati_in_scadenza: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT HEALTH CHECK =====

@app.get("/health", summary="Health check")
async def health_check():
    """Endpoint per verificare lo stato dell'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/", summary="Root endpoint")
async def root():
    """Endpoint radice con informazioni sull'API"""
    return {
        "message": "UMAMI API - Sistema di gestione ASD",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# ===== CONFIGURAZIONE CORS (se necessario) =====
# from fastapi.middleware.cors import CORSMiddleware
# 
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In produzione specificare domini specifici
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
