"""
Company management functions for TallyPrimeConnect.
Handles company CRUD operations and sync status management.
"""

import logging
import datetime
from .core import execute_query

logger = logging.getLogger(__name__)

def add_company_to_db(name, number, description=""):
    """Adds a company or reactivates it if soft-deleted. Returns True if added/reactivated."""
    if not name or not number:
        logger.error("Add company failed: Name or number is empty.")
        return False
    
    number_str = str(number)
    check_sql = "SELECT id, is_active, is_deleted FROM companies WHERE tally_company_number = ?"
    existing = execute_query(check_sql, (number_str,), fetch_one=True)
    
    if existing:
        if existing['is_deleted'] == 1 or existing['is_active'] == 0:
            # Company exists but is inactive or deleted
            logger.info(f"Reactivating company {number_str} ('{name}').")
            
            # Reset sync status on reactivation
            update_sql = """
            UPDATE companies 
            SET tally_company_name = ?, description = ?, is_active = 1, is_deleted = 0, 
                sync_status = 'Not Synced', updated_timestamp = CURRENT_TIMESTAMP 
            WHERE tally_company_number = ?
            """
            rowcount = execute_query(update_sql, (name, description, number_str), commit=True)
            
            if rowcount:
                log_change(number_str, "REACTIVATE", f"Name: '{name}'")
                return True
            else:
                logger.error(f"Failed to reactivate company {number_str}")
                return False
        else:
            # Company exists and is already active
            logger.info(f"Company {number_str} ('{name}') already active in database.")
            return False  # Not newly added or reactivated
    else:
        # Company does not exist at all
        logger.info(f"Adding new company {number_str} ('{name}').")
        
        insert_sql = """
        INSERT INTO companies (
            tally_company_number, tally_company_name, description, 
            is_active, is_deleted, sync_status
        ) VALUES (?, ?, ?, 1, 0, 'Not Synced')
        """
        rowcount = execute_query(insert_sql, (number_str, name, description), commit=True)
        
        if rowcount:
            log_change(number_str, "ADD", f"Name: '{name}'")
            return True
        else:
            logger.error(f"Failed to insert new company {number_str}")
            return False

def get_added_companies():
    """Retrieves all active companies with basic details."""
    sql = """
    SELECT id, tally_company_name, tally_company_number, description, sync_status, 
           last_sync_timestamp, is_active, is_deleted
    FROM companies
    WHERE is_active = 1 AND is_deleted = 0
    ORDER BY tally_company_name
    """
    
    rows = execute_query(sql, fetch_all=True)
    return [dict(row) for row in rows] if rows else []

def get_company_details(company_id):
    """Retrieve details for a specific company by ID or number."""
    if isinstance(company_id, int) or (isinstance(company_id, str) and company_id.isdigit()):
        # Search by ID
        sql = """
        SELECT * FROM companies 
        WHERE id = ? AND is_active = 1 AND is_deleted = 0
        """
        params = (int(company_id),)
    else:
        # Search by company number
        sql = """
        SELECT * FROM companies 
        WHERE tally_company_number = ? AND is_active = 1 AND is_deleted = 0
        """
        params = (str(company_id),)
    
    row = execute_query(sql, params, fetch_one=True)
    return dict(row) if row else None

