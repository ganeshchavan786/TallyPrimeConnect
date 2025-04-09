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

# --- Column Definitions for 'companies' Table ---
COMPANY_DETAIL_COLUMNS = {
    "tally_company_name": "TEXT NOT NULL", "formal_name": "TEXT", "address": "TEXT",
    "state_name": "TEXT", "country_name": "TEXT", "pincode": "TEXT", "phone_number": "TEXT",
    "mobile_no": "TEXT", "fax_number": "TEXT", "email": "TEXT", "website": "TEXT",
    "start_date": "TEXT", "books_date": "TEXT", "is_security_on": "BOOLEAN", "owner_name": "TEXT",
    "is_tally_audit_on": "BOOLEAN", "is_disallow_edu": "BOOLEAN", "currency_name": "TEXT",
    "currency_formal_name": "TEXT", "is_currency_suffix": "BOOLEAN", "in_millions": "BOOLEAN",
    "decimal_places": "INTEGER", "decimal_symbol": "TEXT", "decimal_places_printing": "INTEGER",
    "guid": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "serial_number": "TEXT", "account_id": "TEXT", "site_id": "TEXT", "admin_email": "TEXT",
    "is_indian": "BOOLEAN", "is_silver": "BOOLEAN", "is_gold": "BOOLEAN", "is_licensed": "BOOLEAN",
    "version": "TEXT", "gateway_server": "TEXT", "acting_as": "TEXT",
    "odbc_enabled": "BOOLEAN", "odbc_port": "INTEGER",
    "sync_status": "TEXT DEFAULT 'Not Synced'", "last_sync_timestamp": "DATETIME"
}

# --- DB Connection ---
def get_db_connection():
    """Establishes and returns a database connection."""
    os.makedirs(DATABASE_DIR, exist_ok=True);
    try: conn = sqlite3.connect(DATABASE_PATH, timeout=SQLITE_TIMEOUT); conn.row_factory = sqlite3.Row; conn.execute("PRAGMA foreign_keys = ON;"); logger.debug(f"DB connection established: {DATABASE_PATH}"); return conn
    except sqlite3.Error as e: logger.exception(f"DB connection error: {e}"); return None

# --- DB Execution Helper ---
def _execute_db(sql: str, params: tuple | list[tuple] = (), fetch_one: bool = False, fetch_all: bool = False, commit: bool = False, executemany: bool = False) -> any:
    """Helper for executing SQLite commands with managed connections and error logging."""
    conn = None
    # Validate params type based on execution mode
    if executemany and not isinstance(params, list):
         logger.error(f"Executemany needs list of sequences, got {type(params)}."); return 0 if commit else None
    if not executemany and not isinstance(params, tuple):
         params = tuple(params) # Ensure tuple for single execute

    try:
        conn = get_db_connection()
        if conn is None: raise sqlite3.Error("Failed DB connection.")
        cursor = conn.cursor()
        op = "executemany" if executemany else "execute"
        logger.debug(f"Executing SQL ({op}): {sql[:100]}... Params: {'Multiple' if executemany else ('Yes' if params else 'No')}")

        if executemany: cursor.executemany(sql, params)
        else: cursor.execute(sql, params)

        result = None
        if commit: conn.commit(); result = cursor.rowcount; logger.debug(f"Commit OK. Rows: {result}")
        elif fetch_one: result = cursor.fetchone(); logger.debug(f"Fetch one OK. Result: {'Row' if result else 'None'}")
        elif fetch_all: result = cursor.fetchall(); logger.debug(f"Fetch all OK. Rows: {len(result) if result else 0}")
        return result

    except sqlite3.IntegrityError as e: # Catch specific IntegrityError first
        logger.warning(f"SQLite IntegrityError: {e}. SQL: {sql[:100]}...")
        if conn and commit: # Check if connection exists and it was a commit operation
            try:
                conn.rollback()
                logger.debug("Rolled back transaction due to IntegrityError.")
            except sqlite3.Error as rb_err:
                logger.error(f"Error during rollback after IntegrityError: {rb_err}")
        # Indicate failure / no change for commit, None otherwise might be better
        return 0 if commit else None # 0 rows affected by failed commit

    except sqlite3.Error as e: # Catch other general SQLite errors
        logger.exception(f"General SQLite Error: {e}. SQL: {sql[:100]}...")
        if conn and commit: # Check if connection exists and it was a commit operation
            try:
                conn.rollback()
                logger.debug("Rolled back transaction due to general SQLiteError during commit.")
            except sqlite3.Error as rb_err:
                logger.error(f"Error during rollback after general error: {rb_err}")
        # Indicate failure based on expected return type
        return None if (fetch_one or fetch_all) else (0 if commit else False)
    finally:
        if conn:
             try: conn.close(); logger.debug("DB connection closed.")
             except sqlite3.Error as e: logger.error(f"Error closing DB: {e}")

