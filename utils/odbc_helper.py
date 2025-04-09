import pyodbc
import logging
import datetime

# --- Setup Logger ---
logger = logging.getLogger(__name__)

# --- Import COMPANY_DETAIL_COLUMNS ---
try:
    from utils.database import COMPANY_DETAIL_COLUMNS as DB_COMPANY_COLUMNS
    logger.debug("Imported COMPANY_DETAIL_COLUMNS from database.py for ODBC helper.")
except ImportError:
    logger.critical("CRITICAL: Failed to import COMPANY_DETAIL_COLUMNS. Type conversion may fail.")
    DB_COMPANY_COLUMNS = {}  # Fallback

# --- Constants ---
TALLY_ODBC_DSN = "TallyODBC64_9001"  # Verify this DSN name
ODBC_CONNECT_TIMEOUT = 15
ODBC_QUERY_TIMEOUT = 60

# --- Field Mapping (COMPANY DETAILS) ---
COMPANY_FIELD_MAP = {
    "Name": "tally_company_name", "BasicCompanyFormalName": "formal_name", "Address": "address",
    "StateName": "state_name", "CountryName": "country_name", "PinCode": "pincode",
    "PhoneNumber": "phone_number", "MobileNo": "mobile_no", "FaxNumber": "fax_number",
    "Email": "email", "Website": "website", "StartingFrom": "start_date", "BooksFrom": "books_date",
    "IsSecurityOn": "is_security_on", "OwnerName": "owner_name", "IsTallyAuditOn": "is_tally_audit_on",
    "IsDisAllowInEduMode": "is_disallow_edu", "CurrencyName": "currency_name",
    "FormalName": "currency_formal_name", "IsSuffix": "is_currency_suffix", "InMillions": "in_millions",
    "DecimalPlaces": "decimal_places", "DecimalSymbol": "decimal_symbol",
    "DecimalPlacesForPrinting": "decimal_places_printing", "GUID": "guid",
    "Masterid": "master_id", "Alterid": "alter_id"
}
COMPANY_FIELD_MAP_LOWER = {k.lower(): v for k, v in COMPANY_FIELD_MAP.items()}

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
LICENSE_FIELD_MAP_LOWER = {k.lower(): v for k, v in LICENSE_FIELD_MAP.items()
                           }
# --- Field Mapping (LEDGERS) ---
LEDGER_FIELD_MAP = {
    "GUID": "tally_guid", "Name": "tally_name", "PARENT": "parent_name", "ISBILLWISEON": "is_billwise_on",
    "OPENINGBALANCE": "opening_balance", "CLOSINGBALANCE": "closing_balance", "CURRENCYNAME": "currency_name",
    "AFFECTSSTOCK": "affects_stock", "ISCOSTCENTRESON": "is_cost_centres_on",
    "GSTREGISTRATIONTYPE": "gst_registration_type", "PARTYGSTIN": "party_gstin"
}
LEDGER_FIELD_TYPES = {
    "tally_guid": "TEXT", "tally_name": "TEXT", "parent_name": "TEXT", "is_billwise_on": "BOOLEAN",
    "opening_balance": "REAL", "closing_balance": "REAL", "currency_name": "TEXT",
    "affects_stock": "BOOLEAN", "is_cost_centres_on": "BOOLEAN",
    "gst_registration_type": "TEXT", "party_gstin": "TEXT"
}
LEDGER_FIELD_MAP_LOWER = {k.lower(): v for k, v in LEDGER_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEMS) ---
STOCK_ITEM_FIELD_MAP = {
    "GUID": "tally_guid", "Name": "tally_name", "PARENT": "parent_name", "CATEGORY": "category_name",
    "BASEUNITS": "base_units", "OPENINGBALANCE": "opening_balance", "OPENINGRATE": "opening_rate",
    "OPENINGVALUE": "opening_value", "CLOSINGBALANCE": "closing_balance", "CLOSINGRATE": "closing_rate",
    "CLOSINGVALUE": "closing_value", "GSTAPPLICABLE": "gst_applicable", "GSTTYPEOFSUPPLY": "gst_type_of_supply",
    "HSNCODE": "hsn_code"
}
STOCK_ITEM_FIELD_TYPES = {
    "tally_guid": "TEXT", "tally_name": "TEXT", "parent_name": "TEXT", "category_name": "TEXT",
    "base_units": "TEXT", "opening_balance": "REAL", "opening_rate": "REAL", "opening_value": "REAL",
    "closing_balance": "REAL", "closing_rate": "REAL", "closing_value": "REAL",
    "gst_applicable": "TEXT", "gst_type_of_supply": "TEXT", "hsn_code": "TEXT"
}
STOCK_ITEM_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_FIELD_MAP.items()}

