# TallyPrimeConnect/utils/database.py
import sqlite3
import os
import datetime
import logging

logger = logging.getLogger(__name__)

# --- Constants & Config ---
try: BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError: BASE_DIR = os.path.dirname(os.getcwd())
DATABASE_DIR = os.path.join(BASE_DIR, 'config')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'biz_analyst_data.db')
SQLITE_TIMEOUT = 5.0

# --- Column Definitions (Map DB Column Name -> SQLite Type/Constraints) ---
# Used by init_db and update_company_details
COMPANY_DETAIL_COLUMNS = {
    "tally_company_name": "TEXT NOT NULL", # Base table
    "formal_name": "TEXT",
    "address": "TEXT",
    "state_name": "TEXT",
    "country_name": "TEXT",
    "pincode": "TEXT",
    "phone_number": "TEXT",
    "mobile_no": "TEXT",
    "fax_number": "TEXT",
    "email": "TEXT",
    "website": "TEXT",
    "start_date": "TEXT",
    "books_date": "TEXT",
    "is_security_on": "BOOLEAN",
    "owner_name": "TEXT",
    "is_tally_audit_on": "BOOLEAN",
    "is_disallow_edu": "BOOLEAN",
    "currency_name": "TEXT",
    "currency_formal_name": "TEXT",
    "is_currency_suffix": "BOOLEAN",
    "in_millions": "BOOLEAN",
    "decimal_places": "INTEGER",
    "decimal_symbol": "TEXT",
    "decimal_places_printing": "INTEGER",
    "guid": "TEXT",
    "master_id": "INTEGER",
    "alter_id": "INTEGER",
    "sync_status": "TEXT DEFAULT 'Not Synced'",
    "last_sync_timestamp": "DATETIME"
    # 'description' and 'is_active' are handled in the base table definition
}