# --- Table Creation Functions ---
def create_tally_accounting_groups_table():
    """Creates the tally_accounting_groups table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_accounting_groups' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_accounting_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        parent TEXT,
        is_subledger BOOLEAN,
        is_addable BOOLEAN,
        basic_group_is_calculable BOOLEAN,
        addl_alloctype TEXT,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_accounting_groups'.")
    else:
        logger.debug("Successfully created/verified 'tally_accounting_groups' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_accgroup_name ON tally_accounting_groups (name);", commit=True)

def create_tally_ledgerbillwise_table():
    """Creates the tally_ledgerbillwise table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_ledgerbillwise' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_ledgerbillwise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ledger_guid TEXT,
        name TEXT,
        billdate TEXT,
        billcreditperiod TEXT,
        isadvance BOOLEAN,
        openingbalance REAL,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (ledger_guid) REFERENCES tally_ledgers(tally_guid)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_ledgerbillwise'.")
    else:
        logger.debug("Successfully created/verified 'tally_ledgerbillwise' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_ledgerbillwise_name ON tally_ledgerbillwise (name);", commit=True)

def create_tally_costcategory_table():
    """Creates the tally_costcategory table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_costcategory' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_costcategory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        allocate_revenue BOOLEAN,
        allocate_nonrevenue BOOLEAN,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_costcategory'.")
    else:
        logger.debug("Successfully created/verified 'tally_costcategory' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_costcategory_name ON tally_costcategory (name);", commit=True)

def create_tally_costcenter_table():
    """Creates the tally_costcenter table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_costcenter' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_costcenter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT,
        parent TEXT,
        revenue_ledger_for_opbal TEXT,
        email_id TEXT,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_costcenter'.")
    else:
        logger.debug("Successfully created/verified 'tally_costcenter' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_costcenter_name ON tally_costcenter (name);", commit=True)

def create_tally_currency_table():
    """Creates the tally_currency table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_currency' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_currency (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        mailing_name TEXT,
        iso_currency_code TEXT,
        decimal_places INTEGER,
        in_millions BOOLEAN,
        is_suffix BOOLEAN,
        has_space BOOLEAN,
        decimal_symbol TEXT,
        decimal_places_printing INTEGER,
        sort_position INTEGER,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_currency'.")
    else:
        logger.debug("Successfully created/verified 'tally_currency' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_currency_name ON tally_currency (name);", commit=True)

def create_tally_vouchertype_table():
    """Creates the tally_vouchertype table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_vouchertype' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_vouchertype (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        parent TEXT,
        additional_name TEXT,
        is_active BOOLEAN,
        numbering_method TEXT,
        prevent_duplicates BOOLEAN,
        effective_date TEXT,
        use_zero_entries BOOLEAN,
        print_after_save BOOLEAN,
        formal_receipt BOOLEAN,
        is_optional BOOLEAN,
        as_mfg_jrnl BOOLEAN,
        common_narration BOOLEAN,
        multi_narration BOOLEAN,
        use_for_pos_invoice BOOLEAN,
        use_for_jobwork BOOLEAN,
        is_for_jobwork_in BOOLEAN,
        allow_consumption BOOLEAN,
        is_default_alloc_enabled BOOLEAN,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_vouchertype'.")
    else:
        logger.debug("Successfully created/verified 'tally_vouchertype' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_vouchertype_name ON tally_vouchertype (name);", commit=True)