# --- Field Mapping (STOCK GROUPS) ---
STOCK_GROUP_FIELD_MAP = {
    "GUID": "tally_guid", "Name": "tally_name", "Parent": "parent_name",
    "IsAddable": "is_addable", "MasterID": "master_id", "ALTERID": "alter_id"
}
STOCK_GROUP_FIELD_TYPES = {
    "tally_guid": "TEXT", "tally_name": "TEXT", "parent_name": "TEXT",
    "is_addable": "BOOLEAN", "master_id": "INTEGER", "alter_id": "INTEGER"
}
STOCK_GROUP_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_GROUP_FIELD_MAP.items()}

# --- Field Mapping (UNITS) ---
UNIT_FIELD_MAP = {
    "GUID": "tally_guid", "NAME": "tally_name", "ORIGINALNAME": "original_name",
    "BASEUNITS": "base_units", "ADDITIONALUNITS": "additional_units",
    "CONVERSION": "conversion", "DecimalPlaces": "decimal_places",
    "ISSIMPLEUNIT": "is_simple_unit", "MasterID": "master_id", "ALTERID": "alter_id"
}
UNIT_FIELD_TYPES = {
    "tally_guid": "TEXT", "tally_name": "TEXT", "original_name": "TEXT",
    "base_units": "TEXT", "additional_units": "TEXT",
    "conversion": "REAL", "decimal_places": "INTEGER",
    "is_simple_unit": "BOOLEAN", "master_id": "INTEGER", "alter_id": "INTEGER"
}
UNIT_FIELD_MAP_LOWER = {k.lower(): v for k, v in UNIT_FIELD_MAP.items()}

# --- Field Mapping (ACCOUNTING GROUPS) ---
ACCOUNTING_GROUP_FIELD_MAP = {
    "Name": "name", "PARENT": "parent", "ISSUBLEDGER": "is_subledger",
    "ISADDABLE": "is_addable", "BASICGROUPISCALCULABLE": "basic_group_is_calculable",
    "ADDLALLOCTYPE": "addl_alloctype", "MasterID": "master_id", "ALTERID": "alter_id"
}
ACCOUNTING_GROUP_FIELD_TYPES = {
    "name": "TEXT", "parent": "TEXT", "is_subledger": "BOOLEAN",
    "is_addable": "BOOLEAN", "basic_group_is_calculable": "BOOLEAN",
    "addl_alloctype": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER"
}
ACCOUNTING_GROUP_FIELD_MAP_LOWER = {k.lower(): v for k, v in ACCOUNTING_GROUP_FIELD_MAP.items()}

# --- Field Mapping (LEDGER BILLWISE) ---
LEDGER_BILLWISE_FIELD_MAP = {
    "LEDName": "ledger_guid", "NAME": "name", "BILLDATE": "billdate",
    "BILLCREDITPERIOD": "billcreditperiod", "ISADVANCE": "isadvance",
    "OPENINGBALANCE": "openingbalance"
}
LEDGER_BILLWISE_FIELD_TYPES = {
    "ledger_guid": "TEXT", "name": "TEXT", "billdate": "TEXT",
    "billcreditperiod": "TEXT", "isadvance": "BOOLEAN", "openingbalance": "REAL"
}
LEDGER_BILLWISE_FIELD_MAP_LOWER = {k.lower(): v for k, v in LEDGER_BILLWISE_FIELD_MAP.items()}

# --- Field Mapping (COST CATEGORY) ---
COST_CATEGORY_FIELD_MAP = {
    "Name": "name", "AllocateRevenue": "allocate_revenue",
    "AllocateNonRevenue": "allocate_nonrevenue", "MasterID": "master_id", "ALTERID": "alter_id"
}
COST_CATEGORY_FIELD_TYPES = {
    "name": "TEXT", "allocate_revenue": "BOOLEAN",
    "allocate_nonrevenue": "BOOLEAN", "master_id": "INTEGER", "alter_id": "INTEGER"
}
COST_CATEGORY_FIELD_MAP_LOWER = {k.lower(): v for k, v in COST_CATEGORY_FIELD_MAP.items()}

