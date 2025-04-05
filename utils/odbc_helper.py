# TallyPrimeConnect/utils/odbc_helper.py
import pyodbc
import logging
import datetime

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Import COMPANY_DETAIL_COLUMNS ---
try:
    from utils.database import COMPANY_DETAIL_COLUMNS
    logger.debug("Imported COMPANY_DETAIL_COLUMNS from database.py for ODBC helper.")
except ImportError:
    logger.critical("CRITICAL: Failed to import COMPANY_DETAIL_COLUMNS. Type conversion may fail.")
    COMPANY_DETAIL_COLUMNS = {} # Fallback

# --- Constants ---
TALLY_ODBC_DSN = "TallyODBC64_9001" # !!! VERIFY THIS NAME !!!
ODBC_CONNECT_TIMEOUT = 15

# --- Field Mapping (ODBC -> Dict Key) ---
FIELD_MAP = {
    "Name": "tally_company_name", "BasicCompanyFormalName": "formal_name",
    "Address": "address", "StateName": "state_name", "CountryName": "country_name",
    "PinCode": "pincode", "PhoneNumber": "phone_number", "MobileNo": "mobile_no",
    "FaxNumber": "fax_number", "Email": "email", "Website": "website",
    "StartingFrom": "start_date", "BooksFrom": "books_date",
    "IsSecurityOn": "is_security_on", "OwnerName": "owner_name",
    "IsTallyAuditOn": "is_tally_audit_on", "IsDisAllowInEduMode": "is_disallow_edu",
    "CurrencyName": "currency_name", "FormalName": "currency_formal_name",
    "IsSuffix": "is_currency_suffix", "InMillions": "in_millions",
    "DecimalPlaces": "decimal_places", "DecimalSymbol": "decimal_symbol",
    "DecimalPlacesForPrinting": "decimal_places_printing", "GUID": "guid",
    "Masterid": "master_id", "Alterid": "alter_id"
}
FIELD_MAP_LOWER = {k.lower(): v for k, v in FIELD_MAP.items()}

# --- Field Mapping for License Info ---
LICENSE_FIELD_MAP = {
    "TallySerialNo": "serial_number", "TallyAccountID": "account_id", "TallySiteID": "site_id",
    "TallyAdminEmailID": "admin_email", "TallyIsIndian": "is_indian", "TallyIsSilver": "is_silver",
    "TallyIsGold": "is_gold", "TallyIsLicensedMode": "is_licensed", "TallyInstalledVersion": "version",
    "TAllygatewayserver": "gateway_server", "TallyActingAs": "acting_as",
    "TallyODBCEnabled": "odbc_enabled", "TallyODBCPort": "odbc_port"
}
LICENSE_FIELD_TYPES = {
    "serial_number": "TEXT", "account_id": "TEXT", "site_id": "TEXT", "admin_email": "TEXT",
    "is_indian": "BOOLEAN", "is_silver": "BOOLEAN", "is_gold": "BOOLEAN", "is_licensed": "BOOLEAN",
    "version": "TEXT", "gateway_server": "TEXT", "acting_as": "TEXT",
    "odbc_enabled": "BOOLEAN", "odbc_port": "INTEGER"
}
LICENSE_FIELD_MAP_LOWER = {k.lower(): v for k, v in LICENSE_FIELD_MAP.items()}

# --- Conversion Helper ---
def _convert_odbc_value(value, target_type: str):
    """Helper to convert pyodbc values to Python/SQLite types."""
    if value is None: return None
    value_str_stripped = None
    if isinstance(value, str): value_str_stripped = value.strip();
    if not value_str_stripped and isinstance(value, str): return None
    original_value_for_logging = value
    try:
        val_to_check = value_str_stripped if value_str_stripped is not None else value
        if target_type == "BOOLEAN": s_val = str(val_to_check).lower(); return s_val in ['yes', 'true', '1']
        elif target_type == "INTEGER":
             if isinstance(val_to_check, str) and not (val_to_check.isdigit() or (val_to_check.startswith('-') and val_to_check[1:].isdigit())): return None
             return int(val_to_check)
        elif target_type == "DATE":
             if isinstance(value, datetime.date): return value.isoformat()
             s_val = str(val_to_check);
             if len(s_val) == 8 and s_val.isdigit(): # YYYYMMDD
                 try: return datetime.datetime.strptime(s_val, '%Y%m%d').date().isoformat()
                 except ValueError: pass
             return s_val # Fallback
        else: return str(val_to_check) # TEXT
    except Exception as e: logger.warning(f"Conv Err: '{original_value_for_logging}' to {target_type}: {e}"); return None