# --- Initialization ---
def init_db():
    """Initializes the database: Creates/updates all required tables."""
    logger.info(f"Initializing DB schema check: {DATABASE_PATH}")
    
    # Create companies table
    sql_base_companies = """CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_company_number TEXT UNIQUE NOT NULL, 
        tally_company_name TEXT NOT NULL, 
        description TEXT, 
        is_active BOOLEAN DEFAULT 1 NOT NULL, 
        added_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )"""
    if _execute_db(sql_base_companies, commit=True) is None: 
        raise sqlite3.Error("Failed create 'companies'.")
    
    # Check and update companies table columns
    conn_check = get_db_connection()
    existing_columns = []
    if conn_check:
        try: 
            existing_columns = [info[1].lower() for info in conn_check.execute("PRAGMA table_info(companies)").fetchall()]
        except sqlite3.Error as e: 
            logger.error(f"Could not get table info companies: {e}")
        finally: 
            conn_check.close()
    else: 
        logger.error("Cannot check columns for companies table.")
    
    # Add missing columns to companies table
    if existing_columns:
        for col_name, col_type in COMPANY_DETAIL_COLUMNS.items():
            if col_name.lower() not in existing_columns and col_name.lower() not in ['id','tally_company_number','tally_company_name','description','is_active','added_timestamp']:
                sql_add = f"ALTER TABLE companies ADD COLUMN `{col_name}` {col_type}"
                if _execute_db(sql_add, commit=True) is not None:
                    logger.info(f"Added/Verified column '{col_name}' in companies.")
                else:
                    logger.error(f"Failed add column {col_name} to companies.")
    
    # Create company_log table
    sql_log = """CREATE TABLE IF NOT EXISTS company_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_company_number TEXT NOT NULL, 
        action TEXT NOT NULL, 
        details TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )"""
    _execute_db(sql_log, commit=True)
    
    # Create accounting groups table
    create_tally_accounting_groups_table()
    
    # Create ledgers table
    logger.debug("Checking/Creating 'tally_ledgers' table...")
    sql_ledgers = """CREATE TABLE IF NOT EXISTS tally_ledgers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_guid TEXT UNIQUE NOT NULL, 
        tally_name TEXT NOT NULL, 
        parent_name TEXT, 
        currency_name TEXT, 
        opening_balance REAL, 
        closing_balance REAL, 
        is_billwise_on BOOLEAN, 
        affects_stock BOOLEAN, 
        is_cost_centres_on BOOLEAN, 
        gst_registration_type TEXT, 
        party_gstin TEXT, 
        last_synced_timestamp DATETIME NOT NULL
    )"""
    if _execute_db(sql_ledgers, commit=True) is None:
        logger.error("Failed create/verify 'tally_ledgers'.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_ledger_guid ON tally_ledgers (tally_guid);", commit=True)
    _execute_db("CREATE INDEX IF NOT EXISTS idx_ledger_name ON tally_ledgers (tally_name);", commit=True)
    
    # Create ledgerbillwise table (after ledgers table due to foreign key)
    create_tally_ledgerbillwise_table()
    
    # Create cost category table
    create_tally_costcategory_table()
    
    # Create cost center table
    create_tally_costcenter_table()
    
    # Create currency table
    create_tally_currency_table()
    
    # Create voucher type table
    create_tally_vouchertype_table()

    create_tally_stockgroupwithgst_table()
    create_tally_stockcategory_table()
    create_tally_godown_table()
    create_tally_stockitem_gst_table()
    create_tally_stockitem_mrp_table()
    create_tally_stockitem_bom_table()
    create_tally_stockitem_standardcost_table()
    create_tally_stockitem_standardprice_table()
    create_tally_stockitem_batchdetails_table()
    
    # Create stock items table
    logger.debug("Checking/Creating 'tally_stock_items' table...")
    sql_stock_items = """CREATE TABLE IF NOT EXISTS tally_stock_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_guid TEXT UNIQUE NOT NULL, 
        tally_name TEXT NOT NULL, 
        parent_name TEXT, 
        category_name TEXT, 
        base_units TEXT, 
        gst_applicable TEXT, 
        gst_type_of_supply TEXT, 
        hsn_code TEXT, 
        opening_balance REAL, 
        opening_rate REAL, 
        opening_value REAL, 
        closing_balance REAL, 
        closing_rate REAL, 
        closing_value REAL, 
        last_synced_timestamp DATETIME NOT NULL
    )"""
    if _execute_db(sql_stock_items, commit=True) is None:
        logger.error("Failed create/verify 'tally_stock_items'.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_guid ON tally_stock_items (tally_guid);", commit=True)
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_name ON tally_stock_items (tally_name);", commit=True)
    
    # Create stock groups table
    logger.debug("Checking/Creating 'tally_stock_groups' table...")
    sql_stock_groups = """CREATE TABLE IF NOT EXISTS tally_stock_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_guid TEXT UNIQUE NOT NULL, 
        tally_name TEXT NOT NULL, 
        parent_name TEXT, 
        is_addable BOOLEAN, 
        master_id INTEGER, 
        alter_id INTEGER, 
        last_synced_timestamp DATETIME NOT NULL
    )"""
    if _execute_db(sql_stock_groups, commit=True) is None:
        logger.error("Failed create/verify 'tally_stock_groups'.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockgroup_guid ON tally_stock_groups (tally_guid);", commit=True)
    
    # Create units table
    logger.debug("Checking/Creating 'tally_units' table...")
    sql_units = """CREATE TABLE IF NOT EXISTS tally_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_guid TEXT UNIQUE NOT NULL, 
        tally_name TEXT NOT NULL, 
        original_name TEXT, 
        base_units TEXT, 
        additional_units TEXT, 
        conversion REAL, 
        decimal_places INTEGER, 
        is_simple_unit BOOLEAN, 
        master_id INTEGER, 
        alter_id INTEGER, 
        last_synced_timestamp DATETIME NOT NULL
    )"""
    if _execute_db(sql_units, commit=True) is None:
        logger.error("Failed create/verify 'tally_units'.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_unit_guid ON tally_units (tally_guid);", commit=True)
    
    logger.info("DB schema initialization check complete.")

