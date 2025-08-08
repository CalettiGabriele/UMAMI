#!/usr/bin/env python3
"""
UMAMI FastAPI Application
=========================

API REST per il sistema di gestione ASD UMAMI.
Implementa tutti gli endpoint descritti nella specifica API.
"""

from fastapi import FastAPI, HTTPException, Query, Path, Body, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date
import logging
import sqlite3
import os
from pathlib import Path as PathLib

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

# Database configuration
DB_PATH = PathLib(__file__).parent.parent / "database" / "data" / "umami.db"

def get_db_connection():
    """Get database connection"""
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Database not found")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# Custom exceptions
class DatabaseError(Exception):
    pass

class NotFoundError(Exception):
    pass

# ===== MODELLI PYDANTIC =====

# Associati Models
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
    stato_associato: str = Field(..., pattern="^(Attivo|Sospeso|Scaduto|Cessato)$")

class AssociatoUpdate(BaseModel):
    fk_associato_riferimento: Optional[int] = None
    nome: Optional[str] = Field(None, min_length=1, max_length=50)
    cognome: Optional[str] = Field(None, min_length=1, max_length=50)
    codice_fiscale: Optional[str] = Field(None, min_length=16, max_length=16)
    data_nascita: Optional[date] = None
    indirizzo: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    stato_associato: Optional[str] = Field(None, pattern="^(Attivo|Sospeso|Scaduto|Cessato)$")

class TesseramentoFIVCreate(BaseModel):
    numero_tessera_fiv: str = Field(..., max_length=20)
    scadenza_tesseramento_fiv: date
    scadenza_certificato_medico: date

# Fornitori Models
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

# Chiavi Elettroniche Models
class ChiaveElettronicaCreate(BaseModel):
    key_code: str = Field(..., max_length=50)
    in_regola: bool = True
    credito: Optional[float] = Field(0.00, ge=0)

class RicaricaCrediti(BaseModel):
    crediti_da_aggiungere: float = Field(..., gt=0)

# Servizi Models
class ServizioFisicoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    descrizione: str = Field(..., max_length=500)
    tipo: str = Field(..., max_length=50)
    stato: str = Field(..., pattern="^(Disponibile|Occupato|In Manutenzione)$")

class ServizioFisicoUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descrizione: Optional[str] = Field(None, max_length=500)
    tipo: Optional[str] = Field(None, max_length=50)
    stato: Optional[str] = Field(None, pattern="^(Disponibile|Occupato|In Manutenzione)$")

class AssegnazioneServizioCreate(BaseModel):
    fk_associato: int
    data_inizio: date
    data_fine: date
    anno_competenza: int
    stato: str = Field("Attivo", pattern="^(Attivo|Sospeso|Terminato)$")

class AssegnazioneServizioUpdate(BaseModel):
    fk_associato: Optional[int] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    anno_competenza: Optional[int] = None
    stato: Optional[str] = Field(None, pattern="^(Attivo|Sospeso|Terminato)$")

class PrestazioneCreate(BaseModel):
    nome_prestazione: str = Field(..., min_length=1, max_length=100)
    descrizione: str = Field(..., max_length=500)
    costo: Optional[float] = Field(0.0, ge=0)

class PrestazioneUpdate(BaseModel):
    nome_prestazione: Optional[str] = Field(None, min_length=1, max_length=100)
    descrizione: Optional[str] = Field(None, max_length=500)
    costo: Optional[float] = Field(None, ge=0)

class ErogazioneCreate(BaseModel):
    fk_associato: int
    data_erogazione: datetime

# Prezzi Servizi Models
class PrezzoServizioCreate(BaseModel):
    id_categoria_servizio: int
    costo: float = Field(..., ge=0)

class PrezzoServizioUpdate(BaseModel):
    costo: Optional[float] = Field(None, ge=0)

# Fatture Models
class DettaglioFatturaCreate(BaseModel):
    descrizione: str = Field(..., max_length=500)
    quantita: int = Field(..., ge=1)
    prezzo_unitario: float = Field(..., ge=0)
    importo_totale: float = Field(..., ge=0)

class FatturaCreate(BaseModel):
    tipo_fattura: str = Field(..., pattern="^(Attiva|Passiva)$")
    fk_associato: Optional[int] = None
    fk_fornitore: Optional[int] = None
    numero_fattura: str = Field(..., max_length=50)
    data_emissione: date
    data_scadenza: date
    importo_imponibile: float = Field(..., ge=0)
    importo_iva: float = Field(..., ge=0)
    importo_totale: float = Field(..., ge=0)
    stato: str = Field("Emessa", pattern="^(Emessa|Pagata|Scaduta|Annullata)$")
    dettagli: List[DettaglioFatturaCreate]

class GenerazioneFattureRequest(BaseModel):
    periodo_inizio: date
    periodo_fine: date
    data_emissione: date
    data_scadenza: date

# Pagamenti Models
class PagamentoCreate(BaseModel):
    data_pagamento: date
    importo: float = Field(..., gt=0)
    metodo: str = Field(..., max_length=50)
    tipo: str = Field(..., pattern="^(Entrata|Uscita)$")

# Response Models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None

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
        content={"error": "Validation Error", "detail": str(exc)}
    )

# ===== UTILITY FUNCTIONS =====

def dict_factory(cursor, row):
    """Convert sqlite row to dict"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = True):
    """Execute database query with error handling"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount
            
        conn.commit()
        conn.close()
        return result
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database operation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise DatabaseError(f"Unexpected error: {str(e)}")

# ===== ENDPOINTS ASSOCIATI =====

