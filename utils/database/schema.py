"""
Database schema definitions for TallyPrimeConnect.
Contains table creation functions and schema management.
"""

import logging
from .core import execute_query

logger = logging.getLogger(__name__)

# --- Column Definitions for 'companies' Table ---
COMPANY_DETAIL_COLUMNS = {
    "tally_company_name": "TEXT NOT NULL",
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
    "serial_number": "TEXT",
    "account_id": "TEXT",
    "site_id": "TEXT",
    "admin_email": "TEXT",
    "is_indian": "BOOLEAN",
    "is_silver": "BOOLEAN",
    "is_gold": "BOOLEAN",
    "is_licensed": "BOOLEAN",
    "version": "TEXT",
    "gateway_server": "TEXT",
    "acting_as": "TEXT",
    "odbc_enabled": "BOOLEAN",
    "odbc_port": "INTEGER",
    "sync_status": "TEXT DEFAULT 'Not Synced'",
    "last_sync_timestamp": "DATETIME"
}

# --- Table Creation Functions ---
def create_companies_table():
    """Creates the companies table if it doesn't exist."""
    logger.info("Checking/Creating 'companies' table...")
    
    # Create base companies table
    sql_base_companies = """
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_company_number TEXT UNIQUE NOT NULL, 
        tally_company_name TEXT NOT NULL, 
        description TEXT, 
        is_active BOOLEAN DEFAULT 1 NOT NULL, 
        is_deleted BOOLEAN DEFAULT 0,
        updated_timestamp DATETIME,
        added_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    if execute_query(sql_base_companies, commit=True) is None:
        raise Exception("Failed to create 'companies' table.")
    
    # Check existing columns
    from .core import get_db_connection
    conn_check = get_db_connection()
    existing_columns = []
    
    if conn_check:
        try:
            existing_columns = [info[1].lower() for info in conn_check.execute("PRAGMA table_info(companies)").fetchall()]
            
            # Add updated_timestamp column if it doesn't exist
            if 'updated_timestamp' not in existing_columns:
                alter_sql = "ALTER TABLE companies ADD COLUMN updated_timestamp DATETIME"
                execute_query(alter_sql, commit=True)
                logger.info("Added 'updated_timestamp' column to companies table.")
        except Exception as e:
            logger.error(f"Could not get table info for companies: {e}")
        finally:
            conn_check.close()
    else:
        logger.error("Cannot check columns for companies table.")
    
    # Add missing columns
    if existing_columns:
        for col_name, col_type in COMPANY_DETAIL_COLUMNS.items():
            if col_name.lower() not in existing_columns and col_name.lower() not in ['id', 'tally_company_number', 'tally_company_name', 'description', 'is_active', 'added_timestamp']:
                sql_add = f"ALTER TABLE companies ADD COLUMN `{col_name}` {col_type}"
                if execute_query(sql_add, commit=True) is not None:
                    logger.info(f"Added/Verified column '{col_name}' in companies.")
                else:
                    logger.error(f"Failed to add column {col_name} to companies.")



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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_accounting_groups'.")
    else:
        logger.debug("Successfully created/verified 'tally_accounting_groups' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_accgroup_name ON tally_accounting_groups (name);", commit=True)

def create_tally_ledgers_table():
    """Creates the tally_ledgers table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_ledgers' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_ledgers (
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
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_ledgers'.")
    else:
        logger.debug("Successfully created/verified 'tally_ledgers' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_ledger_guid ON tally_ledgers (tally_guid);", commit=True)
    execute_query("CREATE INDEX IF NOT EXISTS idx_ledger_name ON tally_ledgers (tally_name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_ledgerbillwise'.")
    else:
        logger.debug("Successfully created/verified 'tally_ledgerbillwise' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_ledgerbillwise_name ON tally_ledgerbillwise (name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_costcategory'.")
    else:
        logger.debug("Successfully created/verified 'tally_costcategory' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_costcategory_name ON tally_costcategory (name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_costcenter'.")
    else:
        logger.debug("Successfully created/verified 'tally_costcenter' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_costcenter_name ON tally_costcenter (name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_currency'.")
    else:
        logger.debug("Successfully created/verified 'tally_currency' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_currency_name ON tally_currency (name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_vouchertype'.")
    else:
        logger.debug("Successfully created/verified 'tally_vouchertype' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_vouchertype_name ON tally_vouchertype (name);", commit=True)