# --- Logging ---
def log_change(tally_company_number: str, action: str, details: str = ""):
    details_str = (details[:1000] + '...') if len(details) > 1003 else details
    sql = "INSERT INTO company_log (tally_company_number, action, details) VALUES (?, ?, ?)"
    rc = _execute_db(sql, (str(tally_company_number), action.upper(), details_str), commit=True)
    if not rc: logger.error(f"Failed log action '{action}' for {tally_company_number}")

# --- Company CRUD Operations ---
def add_company_to_db(name: str, number: str) -> bool:
    """Adds a company or reactivates it if soft-deleted. Logs the action. Returns True if added/reactivated."""
    if not name or not number: logger.error("Add company failed: Name or number is empty."); return False
    number_str = str(number)
    check_sql = "SELECT id, is_active FROM companies WHERE tally_company_number = ?"
    existing = _execute_db(check_sql, (number_str,), fetch_one=True)
    if existing:
        if not existing['is_active']: # Company exists but is inactive
            logger.info(f"Reactivating company {number_str} ('{name}').")
            # Reset sync status on reactivation
            update_sql = "UPDATE companies SET tally_company_name = ?, is_active = 1, sync_status = 'Not Synced' WHERE tally_company_number = ?"
            rowcount = _execute_db(update_sql, (name, number_str), commit=True)
            if rowcount: log_change(number_str, "REACTIVATE", f"Name: '{name}'"); return True
            else: logger.error(f"Failed to reactivate company {number_str}"); return False
        else: # Company exists and is already active
            logger.info(f"Company {number_str} ('{name}') already active in database."); return False # Not newly added or reactivated
    else: # Company does not exist at all
        logger.info(f"Adding new company {number_str} ('{name}').")
        insert_sql = "INSERT INTO companies (tally_company_number, tally_company_name, is_active, sync_status) VALUES (?, ?, 1, 'Not Synced')"
        rowcount = _execute_db(insert_sql, (number_str, name), commit=True)
        if rowcount: log_change(number_str, "ADD", f"Name: '{name}'"); return True
        else: logger.error(f"Failed to insert new company {number_str}"); return False

def get_added_companies() -> list[dict]:
    """Retrieves all ACTIVE companies with basic details + sync status."""
    sql = "SELECT tally_company_name, tally_company_number, description, sync_status FROM companies WHERE is_active = 1 ORDER BY tally_company_name"
    rows = _execute_db(sql, fetch_all=True)
    return [dict(row) for row in rows] if rows else []

def get_company_details(tally_company_number: str) -> dict | None:
    """Retrieves editable details (Name, Description) for a specific active company."""
    sql = "SELECT tally_company_name, tally_company_number, description FROM companies WHERE tally_company_number = ? AND is_active = 1"
    row = _execute_db(sql, (str(tally_company_number),), fetch_one=True)
    return dict(row) if row else None

