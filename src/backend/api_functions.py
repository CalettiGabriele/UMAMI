#!/usr/bin/env python3
"""
UMAMI API Functions - Business Logic
====================================

Questo modulo contiene tutte le funzioni di business logic per le API REST del sistema UMAMI.
Le funzioni sono organizzate per area funzionale e utilizzano SQLite come database.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from contextlib import contextmanager

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path del database
DB_PATH = Path(__file__).parent.parent / "database" / "data" / "umami.db"

class DatabaseError(Exception):
    """Eccezione personalizzata per errori del database"""
    pass

class NotFoundError(Exception):
    """Eccezione per risorse non trovate"""
    pass

@contextmanager
def get_db_connection():
    """Context manager per la connessione al database"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# ===== ASSOCIATI =====

def get_associati(limit: int = 20, offset: int = 0, search: Optional[str] = None, 
                  stato: Optional[str] = None, tesserato_fiv: Optional[bool] = None) -> Dict[str, Any]:
    """Recupera lista associati con filtri e paginazione"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Query base
        query = """
        SELECT a.*, 
               CASE WHEN t.fk_associato IS NOT NULL THEN 1 ELSE 0 END as has_tessera_fiv
        FROM Associati a
        LEFT JOIN TessereFIV t ON a.id_associato = t.fk_associato
        WHERE 1=1
        """
        params = []
        
        # Filtri
        if search:
            query += " AND (a.nome LIKE ? OR a.cognome LIKE ? OR a.email LIKE ? OR a.codice_fiscale LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        if stato:
            query += " AND a.stato_associato = ?"
            params.append(stato)
        
        if tesserato_fiv is not None:
            if tesserato_fiv:
                query += " AND t.fk_associato IS NOT NULL"
            else:
                query += " AND t.fk_associato IS NULL"
        
        # Count totale
        count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Paginazione
        query += " ORDER BY a.cognome, a.nome LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "count": total_count,
            "results": results
        }

def create_associato(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuovo associato"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        INSERT INTO Associati (fk_associato_riferimento, nome, cognome, codice_fiscale, 
                              data_nascita, indirizzo, email, telefono, data_iscrizione, stato_associato)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = [
            data.get('fk_associato_riferimento'),
            data['nome'],
            data['cognome'],
            data['codice_fiscale'],
            data['data_nascita'],
            data['indirizzo'],
            data['email'],
            data['telefono'],
            data['data_iscrizione'],
            data['stato_associato']
        ]
        
        cursor.execute(query, params)
        conn.commit()
        
        # Recupera l'associato creato
        associato_id = cursor.lastrowid
        return get_associato_by_id(associato_id)

def get_associato_by_id(associato_id: int) -> Dict[str, Any]:
    """Recupera un associato per ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        SELECT a.*, 
               CASE WHEN t.fk_associato IS NOT NULL THEN 1 ELSE 0 END as has_tessera_fiv
        FROM Associati a
        LEFT JOIN TessereFIV t ON a.id_associato = t.fk_associato
        WHERE a.id_associato = ?
        """
        
        cursor.execute(query, [associato_id])
        result = cursor.fetchone()
        
        if not result:
            raise NotFoundError(f"Associato con ID {associato_id} non trovato")
        
        return dict(result)

def update_associato(associato_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiorna un associato"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza
        get_associato_by_id(associato_id)
        
        # Costruisce query dinamica
        fields = []
        params = []
        
        for field in ['fk_associato_riferimento', 'nome', 'cognome', 'codice_fiscale', 
                      'data_nascita', 'indirizzo', 'email', 'telefono', 'stato_associato']:
            if field in data:
                fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not fields:
            return get_associato_by_id(associato_id)
        
        params.append(associato_id)
        query = f"UPDATE Associati SET {', '.join(fields)} WHERE id_associato = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        return get_associato_by_id(associato_id)

def create_tesseramento_fiv(associato_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea o aggiorna tesseramento FIV"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza associato
        get_associato_by_id(associato_id)
        
        # Verifica se esiste già un tesseramento
        cursor.execute("SELECT * FROM TessereFIV WHERE fk_associato = ?", [associato_id])
        existing = cursor.fetchone()
        
        if existing:
            # Update
            query = """
            UPDATE TessereFIV 
            SET numero_tessera_fiv = ?, scadenza_tesseramento_fiv = ?, scadenza_certificato_medico = ?
            WHERE fk_associato = ?
            """
            params = [
                data['numero_tessera_fiv'],
                data['scadenza_tesseramento_fiv'],
                data['scadenza_certificato_medico'],
                associato_id
            ]
        else:
            # Insert
            query = """
            INSERT INTO TessereFIV (fk_associato, numero_tessera_fiv, scadenza_tesseramento_fiv, scadenza_certificato_medico)
            VALUES (?, ?, ?, ?)
            """
            params = [
                associato_id,
                data['numero_tessera_fiv'],
                data['scadenza_tesseramento_fiv'],
                data['scadenza_certificato_medico']
            ]
        
        cursor.execute(query, params)
        conn.commit()
        
        # Recupera il tesseramento
        cursor.execute("SELECT * FROM TessereFIV WHERE fk_associato = ?", [associato_id])
        result = cursor.fetchone()
        return dict(result)

# ===== FORNITORI =====

def get_fornitori(limit: int = 20, offset: int = 0, search: Optional[str] = None, 
                  attivo: Optional[bool] = None) -> Dict[str, Any]:
    """Recupera lista fornitori con filtri e paginazione"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM Fornitori WHERE 1=1"
        params = []
        
        if search:
            query += " AND (ragione_sociale LIKE ? OR partita_iva LIKE ? OR email LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Count totale
        count_query = f"SELECT COUNT(*) FROM ({query}) as subquery"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Paginazione
        query += " ORDER BY ragione_sociale LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "count": total_count,
            "results": results
        }

