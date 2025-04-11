"""
Accounting data functions for TallyPrimeConnect.
Handles ledgers, accounting groups, and other accounting master data.
"""

import logging
from .core import save_masters_bulk

logger = logging.getLogger(__name__)

def save_ledgers(ledgers_data):
    """Saves a list of ledger data to the tally_ledgers table."""
    column_order = [
        "tally_guid", "tally_name", "parent_name", "currency_name", 
        "opening_balance", "closing_balance", "is_billwise_on", 
        "affects_stock", "is_cost_centres_on", "gst_registration_type", "party_gstin"
    ]
    return save_masters_bulk("tally_ledgers", "tally_guid", ledgers_data, column_order)

def save_accounting_groups(groups_data):
    """Saves a list of accounting group data to the tally_accounting_groups table."""
    column_order = [
        "name", "parent", "is_subledger", "is_addable", 
        "basic_group_is_calculable", "addl_alloctype", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_accounting_groups", "name", groups_data, column_order)

def save_ledgerbillwise(ledgerbillwise_data):
    """Saves a list of ledger billwise data to the tally_ledgerbillwise table."""
    column_order = [
        "ledger_guid", "name", "billdate", "billcreditperiod", "isadvance", "openingbalance"
    ]
    return save_masters_bulk("tally_ledgerbillwise", "name", ledgerbillwise_data, column_order)

def save_costcategory(costcategory_data):
    """Saves a list of cost category data to the tally_costcategory table."""
    column_order = [
        "name", "allocate_revenue", "allocate_nonrevenue", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_costcategory", "name", costcategory_data, column_order)

def save_costcenter(costcenter_data):
    """Saves a list of cost center data to the tally_costcenter table."""
    column_order = [
        "name", "category", "parent", "revenue_ledger_for_opbal", 
        "email_id", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_costcenter", "name", costcenter_data, column_order)

def save_currency(currency_data):
    """Saves a list of currency data to the tally_currency table."""
    column_order = [
        "name", "mailing_name", "iso_currency_code", "decimal_places", 
        "in_millions", "is_suffix", "has_space", "decimal_symbol", 
        "decimal_places_printing", "sort_position", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_currency", "name", currency_data, column_order)

def save_vouchertype(vouchertype_data):
    """Saves a list of voucher type data to the tally_vouchertype table."""
    column_order = [
        "name", "parent", "additional_name", "is_active", "numbering_method", 
        "prevent_duplicates", "effective_date", "use_zero_entries", "print_after_save",
        "formal_receipt", "is_optional", "as_mfg_jrnl", "common_narration", 
        "multi_narration", "use_for_pos_invoice", "use_for_jobwork", 
        "is_for_jobwork_in", "allow_consumption", "is_default_alloc_enabled",
        "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_vouchertype", "name", vouchertype_data, column_order)