def edit_company_in_db(tally_company_number: str, new_name: str, new_description: str | None) -> bool:
    """Updates Name and Description for an active company. Returns True on success."""
    if not tally_company_number or not new_name: logger.error("Edit failed: Number/Name empty."); return False
    num_str=str(tally_company_number); desc=new_description if new_description is not None else ""
    check_sql = "SELECT 1 FROM companies WHERE tally_company_name = ? AND tally_company_number != ? AND is_active = 1 LIMIT 1"
    if _execute_db(check_sql, (new_name, num_str), fetch_one=True): logger.warning(f"Edit fail {num_str}: Name '{new_name}' exists."); return False
    current=get_company_details(num_str)
    if not current: logger.error(f"Edit fail {num_str}: Not found/inactive."); return False
    current_name=current['tally_company_name']; current_desc=current.get('description', '') or ""
    if current_name == new_name and current_desc == desc: logger.info(f"No changes for {num_str}."); return False
    update_sql = "UPDATE companies SET tally_company_name = ?, description = ? WHERE tally_company_number = ? AND is_active = 1"; rc = _execute_db(update_sql, (new_name, desc, num_str), commit=True)
    if rc:
        log_items = [];
        if current_name != new_name: log_items.append(f"Name:'{current_name}'->'{new_name}'")
        if current_desc != desc: log_items.append("Desc updated")
        if log_items: log_change(num_str, "EDIT", "; ".join(log_items))
        logger.info(f"Company {num_str} updated."); return True
    else: logger.error(f"Edit unexpected fail {num_str}."); return False

def soft_delete_company(tally_company_number: str) -> bool:
    """Marks a company as inactive. Returns True on success."""
    num_str = str(tally_company_number); sql = "UPDATE companies SET is_active = 0 WHERE tally_company_number = ? AND is_active = 1"; rc = _execute_db(sql, (num_str,), commit=True)
    if rc: log_change(num_str, "SOFT_DELETE", "Marked inactive"); logger.info(f"{num_str} inactive."); return True
    else: logger.warning(f"Soft delete fail {num_str}: Not found/inactive."); return False

def update_company_details(tally_company_number: str, details: dict) -> bool:
    """Updates company row with details from sync. Sets status 'Synced'."""
    if not tally_company_number or not details: logger.error(f"Update details fail {tally_company_number}: Invalid input."); return False
    num_str = str(tally_company_number); now_iso = datetime.datetime.now().isoformat(sep=' ', timespec='seconds');
    set_clauses = []; params = [];
    for key, value in details.items():
        db_key = key.lower()
        if db_key in COMPANY_DETAIL_COLUMNS:
             # If name update is desired, ensure 'tally_company_name' IS NOT skipped here
             # if db_key == 'tally_company_name': continue # Uncomment to SKIP name update
             params.append(value); set_clauses.append(f"`{db_key}` = ?")
        elif db_key not in ['id','description', 'is_active', 'tally_company_number','added_timestamp']: logger.warning(f"Skipping unknown key '{key}' update {num_str}")
    if not set_clauses: logger.warning(f"No valid details for {num_str}"); update_company_sync_status(num_str, 'Sync Failed'); return False
    set_clauses.append("`sync_status` = ?"); params.append("Synced")
    set_clauses.append("`last_sync_timestamp` = ?"); params.append(now_iso)
    params.append(num_str) # For WHERE
    sql = f"UPDATE companies SET {', '.join(set_clauses)} WHERE `tally_company_number` = ? AND `is_active` = 1"; rc = _execute_db(sql, tuple(params), commit=True)
    if rc: log_change(num_str, "SYNC_SUCCESS", "Details updated from sync"); logger.info(f"Details updated OK {num_str}."); return True
    else: logger.error(f"Failed DB update for {num_str}."); update_company_sync_status(num_str, 'Sync Failed'); return False

def update_company_sync_status(tally_company_number: str, status: str):
    """Explicitly sets the sync_status and logs."""
    logger.info(f"Setting sync status '{status}' for {tally_company_number}"); num_str=str(tally_company_number); now_iso = datetime.datetime.now().isoformat(sep=' ', timespec='seconds'); sql = "UPDATE companies SET sync_status = ?, last_sync_timestamp = ? WHERE tally_company_number = ?"; rc = _execute_db(sql, (status, now_iso, num_str), commit=True)
    if rc: log_change(num_str, "STATUS_UPDATE", f"Sync status set to '{status}'"); logger.debug(f"Status updated {status} for {num_str}")
    else: logger.warning(f"Failed update sync status to {status} for {num_str}"); log_change(num_str, "STATUS_UPDATE_FAIL", f"Failed set status '{status}'")