def edit_company_in_db(company_id, new_name, new_description=None):
    """Update company name and description."""
    # Get company details first
    company = get_company_details(company_id)
    if not company:
        logger.error(f"Edit failed: Company {company_id} not found or inactive.")
        return False
    
    if isinstance(company_id, int) or (isinstance(company_id, str) and company_id.isdigit()):
        # Using ID
        id_field = "id"
        id_value = int(company_id)
    else:
        # Using company number
        id_field = "tally_company_number"
        id_value = str(company_id)
    
    # Check if another company already has this name
    check_sql = f"""
    SELECT 1 FROM companies 
    WHERE tally_company_name = ? AND {id_field} != ? 
    AND is_active = 1 AND is_deleted = 0 
    LIMIT 1
    """
    
    if execute_query(check_sql, (new_name, id_value), fetch_one=True):
        logger.warning(f"Edit failed: Name '{new_name}' already exists.")
        return False
    
    # Get current values for comparison
    current_name = company['tally_company_name']
    current_desc = company.get('description', '') or ""
    desc = new_description if new_description is not None else current_desc
    
    # Check if there are actual changes
    if current_name == new_name and current_desc == desc:
        logger.info(f"No changes for company {company_id}.")
        return False
    
    # Update the company
    update_sql = f"""
    UPDATE companies 
    SET tally_company_name = ?, description = ?, updated_timestamp = CURRENT_TIMESTAMP 
    WHERE {id_field} = ? AND is_active = 1 AND is_deleted = 0
    """
    
    rowcount = execute_query(update_sql, (new_name, desc, id_value), commit=True)
    
    if rowcount:
        log_items = []
        if current_name != new_name:
            log_items.append(f"Name: '{current_name}' -> '{new_name}'")
        if current_desc != desc:
            log_items.append("Description updated")
        
        if log_items:
            company_number = company['tally_company_number']
            log_change(company_number, "EDIT", "; ".join(log_items))
        
        logger.info(f"Company {company_id} updated successfully.")
        return True
    else:
        logger.error(f"Edit failed unexpectedly for company {company_id}.")
        return False

def soft_delete_company(company_id):
    """Mark a company as deleted (soft delete)."""
    # Get company details first
    company = get_company_details(company_id)
    if not company:
        logger.warning(f"Soft delete failed: Company {company_id} not found or already inactive.")
        return False
    
    if isinstance(company_id, int) or (isinstance(company_id, str) and company_id.isdigit()):
        # Using ID
        id_field = "id"
        id_value = int(company_id)
    else:
        # Using company number
        id_field = "tally_company_number"
        id_value = str(company_id)
    
    # Soft delete the company
    sql = f"""
    UPDATE companies 
    SET is_active = 0, is_deleted = 1, updated_timestamp = CURRENT_TIMESTAMP 
    WHERE {id_field} = ? AND is_active = 1 AND is_deleted = 0
    """
    
    rowcount = execute_query(sql, (id_value,), commit=True)
    
    if rowcount:
        company_number = company['tally_company_number']
        log_change(company_number, "SOFT_DELETE", "Marked as deleted")
        logger.info(f"Company {company_id} marked as deleted.")
        return True
    else:
        logger.error(f"Soft delete failed for company {company_id}.")
        return False