# --- Field Mapping (COST CENTER) ---
COST_CENTER_FIELD_MAP = {
    "Name": "name", "CATEGORY": "category", "Parent": "parent",
    "RevenueLedForOpBal": "revenue_ledger_for_opbal", "EMailID": "email_id",
    "MasterID": "master_id", "ALTERID": "alter_id"
}
COST_CENTER_FIELD_TYPES = {
    "name": "TEXT", "category": "TEXT", "parent": "TEXT",
    "revenue_ledger_for_opbal": "TEXT", "email_id": "TEXT",
    "master_id": "INTEGER", "alter_id": "INTEGER"
}
COST_CENTER_FIELD_MAP_LOWER = {k.lower(): v for k, v in COST_CENTER_FIELD_MAP.items()}

# --- Field Mapping (CURRENCY) ---
CURRENCY_FIELD_MAP = {
    "Name": "name", "MAILINGNAME": "mailing_name", "ISOCurrencyCode": "iso_currency_code",
    "DECIMALPLACES": "decimal_places", "INMILLIONS": "in_millions", "ISSUFFIX": "is_suffix",
    "HASSPACE": "has_space", "DECIMALSYMBOL": "decimal_symbol",
    "DECIMALPLACESFORPRINTING": "decimal_places_printing", "SORTPOSITION": "sort_position",
    "MasterID": "master_id", "ALTERID": "alter_id"
}
CURRENCY_FIELD_TYPES = {
    "name": "TEXT", "mailing_name": "TEXT", "iso_currency_code": "TEXT",
    "decimal_places": "INTEGER", "in_millions": "BOOLEAN", "is_suffix": "BOOLEAN",
    "has_space": "BOOLEAN", "decimal_symbol": "TEXT",
    "decimal_places_printing": "INTEGER", "sort_position": "INTEGER",
    "master_id": "INTEGER", "alter_id": "INTEGER"
}
CURRENCY_FIELD_MAP_LOWER = {k.lower(): v for k, v in CURRENCY_FIELD_MAP.items()}

# --- Field Mapping (VOUCHER TYPE) ---
VOUCHER_TYPE_FIELD_MAP = {
    "Name": "name", "PARENT": "parent", "AdditionalName": "additional_name",
    "ISACTIVE": "is_active", "NUMBERINGMETHOD": "numbering_method",
    "PREVENTDUPLICATES": "prevent_duplicates", "EffectiveDate": "effective_date",
    "USEZEROENTRIES": "use_zero_entries", "PRINTAFTERSAVE": "print_after_save",
    "FORMALRECEIPT": "formal_receipt", "ISOPTIONAL": "is_optional",
    "ASMFGJRNL": "as_mfg_jrnl", "COMMONNARRATION": "common_narration",
    "MULTINARRATION": "multi_narration", "USEFORPOSINVOICE": "use_for_pos_invoice",
    "USEFORJOBWORK": "use_for_jobwork", "ISFORJOBWORKIN": "is_for_jobwork_in",
    "ALLOWCONSUMPTION": "allow_consumption", "ISDEFAULTALLOCENABLED": "is_default_alloc_enabled",
    "MasterID": "master_id", "ALTERID": "alter_id"
}
VOUCHER_TYPE_FIELD_TYPES = {
    "name": "TEXT", "parent": "TEXT", "additional_name": "TEXT",
    "is_active": "BOOLEAN", "numbering_method": "TEXT",
    "prevent_duplicates": "BOOLEAN", "effective_date": "TEXT",
    "use_zero_entries": "BOOLEAN", "print_after_save": "BOOLEAN",
    "formal_receipt": "BOOLEAN", "is_optional": "BOOLEAN",
    "as_mfg_jrnl": "BOOLEAN", "common_narration": "BOOLEAN",
    "multi_narration": "BOOLEAN", "use_for_pos_invoice": "BOOLEAN",
    "use_for_jobwork": "BOOLEAN", "is_for_jobwork_in": "BOOLEAN",
    "allow_consumption": "BOOLEAN", "is_default_alloc_enabled": "BOOLEAN",
    "master_id": "INTEGER", "alter_id": "INTEGER"
}
VOUCHER_TYPE_FIELD_MAP_LOWER = {k.lower(): v for k, v in VOUCHER_TYPE_FIELD_MAP.items()}