# --- Master Data DB Operations ---
def save_masters_bulk(table_name: str, unique_key_column: str, data_list: list[dict], column_map: list[str]):
    """Generic function to save master data using INSERT OR REPLACE."""
    if not data_list: logger.info(f"No data provided for table '{table_name}'."); return 0
    logger.info(f"Bulk save: {len(data_list)} records into '{table_name}'...")
    now_ts = datetime.datetime.now().isoformat(sep=' ', timespec='seconds'); records = []; skipped = 0
    for item_dict in data_list:
        if not item_dict or not item_dict.get(unique_key_column): logger.warning(f"Skip {table_name}, missing key '{unique_key_column}': {item_dict}"); skipped += 1; continue
        record_tuple = [item_dict.get(key) for key in column_map] + [now_ts]; records.append(tuple(record_tuple))
    if skipped: logger.warning(f"Skipped {skipped} records for '{table_name}'.")
    if not records: logger.warning(f"No valid records to save for '{table_name}'."); return 0
    sql_columns = column_map + ["last_synced_timestamp"]; cols_sql = ", ".join([f"`{c}`" for c in sql_columns]); placeholders = ", ".join(["?"] * len(sql_columns))
    sql = f"INSERT OR REPLACE INTO `{table_name}` ({cols_sql}) VALUES ({placeholders})"
    rows_affected = _execute_db(sql, records, commit=True, executemany=True); processed_count = len(records)
    if rows_affected is not None: logger.info(f"Bulk save '{table_name}' OK. Processed {processed_count}. DB Rows: {rows_affected}.")
    else: logger.error(f"Bulk save '{table_name}' failed."); processed_count = 0
    return processed_count

def save_ledgers(ledgers_data: list[dict]) -> int:
    """Saves a list of ledger data to the tally_ledgers table."""
    column_order = ["tally_guid", "tally_name", "parent_name", "currency_name", "opening_balance", "closing_balance", "is_billwise_on", "affects_stock", "is_cost_centres_on", "gst_registration_type", "party_gstin"]
    return save_masters_bulk("tally_ledgers", "tally_guid", ledgers_data, column_order)

def save_stock_items(items_data: list[dict]) -> int:
    """Saves a list of stock item data to the tally_stock_items table."""

# Add these functions to database.py

def save_stock_groups(groups_data: list[dict]) -> int:
    """Saves a list of stock group data to the tally_stock_groups table."""
    column_order = ["tally_guid", "tally_name", "parent_name", "is_addable", "master_id", "alter_id"]
    return save_masters_bulk("tally_stock_groups", "tally_guid", groups_data, column_order)

def save_stock_items(items_data: list[dict]) -> int:
    """Saves a list of stock item data to the tally_stock_items table."""
    column_order = ["tally_guid", "tally_name", "parent_name", "category_name", "base_units", 
                   "opening_balance", "opening_rate", "opening_value", "closing_balance", 
                   "closing_rate", "closing_value", "gst_applicable", "gst_type_of_supply", "hsn_code"]
    return save_masters_bulk("tally_stock_items", "tally_guid", items_data, column_order)

def save_units(units_data: list[dict]) -> int:
    """Saves a list of unit data to the tally_units table."""
    column_order = ["tally_guid", "tally_name", "original_name", "base_units", "additional_units", 
                   "conversion", "decimal_places", "is_simple_unit", "master_id", "alter_id"]
    return save_masters_bulk("tally_units", "tally_guid", units_data, column_order)

def save_costcategory(costcategory_data: list[dict]) -> int:
    """Saves a list of cost category data to the tally_costcategory table."""
    column_order = ["name", "allocate_revenue", "allocate_nonrevenue", "master_id", "alter_id"]
    return save_masters_bulk("tally_costcategory", "name", costcategory_data, column_order)

def save_costcenter(costcenter_data: list[dict]) -> int:
    """Saves a list of cost center data to the tally_costcenter table."""
    column_order = ["name", "category", "parent", "revenue_ledger_for_opbal", "email_id", 
                   "master_id", "alter_id"]
    return save_masters_bulk("tally_costcenter", "name", costcenter_data, column_order)

def save_currency(currency_data: list[dict]) -> int:
    """Saves a list of currency data to the tally_currency table."""
    column_order = ["name", "mailing_name", "iso_currency_code", "decimal_places", "in_millions", 
                   "is_suffix", "has_space", "decimal_symbol", "decimal_places_printing", 
                   "sort_position", "master_id", "alter_id"]
    return save_masters_bulk("tally_currency", "name", currency_data, column_order)

def save_vouchertype(vouchertype_data: list[dict]) -> int:
    """Saves a list of voucher type data to the tally_vouchertype table."""
    column_order = ["name", "parent", "additional_name", "is_active", "numbering_method", 
                   "prevent_duplicates", "effective_date", "use_zero_entries", "print_after_save",
                   "formal_receipt", "is_optional", "as_mfg_jrnl", "common_narration", 
                   "multi_narration", "use_for_pos_invoice", "use_for_jobwork", 
                   "is_for_jobwork_in", "allow_consumption", "is_default_alloc_enabled",
                   "master_id", "alter_id"]
    return save_masters_bulk("tally_vouchertype", "name", vouchertype_data, column_order)