# --- Fetch Company Details ---
def fetch_company_details_odbc(company_number_context: str) -> dict | None:
    """Fetches detailed metadata via Tally ODBC for the *currently loaded* company."""
    select_fields = ", ".join([f"${key}" for key in FIELD_MAP.keys()])
    query = f"SELECT {select_fields} FROM HSp_CMPScreennColl"; params = ()
    conn = None; details = None; logger.info(f"ODBC Connect DSN: {TALLY_ODBC_DSN} (Context: {company_number_context})")
    try:
        conn = pyodbc.connect(f'DSN={TALLY_ODBC_DSN}', autocommit=True, timeout=ODBC_CONNECT_TIMEOUT); cursor = conn.cursor()
        logger.info(f"Executing ODBC query for details (Context: {company_number_context})..."); cursor.execute(query, params); row = cursor.fetchone()
        if row:
            logger.info(f"Fetched details row via ODBC (Context: {company_number_context})."); details = {}; column_names = [col[0] for col in cursor.description]; conversion_errors = 0
            for i, col_name_prefix in enumerate(column_names):
                field_name_lower = col_name_prefix.strip('$').lower(); dict_key = FIELD_MAP_LOWER.get(field_name_lower)
                if dict_key:
                    target_db_type = COMPANY_DETAIL_COLUMNS.get(dict_key, "TEXT"); converted_value = _convert_odbc_value(row[i], target_db_type); details[dict_key] = converted_value
                    if converted_value is None and row[i] is not None and str(row[i]).strip() != '': conversion_errors += 1; logger.warning(f"ODBC Conv None: '{row[i]}' (Col: {col_name_prefix}, Target: {target_db_type})")
                else: logger.debug(f"Ignoring unmapped ODBC column: {col_name_prefix}")
            fetched_name = details.get('tally_company_name'); logger.info(f"ODBC details parsed. Name: '{fetched_name}'")
            if conversion_errors > 0: logger.warning(f"Found {conversion_errors} conversion issues for {company_number_context}.")
        else: logger.warning(f"ODBC query no rows (Context: {company_number_context}). Tally running? Company loaded?")
    except pyodbc.Error as e:
        sqlstate = e.args[0]
        if sqlstate == 'IM002': logger.critical(f"ODBC Connection Error: DSN '{TALLY_ODBC_DSN}' not found. Verify config. {e}", exc_info=True)
        elif sqlstate.startswith('08'): logger.error(f"ODBC Connection Error: Could not connect. Tally running? {e}", exc_info=True)
        else: logger.exception(f"ODBC Error executing query: {e}")
    except NameError as e: logger.critical(f"NameError (Import COMPANY_DETAIL_COLUMNS?): {e}", exc_info=True)
    except Exception as e: logger.exception(f"Unexpected ODBC fetch error (Context: {company_number_context}): {e}")
    finally:
        # --- !!! CORRECTED FINALLY BLOCK !!! ---
        if conn:
            try:
                conn.close()
                logger.debug("ODBC connection closed (company details fetch).")
            except pyodbc.Error as e:
                logger.error(f"Error closing ODBC connection (company details fetch): {e}")
        # --- End Correction ---
    return details

# --- Fetch License Info ---
def fetch_tally_license_info_odbc() -> dict | None:
    """Fetches Tally License information via ODBC using HSPTallyLicensecoll."""
    select_fields = ", ".join([f"${key}" for key in LICENSE_FIELD_MAP.keys()])
    query = f"SELECT {select_fields} FROM HSPTallyLicensecoll"; params = ()
    conn = None; details = None; logger.info(f"ODBC Connect for License Info (DSN: {TALLY_ODBC_DSN})...")
    try:
        conn = pyodbc.connect(f'DSN={TALLY_ODBC_DSN}', autocommit=True, timeout=ODBC_CONNECT_TIMEOUT); cursor = conn.cursor()
        logger.info("Executing ODBC query for license details..."); cursor.execute(query, params); row = cursor.fetchone()
        if row:
            logger.info("Fetched license row via ODBC."); details = {}; column_names = [col[0] for col in cursor.description]; conversion_errors = 0
            for i, col_name_prefix in enumerate(column_names):
                field_name_lower = col_name_prefix.strip('$').lower(); dict_key = LICENSE_FIELD_MAP_LOWER.get(field_name_lower)
                if dict_key:
                    target_type = LICENSE_FIELD_TYPES.get(dict_key, "TEXT"); converted_value = _convert_odbc_value(row[i], target_type); details[dict_key] = converted_value
                    if converted_value is None and row[i] is not None and str(row[i]).strip() != '': conversion_errors += 1; logger.warning(f"License Conv None: '{row[i]}' (Col: {col_name_prefix}, Target: {target_type})")
                else: logger.debug(f"Ignoring unmapped license column: {col_name_prefix}")
            logger.info("License details parsed.");
            if conversion_errors > 0: logger.warning(f"Found {conversion_errors} conversion issues for license info.")
        else: logger.warning("ODBC query for license returned no rows.")
    except pyodbc.Error as e: # Corrected indentation for this block too
        sqlstate = e.args[0]
        if sqlstate == 'IM002': logger.critical(f"ODBC DSN '{TALLY_ODBC_DSN}' not found. {e}", exc_info=True)
        elif sqlstate.startswith('08'): logger.error(f"ODBC Connection Error: {e}", exc_info=True)
        else: logger.exception(f"ODBC Error license query: {e}")
    except Exception as e: logger.exception(f"Unexpected error during ODBC license fetch: {e}")
    finally:
        # --- !!! CORRECTED FINALLY BLOCK !!! ---
        if conn:
            try:
                conn.close()
                logger.debug("ODBC connection closed (license fetch).")
            except pyodbc.Error as e:
                logger.error(f"Error closing ODBC connection (license fetch): {e}")
        # --- End Correction ---
    return details