# --- Field Mapping (STOCK GROUP WITH GST) ---
STOCK_GROUP_GST_FIELD_MAP = {
    "Name": "name", "Parent": "parent", "IsAddable": "is_addable",
    "MasterID": "master_id", "ALTERID": "alter_id", "GSTRATEDUTYHEAD": "gst_rate_duty_head",
    "GSTRATEVALUATIONTYPE": "gst_rate_valuation_type", "GSTRATE": "gst_rate",
    "APPLICABLEFROM": "applicable_from", "HSNCODE": "hsn_code", "HSN": "hsn",
    "TAXABILITY": "taxability", "ISREVERSECHARGEAPPLICABLE": "is_reverse_charge_applicable",
    "ISNONGSTGOODS": "is_non_gst_goods", "GSTINELIGIBLEITC": "gst_ineligible_itc"
}
STOCK_GROUP_GST_FIELD_TYPES = {
    "name": "TEXT", "parent": "TEXT", "is_addable": "BOOLEAN",
    "master_id": "INTEGER", "alter_id": "INTEGER", "gst_rate_duty_head": "TEXT",
    "gst_rate_valuation_type": "TEXT", "gst_rate": "REAL",
    "applicable_from": "TEXT", "hsn_code": "TEXT", "hsn": "TEXT",
    "taxability": "TEXT", "is_reverse_charge_applicable": "BOOLEAN",
    "is_non_gst_goods": "BOOLEAN", "gst_ineligible_itc": "BOOLEAN"
}
STOCK_GROUP_GST_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_GROUP_GST_FIELD_MAP.items()}

# --- Field Mapping (STOCK CATEGORY) ---
STOCK_CATEGORY_FIELD_MAP = {
    "Name": "name", "Parent": "parent", "MasterID": "master_id", "ALTERID": "alter_id"
}
STOCK_CATEGORY_FIELD_TYPES = {
    "name": "TEXT", "parent": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER"
}
STOCK_CATEGORY_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_CATEGORY_FIELD_MAP.items()}

# --- Field Mapping (GODOWN) ---
GODOWN_FIELD_MAP = {
    "Name": "name", "Parent": "parent", "HasNoSpace": "has_no_space",
    "ISINTERNAL": "is_internal", "ISEXTERNAL": "is_external",
    "GDNaddress": "address", "MasterID": "master_id", "ALTERID": "alter_id"
}
GODOWN_FIELD_TYPES = {
    "name": "TEXT", "parent": "TEXT", "has_no_space": "BOOLEAN",
    "is_internal": "BOOLEAN", "is_external": "BOOLEAN",
    "address": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER"
}
GODOWN_FIELD_MAP_LOWER = {k.lower(): v for k, v in GODOWN_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEM GST) ---
STOCK_ITEM_GST_FIELD_MAP = {
    "Name": "name", "MasterID": "master_id", "ALTERID": "alter_id",
    "GSTRATEDUTYHEAD": "gst_rate_duty_head", "GSTRATEVALUATIONTYPE": "gst_rate_valuation_type",
    "GSTRATE": "gst_rate", "APPLICABLEFROM": "applicable_from",
    "HSNCODE": "hsn_code", "HSN": "hsn", "TAXABILITY": "taxability",
    "ISREVERSECHARGEAPPLICABLE": "is_reverse_charge_applicable",
    "ISNONGSTGOODS": "is_non_gst_goods", "GSTINELIGIBLEITC": "gst_ineligible_itc"
}
STOCK_ITEM_GST_FIELD_TYPES = {
    "name": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "gst_rate_duty_head": "TEXT", "gst_rate_valuation_type": "TEXT",
    "gst_rate": "REAL", "applicable_from": "TEXT",
    "hsn_code": "TEXT", "hsn": "TEXT", "taxability": "TEXT",
    "is_reverse_charge_applicable": "BOOLEAN",
    "is_non_gst_goods": "BOOLEAN", "gst_ineligible_itc": "BOOLEAN"
}
STOCK_ITEM_GST_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_GST_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEM MRP) ---
STOCK_ITEM_MRP_FIELD_MAP = {
    "Name": "name", "MasterID": "master_id", "ALTERID": "alter_id",
    "FROMDATE": "from_date", "STATENAME": "state_name", "MRPRATE": "mrp_rate"
}
STOCK_ITEM_MRP_FIELD_TYPES = {
    "name": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "from_date": "TEXT", "state_name": "TEXT", "mrp_rate": "REAL"
}
STOCK_ITEM_MRP_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_MRP_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEM BOM) ---
STOCK_ITEM_BOM_FIELD_MAP = {
    "Name": "name", "MasterID": "master_id", "ALTERID": "alter_id",
    "NATUREOFITEM": "nature_of_item", "STOCKITEMNAME": "stockitem_name",
    "GODOWNNAME": "godown_name", "ACTUALQTY": "actual_qty",
    "COMPONENTLISTNAME": "component_list_name", "COMPONENTBASICQTY": "component_basic_qty"
}
STOCK_ITEM_BOM_FIELD_TYPES = {
    "name": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "nature_of_item": "TEXT", "stockitem_name": "TEXT",
    "godown_name": "TEXT", "actual_qty": "REAL",
    "component_list_name": "TEXT", "component_basic_qty": "REAL"
}
STOCK_ITEM_BOM_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_BOM_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEM STANDARD COST) ---
STOCK_ITEM_STANDARDCOST_FIELD_MAP = {
    "Name": "name", "MasterID": "master_id", "ALTERID": "alter_id",
    "SDDATE": "date", "SDRATE": "rate"
}
STOCK_ITEM_STANDARDCOST_FIELD_TYPES = {
    "name": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "date": "TEXT", "rate": "REAL"
}
STOCK_ITEM_STANDARDCOST_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_STANDARDCOST_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEM STANDARD PRICE) ---
STOCK_ITEM_STANDARDPRICE_FIELD_MAP = {
    "Name": "name", "MasterID": "master_id", "ALTERID": "alter_id",
    "SPDATE": "date", "SPRATE": "rate"
}
STOCK_ITEM_STANDARDPRICE_FIELD_TYPES = {
    "name": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "date": "TEXT", "rate": "REAL"
}
STOCK_ITEM_STANDARDPRICE_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_STANDARDPRICE_FIELD_MAP.items()}