# --- DB Connection ---
def get_db_connection():
    """Establishes and returns a database connection."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=SQLITE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        logger.debug(f"Database connection established to {DATABASE_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.exception(f"Database connection error: {e}")
        return None

# --- DB Execution Helper ---
def _execute_db(sql: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False, commit: bool = False) -> any:
    """Helper function to execute SQLite commands with error handling and connection management."""
    conn = None
    try:
        conn = get_db_connection()
        if conn is None: raise sqlite3.Error("Failed to establish database connection.")
        cursor = conn.cursor()
        logger.debug(f"Executing SQL: {sql[:100]}... with params: {'Present' if params else 'None'}")
        cursor.execute(sql, params)
        result = None
        if commit:
            conn.commit(); result = cursor.rowcount
            logger.debug(f"SQL Commit successful. Rows affected: {result}")
        elif fetch_one: result = cursor.fetchone(); logger.debug(f"SQL Fetch one successful.")
        elif fetch_all: result = cursor.fetchall(); logger.debug(f"SQL Fetch all successful. Rows: {len(result) if result else 0}")
        return result
    except sqlite3.Error as e:
        logger.exception(f"SQLite Error: {e}. SQL: {sql[:100]}...")
        if conn and commit: conn.rollback()
        return None if (fetch_one or fetch_all) else (0 if commit else False) # Indicate failure consistently
    finally:
        if conn:
             try: conn.close(); logger.debug("Database connection closed.")
             except sqlite3.Error as e: logger.error(f"Error closing DB connection: {e}")

# --- Initialization ---
def init_db():
    """Initializes the database and creates/updates tables."""
    logger.info(f"Initializing database schema check at: {DATABASE_PATH}")
    # Base Companies Table Structure
    sql_companies = """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tally_company_number TEXT UNIQUE NOT NULL,
            tally_company_name TEXT NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT 1 NOT NULL,
            added_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    if _execute_db(sql_companies, commit=True) is None:
        logger.critical("Failed to create base 'companies' table.")
        raise sqlite3.Error("Failed to create base 'companies' table.")

    # Safely Add Columns
    conn_check = get_db_connection()
    existing_columns = []
    if conn_check:
        try: existing_columns = [info[1] for info in conn_check.execute("PRAGMA table_info(companies)").fetchall()]
        except sqlite3.Error as e: logger.error(f"Could not get table info: {e}")
        finally: conn_check.close()
    else: logger.error("Cannot check existing columns, DB connection failed during init.")

    for col_name, col_type in COMPANY_DETAIL_COLUMNS.items():
        # Skip base columns already defined explicitly
        if col_name in ['id', 'tally_company_number', 'tally_company_name', 'description', 'is_active', 'added_timestamp']:
            continue
        if col_name not in existing_columns:
            logger.info(f"Attempting to add column '{col_name}'...")
            sql_add = f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}"
            if _execute_db(sql_add, commit=True) is not None: logger.info(f"Added column '{col_name}'.")
            else: logger.error(f"Failed to add column {col_name}.")

    # Log Table
    sql_log = """
        CREATE TABLE IF NOT EXISTS company_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tally_company_number TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    _execute_db(sql_log, commit=True)
    logger.info("Database schema check complete.")

# --- Logging ---
def log_change(tally_company_number: str, action: str, details: str = ""):
    """Logs an action related to a company."""
    sql = "INSERT INTO company_log (tally_company_number, action, details) VALUES (?, ?, ?)"
    _execute_db(sql, (str(tally_company_number), action.upper(), details), commit=True)
    # Basic logging already done by _execute_db

# --- CRUD Operations ---
def add_company_to_db(name: str, number: str) -> bool:
    """Adds a company or reactivates it. Returns True if added/reactivated."""
    if not name or not number: logger.error("Add failed: Name/Number empty."); return False
    number_str = str(number)
    check_sql = "SELECT id, is_active FROM companies WHERE tally_company_number = ?"; existing = _execute_db(check_sql, (number_str,), fetch_one=True)
    if existing:
        if not existing['is_active']:
            logger.info(f"Reactivating {number_str} ('{name}').")
            update_sql = "UPDATE companies SET tally_company_name = ?, is_active = 1, sync_status = 'Not Synced' WHERE tally_company_number = ?"; rowcount = _execute_db(update_sql, (name, number_str), commit=True)
            if rowcount: log_change(number_str, "REACTIVATE", f"Name: '{name}'"); return True
            else: logger.error(f"Failed reactivate {number_str}"); return False
        else: logger.info(f"{number_str} already active."); return False
    else:
        logger.info(f"Adding new {number_str} ('{name}').")
        insert_sql = "INSERT INTO companies (tally_company_number, tally_company_name, is_active, sync_status) VALUES (?, ?, 1, 'Not Synced')"; rowcount = _execute_db(insert_sql, (number_str, name), commit=True)
        if rowcount: log_change(number_str, "ADD", f"Name: '{name}'"); return True
        else: logger.error(f"Failed insert {number_str}"); return False

def get_added_companies() -> list[dict]:
    """Retrieves all ACTIVE companies with basic details + sync status."""
    sql = "SELECT tally_company_name, tally_company_number, description, sync_status FROM companies WHERE is_active = 1 ORDER BY tally_company_name"; rows = _execute_db(sql, fetch_all=True); return [dict(row) for row in rows] if rows else []

def get_company_details(tally_company_number: str) -> dict | None:
    """Retrieves editable details (Name, Description) for an active company."""
    sql = "SELECT tally_company_name, tally_company_number, description FROM companies WHERE tally_company_number = ? AND is_active = 1"; row = _execute_db(sql, (str(tally_company_number),), fetch_one=True); return dict(row) if row else None

def edit_company_in_db(tally_company_number: str, new_name: str, new_description: str | None) -> bool:
    """Updates Name and Description for an active company. Returns True on success."""
    if not tally_company_number or not new_name: logger.error("Edit failed: Number/Name empty."); return False
    number_str=str(tally_company_number); desc=new_description if new_description is not None else ""
    check_sql = "SELECT 1 FROM companies WHERE tally_company_name = ? AND tally_company_number != ? AND is_active = 1 LIMIT 1"
    if _execute_db(check_sql, (new_name, number_str), fetch_one=True): logger.warning(f"Edit fail {number_str}: Name '{new_name}' exists."); return False
    current=get_company_details(number_str)
    if not current: logger.error(f"Edit fail {number_str}: Not found/inactive."); return False
    current_name=current['tally_company_name']; current_desc=current.get('description', '') or ""
    if current_name == new_name and current_desc == desc: logger.info(f"No changes for {number_str}."); return False
    update_sql = "UPDATE companies SET tally_company_name = ?, description = ? WHERE tally_company_number = ? AND is_active = 1"; rowcount = _execute_db(update_sql, (new_name, desc, number_str), commit=True)
    if rowcount:
        log_items = [];
        if current_name != new_name: log_items.append(f"Name: '{current_name}'->'{new_name}'")
        if current_desc != desc: log_items.append("Desc updated")
        if log_items: log_change(number_str, "EDIT", "; ".join(log_items))
        logger.info(f"Company {number_str} updated."); return True
    else: logger.error(f"Edit unexpected fail {number_str}."); return False

def soft_delete_company(tally_company_number: str) -> bool:
    """Marks a company as inactive. Returns True on success."""
    number_str = str(tally_company_number); sql = "UPDATE companies SET is_active = 0 WHERE tally_company_number = ? AND is_active = 1"; rowcount = _execute_db(sql, (number_str,), commit=True)
    if rowcount: log_change(number_str, "SOFT_DELETE", "Marked inactive"); logger.info(f"{number_str} inactive."); return True
    else: logger.warning(f"Soft delete fail {number_str}: Not found/inactive."); return False

# --- Update Company Details from Sync ---
def update_company_details(tally_company_number: str, details: dict) -> bool:
    """Updates a company row with details fetched from sync. Sets status to 'Synced'."""
    if not tally_company_number or not details: logger.error(f"Update details fail {tally_company_number}: Invalid input."); return False
    number_str = str(tally_company_number); now_iso = datetime.datetime.now().isoformat()
    set_clauses = []; params = [];

    for key, value in details.items():
        db_key = key.lower()
        # Check against COMPANY_DETAIL_COLUMNS *keys* defined at top of file
        if db_key in COMPANY_DETAIL_COLUMNS:
             # --- Optional: Skip name update here if needed ---
             # if db_key == 'tally_company_name': continue
             # ---
             params.append(value); set_clauses.append(f"{db_key} = ?")
        elif db_key not in ['description', 'is_active', 'tally_company_number']: # Ignore base/managed columns
             logger.warning(f"Skipping unknown/unmanaged key '{key}' during update for {number_str}")

    if not set_clauses: logger.warning(f"No valid details to update for {number_str}"); update_company_sync_status(number_str, 'Sync Failed'); return False # Mark failed if no data

    set_clauses.append("sync_status = ?"); params.append("Synced")
    set_clauses.append("last_sync_timestamp = ?"); params.append(now_iso)
    params.append(number_str) # For WHERE clause

    sql = f"UPDATE companies SET {', '.join(set_clauses)} WHERE tally_company_number = ? AND is_active = 1"
    logger.info(f"Updating details in DB for {number_str}...")
    rowcount = _execute_db(sql, tuple(params), commit=True)

    if rowcount:
        log_change(number_str, "SYNC_SUCCESS", "Details updated from sync"); logger.info(f"Details updated OK {number_str}."); return True
    else:
        logger.error(f"Failed DB update for {number_str} (not found/inactive?)."); update_company_sync_status(number_str, 'Sync Failed'); return False

def update_company_sync_status(tally_company_number: str, status: str):
    """Explicitly sets the sync_status for a company and logs it."""
    logger.info(f"Setting sync status to '{status}' for {tally_company_number}"); number_str=str(tally_company_number); now_iso = datetime.datetime.now().isoformat(); sql = "UPDATE companies SET sync_status = ?, last_sync_timestamp = ? WHERE tally_company_number = ?"; rowcount = _execute_db(sql, (status, now_iso, number_str), commit=True)
    if rowcount: log_change(number_str, "STATUS_UPDATE", f"Sync status set to '{status}'"); logger.debug(f"Status updated to {status} for {number_str}")
    else: logger.warning(f"Failed update sync status to {status} for {number_str}"); log_change(number_str, "STATUS_UPDATE_FAIL", f"Failed set status to '{status}'")