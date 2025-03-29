# TallyPrimeConnect/utils/database.py
import sqlite3
import os
import datetime
import logging

logger = logging.getLogger(__name__)

# Determine the base directory and database path
try:
    # Robustly find base directory
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    BASE_DIR = os.path.dirname(os.getcwd()) # Fallback if __file__ not defined

DATABASE_DIR = os.path.join(BASE_DIR, 'config')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'biz_analyst_data.db')

# --- Constants ---
SQLITE_TIMEOUT = 5.0 # Seconds

# --- Helper ---
def _execute_db(sql: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False, commit: bool = False) -> any:
    """Helper function to execute SQLite commands with error handling and connection management."""
    conn = None # Ensure conn is defined in outer scope
    try:
        os.makedirs(DATABASE_DIR, exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH, timeout=SQLITE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)

        result = None
        if commit:
            conn.commit()
            result = cursor.rowcount # Return affected rows for commit operations
        elif fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()

        return result

    except sqlite3.OperationalError as e:
        # Handle specific errors like "database is locked"
        logger.error(f"SQLite OperationalError: {e}. SQL: {sql[:100]}...")
        if "database is locked" in str(e):
            logger.warning("Database is locked, operation may need retry or adjustment.")
        # Potentially re-raise or return specific error indicator
        return None if (fetch_one or fetch_all) else (0 if commit else False) # Indicate failure
    except sqlite3.IntegrityError as e:
        logger.warning(f"SQLite IntegrityError (e.g., UNIQUE constraint failed): {e}. SQL: {sql[:100]}...")
        conn.rollback() # Rollback on integrity error during commit
        return 0 if commit else False # Indicate failure / no change
    except sqlite3.Error as e:
        logger.exception(f"General SQLite Error: {e}. SQL: {sql[:100]}...")
        if conn and commit: conn.rollback() # Rollback on error during commit
        return None if (fetch_one or fetch_all) else (0 if commit else False)
    finally:
        if conn:
            conn.close()


# --- Initialization ---
def init_db():
    """Initializes the database and creates/updates tables."""
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    # Companies Table
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
    _execute_db(sql_companies, commit=True)

    # Attempt to add columns safely (ignore errors if they exist)
    sql_add_desc = "ALTER TABLE companies ADD COLUMN description TEXT"
    sql_add_active = "ALTER TABLE companies ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"
    try: _execute_db(sql_add_desc, commit=True)
    except Exception: pass # Ignore error if column exists
    try: _execute_db(sql_add_active, commit=True)
    except Exception: pass # Ignore error if column exists

    # Company Log Table
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
    logger.info("Database initialization check complete.")


# --- Logging ---
def log_change(tally_company_number: str, action: str, details: str = ""):
    """Logs an action related to a company."""
    sql = "INSERT INTO company_log (tally_company_number, action, details) VALUES (?, ?, ?)"
    rowcount = _execute_db(sql, (str(tally_company_number), action.upper(), details), commit=True)
    if rowcount:
        logger.info(f"Logged action: {action.upper()} for {tally_company_number}")
    else:
        logger.error(f"Failed to log action {action.upper()} for {tally_company_number}")


# --- CRUD Operations ---
def add_company_to_db(name: str, number: str) -> bool:
    """Adds a company or reactivates it if soft-deleted. Logs the action. Returns True if added/reactivated."""
    if not name or not number:
        logger.error("Add company failed: Name or number is empty.")
        return False

    number_str = str(number)
    # Check existence (including inactive)
    check_sql = "SELECT id, is_active FROM companies WHERE tally_company_number = ?"
    existing = _execute_db(check_sql, (number_str,), fetch_one=True)

    if existing:
        if not existing['is_active']:
            logger.info(f"Reactivating company {number_str} ('{name}').")
            update_sql = "UPDATE companies SET tally_company_name = ?, description = COALESCE(description, ''), is_active = 1 WHERE tally_company_number = ?"
            rowcount = _execute_db(update_sql, (name, number_str), commit=True)
            if rowcount:
                log_change(number_str, "REACTIVATE", f"Reactivated with name '{name}'")
                return True
            else:
                 logger.error(f"Failed to reactivate company {number_str}")
                 return False
        else:
            logger.info(f"Company {number_str} ('{name}') already active.")
            # Optional: Update name if changed logic here
            return False # Not newly added or reactivated
    else:
        logger.info(f"Adding new company {number_str} ('{name}').")
        insert_sql = "INSERT INTO companies (tally_company_number, tally_company_name, is_active) VALUES (?, ?, 1)"
        rowcount = _execute_db(insert_sql, (number_str, name), commit=True)
        if rowcount:
            log_change(number_str, "ADD", f"Added company '{name}'")
            return True
        else:
            logger.error(f"Failed to insert company {number_str}")
            return False