# --- Field Mapping (STOCK ITEM BATCH DETAILS) ---
STOCK_ITEM_BATCHDETAILS_FIELD_MAP = {
    "Name": "name", "MasterID": "master_id", "ALTERID": "alter_id",
    "MFDON": "mfg_date", "GODOWNNAME": "godown_name", "BATCHNAME": "batch_name",
    "BOPENINGBALANCE": "opening_balance", "BOPENINGVALUE": "opening_value",
    "BOPENINGRATE": "opening_rate", "EXPIRYPERIOD": "expiry_period"
}
STOCK_ITEM_BATCHDETAILS_FIELD_TYPES = {
    "name": "TEXT", "master_id": "INTEGER", "alter_id": "INTEGER",
    "mfg_date": "TEXT", "godown_name": "TEXT", "batch_name": "TEXT",
    "opening_balance": "REAL", "opening_value": "REAL",
    "opening_rate": "REAL", "expiry_period": "TEXT"
}
STOCK_ITEM_BATCHDETAILS_FIELD_MAP_LOWER = {k.lower(): v for k, v in STOCK_ITEM_BATCHDETAILS_FIELD_MAP.items()}

# --- Conversion Helper ---
# --- Conversion Helper ---
def _convert_odbc_value(value, target_type: str):
    """Helper to convert pyodbc values to Python/SQLite types."""
    if value is None:
        return None
    try:
        if target_type == "BOOLEAN":
            return str(value).strip().lower() in ['yes', 'true', '1']
        elif target_type == "INTEGER":
            return int(value)
        elif target_type == "REAL":
            return float(value)
        elif target_type == "DATE":
            if isinstance(value, datetime.date):
                return value.isoformat()
            return datetime.datetime.strptime(str(value).strip(), '%Y%m%d').date().isoformat()
        else:  # Default to TEXT
            return str(value).strip()
    except (ValueError, TypeError) as e:
        logger.warning(f"Conversion error: '{value}' to {target_type}: {e}")
        return None