def save_ledgerbillwise(ledgerbillwise_data: list[dict]) -> int:
    """Saves a list of ledger billwise data to the tally_ledgerbillwise table."""
    column_order = ["ledger_guid", "name", "billdate", "billcreditperiod", "isadvance", "openingbalance"]
    return save_masters_bulk("tally_ledgerbillwise", "name", ledgerbillwise_data, column_order)

def save_accounting_groups(groups_data: list[dict]) -> int:
    """Saves a list of accounting group data to the tally_accounting_groups table."""
    column_order = ["name", "parent", "is_subledger", "is_addable", "basic_group_is_calculable", 
                   "addl_alloctype", "master_id", "alter_id"]
    return save_masters_bulk("tally_accounting_groups", "name", groups_data, column_order)

def create_tally_stockgroupwithgst_table():
    """Creates the tally_stockgroupwithgst table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockgroupwithgst' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockgroupwithgst (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        parent TEXT,
        is_addable BOOLEAN,
        master_id INTEGER,
        alter_id INTEGER,
        gst_rate_duty_head TEXT,
        gst_rate_valuation_type TEXT,
        gst_rate REAL,
        applicable_from TEXT,
        hsn_code TEXT,
        hsn TEXT,
        taxability TEXT,
        is_reverse_charge_applicable BOOLEAN,
        is_non_gst_goods BOOLEAN,
        gst_ineligible_itc BOOLEAN,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_groups(tally_name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockgroupwithgst'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockgroupwithgst' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockgroupwithgst_name ON tally_stockgroupwithgst (name);", commit=True)

def create_tally_stockcategory_table():
    """Creates the tally_stockcategory table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockcategory' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockcategory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        parent TEXT,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockcategory'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockcategory' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockcategory_name ON tally_stockcategory (name);", commit=True)

def create_tally_godown_table():
    """Creates the tally_godown table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_godown' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_godown (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        parent TEXT,
        has_no_space BOOLEAN,
        is_internal BOOLEAN,
        is_external BOOLEAN,
        address TEXT,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_godown'.")
    else:
        logger.debug("Successfully created/verified 'tally_godown' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_godown_name ON tally_godown (name);", commit=True)

def create_tally_stockitem_gst_table():
    """Creates the tally_stockitem_gst table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockitem_gst' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockitem_gst (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        master_id INTEGER,
        alter_id INTEGER,
        gst_rate_duty_head TEXT,
        gst_rate_valuation_type TEXT,
        gst_rate REAL,
        applicable_from TEXT,
        hsn_code TEXT,
        hsn TEXT,
        taxability TEXT,
        is_reverse_charge_applicable BOOLEAN,
        is_non_gst_goods BOOLEAN,
        gst_ineligible_itc BOOLEAN,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_gst'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_gst' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_gst_name ON tally_stockitem_gst (name);", commit=True)

