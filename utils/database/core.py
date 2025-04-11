"""
Core database functionality for TallyPrimeConnect.
Provides connection management, query execution, and schema initialization.
"""

import sqlite3
import os
import datetime
import logging
import time

logger = logging.getLogger(__name__)

# --- Constants & Configuration ---
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
except NameError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.getcwd()))

DATABASE_DIR = os.path.join(BASE_DIR, 'config')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'biz_analyst_data.db')
SQLITE_TIMEOUT = 5.0

# --- DB Connection ---
def get_db_connection():
    """Establishes and returns a database connection."""
    os.makedirs(DATABASE_DIR, exist_ok=True)
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=SQLITE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        logger.debug(f"DB connection established: {DATABASE_PATH}")
        return conn
    except sqlite3.Error as e:
        logger.exception(f"DB connection error: {e}")
        return None

# --- DB Execution Helper ---
def execute_query(sql, params=(), fetch_one=False, fetch_all=False, commit=False, executemany=False):
    """Helper for executing SQLite commands with managed connections and error logging."""
    conn = None
    
    # Validate params type based on execution mode
    if executemany and not isinstance(params, list):
        logger.error(f"Executemany needs list of sequences, got {type(params)}.")
        return 0 if commit else None
    
    if not executemany and not isinstance(params, tuple):
        params = tuple(params)  # Ensure tuple for single execute
    
    try:
        conn = get_db_connection()
        if conn is None:
            raise sqlite3.Error("Failed DB connection.")
        
        cursor = conn.cursor()
        op = "executemany" if executemany else "execute"
        logger.debug(f"Executing SQL ({op}): {sql[:100]}... Params: {'Multiple' if executemany else ('Yes' if params else 'No')}")
        
        if executemany:
            cursor.executemany(sql, params)
        else:
            cursor.execute(sql, params)
        
        result = None
        if commit:
            conn.commit()
            result = cursor.rowcount
            logger.debug(f"Commit OK. Rows: {result}")
        elif fetch_one:
            result = cursor.fetchone()
            logger.debug(f"Fetch one OK. Result: {'Row' if result else 'None'}")
        elif fetch_all:
            result = cursor.fetchall()
            logger.debug(f"Fetch all OK. Rows: {len(result) if result else 0}")
        
        return result
        
    except sqlite3.IntegrityError as e:
        logger.warning(f"SQLite IntegrityError: {e}. SQL: {sql[:100]}...")
        if conn and commit:
            try:
                conn.rollback()
                logger.debug("Rolled back transaction due to IntegrityError.")
            except sqlite3.Error as rb_err:
                logger.error(f"Error during rollback after IntegrityError: {rb_err}")
        return 0 if commit else None
        
    except sqlite3.Error as e:
        logger.exception(f"General SQLite Error: {e}. SQL: {sql[:100]}...")
        if conn and commit:
            try:
                conn.rollback()
                logger.debug("Rolled back transaction due to general SQLiteError during commit.")
            except sqlite3.Error as rb_err:
                logger.error(f"Error during rollback after general error: {rb_err}")
        return None if (fetch_one or fetch_all) else (0 if commit else False)
        
    finally:
        if conn:
            try:
                conn.close()
                logger.debug("DB connection closed.")
            except sqlite3.Error as e:
                logger.error(f"Error closing DB: {e}")

# --- Generic Save Function ---
def save_masters_bulk(table_name, unique_key_column, data_list, column_map):
    """Generic function to save master data using INSERT OR REPLACE."""
    if not data_list:
        logger.info(f"No data provided for table '{table_name}'.")
        return 0
    
    logger.info(f"Bulk save: {len(data_list)} records into '{table_name}'...")
    now_ts = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    records = []
    skipped = 0
    
    for item_dict in data_list:
        if not item_dict or not item_dict.get(unique_key_column):
            logger.warning(f"Skip {table_name}, missing key '{unique_key_column}': {item_dict}")
            skipped += 1
            continue
        
        record_tuple = [item_dict.get(key) for key in column_map] + [now_ts]
        records.append(tuple(record_tuple))
    
    if skipped:
        logger.warning(f"Skipped {skipped} records for '{table_name}'.")
    
    if not records:
        logger.warning(f"No valid records to save for '{table_name}'.")
        return 0
    
    sql_columns = column_map + ["last_synced_timestamp"]
    cols_sql = ", ".join([f"`{c}`" for c in sql_columns])
    placeholders = ", ".join(["?"] * len(sql_columns))
    
    sql = f"INSERT OR REPLACE INTO `{table_name}` ({cols_sql}) VALUES ({placeholders})"
    rows_affected = execute_query(sql, records, commit=True, executemany=True)
    processed_count = len(records)
    
    if rows_affected is not None:
        logger.info(f"Bulk save '{table_name}' OK. Processed {processed_count}. DB Rows: {rows_affected}.")
    else:
        logger.error(f"Bulk save '{table_name}' failed.")
        processed_count = 0
    
    return processed_count


# --- Initialize Database ---
def init_db():
    """Initializes the database by importing and running schema creation."""
    from .schema import create_all_tables, clean_orphaned_rows
    
    logger.info(f"Initializing DB schema check: {DATABASE_PATH}")
    create_all_tables()
    clean_orphaned_rows()
    logger.info("DB schema initialization and cleanup complete.")