# --- Base Fetch Function ---
def _fetch_odbc_data(query: str, params: tuple, field_map: dict, type_map: dict, description: str) -> list[dict] | None:
    """Generic helper to fetch data via ODBC, map fields, and convert types."""
    conn = None
    results = []
    logger.info(f"ODBC Connect {description} (DSN: {TALLY_ODBC_DSN})...")
    try:
        conn = pyodbc.connect(f'DSN={TALLY_ODBC_DSN}', autocommit=True, timeout=ODBC_CONNECT_TIMEOUT)
        cursor = conn.cursor()
        try:
            cursor.settimeout(ODBC_QUERY_TIMEOUT)
        except AttributeError:
            logger.warning("ODBC driver does not support settimeout().")
        logger.info(f"Executing ODBC query for {description}...")
        cursor.execute(query, params)
        rows = cursor.fetchall()
        logger.info(f"Fetched {len(rows)} rows for {description}.")
        if rows:
            colnames = [col[0] for col in cursor.description]
            map_lower = {k.lower(): v for k, v in field_map.items()}
            for row in rows:
                item = {}
                for i, col_name in enumerate(colnames):
                    field_key = map_lower.get(col_name.strip('$').lower())
                    if field_key:
                        target_type = type_map.get(field_key, "TEXT")
                        item[field_key] = _convert_odbc_value(row[i], target_type)
                if item:
                    results.append(item)
    except pyodbc.Error as e:
        logger.error(f"ODBC Error {description}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during ODBC fetch {description}: {e}")
        return None
    finally:
        if conn:
            try:
                conn.close()
                logger.debug(f"ODBC connection closed ({description}).")
            except pyodbc.Error as e:
                logger.error(f"Error closing ODBC connection: {e}")
    return results
def fetch_ledgers_odbc() -> list[dict] | None:
    """Fetches Ledger master data via Tally ODBC."""
    logger.info("Fetching Ledgers via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $Parent, $IsBillwiseOn, $OpeningBalance, $ClosingBalance, "
        "$CurrencyName, $AffectsStock, $IsCostCentresOn, $GSTRegistrationType, "
        "$PartyGSTIN, $GUID FROM Ledger",
        (), LEDGER_FIELD_MAP, LEDGER_FIELD_TYPES, "Ledgers"
    )


def fetch_stock_items_odbc() -> list[dict] | None:
    """Fetches Stock Items master data via Tally ODBC."""
    logger.info("Fetching Stock Items via ODBC...")
    return _fetch_odbc_data(
        "SELECT $GUID, $Name, $Parent, $Category, $BaseUnits, $OpeningBalance, "
        "$OpeningRate, $OpeningValue, $ClosingBalance, $ClosingRate, "
        "$ClosingValue, $GSTApplicable, $GSTTypeOfSupply, $HSNCode FROM StockItem",
        (), STOCK_ITEM_FIELD_MAP, STOCK_ITEM_FIELD_TYPES, "Stock Items"
    )

def fetch_stock_groups_odbc() -> list[dict] | None:
    """Fetches Stock Groups master data via Tally ODBC."""
    logger.info("Fetching Stock Groups via ODBC...")
    return _fetch_odbc_data(
        "SELECT $GUID, $Name, $Parent, $IsAddable, $MasterID, $ALTERID FROM StockGroup",
        (), STOCK_GROUP_FIELD_MAP, STOCK_GROUP_FIELD_TYPES, "Stock Groups"
    )

def fetch_units_odbc() -> list[dict] | None:
    """Fetches Units master data via Tally ODBC."""
    logger.info("Fetching Units via ODBC...")
    return _fetch_odbc_data(
        "SELECT $GUID, $NAME, $ORIGINALNAME, $BASEUNITS, $ADDITIONALUNITS, "
        "$CONVERSION, $DecimalPlaces, $ISSIMPLEUNIT, $MasterID, $ALTERID FROM Unit",
        (), UNIT_FIELD_MAP, UNIT_FIELD_TYPES, "Units"
    )

def fetch_accounting_groups_odbc() -> list[dict] | None:
    """Fetches Accounting Groups master data via Tally ODBC."""
    logger.info("Fetching Accounting Groups via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $PARENT, $ISSUBLEDGER, $ISADDABLE, $BASICGROUPISCALCULABLE, "
        "$ADDLALLOCTYPE, $MasterID, $ALTERID FROM Group",
        (), ACCOUNTING_GROUP_FIELD_MAP, ACCOUNTING_GROUP_FIELD_TYPES, "Accounting Groups"
    )

def fetch_ledgerbillwise_odbc() -> list[dict] | None:
    """Fetches Ledger Billwise details via Tally ODBC."""
    logger.info("Fetching Ledger Billwise details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $LEDName, $NAME, $BILLDATE, $BILLCREDITPERIOD, $ISADVANCE, "
        "$OPENINGBALANCE FROM LedgerBillwise",
        (), LEDGER_BILLWISE_FIELD_MAP, LEDGER_BILLWISE_FIELD_TYPES, "Ledger Billwise"
    )