def update_company_details(company_id, details):
    """Update company details from fetched data. Creates company if it doesn't exist."""
    if not company_id or not details:
        logger.error("Update company details failed: Missing data.")
        return False
    
    # Get company name from details
    company_name = details.get('tally_company_name')
    if not company_name:
        logger.error(f"Update details failed: Missing company name in details for {company_id}.")
        return False
    
    # Check if company exists
    company = get_company_details(company_id)
    
    # If company doesn't exist, add it first
    if not company:
        logger.info(f"Company {company_id} not found. Adding it to database first.")
        success = add_company_to_db(company_name, str(company_id), details.get('description', ''))
        if not success:
            logger.error(f"Failed to add company {company_id} during sync.")
            return False
        # Get the newly added company
        company = get_company_details(company_id)
        if not company:
            logger.error(f"Failed to retrieve newly added company {company_id}.")
            return False
    
    # Determine if we're using ID or company number
    if isinstance(company_id, int) or (isinstance(company_id, str) and company_id.isdigit()):
        # Using ID
        id_field = "id"
        id_value = int(company_id)
    else:
        # Using company number
        id_field = "tally_company_number"
        id_value = str(company_id)
    
    # Check if updated_timestamp column exists
    from .core import get_db_connection
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(companies)")
            columns = [info[1].lower() for info in cursor.fetchall()]
            has_updated_timestamp = 'updated_timestamp' in columns
        except Exception as e:
            logger.error(f"Error checking columns: {e}")
            has_updated_timestamp = False
        finally:
            conn.close()
    else:
        has_updated_timestamp = False
    
    # Extract fields to update
    update_fields = []
    update_values = []
    
    # Map of database fields to details keys
    field_mappings = {
        "tally_company_name": "tally_company_name",
        "formal_name": "formal_name",
        "address": "address",
        "state_name": "state_name",
        "country_name": "country_name",
        "pincode": "pincode",
        "phone_number": "phone_number",
        "mobile_no": "mobile_no",
        "fax_number": "fax_number",
        "email": "email",
        "website": "website",
        "start_date": "start_date",
        "books_date": "books_date",
        "is_security_on": "is_security_on",
        "owner_name": "owner_name",
        "is_tally_audit_on": "is_tally_audit_on",
        "is_disallow_edu": "is_disallow_edu",
        "currency_name": "currency_name",
        "currency_formal_name": "currency_formal_name",
        "is_currency_suffix": "is_currency_suffix",
        "in_millions": "in_millions",
        "decimal_places": "decimal_places",
        "decimal_symbol": "decimal_symbol",
        "decimal_places_printing": "decimal_places_printing",
        "guid": "guid",
        "master_id": "master_id",
        "alter_id": "alter_id",
        "serial_number": "serial_number",
        "account_id": "account_id",
        "site_id": "site_id",
        "admin_email": "admin_email",
        "is_indian": "is_indian",
        "is_silver": "is_silver",
        "is_gold": "is_gold",
        "is_licensed": "is_licensed",
        "version": "version",
        "gateway_server": "gateway_server",
        "acting_as": "acting_as",
        "odbc_enabled": "odbc_enabled",
        "odbc_port": "odbc_port"
    }
    
    # Build update fields and values
    for db_field, details_key in field_mappings.items():
        if details_key in details and details[details_key] is not None:
            update_fields.append(f"`{db_field}` = ?")
            update_values.append(details[details_key])
    
    # Add timestamp fields
    if has_updated_timestamp:
        update_fields.append("updated_timestamp = CURRENT_TIMESTAMP")
    update_fields.append("sync_status = 'Synced'")
    update_fields.append("last_sync_timestamp = CURRENT_TIMESTAMP")
    
    # If no fields to update, return early
    if not update_fields:
        logger.warning(f"No fields to update for company {company_id}.")
        return True
    
    # Build and execute update query
    update_sql = f"""
    UPDATE companies 
    SET {', '.join(update_fields)}
    WHERE {id_field} = ? AND is_active = 1 AND is_deleted = 0
    """
    
    # Add the company ID as the last parameter
    update_values.append(id_value)
    
    rowcount = execute_query(update_sql, tuple(update_values), commit=True)
    
    if rowcount:
        logger.info(f"Updated details for company {company_id}.")
        log_change(str(company_id) if isinstance(company_id, int) else company_id, 
                  "UPDATE_DETAILS", f"Updated {len(update_fields) - (3 if has_updated_timestamp else 2)} fields")
        return True
    else:
        logger.error(f"Failed to update details for company {company_id}.")
        return False

def update_company_sync_status(company_id, status):
    """Update the sync status of a company."""
    if not status:
        logger.error("Update sync status failed: Status is empty.")
        return False
    
    # Determine if we're using ID or company number
    if isinstance(company_id, int) or (isinstance(company_id, str) and company_id.isdigit()):
        # Using ID
        id_field = "id"
        id_value = int(company_id)
    else:
        # Using company number
        id_field = "tally_company_number"
        id_value = str(company_id)
    
    # Update the sync status
    sql = f"""
    UPDATE companies 
    SET sync_status = ?, last_sync_timestamp = CURRENT_TIMESTAMP, updated_timestamp = CURRENT_TIMESTAMP 
    WHERE {id_field} = ? AND is_active = 1 AND is_deleted = 0
    """
    
    rowcount = execute_query(sql, (status, id_value), commit=True)
    
    if rowcount:
        logger.info(f"Company {company_id} sync status updated to '{status}'.")
        return True
    else:
        logger.error(f"Failed to update sync status for company {company_id}.")
        return False

def log_change(tally_company_number, action, details=""):
    """Log a company change to the company_log table."""
    details_str = (details[:1000] + '...') if len(details) > 1003 else details
    sql = "INSERT INTO company_log (tally_company_number, action, details) VALUES (?, ?, ?)"
    rowcount = execute_query(sql, (str(tally_company_number), action.upper(), details_str), commit=True)
    
    if rowcount:
        logger.debug(f"Logged action '{action}' for company {tally_company_number}")
        return True
    else:
        logger.error(f"Failed to log action '{action}' for company {tally_company_number}")
        return False