def create_fornitore(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuovo fornitore"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        INSERT INTO Fornitori (ragione_sociale, partita_iva, email, telefono)
        VALUES (?, ?, ?, ?)
        """
        
        params = [
            data['ragione_sociale'],
            data['partita_iva'],
            data['email'],
            data['telefono']
        ]
        
        cursor.execute(query, params)
        conn.commit()
        
        fornitore_id = cursor.lastrowid
        return get_fornitore_by_id(fornitore_id)

def get_fornitore_by_id(fornitore_id: int) -> Dict[str, Any]:
    """Recupera un fornitore per ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Fornitori WHERE id_fornitore = ?", [fornitore_id])
        result = cursor.fetchone()
        
        if not result:
            raise NotFoundError(f"Fornitore con ID {fornitore_id} non trovato")
        
        return dict(result)

def update_fornitore(fornitore_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Aggiorna un fornitore"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza
        get_fornitore_by_id(fornitore_id)
        
        # Costruisce query dinamica
        fields = []
        params = []
        
        for field in ['ragione_sociale', 'partita_iva', 'email', 'telefono']:
            if field in data:
                fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not fields:
            return get_fornitore_by_id(fornitore_id)
        
        params.append(fornitore_id)
        query = f"UPDATE Fornitori SET {', '.join(fields)} WHERE id_fornitore = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        return get_fornitore_by_id(fornitore_id)

def delete_fornitore(fornitore_id: int) -> bool:
    """Elimina un fornitore (solo se non ha fatture associate)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza
        get_fornitore_by_id(fornitore_id)
        
        # Verifica se ha fatture associate
        cursor.execute("SELECT COUNT(*) FROM Fatture WHERE fk_fornitore = ?", [fornitore_id])
        fatture_count = cursor.fetchone()[0]
        
        if fatture_count > 0:
            raise DatabaseError("Impossibile eliminare fornitore: ha fatture associate")
        
        cursor.execute("DELETE FROM Fornitori WHERE id_fornitore = ?", [fornitore_id])
        conn.commit()
        
        return True

# ===== CHIAVI ELETTRONICHE =====

def get_chiave_elettronica(associato_id: int) -> Dict[str, Any]:
    """Recupera chiave elettronica di un associato"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza associato
        get_associato_by_id(associato_id)
        
        cursor.execute("SELECT * FROM ChiaviElettroniche WHERE fk_associato = ?", [associato_id])
        result = cursor.fetchone()
        
        if not result:
            raise NotFoundError(f"Chiave elettronica per associato {associato_id} non trovata")
        
        return dict(result)

def create_or_update_chiave_elettronica(associato_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea o aggiorna chiave elettronica"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza associato
        get_associato_by_id(associato_id)
        
        # Verifica se esiste già
        cursor.execute("SELECT * FROM ChiaviElettroniche WHERE fk_associato = ?", [associato_id])
        existing = cursor.fetchone()
        
        if existing:
            # Update
            query = """
            UPDATE ChiaviElettroniche 
            SET key_code = ?, in_regola = ?, credito = ?
            WHERE fk_associato = ?
            """
            params = [
                data['key_code'],
                data['in_regola'],
                data.get('credito', existing['credito']),
                associato_id
            ]
        else:
            # Insert
            query = """
            INSERT INTO ChiaviElettroniche (fk_associato, key_code, in_regola, credito)
            VALUES (?, ?, ?, ?)
            """
            params = [
                associato_id,
                data['key_code'],
                data['in_regola'],
                data.get('credito', 0.00)
            ]
        
        cursor.execute(query, params)
        conn.commit()
        
        return get_chiave_elettronica(associato_id)

def ricarica_crediti_docce(associato_id: int, crediti_da_aggiungere: float) -> Dict[str, Any]:
    """Ricarica crediti docce per una chiave elettronica"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verifica esistenza chiave
        chiave = get_chiave_elettronica(associato_id)
        
        nuovo_credito = chiave['credito'] + crediti_da_aggiungere
        
        cursor.execute(
            "UPDATE ChiaviElettroniche SET credito = ? WHERE fk_associato = ?",
            [nuovo_credito, associato_id]
        )
        conn.commit()
        
        return get_chiave_elettronica(associato_id)

# ===== SERVIZI FISICI =====

def get_servizi_fisici(stato: Optional[str] = None, tipo: Optional[str] = None) -> Dict[str, Any]:
    """Recupera lista servizi fisici"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM ServiziFisici WHERE 1=1"
        params = []
        
        if stato:
            query += " AND stato = ?"
            params.append(stato)
        
        if tipo:
            query += " AND categoria = ?"
            params.append(tipo)
        
        query += " ORDER BY nome"
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        return {
            "count": len(results),
            "results": results
        }

def create_servizio_fisico(data: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un nuovo servizio fisico"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        INSERT INTO ServiziFisici (nome, descrizione, categoria, stato)
        VALUES (?, ?, ?, ?)
        """
        
        params = [
            data['nome'],
            data['descrizione'],
            data['tipo'],
            data['stato']
        ]
        
        cursor.execute(query, params)
        conn.commit()
        
        servizio_id = cursor.lastrowid
        return get_servizio_fisico_by_id(servizio_id)

def get_servizio_fisico_by_id(servizio_id: int) -> Dict[str, Any]:
    """Recupera un servizio fisico per ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ServiziFisici WHERE id_servizio_fisico = ?", [servizio_id])
        result = cursor.fetchone()
        
        if not result:
            raise NotFoundError(f"Servizio fisico con ID {servizio_id} non trovato")
        
        return dict(result)

# ===== REPORT =====

def get_soci_morosi(giorni_scadenza: int = 0, importo_minimo: Optional[float] = None, 
                    include_sospesi: bool = False) -> Dict[str, Any]:
    """Genera report soci morosi"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        SELECT a.id_associato, a.nome, a.cognome, a.email, a.telefono, a.stato_associato,
               f.id_fattura, f.numero_fattura, f.data_emissione, f.data_scadenza, 
               f.importo_totale, f.stato,
               CASE 
                   WHEN f.data_scadenza < date('now') 
                   THEN julianday('now') - julianday(f.data_scadenza)
                   ELSE 0 
               END as giorni_scadenza
        FROM Associati a
        JOIN Fatture f ON a.id_associato = f.fk_associato
        WHERE f.stato IN ('Emessa', 'Scaduta')
        """
        params = []
        
        if giorni_scadenza > 0:
            query += " AND julianday('now') - julianday(f.data_scadenza) >= ?"
            params.append(giorni_scadenza)
        
        if importo_minimo:
            query += " AND f.importo_totale >= ?"
            params.append(importo_minimo)
        
        if not include_sospesi:
            query += " AND a.stato_associato != 'Sospeso'"
        
        query += " ORDER BY a.cognome, a.nome, f.data_scadenza"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Raggruppa per socio
        soci_morosi = {}
        totale_crediti = 0
        
        for row in rows:
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
                'giorni_scadenza': int(row['giorni_scadenza']),
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

def get_tesserati_fiv(stato_tesseramento: Optional[str] = None) -> List[Dict[str, Any]]:
    """Genera report tesserati FIV"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        SELECT a.*, t.numero_tessera_fiv, t.scadenza_tesseramento_fiv, t.scadenza_certificato_medico
        FROM Associati a
        JOIN TessereFIV t ON a.id_associato = t.fk_associato
        WHERE 1=1
        """
        params = []
        
        # Nota: nella nuova struttura non abbiamo più stato_tesseramento, 
        # quindi filtriamo sulla base della scadenza
        if stato_tesseramento == 'Attivo':
            query += " AND t.scadenza_tesseramento_fiv >= date('now')"
        elif stato_tesseramento == 'Scaduto':
            query += " AND t.scadenza_tesseramento_fiv < date('now')"
        
        query += " ORDER BY a.cognome, a.nome"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_certificati_in_scadenza(giorni_alla_scadenza: int = 30) -> List[Dict[str, Any]]:
    """Genera report certificati medici in scadenza"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
        SELECT a.*, t.numero_tessera_fiv, t.scadenza_certificato_medico,
               julianday(t.scadenza_certificato_medico) - julianday('now') as giorni_rimanenti
        FROM Associati a
        JOIN TessereFIV t ON a.id_associato = t.fk_associato
        WHERE t.scadenza_certificato_medico BETWEEN date('now') AND date('now', '+' || ? || ' days')
        ORDER BY t.scadenza_certificato_medico, a.cognome, a.nome
        """
        
        cursor.execute(query, [giorni_alla_scadenza])
        return [dict(row) for row in cursor.fetchall()]