def fetch_costcategory_odbc() -> list[dict] | None:
    """Fetches Cost Category master data via Tally ODBC."""
    logger.info("Fetching Cost Categories via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $AllocateRevenue, $AllocateNonRevenue, $MasterID, $ALTERID FROM CostCategory",
        (), COST_CATEGORY_FIELD_MAP, COST_CATEGORY_FIELD_TYPES, "Cost Categories"
    )

def fetch_costcenter_odbc() -> list[dict] | None:
    """Fetches Cost Center master data via Tally ODBC."""
    logger.info("Fetching Cost Centers via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $CATEGORY, $Parent, $RevenueLedForOpBal, $EMailID, "
        "$MasterID, $ALTERID FROM CostCenter",
        (), COST_CENTER_FIELD_MAP, COST_CENTER_FIELD_TYPES, "Cost Centers"
    )

def fetch_currency_odbc() -> list[dict] | None:
    """Fetches Currency master data via Tally ODBC."""
    logger.info("Fetching Currencies via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MAILINGNAME, $ISOCurrencyCode, $DECIMALPLACES, $INMILLIONS, "
        "$ISSUFFIX, $HASSPACE, $DECIMALSYMBOL, $DECIMALPLACESFORPRINTING, "
        "$SORTPOSITION, $MasterID, $ALTERID FROM Currency",
        (), CURRENCY_FIELD_MAP, CURRENCY_FIELD_TYPES, "Currencies"
    )

def fetch_vouchertype_odbc() -> list[dict] | None:
    """Fetches Voucher Type master data via Tally ODBC."""
    logger.info("Fetching Voucher Types via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $PARENT, $AdditionalName, $ISACTIVE, $NUMBERINGMETHOD, "
        "$PREVENTDUPLICATES, $EffectiveDate, $USEZEROENTRIES, $PRINTAFTERSAVE, "
        "$FORMALRECEIPT, $ISOPTIONAL, $ASMFGJRNL, $COMMONNARRATION, $MULTINARRATION, "
        "$USEFORPOSINVOICE, $USEFORJOBWORK, $ISFORJOBWORKIN, $ALLOWCONSUMPTION, "
        "$ISDEFAULTALLOCENABLED, $MasterID, $ALTERID FROM VoucherType",
        (), VOUCHER_TYPE_FIELD_MAP, VOUCHER_TYPE_FIELD_TYPES, "Voucher Types"
    )

def fetch_stockgroupwithgst_odbc() -> list[dict] | None:
    """Fetches Stock Group with GST details via Tally ODBC."""
    logger.info("Fetching Stock Groups with GST via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $Parent, $IsAddable, $MasterID, $ALTERID, $GSTRATEDUTYHEAD, "
        "$GSTRATEVALUATIONTYPE, $GSTRATE, $APPLICABLEFROM, $HSNCODE, $HSN, "
        "$TAXABILITY, $ISREVERSECHARGEAPPLICABLE, $ISNONGSTGOODS, "
        "$GSTINELIGIBLEITC FROM StockGroupGST",
        (), STOCK_GROUP_GST_FIELD_MAP, STOCK_GROUP_GST_FIELD_TYPES, "Stock Groups GST"
    )

def fetch_stockcategory_odbc() -> list[dict] | None:
    """Fetches Stock Category master data via Tally ODBC."""
    logger.info("Fetching Stock Categories via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $Parent, $MasterID, $ALTERID FROM StockCategory",
        (), STOCK_CATEGORY_FIELD_MAP, STOCK_CATEGORY_FIELD_TYPES, "Stock Categories"
    )

def fetch_godown_odbc() -> list[dict] | None:
    """Fetches Godown master data via Tally ODBC."""
    logger.info("Fetching Godowns via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $Parent, $HasNoSpace, $ISINTERNAL, $ISEXTERNAL, "
        "$GDNaddress, $MasterID, $ALTERID FROM Godown",
        (), GODOWN_FIELD_MAP, GODOWN_FIELD_TYPES, "Godowns"
    )