def get_added_companies() -> list[dict]:
    """Retrieves all ACTIVE companies stored in the database."""
    sql = "SELECT tally_company_name, tally_company_number, description FROM companies WHERE is_active = 1 ORDER BY tally_company_name"
    rows = _execute_db(sql, fetch_all=True)
    return [dict(row) for row in rows] if rows else []


def get_company_details(tally_company_number: str) -> dict | None:
    """Retrieves details for a specific active company."""
    sql = "SELECT tally_company_name, tally_company_number, description FROM companies WHERE tally_company_number = ? AND is_active = 1"
    row = _execute_db(sql, (str(tally_company_number),), fetch_one=True)
    return dict(row) if row else None


def edit_company_in_db(tally_company_number: str, new_name: str, new_description: str | None) -> bool:
    """Updates the name and description of an active company. Logs changes. Returns True on success."""
    if not tally_company_number or not new_name:
        logger.error("Edit failed: Company number or new name is empty.")
        return False

    number_str = str(tally_company_number)
    desc = new_description if new_description is not None else ""

    # Check for duplicate name (among *other* active companies)
    check_sql = "SELECT 1 FROM companies WHERE tally_company_name = ? AND tally_company_number != ? AND is_active = 1 LIMIT 1"
    if _execute_db(check_sql, (new_name, number_str), fetch_one=True):
        logger.warning(f"Edit failed for {number_str}: Name '{new_name}' already used by another active company.")
        return False # Duplicate name

    # Get current details for logging and change detection
    current = get_company_details(number_str)
    if not current:
        logger.error(f"Edit failed for {number_str}: Company not found or inactive.")
        return False

    current_name = current['tally_company_name']
    current_desc = current['description'] if current['description'] is not None else ""

    if current_name == new_name and current_desc == desc:
        logger.info(f"No changes detected for company {number_str}.")
        return False # Indicate no update needed

    # Perform update
    update_sql = "UPDATE companies SET tally_company_name = ?, description = ? WHERE tally_company_number = ? AND is_active = 1"
    rowcount = _execute_db(update_sql, (new_name, desc, number_str), commit=True)

    if rowcount:
        log_items = []
        if current_name != new_name: log_items.append(f"Name: '{current_name}' -> '{new_name}'")
        if current_desc != desc: log_items.append("Description updated")
        if log_items: log_change(number_str, "EDIT", "; ".join(log_items))
        logger.info(f"Company {number_str} updated successfully.")
        return True
    else:
        logger.error(f"Edit failed unexpectedly for {number_str} after checks.")
        return False


def soft_delete_company(tally_company_number: str) -> bool:
    """Marks a company as inactive. Logs the action. Returns True on success."""
    number_str = str(tally_company_number)
    sql = "UPDATE companies SET is_active = 0 WHERE tally_company_number = ? AND is_active = 1"
    rowcount = _execute_db(sql, (number_str,), commit=True)
    if rowcount:
        log_change(number_str, "SOFT_DELETE", "Marked as inactive")
        logger.info(f"Company {number_str} marked as inactive.")
        return True
    else:
        logger.warning(f"Soft delete failed for {number_str}: Not found or already inactive.")
        return False