def create_tally_stockitem_mrp_table():
    """Creates the tally_stockitem_mrp table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockitem_mrp' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockitem_mrp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        master_id INTEGER,
        alter_id INTEGER,
        from_date TEXT,
        state_name TEXT,
        mrp_rate REAL,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_mrp'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_mrp' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_mrp_name ON tally_stockitem_mrp (name);", commit=True)

def create_tally_stockitem_bom_table():
    """Creates the tally_stockitem_bom table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockitem_bom' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockitem_bom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        master_id INTEGER,
        alter_id INTEGER,
        nature_of_item TEXT,
        stockitem_name TEXT,
        godown_name TEXT,
        actual_qty REAL,
        component_list_name TEXT,
        component_basic_qty REAL,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_name),
        FOREIGN KEY (godown_name) REFERENCES tally_godown(name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_bom'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_bom' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_bom_name ON tally_stockitem_bom (name);", commit=True)

def create_tally_stockitem_standardcost_table():
    """Creates the tally_stockitem_standardcost table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockitem_standardcost' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockitem_standardcost (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        master_id INTEGER,
        alter_id INTEGER,
        date TEXT,
        rate REAL,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_standardcost'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_standardcost' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_standardcost_name ON tally_stockitem_standardcost (name);", commit=True)

def create_tally_stockitem_standardprice_table():
    """Creates the tally_stockitem_standardprice table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockitem_standardprice' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockitem_standardprice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        master_id INTEGER,
        alter_id INTEGER,
        date TEXT,
        rate REAL,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_standardprice'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_standardprice' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_standardprice_name ON tally_stockitem_standardprice (name);", commit=True)

def create_tally_stockitem_batchdetails_table():
    """Creates the tally_stockitem_batchdetails table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stockitem_batchdetails' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stockitem_batchdetails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        master_id INTEGER,
        alter_id INTEGER,
        mfg_date TEXT,
        godown_name TEXT,
        batch_name TEXT,
        opening_balance REAL,
        opening_value REAL,
        opening_rate REAL,
        expiry_period TEXT,
        last_synced_timestamp DATETIME NOT NULL,
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_name),
        FOREIGN KEY (godown_name) REFERENCES tally_godown(name)
    )
    """
    if _execute_db(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_batchdetails'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_batchdetails' table.")
    _execute_db("CREATE INDEX IF NOT EXISTS idx_stockitem_batchdetails_name ON tally_stockitem_batchdetails (name);", commit=True)


def save_stockgroupwithgst(groups_data: list[dict]) -> int:
    """Saves a list of stock group GST data to the tally_stockgroupwithgst table."""
    column_order = [
        "name", "parent", "is_addable", "master_id", "alter_id",
        "gst_rate_duty_head", "gst_rate_valuation_type", "gst_rate",
        "applicable_from", "hsn_code", "hsn", "taxability",
        "is_reverse_charge_applicable", "is_non_gst_goods", "gst_ineligible_itc"
    ]
    return save_masters_bulk("tally_stockgroupwithgst", "name", groups_data, column_order)

def save_stockcategory(category_data: list[dict]) -> int:
    """Saves a list of stock category data to the tally_stockcategory table."""
    column_order = ["name", "parent", "master_id", "alter_id"]
    return save_masters_bulk("tally_stockcategory", "name", category_data, column_order)

def save_godown(godown_data: list[dict]) -> int:
    """Saves a list of godown data to the tally_godown table."""
    column_order = [
        "name", "parent", "has_no_space", "is_internal", 
        "is_external", "address", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_godown", "name", godown_data, column_order)

def save_stockitem_gst(gst_data: list[dict]) -> int:
    """Saves a list of stock item GST data to the tally_stockitem_gst table."""
    column_order = [
        "name", "master_id", "alter_id", "gst_rate_duty_head",
        "gst_rate_valuation_type", "gst_rate", "applicable_from",
        "hsn_code", "hsn", "taxability", "is_reverse_charge_applicable",
        "is_non_gst_goods", "gst_ineligible_itc"
    ]
    return save_masters_bulk("tally_stockitem_gst", "name", gst_data, column_order)

def save_stockitem_mrp(mrp_data: list[dict]) -> int:
    """Saves a list of stock item MRP data to the tally_stockitem_mrp table."""
    column_order = [
        "name", "master_id", "alter_id", "from_date",
        "state_name", "mrp_rate"
    ]
    return save_masters_bulk("tally_stockitem_mrp", "name", mrp_data, column_order)

def save_stockitem_bom(bom_data: list[dict]) -> int:
    """Saves a list of stock item BOM data to the tally_stockitem_bom table."""
    column_order = [
        "name", "master_id", "alter_id", "nature_of_item",
        "stockitem_name", "godown_name", "actual_qty",
        "component_list_name", "component_basic_qty"
    ]
    return save_masters_bulk("tally_stockitem_bom", "name", bom_data, column_order)

def save_stockitem_standardcost(cost_data: list[dict]) -> int:
    """Saves a list of stock item standard cost data to the tally_stockitem_standardcost table."""
    column_order = ["name", "master_id", "alter_id", "date", "rate"]
    return save_masters_bulk("tally_stockitem_standardcost", "name", cost_data, column_order)

def save_stockitem_standardprice(price_data: list[dict]) -> int:
    """Saves a list of stock item standard price data to the tally_stockitem_standardprice table."""
    column_order = ["name", "master_id", "alter_id", "date", "rate"]
    return save_masters_bulk("tally_stockitem_standardprice", "name", price_data, column_order)

def save_stockitem_batchdetails(batch_data: list[dict]) -> int:
    """Saves a list of stock item batch details to the tally_stockitem_batchdetails table."""
    column_order = [
        "name", "master_id", "alter_id", "mfg_date", "godown_name",
        "batch_name", "opening_balance", "opening_value", "opening_rate",
        "expiry_period"
    ]
    return save_masters_bulk("tally_stockitem_batchdetails", "name", batch_data, column_order)