def create_tally_stock_groups_table():
    """Creates the tally_stock_groups table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stock_groups' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stock_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tally_guid TEXT UNIQUE NOT NULL,
        tally_name TEXT NOT NULL,
        parent_name TEXT,
        is_addable BOOLEAN,
        master_id INTEGER,
        alter_id INTEGER,
        last_synced_timestamp DATETIME NOT NULL
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stock_groups'.")
    else:
        logger.debug("Successfully created/verified 'tally_stock_groups' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockgroup_guid ON tally_stock_groups (tally_guid);", commit=True)
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockgroup_name ON tally_stock_groups (tally_name);", commit=True)

def create_tally_stock_items_table():
    """Creates the tally_stock_items table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_stock_items' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_stock_items (
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
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stock_items'.")
    else:
        logger.debug("Successfully created/verified 'tally_stock_items' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_guid ON tally_stock_items (tally_guid);", commit=True)
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_name ON tally_stock_items (tally_name);", commit=True)

def create_tally_units_table():
    """Creates the tally_units table if it doesn't exist."""
    logger.info("Checking/Creating 'tally_units' table...")
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS tally_units (
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
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_units'.")
    else:
        logger.debug("Successfully created/verified 'tally_units' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_unit_guid ON tally_units (tally_guid);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_groups(tally_guid)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockgroupwithgst'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockgroupwithgst' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockgroupwithgst_name ON tally_stockgroupwithgst (name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockcategory'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockcategory' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockcategory_name ON tally_stockcategory (name);", commit=True)

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
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_godown'.")
    else:
        logger.debug("Successfully created/verified 'tally_godown' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_godown_name ON tally_godown (name);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_guid)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_gst'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_gst' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_gst_name ON tally_stockitem_gst (name);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_guid)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_mrp'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_mrp' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_mrp_name ON tally_stockitem_mrp (name);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_guid),
        FOREIGN KEY (godown_name) REFERENCES tally_godown(name)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_bom'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_bom' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_bom_name ON tally_stockitem_bom (name);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_guid)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_standardcost'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_standardcost' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_standardcost_name ON tally_stockitem_standardcost (name);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_guid)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_standardprice'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_standardprice' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_standardprice_name ON tally_stockitem_standardprice (name);", commit=True)

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
        FOREIGN KEY (name) REFERENCES tally_stock_items(tally_guid),
        FOREIGN KEY (godown_name) REFERENCES tally_godown(name)
    )
    """
    if execute_query(sql_create_table, commit=True) is None:
        logger.error("Failed to create/verify 'tally_stockitem_batchdetails'.")
    else:
        logger.debug("Successfully created/verified 'tally_stockitem_batchdetails' table.")
    execute_query("CREATE INDEX IF NOT EXISTS idx_stockitem_batchdetails_name ON tally_stockitem_batchdetails (name);", commit=True)



def create_company_log_table():
    """Creates the company_log table if it doesn't exist."""
    logger.info("Checking/Creating 'company_log' table...")
    
    sql_log = """
    CREATE TABLE IF NOT EXISTS company_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        tally_company_number TEXT NOT NULL, 
        action TEXT NOT NULL, 
        details TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    if execute_query(sql_log, commit=True) is None:
        logger.error("Failed to create 'company_log' table.")
    else:
        logger.info("Successfully created/verified 'company_log' table.")

# Include all other table creation functions from the original file...

def create_all_tables():
    """Creates all database tables."""
    # Create company tables
    create_companies_table()
    create_company_log_table()
    
    # Create accounting tables
    create_tally_accounting_groups_table()
    create_tally_ledgers_table()
    create_tally_ledgerbillwise_table()
    create_tally_costcategory_table()
    create_tally_costcenter_table()
    create_tally_currency_table()
    create_tally_vouchertype_table()
    
    # Create inventory tables
    create_tally_stock_groups_table()
    create_tally_stock_items_table()
    create_tally_units_table()
    create_tally_stockgroupwithgst_table()
    create_tally_stockcategory_table()
    create_tally_godown_table()
    create_tally_stockitem_gst_table()
    create_tally_stockitem_mrp_table()
    create_tally_stockitem_bom_table()
    create_tally_stockitem_standardcost_table()
    create_tally_stockitem_standardprice_table()
    create_tally_stockitem_batchdetails_table()

def clean_orphaned_rows():
    """Removes orphaned rows from child tables."""
    logger.info("Cleaning orphaned rows from child tables...")
    
    queries = [
        # Remove orphaned rows from tally_stockitem_batchdetails
        """
        DELETE FROM tally_stockitem_batchdetails
        WHERE name NOT IN (SELECT tally_guid FROM tally_stock_items)
        """,
        # Remove orphaned rows from tally_stockgroupwithgst
        """
        DELETE FROM tally_stockgroupwithgst
        WHERE name NOT IN (SELECT tally_guid FROM tally_stock_groups)
        """
    ]
    
    for query in queries:
        if execute_query(query, commit=True) is not None:
            logger.info(f"Orphaned rows cleaned for query: {query[:50]}...")
        else:
            logger.error(f"Failed to clean orphaned rows for query: {query[:50]}...")