def fetch_stockitem_gst_odbc() -> list[dict] | None:
    """Fetches Stock Item GST details via Tally ODBC."""
    logger.info("Fetching Stock Item GST details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MasterID, $ALTERID, $GSTRATEDUTYHEAD, $GSTRATEVALUATIONTYPE, "
        "$GSTRATE, $APPLICABLEFROM, $HSNCODE, $HSN, $TAXABILITY, "
        "$ISREVERSECHARGEAPPLICABLE, $ISNONGSTGOODS, $GSTINELIGIBLEITC FROM StockItemGST",
        (), STOCK_ITEM_GST_FIELD_MAP, STOCK_ITEM_GST_FIELD_TYPES, "Stock Item GST"
    )

def fetch_stockitem_mrp_odbc() -> list[dict] | None:
    """Fetches Stock Item MRP details via Tally ODBC."""
    logger.info("Fetching Stock Item MRP details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MasterID, $ALTERID, $FROMDATE, $STATENAME, $MRPRATE FROM StockItemMRP",
        (), STOCK_ITEM_MRP_FIELD_MAP, STOCK_ITEM_MRP_FIELD_TYPES, "Stock Item MRP"
    )

def fetch_stockitem_bom_odbc() -> list[dict] | None:
    """Fetches Stock Item BOM details via Tally ODBC."""
    logger.info("Fetching Stock Item BOM details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MasterID, $ALTERID, $NATUREOFITEM, $STOCKITEMNAME, "
        "$GODOWNNAME, $ACTUALQTY, $COMPONENTLISTNAME, $COMPONENTBASICQTY FROM StockItemBOM",
        (), STOCK_ITEM_BOM_FIELD_MAP, STOCK_ITEM_BOM_FIELD_TYPES, "Stock Item BOM"
    )

def fetch_stockitem_standardcost_odbc() -> list[dict] | None:
    """Fetches Stock Item Standard Cost details via Tally ODBC."""
    logger.info("Fetching Stock Item Standard Cost details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MasterID, $ALTERID, $SDDATE, $SDRATE FROM StockItemStandardCost",
        (), STOCK_ITEM_STANDARDCOST_FIELD_MAP, STOCK_ITEM_STANDARDCOST_FIELD_TYPES, "Stock Item Standard Cost"
    )

def fetch_stockitem_standardprice_odbc() -> list[dict] | None:
    """Fetches Stock Item Standard Price details via Tally ODBC."""
    logger.info("Fetching Stock Item Standard Price details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MasterID, $ALTERID, $SPDATE, $SPRATE FROM StockItemStandardPrice",
        (), STOCK_ITEM_STANDARDPRICE_FIELD_MAP, STOCK_ITEM_STANDARDPRICE_FIELD_TYPES, "Stock Item Standard Price"
    )

def fetch_stockitem_batchdetails_odbc() -> list[dict] | None:
    """Fetches Stock Item Batch details via Tally ODBC."""
    logger.info("Fetching Stock Item Batch details via ODBC...")
    return _fetch_odbc_data(
        "SELECT $Name, $MasterID, $ALTERID, $MFDON, $GODOWNNAME, $BATCHNAME, "
        "$BOPENINGBALANCE, $BOPENINGVALUE, $BOPENINGRATE, $EXPIRYPERIOD FROM StockItemBatchDetails",
        (), STOCK_ITEM_BATCHDETAILS_FIELD_MAP, STOCK_ITEM_BATCHDETAILS_FIELD_TYPES, "Stock Item Batch Details"
    )


# --- Fetch Company Details ---
def fetch_company_details_odbc(company_number_context: str) -> dict | None:
    """Fetches detailed metadata via Tally ODBC for the *currently loaded* company."""
    select_fields = ", ".join([f"${key}" for key in COMPANY_FIELD_MAP.keys()])
    query = f"SELECT {select_fields} FROM HSp_CMPScreennColl"
    logger.info(f"ODBC Connect DSN: {TALLY_ODBC_DSN} (Context: {company_number_context})")
    try:
        results = _fetch_odbc_data(
            query,
            (),
            COMPANY_FIELD_MAP,
            DB_COMPANY_COLUMNS,
            f"Company Details ({company_number_context})"
        )
        if results:
            logger.info(f"Fetched company details for {company_number_context}.")
            return results[0]  # Return the first result
        else:
            logger.warning(f"No data found for company {company_number_context}.")
            return None
    except Exception as e:
        logger.exception(f"Error fetching company details for {company_number_context}: {e}")
        return None

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