@app.get("/associati", summary="Lista associati")
async def list_associati(
    limit: int = Query(20, ge=1, le=100, description="Numero massimo di risultati"),
    offset: int = Query(0, ge=0, description="Offset per paginazione"),
    search: Optional[str] = Query(None, description="Ricerca per nome, cognome, email o codice fiscale"),
    stato: Optional[str] = Query(None, pattern="^(Attivo|Sospeso|Scaduto|Cessato)$", description="Filtra per stato"),
    tesserato_fiv: Optional[bool] = Query(None, description="Filtra per tesseramento FIV")
):
    """Recupera la lista degli associati con filtri e paginazione"""
    try:
        # Build query with filters
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("(nome LIKE ? OR cognome LIKE ? OR email LIKE ? OR codice_fiscale LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if stato:
            where_clauses.append("stato_associato = ?")
            params.append(stato)
        
        if tesserato_fiv is not None:
            if tesserato_fiv:
                where_clauses.append("id_associato IN (SELECT fk_associato FROM TessereFIV)")
            else:
                where_clauses.append("id_associato NOT IN (SELECT fk_associato FROM TessereFIV)")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Count total
        count_query = f"SELECT COUNT(*) as count FROM Associati WHERE {where_clause}"
        count_result = execute_query(count_query, tuple(params), fetch_one=True)
        total_count = count_result['count'] if count_result else 0
        
        # Get results
        query = f"""
        SELECT id_associato, nome, cognome, codice_fiscale, stato_associato, fk_associato_riferimento
        FROM Associati 
        WHERE {where_clause}
        ORDER BY cognome, nome
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = execute_query(query, tuple(params))
        
        return {
            "count": total_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in list_associati: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/associati", status_code=201, summary="Crea associato")
async def create_associato_endpoint(associato: AssociatoCreate):
    """Crea un nuovo associato"""
    try:
        # Check if codice_fiscale already exists
        check_query = "SELECT id_associato FROM Associati WHERE codice_fiscale = ?"
        existing = execute_query(check_query, (associato.codice_fiscale,), fetch_one=True)
        if existing:
            raise HTTPException(status_code=400, detail="Codice fiscale già esistente")
        
        # Insert new associato
        insert_query = """
        INSERT INTO Associati (fk_associato_riferimento, nome, cognome, codice_fiscale, 
                              data_nascita, indirizzo, email, telefono, data_iscrizione, stato_associato)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            associato.fk_associato_riferimento,
            associato.nome,
            associato.cognome,
            associato.codice_fiscale,
            associato.data_nascita.isoformat(),
            associato.indirizzo,
            associato.email,
            associato.telefono,
            associato.data_iscrizione.isoformat(),
            associato.stato_associato
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, params)
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return created associato
        return_query = "SELECT * FROM Associati WHERE id_associato = ?"
        result = execute_query(return_query, (new_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_associato: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/associati/{associato_id}", summary="Dettagli associato")
async def get_associato_endpoint(
    associato_id: int = Path(..., description="ID dell'associato")
):
    """Recupera i dettagli di un associato con tutte le relazioni"""
    try:
        # Get associato base info
        query = "SELECT * FROM Associati WHERE id_associato = ?"
        associato = execute_query(query, (associato_id,), fetch_one=True)
        
        if not associato:
            raise HTTPException(status_code=404, detail="Associato non trovato")
        
        # Get tesseramento FIV if exists
        fiv_query = "SELECT * FROM TessereFIV WHERE fk_associato = ?"
        tesseramento_fiv = execute_query(fiv_query, (associato_id,), fetch_one=True)
        
        # Get chiave elettronica if exists
        chiave_query = "SELECT * FROM ChiaviElettroniche WHERE fk_associato = ?"
        chiave_elettronica = execute_query(chiave_query, (associato_id,), fetch_one=True)
        
        # Get servizi fisici assegnati
        servizi_query = """
        SELECT sf.*, asf.data_inizio, asf.data_fine, asf.anno_competenza, asf.stato as stato_assegnazione
        FROM ServiziFisici sf
        JOIN AssegnazioniServiziFisici asf ON sf.id_servizio_fisico = asf.fk_servizio_fisico
        WHERE asf.fk_associato = ?
        ORDER BY asf.anno_competenza DESC
        """
        servizi_fisici = execute_query(servizi_query, (associato_id,))
        
        # Get erogazioni prestazioni
        prestazioni_query = """
        SELECT p.*, ep.data_erogazione
        FROM Prestazioni p
        JOIN ErogazioniPrestazioni ep ON p.id_prestazione = ep.fk_prestazione
        WHERE ep.fk_associato = ?
        ORDER BY ep.data_erogazione DESC
        """
        prestazioni = execute_query(prestazioni_query, (associato_id,))
        
        result = dict(associato)
        result['tesseramento_fiv'] = tesseramento_fiv
        result['chiave_elettronica'] = chiave_elettronica
        result['servizi_fisici'] = servizi_fisici
        result['prestazioni'] = prestazioni
        
        return result
        
    except HTTPException:
        raise
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
        # Check if associato exists
        check_query = "SELECT id_associato FROM Associati WHERE id_associato = ?"
        existing = execute_query(check_query, (associato_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Associato non trovato")
        
        # Build update query with only non-None fields
        update_data = {k: v for k, v in associato.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
        
        # Check codice_fiscale uniqueness if being updated
        if 'codice_fiscale' in update_data:
            cf_check_query = "SELECT id_associato FROM Associati WHERE codice_fiscale = ? AND id_associato != ?"
            cf_existing = execute_query(cf_check_query, (update_data['codice_fiscale'], associato_id), fetch_one=True)
            if cf_existing:
                raise HTTPException(status_code=400, detail="Codice fiscale già esistente")
        
        # Convert dates to ISO format
        if 'data_nascita' in update_data:
            update_data['data_nascita'] = update_data['data_nascita'].isoformat()
        
        set_clauses = [f"{k} = ?" for k in update_data.keys()]
        update_query = f"UPDATE Associati SET {', '.join(set_clauses)} WHERE id_associato = ?"
        
        params = list(update_data.values()) + [associato_id]
        execute_query(update_query, tuple(params), fetch_all=False)
        
        # Return updated associato
        return_query = "SELECT * FROM Associati WHERE id_associato = ?"
        result = execute_query(return_query, (associato_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
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
        # Check if associato exists
        check_query = "SELECT id_associato FROM Associati WHERE id_associato = ?"
        existing = execute_query(check_query, (associato_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Associato non trovato")
        
        # Check if tessera number is unique
        tessera_check_query = "SELECT fk_associato FROM TessereFIV WHERE numero_tessera_fiv = ? AND fk_associato != ?"
        tessera_existing = execute_query(tessera_check_query, (tesseramento.numero_tessera_fiv, associato_id), fetch_one=True)
        if tessera_existing:
            raise HTTPException(status_code=400, detail="Numero tessera FIV già esistente")
        
        # Check if tesseramento already exists for this associato
        existing_fiv_query = "SELECT fk_associato FROM TessereFIV WHERE fk_associato = ?"
        existing_fiv = execute_query(existing_fiv_query, (associato_id,), fetch_one=True)
        
        if existing_fiv:
            # Update existing
            update_query = """
            UPDATE TessereFIV 
            SET numero_tessera_fiv = ?, scadenza_tesseramento_fiv = ?, scadenza_certificato_medico = ?
            WHERE fk_associato = ?
            """
            params = (
                tesseramento.numero_tessera_fiv,
                tesseramento.scadenza_tesseramento_fiv.isoformat(),
                tesseramento.scadenza_certificato_medico.isoformat(),
                associato_id
            )
        else:
            # Insert new
            update_query = """
            INSERT INTO TessereFIV (fk_associato, numero_tessera_fiv, scadenza_tesseramento_fiv, scadenza_certificato_medico)
            VALUES (?, ?, ?, ?)
            """
            params = (
                associato_id,
                tesseramento.numero_tessera_fiv,
                tesseramento.scadenza_tesseramento_fiv.isoformat(),
                tesseramento.scadenza_certificato_medico.isoformat()
            )
        
        execute_query(update_query, params, fetch_all=False)
        
        # Return created/updated tesseramento
        return_query = "SELECT * FROM TessereFIV WHERE fk_associato = ?"
        result = execute_query(return_query, (associato_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
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
        # Build query with filters
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("(ragione_sociale LIKE ? OR partita_iva LIKE ? OR email LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Note: attivo filter not implemented as there's no 'attivo' field in Fornitori table
        # This would require adding an 'attivo' boolean field to the database schema
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Count total
        count_query = f"SELECT COUNT(*) as count FROM Fornitori WHERE {where_clause}"
        count_result = execute_query(count_query, tuple(params), fetch_one=True)
        total_count = count_result['count'] if count_result else 0
        
        # Get results
        query = f"""
        SELECT id_fornitore, ragione_sociale, partita_iva, email, telefono
        FROM Fornitori 
        WHERE {where_clause}
        ORDER BY ragione_sociale
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        results = execute_query(query, tuple(params))
        
        return {
            "count": total_count,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in list_fornitori: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fornitori", status_code=201, summary="Crea fornitore")
async def create_fornitore_endpoint(fornitore: FornitoreCreate):
    """Crea un nuovo fornitore"""
    try:
        # Check if partita_iva already exists
        check_query = "SELECT id_fornitore FROM Fornitori WHERE partita_iva = ?"
        existing = execute_query(check_query, (fornitore.partita_iva,), fetch_one=True)
        if existing:
            raise HTTPException(status_code=400, detail="Partita IVA già esistente")
        
        # Insert new fornitore
        insert_query = """
        INSERT INTO Fornitori (ragione_sociale, partita_iva, email, telefono)
        VALUES (?, ?, ?, ?)
        """
        
        params = (
            fornitore.ragione_sociale,
            fornitore.partita_iva,
            fornitore.email,
            fornitore.telefono
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, params)
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return created fornitore
        return_query = "SELECT * FROM Fornitori WHERE id_fornitore = ?"
        result = execute_query(return_query, (new_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_fornitore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/fornitori/{fornitore_id}", summary="Dettagli fornitore")
async def get_fornitore_endpoint(
    fornitore_id: int = Path(..., description="ID del fornitore")
):
    """Recupera i dettagli di un fornitore con fatture associate"""
    try:
        # Get fornitore base info
        query = "SELECT * FROM Fornitori WHERE id_fornitore = ?"
        fornitore = execute_query(query, (fornitore_id,), fetch_one=True)
        
        if not fornitore:
            raise HTTPException(status_code=404, detail="Fornitore non trovato")
        
        # Get fatture associate
        fatture_query = """
        SELECT id_fattura, numero_fattura, data_emissione, data_scadenza, 
               importo_totale, stato
        FROM Fatture 
        WHERE fk_fornitore = ?
        ORDER BY data_emissione DESC
        """
        fatture = execute_query(fatture_query, (fornitore_id,))
        
        result = dict(fornitore)
        result['fatture'] = fatture
        
        return result
        
    except HTTPException:
        raise
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
        # Check if fornitore exists
        check_query = "SELECT id_fornitore FROM Fornitori WHERE id_fornitore = ?"
        existing = execute_query(check_query, (fornitore_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Fornitore non trovato")
        
        # Build update query with only non-None fields
        update_data = {k: v for k, v in fornitore.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
        
        # Check partita_iva uniqueness if being updated
        if 'partita_iva' in update_data:
            piva_check_query = "SELECT id_fornitore FROM Fornitori WHERE partita_iva = ? AND id_fornitore != ?"
            piva_existing = execute_query(piva_check_query, (update_data['partita_iva'], fornitore_id), fetch_one=True)
            if piva_existing:
                raise HTTPException(status_code=400, detail="Partita IVA già esistente")
        
        set_clauses = [f"{k} = ?" for k in update_data.keys()]
        update_query = f"UPDATE Fornitori SET {', '.join(set_clauses)} WHERE id_fornitore = ?"
        
        params = list(update_data.values()) + [fornitore_id]
        execute_query(update_query, tuple(params), fetch_all=False)
        
        # Return updated fornitore
        return_query = "SELECT * FROM Fornitori WHERE id_fornitore = ?"
        result = execute_query(return_query, (fornitore_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_fornitore: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/fornitori/{fornitore_id}", status_code=204, summary="Elimina fornitore")
async def delete_fornitore_endpoint(
    fornitore_id: int = Path(..., description="ID del fornitore")
):
    """Elimina un fornitore (solo se non ha fatture associate)"""
    try:
        # Check if fornitore exists
        check_query = "SELECT id_fornitore FROM Fornitori WHERE id_fornitore = ?"
        existing = execute_query(check_query, (fornitore_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Fornitore non trovato")
        
        # Check if fornitore has associated fatture
        fatture_query = "SELECT COUNT(*) as count FROM Fatture WHERE fk_fornitore = ?"
        fatture_count = execute_query(fatture_query, (fornitore_id,), fetch_one=True)
        if fatture_count and fatture_count['count'] > 0:
            raise HTTPException(status_code=400, detail="Impossibile eliminare: fornitore ha fatture associate")
        
        # Delete fornitore
        delete_query = "DELETE FROM Fornitori WHERE id_fornitore = ?"
        execute_query(delete_query, (fornitore_id,), fetch_all=False)
        
        return {"message": "Fornitore eliminato con successo"}
        
    except HTTPException:
        raise
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
        # Check if associato exists
        check_query = "SELECT id_associato FROM Associati WHERE id_associato = ?"
        existing = execute_query(check_query, (associato_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Associato non trovato")
        
        # Get chiave elettronica
        query = "SELECT * FROM ChiaviElettroniche WHERE fk_associato = ?"
        chiave = execute_query(query, (associato_id,), fetch_one=True)
        
        if not chiave:
            raise HTTPException(status_code=404, detail="Chiave elettronica non trovata")
        
        return chiave
        
    except HTTPException:
        raise
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
        # Check if associato exists
        check_query = "SELECT id_associato FROM Associati WHERE id_associato = ?"
        existing = execute_query(check_query, (associato_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Associato non trovato")
        
        # Check if key_code is unique
        key_check_query = "SELECT fk_associato FROM ChiaviElettroniche WHERE key_code = ? AND fk_associato != ?"
        key_existing = execute_query(key_check_query, (chiave.key_code, associato_id), fetch_one=True)
        if key_existing:
            raise HTTPException(status_code=400, detail="Codice chiave già esistente")
        
        # Check if chiave already exists for this associato
        existing_chiave_query = "SELECT fk_associato FROM ChiaviElettroniche WHERE fk_associato = ?"
        existing_chiave = execute_query(existing_chiave_query, (associato_id,), fetch_one=True)
        
        if existing_chiave:
            # Update existing
            update_query = """
            UPDATE ChiaviElettroniche 
            SET key_code = ?, in_regola = ?, credito = ?
            WHERE fk_associato = ?
            """
            params = (chiave.key_code, chiave.in_regola, chiave.credito, associato_id)
        else:
            # Insert new
            update_query = """
            INSERT INTO ChiaviElettroniche (fk_associato, key_code, in_regola, credito)
            VALUES (?, ?, ?, ?)
            """
            params = (associato_id, chiave.key_code, chiave.in_regola, chiave.credito)
        
        execute_query(update_query, params, fetch_all=False)
        
        # Return created/updated chiave
        return_query = "SELECT * FROM ChiaviElettroniche WHERE fk_associato = ?"
        result = execute_query(return_query, (associato_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_chiave_elettronica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/associati/{associato_id}/chiave-elettronica/ricarica-crediti", summary="Ricarica crediti docce")
async def ricarica_crediti_endpoint(
    associato_id: int = Path(..., description="ID dell'associato"),
    ricarica: RicaricaCrediti = Body(...)
):
    """Ricarica i crediti docce per una chiave elettronica"""
    try:
        # Check if chiave exists
        check_query = "SELECT credito FROM ChiaviElettroniche WHERE fk_associato = ?"
        existing = execute_query(check_query, (associato_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Chiave elettronica non trovata")
        
        # Update credito
        new_credito = existing['credito'] + ricarica.crediti_da_aggiungere
        update_query = "UPDATE ChiaviElettroniche SET credito = ? WHERE fk_associato = ?"
        execute_query(update_query, (new_credito, associato_id), fetch_all=False)
        
        # Return updated chiave
        return_query = "SELECT * FROM ChiaviElettroniche WHERE fk_associato = ?"
        result = execute_query(return_query, (associato_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
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
        # Build query with filters
        where_clauses = []
        params = []
        
        if stato:
            where_clauses.append("sf.stato = ?")
            params.append(stato)
        
        if tipo:
            where_clauses.append("sf.categoria = ?")
            params.append(tipo)
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get results with current assignments
        query = f"""
        SELECT sf.id_servizio_fisico, sf.nome, sf.categoria, sf.descrizione, sf.stato,
               ps.costo,
               asf.fk_associato,
               a.nome as assegnatario_nome, a.cognome as assegnatario_cognome
        FROM ServiziFisici sf
        LEFT JOIN PrezziServizi ps ON sf.categoria = ps.id_categoria_servizio
        LEFT JOIN AssegnazioniServiziFisici asf ON sf.id_servizio_fisico = asf.fk_servizio_fisico 
                  AND asf.stato = 'Attivo' AND asf.data_fine >= date('now')
        LEFT JOIN Associati a ON asf.fk_associato = a.id_associato
        WHERE {where_clause}
        ORDER BY sf.categoria, sf.id_servizio_fisico
        """
        
        results = execute_query(query, tuple(params))
        
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in list_servizi_fisici: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/servizi-fisici", status_code=201, summary="Crea servizio fisico")
async def create_servizio_fisico_endpoint(servizio: ServizioFisicoCreate):
    """Crea un nuovo servizio fisico"""
    try:
        # Insert new servizio fisico
        insert_query = """
        INSERT INTO ServiziFisici (nome, descrizione, categoria, stato)
        VALUES (?, ?, ?, ?)
        """
        
        # Use the correct field mapping
        params = (servizio.nome, servizio.descrizione, servizio.tipo, servizio.stato)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, params)
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Return created servizio
        return_query = "SELECT * FROM ServiziFisici WHERE id_servizio_fisico = ?"
        result = execute_query(return_query, (new_id,), fetch_one=True)
        return result
        
    except Exception as e:
        logger.error(f"Error in create_servizio_fisico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/servizi-fisici/{servizio_id}", summary="Dettagli servizio fisico")
async def get_servizio_fisico_endpoint(
    servizio_id: int = Path(..., description="ID del servizio fisico")
):
    """Recupera i dettagli di un servizio fisico con assegnazioni storiche"""
    try:
        # Get servizio base info
        query = "SELECT * FROM ServiziFisici WHERE id_servizio_fisico = ?"
        servizio = execute_query(query, (servizio_id,), fetch_one=True)
        
        if not servizio:
            raise HTTPException(status_code=404, detail="Servizio fisico non trovato")
        
        # Get assegnazioni storiche
        assegnazioni_query = """
        SELECT asf.*, a.nome, a.cognome, a.email
        FROM AssegnazioniServiziFisici asf
        JOIN Associati a ON asf.fk_associato = a.id_associato
        WHERE asf.fk_servizio_fisico = ?
        ORDER BY asf.anno_competenza DESC, asf.data_inizio DESC
        """
        assegnazioni = execute_query(assegnazioni_query, (servizio_id,))
        
        result = dict(servizio)
        result['assegnazioni'] = assegnazioni
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_servizio_fisico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/servizi-fisici/{servizio_id}", summary="Aggiorna servizio fisico")
async def update_servizio_fisico_endpoint(
    servizio_id: int = Path(..., description="ID del servizio fisico"),
    servizio: ServizioFisicoUpdate = Body(...)
):
    """Aggiorna i dati di un servizio fisico"""
    try:
        # Check if servizio exists
        check_query = "SELECT id_servizio_fisico FROM ServiziFisici WHERE id_servizio_fisico = ?"
        existing = execute_query(check_query, (servizio_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Servizio fisico non trovato")
        
        # Build update query with only non-None fields
        update_data = {k: v for k, v in servizio.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
        
        # Map model fields to database columns
        field_mapping = {
            'nome': 'nome',
            'descrizione': 'descrizione', 
            'tipo': 'categoria',
            'stato': 'stato'
        }
        
        set_clauses = [f"{field_mapping.get(k, k)} = ?" for k in update_data.keys()]
        update_query = f"UPDATE ServiziFisici SET {', '.join(set_clauses)} WHERE id_servizio_fisico = ?"
        
        params = list(update_data.values()) + [servizio_id]
        execute_query(update_query, tuple(params), fetch_all=False)
        
        # Return updated servizio
        return_query = "SELECT * FROM ServiziFisici WHERE id_servizio_fisico = ?"
        result = execute_query(return_query, (servizio_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_servizio_fisico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/servizi-fisici/{servizio_id}/assegnazioni", status_code=201, summary="Assegna servizio fisico")
async def create_assegnazione_servizio_endpoint(
    servizio_id: int = Path(..., description="ID del servizio fisico"),
    assegnazione: AssegnazioneServizioCreate = Body(...)
):
    """Assegna un servizio fisico a un socio"""
    try:
        # Check if servizio exists and get details
        servizio_query = "SELECT id_servizio_fisico, nome, categoria FROM ServiziFisici WHERE id_servizio_fisico = ?"
        servizio_row = execute_query(servizio_query, (servizio_id,), fetch_one=True)
        if not servizio_row:
            raise HTTPException(status_code=404, detail="Servizio fisico non trovato")
        
        # Check if associato exists
        associato_query = "SELECT id_associato FROM Associati WHERE id_associato = ?"
        associato_exists = execute_query(associato_query, (assegnazione.fk_associato,), fetch_one=True)
        if not associato_exists:
            raise HTTPException(status_code=404, detail="Associato non trovato")
        
        # Check for overlapping assignments
        overlap_query = """
        SELECT id_assegnazione FROM AssegnazioniServiziFisici 
        WHERE fk_servizio_fisico = ? AND stato = 'Attivo'
        AND ((data_inizio <= ? AND data_fine >= ?) OR (data_inizio <= ? AND data_fine >= ?))
        """
        overlap_exists = execute_query(overlap_query, (
            servizio_id, 
            assegnazione.data_inizio.isoformat(), assegnazione.data_inizio.isoformat(),
            assegnazione.data_fine.isoformat(), assegnazione.data_fine.isoformat()
        ), fetch_one=True)
        
        if overlap_exists:
            raise HTTPException(status_code=400, detail="Servizio già assegnato nel periodo specificato")
        
        # Compute prezzo for the service category
        prezzo_row = execute_query(
            "SELECT costo FROM PrezziServizi WHERE id_categoria_servizio = ?",
            (servizio_row["categoria"],),
            fetch_one=True,
        )
        costo = float(prezzo_row.get("costo") if prezzo_row else 0.0)

        # Transaction: create assegnazione, set servizio Occupato, create fattura + dettaglio
        conn = get_db_connection()
        try:
            cur = conn.cursor()

            # 1) Insert new assegnazione
            insert_query = """
            INSERT INTO AssegnazioniServiziFisici (fk_servizio_fisico, fk_associato, data_inizio, data_fine, anno_competenza, stato)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cur.execute(
                insert_query,
                (
                    servizio_id,
                    assegnazione.fk_associato,
                    assegnazione.data_inizio.isoformat(),
                    assegnazione.data_fine.isoformat(),
                    assegnazione.anno_competenza,
                    assegnazione.stato,
                ),
            )
            new_id = cur.lastrowid

            # 2) Update servizio status to Occupato
            cur.execute("UPDATE ServiziFisici SET stato = 'Occupato' WHERE id_servizio_fisico = ?", (servizio_id,))

            # 3) Create Fattura (Attiva)
            imponibile = costo
            iva = 0.00  # IVA management can be added later
            totale = imponibile + iva
            today = date.today()
            scadenza = today + timedelta(days=30)
            numero_fattura = f"SF-{assegnazione.fk_associato}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            attempt = 0
            while True:
                check = cur.execute("SELECT 1 FROM Fatture WHERE numero_fattura = ?", (numero_fattura,)).fetchone()
                if not check:
                    break
                attempt += 1
                numero_fattura = f"SF-{assegnazione.fk_associato}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{attempt}"

            cur.execute(
                """
                INSERT INTO Fatture (
                    numero_fattura, data_emissione, data_scadenza, fk_associato,
                    fk_fornitore, tipo_fattura, importo_imponibile, importo_iva, importo_totale, stato
                ) VALUES (?, ?, ?, ?, NULL, 'Attiva', ?, ?, ?, 'Emessa')
                """,
                (
                    numero_fattura,
                    today.strftime("%Y-%m-%d"),
                    scadenza.strftime("%Y-%m-%d"),
                    assegnazione.fk_associato,
                    imponibile,
                    iva,
                    totale,
                ),
            )
            id_fattura = cur.lastrowid

            # 4) Create DettaglioFattura linked to this assegnazione
            descr = (
                f"Assegnazione {servizio_row['nome']} (servizio {servizio_id}) "
                f"dal {assegnazione.data_inizio.isoformat()} al {assegnazione.data_fine.isoformat()}"
            )
            cur.execute(
                """
                INSERT INTO DettagliFatture (
                    fk_fattura, descrizione, quantita, prezzo_unitario, importo_totale,
                    fk_assegnazione_servizio_fisico, fk_erogazione_servizio_prestazionale
                ) VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    id_fattura,
                    descr,
                    1.0,
                    costo,
                    costo,
                    new_id,
                ),
            )

            conn.commit()

            # Return created assegnazione plus invoice info
            created = execute_query("SELECT * FROM AssegnazioniServiziFisici WHERE id_assegnazione = ?", (new_id,), fetch_one=True)
            created = dict(created)
            created.update({
                "id_fattura": id_fattura,
                "numero_fattura": numero_fattura,
                "importo_totale": totale,
            })
            return created
        except Exception as inner_e:
            conn.rollback()
            logger.error(f"Transaction error in create_assegnazione_servizio: {inner_e}")
            raise HTTPException(status_code=500, detail=str(inner_e))
        finally:
            conn.close()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_assegnazione_servizio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/assegnazioni-servizi-fisici/{assegnazione_id}", summary="Aggiorna assegnazione servizio fisico")
async def update_assegnazione_servizio_endpoint(
    assegnazione_id: int = Path(..., description="ID dell'assegnazione"),
    assegnazione: AssegnazioneServizioUpdate = Body(...)
):
    """Aggiorna un'assegnazione di servizio fisico esistente"""
    try:
        # Check if assegnazione exists
        check_query = "SELECT * FROM AssegnazioniServiziFisici WHERE id_assegnazione = ?"
        existing = execute_query(check_query, (assegnazione_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Assegnazione non trovata")
        
        # Build update query dynamically
        update_data = assegnazione.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
        
        # Convert dates to ISO format if present
        if 'data_inizio' in update_data and update_data['data_inizio']:
            update_data['data_inizio'] = update_data['data_inizio'].isoformat()
        if 'data_fine' in update_data and update_data['data_fine']:
            update_data['data_fine'] = update_data['data_fine'].isoformat()
        
        set_clauses = [f"{key} = ?" for key in update_data.keys()]
        update_query = f"UPDATE AssegnazioniServiziFisici SET {', '.join(set_clauses)} WHERE id_assegnazione = ?"
        
        params = list(update_data.values()) + [assegnazione_id]
        execute_query(update_query, tuple(params), fetch_all=False)
        
        # Return updated assegnazione
        return_query = "SELECT * FROM AssegnazioniServiziFisici WHERE id_assegnazione = ?"
        result = execute_query(return_query, (assegnazione_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_assegnazione_servizio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS SERVIZI PRESTAZIONALI =====

@app.get("/servizi-prestazionali", summary="Lista servizi prestazionali")
async def list_servizi_prestazionali(
    search: Optional[str] = Query(None, description="Cerca per nome prestazione")
):
    """Recupera la lista dei servizi prestazionali"""
    try:
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("nome_prestazione LIKE ?")
            params.append(f"%{search}%")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT id_prestazione, nome_prestazione, descrizione, costo
        FROM Prestazioni 
        WHERE {where_clause}
        ORDER BY nome_prestazione
        """
        
        results = execute_query(query, tuple(params))
        
        return {
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in list_servizi_prestazionali: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/servizi-prestazionali", status_code=201, summary="Crea servizio prestazionale")
async def create_servizio_prestazionale_endpoint(prestazione: PrestazioneCreate):
    """Crea un nuovo servizio prestazionale"""
    try:
        insert_query = """
        INSERT INTO Prestazioni (nome_prestazione, descrizione, costo)
        VALUES (?, ?, ?)
        """
        
        params = (
            prestazione.nome_prestazione,
            prestazione.descrizione,
            prestazione.costo
        )
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(insert_query, params)
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return_query = "SELECT * FROM Prestazioni WHERE id_prestazione = ?"
        result = execute_query(return_query, (new_id,), fetch_one=True)
        return result
        
    except Exception as e:
        logger.error(f"Error in create_servizio_prestazionale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/servizi-prestazionali/{prestazione_id}", summary="Dettagli servizio prestazionale")
async def get_servizio_prestazionale_endpoint(
    prestazione_id: int = Path(..., description="ID del servizio prestazionale")
):
    """Recupera i dettagli di un servizio prestazionale"""
    try:
        query = "SELECT * FROM Prestazioni WHERE id_prestazione = ?"
        prestazione = execute_query(query, (prestazione_id,), fetch_one=True)
        
        if not prestazione:
            raise HTTPException(status_code=404, detail="Servizio prestazionale non trovato")
        
        return prestazione
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_servizio_prestazionale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/servizi-prestazionali/{prestazione_id}", summary="Aggiorna servizio prestazionale")
async def update_servizio_prestazionale_endpoint(
    prestazione_id: int = Path(..., description="ID del servizio prestazionale"),
    prestazione: PrestazioneUpdate = Body(...)
):
    """Aggiorna i dati di un servizio prestazionale"""
    try:
        check_query = "SELECT id_prestazione FROM Prestazioni WHERE id_prestazione = ?"
        existing = execute_query(check_query, (prestazione_id,), fetch_one=True)
        if not existing:
            raise HTTPException(status_code=404, detail="Servizio prestazionale non trovato")
        
        update_data = {k: v for k, v in prestazione.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
        
        set_clauses = [f"{k} = ?" for k in update_data.keys()]
        update_query = f"UPDATE Prestazioni SET {', '.join(set_clauses)} WHERE id_prestazione = ?"
        
        params = list(update_data.values()) + [prestazione_id]
        execute_query(update_query, tuple(params), fetch_all=False)
        
        return_query = "SELECT * FROM Prestazioni WHERE id_prestazione = ?"
        result = execute_query(return_query, (prestazione_id,), fetch_one=True)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_servizio_prestazionale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS EROGAZIONI PRESTAZIONI =====

@app.get("/erogazioni-prestazioni", summary="Lista erogazioni prestazioni")
async def list_erogazioni_prestazioni(
    associato_id: Optional[int] = Query(None, description="Filtra per ID associato"),
    prestazione_id: Optional[int] = Query(None, description="Filtra per ID prestazione"),
    data_da: Optional[str] = Query(None, description="Data inizio (YYYY-MM-DD)"),
    data_a: Optional[str] = Query(None, description="Data fine (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Ricerca testuale su nome/cognome associato e nome/descrizione prestazione")
):
    """Recupera la lista delle erogazioni prestazioni con filtri.
    Se non sono presenti filtri ID, restituisce tutte le erogazioni. Il parametro `search` filtra sui campi testuali.
    """
    try:
        where_clauses = []
        params = []
        
        if associato_id:
            where_clauses.append("ep.fk_associato = ?")
            params.append(associato_id)
            
        if prestazione_id:
            where_clauses.append("ep.fk_prestazione = ?")
            params.append(prestazione_id)
            
        if data_da:
            where_clauses.append("DATE(ep.data_erogazione) >= ?")
            params.append(data_da)
            
        if data_a:
            where_clauses.append("DATE(ep.data_erogazione) <= ?")
            params.append(data_a)

        if search:
            like = f"%{search}%"
            where_clauses.append("(a.nome LIKE ? OR a.cognome LIKE ? OR p.nome_prestazione LIKE ? OR p.descrizione LIKE ?)")
            params.extend([like, like, like, like])
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT 
            ep.id_erogazione,
            ep.data_erogazione,
            a.nome || ' ' || a.cognome as associato_nome,
            a.id_associato,
            p.nome_prestazione,
            p.descrizione,
            p.costo,
            p.id_prestazione
        FROM ErogazioniPrestazioni ep
        JOIN Associati a ON ep.fk_associato = a.id_associato
        JOIN Prestazioni p ON ep.fk_prestazione = p.id_prestazione
        WHERE {where_clause}
        ORDER BY ep.data_erogazione DESC
        """
        
        result = execute_query(query, tuple(params))
        return result
        
    except Exception as e:
        logger.error(f"Error in list_erogazioni_prestazioni: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/erogazioni-prestazioni", status_code=201, summary="Crea erogazione prestazione")
async def create_erogazione_prestazione(payload: dict):
    """Crea una nuova erogazione di prestazione.
    Richiede: fk_associato (int), fk_prestazione (int), data_erogazione (str opzionale: YYYY-MM-DD o ISO datetime)
    """
    try:
        fk_associato = payload.get("fk_associato")
        fk_prestazione = payload.get("fk_prestazione")
        data_erogazione = payload.get("data_erogazione")

        if not fk_associato or not fk_prestazione:
            raise HTTPException(status_code=400, detail="fk_associato e fk_prestazione sono obbligatori")

        # Validate associato
        assoc = execute_query("SELECT id_associato FROM Associati WHERE id_associato = ?", (fk_associato,), fetch_one=True)
        if not assoc:
            raise HTTPException(status_code=404, detail="Associato non trovato")

        # Validate prestazione
        prest = execute_query("SELECT id_prestazione, nome_prestazione, costo FROM Prestazioni WHERE id_prestazione = ?", (fk_prestazione,), fetch_one=True)
        if not prest:
            raise HTTPException(status_code=404, detail="Prestazione non trovata")

        # Parse/normalize date
        if data_erogazione and isinstance(data_erogazione, str) and data_erogazione.strip():
            # Accept YYYY-MM-DD or full ISO
            try:
                if len(data_erogazione.strip()) == 10:
                    # date only
                    dt = datetime.strptime(data_erogazione.strip(), "%Y-%m-%d")
                    data_erogazione_norm = dt.strftime("%Y-%m-%d 00:00:00")
                else:
                    dt = datetime.fromisoformat(data_erogazione.strip().replace("Z", ""))
                    data_erogazione_norm = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                raise HTTPException(status_code=400, detail="Formato data_erogazione non valido")
        else:
            data_erogazione_norm = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Begin transaction to insert erogazione, fattura, dettaglio fattura
        conn = get_db_connection()
        try:
            cur = conn.cursor()

            # 1) Insert ErogazionePrestazione
            insert_erog = (
                "INSERT INTO ErogazioniPrestazioni (fk_associato, fk_prestazione, data_erogazione) "
                "VALUES (?, ?, ?)"
            )
            cur.execute(insert_erog, (fk_associato, fk_prestazione, data_erogazione_norm))
            id_erogazione = cur.lastrowid

            # 2) Create Fattura (Attiva) for this erogazione
            costo = float(prest["costo"]) if prest and prest["costo"] is not None else 0.0
            imponibile = costo
            iva = 0.00  # IVA non gestita per ora; aggiornabile in futuro
            totale = imponibile + iva

            today = date.today()
            scadenza = today + timedelta(days=30)
            numero_fattura = f"EP-{fk_associato}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Ensure numero_fattura uniqueness (best-effort: retry suffix if collision)
            attempt = 0
            while True:
                check = cur.execute("SELECT 1 FROM Fatture WHERE numero_fattura = ?", (numero_fattura,)).fetchone()
                if not check:
                    break
                attempt += 1
                numero_fattura = f"EP-{fk_associato}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{attempt}"

            insert_fatt = (
                """
                INSERT INTO Fatture (
                    numero_fattura, data_emissione, data_scadenza, fk_associato,
                    fk_fornitore, tipo_fattura, importo_imponibile, importo_iva,
                    importo_totale, stato
                ) VALUES (?, ?, ?, ?, NULL, 'Attiva', ?, ?, ?, 'Emessa')
                """
            )
            cur.execute(
                insert_fatt,
                (
                    numero_fattura,
                    today.strftime("%Y-%m-%d"),
                    scadenza.strftime("%Y-%m-%d"),
                    fk_associato,
                    imponibile,
                    iva,
                    totale,
                ),
            )
            id_fattura = cur.lastrowid

            # 3) Insert DettaglioFattura linked to erogazione
            descr = f"{prest['nome_prestazione']} (erogazione {id_erogazione})"
            insert_det = (
                """
                INSERT INTO DettagliFatture (
                    fk_fattura, descrizione, quantita, prezzo_unitario, importo_totale,
                    fk_assegnazione_servizio_fisico, fk_erogazione_servizio_prestazionale
                ) VALUES (?, ?, ?, ?, ?, NULL, ?)
                """
            )
            cur.execute(
                insert_det,
                (
                    id_fattura,
                    descr,
                    1.0,
                    costo,
                    costo,
                    id_erogazione,
                ),
            )

            conn.commit()
            return {"status": "created", "id_erogazione": id_erogazione, "id_fattura": id_fattura, "numero_fattura": numero_fattura}
        except Exception as inner_e:
            conn.rollback()
            logger.error(f"Transaction error in create_erogazione_prestazione: {inner_e}")
            raise HTTPException(status_code=500, detail=str(inner_e))
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_erogazione_prestazione: {e}")
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
        # Build query for soci morosi
        where_clauses = ["f.stato IN ('Emessa', 'Scaduta')"]
        params = []
        
        if giorni_scadenza > 0:
            where_clauses.append("julianday('now') - julianday(f.data_scadenza) >= ?")
            params.append(giorni_scadenza)
        
        if importo_minimo:
            where_clauses.append("f.importo_totale >= ?")
            params.append(importo_minimo)
        
        if not include_sospesi:
            where_clauses.append("a.stato_associato != 'Sospeso'")
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
        SELECT a.id_associato, a.nome, a.cognome, a.email, a.telefono, a.stato_associato,
               f.id_fattura, f.numero_fattura, f.data_emissione, f.data_scadenza, 
               f.importo_totale, f.stato,
               CAST(julianday('now') - julianday(f.data_scadenza) AS INTEGER) as giorni_scadenza
        FROM Associati a
        JOIN Fatture f ON a.id_associato = f.fk_associato
        WHERE {where_clause}
        ORDER BY a.cognome, a.nome, f.data_scadenza
        """
        
        results = execute_query(query, tuple(params))
        
        # Group by associato
        soci_morosi = {}
        totale_crediti = 0
        
        for row in results:
            associato_id = row['id_associato']
            if associato_id not in soci_morosi:
                soci_morosi[associato_id] = {
                    'id_associato': row['id_associato'],
                    'nome': row['nome'],
                    'cognome': row['cognome'],
                    'email': row['email'],
                    'telefono': row['telefono'],
                    'stato_associato': row['stato_associato'],
                    'fatture_non_pagate': [],
                    'totale_dovuto': 0
                }
            
            fattura = {
                'id_fattura': row['id_fattura'],
                'numero_fattura': row['numero_fattura'],
                'data_emissione': row['data_emissione'],
                'data_scadenza': row['data_scadenza'],
                'importo_totale': row['importo_totale'],
                'giorni_scadenza': row['giorni_scadenza'],
                'stato': row['stato']
            }
            
            soci_morosi[associato_id]['fatture_non_pagate'].append(fattura)
            soci_morosi[associato_id]['totale_dovuto'] += row['importo_totale']
            totale_crediti += row['importo_totale']
        
        return {
            "count": len(soci_morosi),
            "totale_crediti": totale_crediti,
            "results": list(soci_morosi.values())
        }
        
    except Exception as e:
        logger.error(f"Error in report_soci_morosi: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/tesserati-fiv", summary="Report tesserati FIV")
async def report_tesserati_fiv(
    stato_tesseramento: Optional[str] = Query(None, pattern="^(Attivo|Scaduto)$", description="Filtra per stato tesseramento")
):
    """Genera il report dei tesserati FIV"""
    try:
        # Build query with filters
        where_clauses = []
        params = []
        
        if stato_tesseramento:
            if stato_tesseramento == "Attivo":
                where_clauses.append("tf.scadenza_tesseramento_fiv >= date('now')")
            elif stato_tesseramento == "Scaduto":
                where_clauses.append("tf.scadenza_tesseramento_fiv < date('now')")
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT a.id_associato, a.nome, a.cognome, a.email, a.stato_associato,
               tf.numero_tessera_fiv, tf.scadenza_tesseramento_fiv, tf.scadenza_certificato_medico,
               CASE 
                   WHEN tf.scadenza_tesseramento_fiv >= date('now') THEN 'Attivo'
                   ELSE 'Scaduto'
               END as stato_tesseramento
        FROM Associati a
        JOIN TessereFIV tf ON a.id_associato = tf.fk_associato
        WHERE {where_clause}
        ORDER BY a.cognome, a.nome
        """
        
        results = execute_query(query, tuple(params))
        
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
        query = """
        SELECT a.id_associato, a.nome, a.cognome, a.email, a.telefono,
               tf.numero_tessera_fiv, tf.scadenza_certificato_medico,
               CAST(julianday(tf.scadenza_certificato_medico) - julianday('now') AS INTEGER) as giorni_alla_scadenza
        FROM Associati a
        JOIN TessereFIV tf ON a.id_associato = tf.fk_associato
        WHERE julianday(tf.scadenza_certificato_medico) - julianday('now') <= ?
        AND tf.scadenza_certificato_medico >= date('now')
        ORDER BY tf.scadenza_certificato_medico, a.cognome, a.nome
        """
        
        results = execute_query(query, (giorni_alla_scadenza,))
        
        return {
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in report_certificati_in_scadenza: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/fatturato", summary="Report fatturato")
async def report_fatturato(
    periodo_inizio: date = Query(..., description="Data inizio periodo"),
    periodo_fine: date = Query(..., description="Data fine periodo")
):
    """Genera un report sul fatturato per un dato periodo"""
    try:
        # Fatturato attivo
        query_attivo = """
        SELECT 
            SUM(importo_imponibile) as imponibile,
            SUM(importo_iva) as iva,
            SUM(importo_totale) as totale
        FROM Fatture 
        WHERE tipo_fattura = 'Attiva' 
        AND data_emissione BETWEEN ? AND ?
        AND stato != 'Annullata'
        """
        
        fatturato_attivo = execute_query(query_attivo, (periodo_inizio.isoformat(), periodo_fine.isoformat()), fetch_one=True)
        
        # Fatturato passivo
        query_passivo = """
        SELECT 
            SUM(importo_imponibile) as imponibile,
            SUM(importo_iva) as iva,
            SUM(importo_totale) as totale
        FROM Fatture 
        WHERE tipo_fattura = 'Passiva' 
        AND data_emissione BETWEEN ? AND ?
        AND stato != 'Annullata'
        """
        
        fatturato_passivo = execute_query(query_passivo, (periodo_inizio.isoformat(), periodo_fine.isoformat()), fetch_one=True)
        
        return {
            "periodo": f"{periodo_inizio.isoformat()} - {periodo_fine.isoformat()}",
            "fatturato_attivo": {
                "imponibile": fatturato_attivo['imponibile'] or 0.00,
                "iva": fatturato_attivo['iva'] or 0.00,
                "totale": fatturato_attivo['totale'] or 0.00
            },
            "fatturato_passivo": {
                "imponibile": fatturato_passivo['imponibile'] or 0.00,
                "iva": fatturato_passivo['iva'] or 0.00,
                "totale": fatturato_passivo['totale'] or 0.00
            }
        }
        
    except Exception as e:
        logger.error(f"Error in report_fatturato: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINT PREZZI SERVIZI =====

class PrezzoServizioCreate(BaseModel):
    id_categoria_servizio: str = Field(..., max_length=50)
    costo: float = Field(..., gt=0)
    validita_dal: date
    validita_al: Optional[date] = None
    note: Optional[str] = Field(None, max_length=200)

class PrezzoServizioUpdate(BaseModel):
    id_categoria_servizio: Optional[str] = Field(None, max_length=50)
    costo: Optional[float] = Field(None, gt=0)
    validita_dal: Optional[date] = None
    validita_al: Optional[date] = None
    note: Optional[str] = Field(None, max_length=200)

@app.get("/prezzi-servizi", summary="Lista prezzi servizi")
async def list_prezzi_servizi(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    categoria: Optional[str] = Query(None)
):
    """Lista prezzi servizi con filtri opzionali"""
    query = "SELECT * FROM PrezziServizi"
    params = []
    
    if categoria:
        query += " WHERE id_categoria_servizio LIKE ?"
        params.append(f"%{categoria}%")
    
    query += " ORDER BY id_categoria_servizio LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    prezzi = execute_query(query, tuple(params))
    return prezzi or []

@app.post("/prezzi-servizi", status_code=201, summary="Crea prezzo servizio")
async def create_prezzo_servizio(prezzo: PrezzoServizioCreate):
    """Crea un nuovo prezzo per categoria servizio"""
    # Check if categoria already exists with overlapping dates
    check_query = """
        SELECT id_prezzo FROM PrezziServizi 
        WHERE id_categoria_servizio = ? 
        AND (validita_al IS NULL OR validita_al >= ?)
        AND validita_dal <= ?
    """
    validita_al = prezzo.validita_al or date(2099, 12, 31)
    existing = execute_query(check_query, (prezzo.id_categoria_servizio, prezzo.validita_dal, validita_al), fetch_one=True)
    
    if existing:
        raise HTTPException(status_code=400, detail="Esiste già un prezzo valido per questa categoria nel periodo specificato")
    
    insert_query = """
        INSERT INTO PrezziServizi (id_categoria_servizio, costo, validita_dal, validita_al, note)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_query(insert_query, (
        prezzo.id_categoria_servizio,
        prezzo.costo,
        prezzo.validita_dal,
        prezzo.validita_al,
        prezzo.note
    ))
    
    # Return created record
    return_query = "SELECT * FROM PrezziServizi WHERE id_categoria_servizio = ? AND validita_dal = ?"
    return execute_query(return_query, (prezzo.id_categoria_servizio, prezzo.validita_dal), fetch_one=True)

@app.get("/prezzi-servizi/{prezzo_id}", summary="Dettagli prezzo servizio")
async def get_prezzo_servizio(prezzo_id: int):
    """Ottieni dettagli di un prezzo servizio"""
    query = "SELECT * FROM PrezziServizi WHERE id_prezzo = ?"
    prezzo = execute_query(query, (prezzo_id,), fetch_one=True)
    
    if not prezzo:
        raise HTTPException(status_code=404, detail="Prezzo servizio non trovato")
    
    return prezzo

@app.put("/prezzi-servizi/{prezzo_id}", summary="Aggiorna prezzo servizio")
async def update_prezzo_servizio(prezzo_id: int, prezzo: PrezzoServizioUpdate):
    """Aggiorna un prezzo servizio esistente"""
    # Check if exists
    check_query = "SELECT id_prezzo FROM PrezziServizi WHERE id_prezzo = ?"
    existing = execute_query(check_query, (prezzo_id,), fetch_one=True)
    
    if not existing:
        raise HTTPException(status_code=404, detail="Prezzo servizio non trovato")
    
    # Build update query
    update_data = prezzo.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")
    
    set_clauses = [f"{key} = ?" for key in update_data.keys()]
    update_query = f"UPDATE PrezziServizi SET {', '.join(set_clauses)} WHERE id_prezzo = ?"
    
    params = list(update_data.values()) + [prezzo_id]
    execute_query(update_query, tuple(params))
    
    # Return updated record
    return_query = "SELECT * FROM PrezziServizi WHERE id_prezzo = ?"
    return execute_query(return_query, (prezzo_id,), fetch_one=True)

@app.delete("/prezzi-servizi/{prezzo_id}", status_code=204, summary="Elimina prezzo servizio")
async def delete_prezzo_servizio(prezzo_id: int):
    """Elimina un prezzo servizio"""
    # Check if exists
    check_query = "SELECT id_prezzo FROM PrezziServizi WHERE id_prezzo = ?"
    existing = execute_query(check_query, (prezzo_id,), fetch_one=True)
    
    if not existing:
        raise HTTPException(status_code=404, detail="Prezzo servizio non trovato")
    
    delete_query = "DELETE FROM PrezziServizi WHERE id_prezzo = ?"
    execute_query(delete_query, (prezzo_id,))

# ===== ENDPOINT FATTURE =====

class FatturaCreate(BaseModel):
    numero_fattura: str = Field(..., max_length=20)
    data_emissione: date
    data_scadenza: date
    fk_associato: Optional[int] = None
    fk_fornitore: Optional[int] = None
    importo_totale: float = Field(..., gt=0)
    stato_pagamento: str = Field(..., pattern="^(Non pagata|Pagata|Parzialmente pagata|Scaduta)$")
    tipo_fattura: str = Field(..., pattern="^(Attiva|Passiva)$")
    note: Optional[str] = Field(None, max_length=500)

class FatturaUpdate(BaseModel):
    numero_fattura: Optional[str] = Field(None, max_length=20)
    data_emissione: Optional[date] = None
    data_scadenza: Optional[date] = None
    fk_associato: Optional[int] = None
    fk_fornitore: Optional[int] = None
    importo_totale: Optional[float] = Field(None, gt=0)
    stato_pagamento: Optional[str] = Field(None, pattern="^(Non pagata|Pagata|Parzialmente pagata|Scaduta)$")
    tipo_fattura: Optional[str] = Field(None, pattern="^(Attiva|Passiva)$")
    note: Optional[str] = Field(None, max_length=500)

@app.get("/fatture", summary="Lista fatture")
async def list_fatture(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tipo: Optional[str] = Query(None, pattern="^(Attiva|Passiva)$"),
    stato: Optional[str] = Query(None, pattern="^(Non pagata|Pagata|Parzialmente pagata|Scaduta)$"),
    search: Optional[str] = Query(None)
):
    """Lista fatture con filtri opzionali"""
    query = """
        SELECT f.*, 
               CASE WHEN f.fk_associato IS NOT NULL 
                    THEN a.nome || ' ' || a.cognome 
                    ELSE fo.ragione_sociale 
               END as cliente_fornitore
        FROM Fatture f
        LEFT JOIN Associati a ON f.fk_associato = a.id_associato
        LEFT JOIN Fornitori fo ON f.fk_fornitore = fo.id_fornitore
        WHERE 1=1
    """
    params = []
    
    if tipo:
        query += " AND f.tipo_fattura = ?"
        params.append(tipo)
    
    if stato:
        # La colonna corretta nel DB è 'stato'
        query += " AND f.stato = ?"
        params.append(stato)
    
    if search:
        query += " AND (f.numero_fattura LIKE ? OR a.nome LIKE ? OR a.cognome LIKE ? OR fo.ragione_sociale LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param, search_param])
    
    query += " ORDER BY f.data_emissione DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    fatture = execute_query(query, tuple(params))
    return fatture or []

@app.post("/fatture", status_code=201, summary="Crea fattura")
async def create_fattura(fattura: FatturaCreate):
    """Crea una nuova fattura"""
    # Validazione relazioni: consentire entrambi vuoti; vietare entrambi valorizzati
    if fattura.fk_associato and fattura.fk_fornitore:
        raise HTTPException(status_code=400, detail="Specificare solo associato o fornitore, non entrambi")
    
    # Check numero_fattura uniqueness
    check_query = "SELECT id_fattura FROM Fatture WHERE numero_fattura = ?"
    existing = execute_query(check_query, (fattura.numero_fattura,), fetch_one=True)
    
    if existing:
        raise HTTPException(status_code=400, detail="Numero fattura già esistente")
    
    # Lo schema Fatture usa la colonna 'stato' con valori ('Emessa','Pagata','Scaduta','Annullata')
    stato_iniziale = 'Emessa'
    insert_query = """
        INSERT INTO Fatture (numero_fattura, data_emissione, data_scadenza, fk_associato, 
                            fk_fornitore, importo_totale, stato, tipo_fattura, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_query(insert_query, (
        fattura.numero_fattura,
        fattura.data_emissione,
        fattura.data_scadenza,
        fattura.fk_associato,
        fattura.fk_fornitore,
        fattura.importo_totale,
        stato_iniziale,
        fattura.tipo_fattura,
        fattura.note
    ))
    
    # Return created record
    return_query = "SELECT * FROM Fatture WHERE numero_fattura = ?"
    return execute_query(return_query, (fattura.numero_fattura,), fetch_one=True)

@app.get("/fatture/{fattura_id}", summary="Dettagli fattura")
async def get_fattura(fattura_id: int):
    """Ottieni dettagli di una fattura"""
    query = """
        SELECT f.*, 
               CASE WHEN f.fk_associato IS NOT NULL 
                    THEN a.nome || ' ' || a.cognome 
                    ELSE fo.ragione_sociale 
               END as cliente_fornitore,
               a.email as email_associato,
               fo.partita_iva
        FROM Fatture f
        LEFT JOIN Associati a ON f.fk_associato = a.id_associato
        LEFT JOIN Fornitori fo ON f.fk_fornitore = fo.id_fornitore
        WHERE f.id_fattura = ?
    """
    fattura = execute_query(query, (fattura_id,), fetch_one=True)
    
    if not fattura:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    
    # Get pagamenti for this fattura
    pagamenti_query = "SELECT * FROM Pagamenti WHERE fk_fattura = ? ORDER BY data_pagamento DESC"
    pagamenti = execute_query(pagamenti_query, (fattura_id,))
    
    fattura['pagamenti'] = pagamenti or []
    return fattura

# ===== ENDPOINT PAGAMENTI =====

class PagamentoCreate(BaseModel):
    fk_fattura: int
    data_pagamento: date
    importo: float = Field(..., gt=0)
    metodo_pagamento: str = Field(..., max_length=50)
    note: Optional[str] = Field(None, max_length=200)

class PagamentoUpdate(BaseModel):
    data_pagamento: Optional[date] = None
    importo: Optional[float] = Field(None, gt=0)
    metodo_pagamento: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = Field(None, max_length=200)

@app.get("/pagamenti", summary="Lista pagamenti")
async def list_pagamenti(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    metodo: Optional[str] = Query(None),
    dal: Optional[date] = Query(None),
    al: Optional[date] = Query(None)
):
    """Lista pagamenti con filtri opzionali"""
    query = """
        SELECT p.*, f.numero_fattura, f.tipo_fattura,
               CASE WHEN f.fk_associato IS NOT NULL 
                    THEN a.nome || ' ' || a.cognome 
                    ELSE fo.ragione_sociale 
               END as cliente_fornitore
        FROM Pagamenti p
        JOIN Fatture f ON p.fk_fattura = f.id_fattura
        LEFT JOIN Associati a ON f.fk_associato = a.id_associato
        LEFT JOIN Fornitori fo ON f.fk_fornitore = fo.id_fornitore
        WHERE 1=1
    """
    params = []
    
    if metodo:
        query += " AND p.metodo LIKE ?"
        params.append(f"%{metodo}%")
    
    if dal:
        query += " AND p.data_pagamento >= ?"
        params.append(dal)
    
    if al:
        query += " AND p.data_pagamento <= ?"
        params.append(al)
    
    query += " ORDER BY p.data_pagamento DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    pagamenti = execute_query(query, tuple(params))
    return pagamenti or []

@app.post("/pagamenti", status_code=201, summary="Registra pagamento")
async def create_pagamento(pagamento: PagamentoCreate):
    """Registra un nuovo pagamento"""
    # Check if fattura exists
    fattura_query = "SELECT * FROM Fatture WHERE id_fattura = ?"
    fattura = execute_query(fattura_query, (pagamento.fk_fattura,), fetch_one=True)
    
    if not fattura:
        raise HTTPException(status_code=404, detail="Fattura non trovata")
    
    # Determina tipo movimento (compatibilità schema con colonna NOT NULL 'tipo')
    # Se fattura è 'Attiva' => Entrata, se 'Passiva' => Uscita
    tipo_mov = 'Entrata' if (fattura.get('tipo_fattura') == 'Attiva') else 'Uscita'

    # Insert pagamento con colonna 'tipo'
    insert_query = """
        INSERT INTO Pagamenti (fk_fattura, data_pagamento, importo, metodo, tipo)
        VALUES (?, ?, ?, ?, ?)
    """
    execute_query(insert_query, (
        pagamento.fk_fattura,
        pagamento.data_pagamento,
        pagamento.importo,
        pagamento.metodo_pagamento,
        tipo_mov,
    ))
    
    # Update fattura status based on total payments
    pagamenti_query = "SELECT SUM(importo) as totale_pagato FROM Pagamenti WHERE fk_fattura = ?"
    totale_pagato = execute_query(pagamenti_query, (pagamento.fk_fattura,), fetch_one=True)
    
    importo_fattura = fattura['importo_totale']
    totale_pagato_val = totale_pagato['totale_pagato'] or 0
    
    if totale_pagato_val >= importo_fattura:
        nuovo_stato = "Pagata"
    else:
        # Non sono gestiti qui 'Scaduta'/'Annullata'; default rimane 'Emessa'
        nuovo_stato = "Emessa"
    
    # Update fattura status
    update_fattura_query = "UPDATE Fatture SET stato = ? WHERE id_fattura = ?"
    execute_query(update_fattura_query, (nuovo_stato, pagamento.fk_fattura))
    
    # Return created record
    return_query = "SELECT * FROM Pagamenti WHERE fk_fattura = ? AND data_pagamento = ? AND importo = ?"
    return execute_query(return_query, (pagamento.fk_fattura, pagamento.data_pagamento, pagamento.importo), fetch_one=True)

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
