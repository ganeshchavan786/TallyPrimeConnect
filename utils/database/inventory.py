"""
Inventory data functions for TallyPrimeConnect.
Handles stock items, stock groups, and other inventory master data.
"""

import logging
from .core import save_masters_bulk

logger = logging.getLogger(__name__)

def save_stock_groups(groups_data):
    """Saves a list of stock group data to the tally_stock_groups table."""
    column_order = [
        "tally_guid", "tally_name", "parent_name", "is_addable", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_stock_groups", "tally_guid", groups_data, column_order)

def save_stock_items(items_data):
    """Saves a list of stock item data to the tally_stock_items table."""
    column_order = [
        "tally_guid", "tally_name", "parent_name", "category_name", "base_units", 
        "gst_applicable", "gst_type_of_supply", "hsn_code",
        "opening_balance", "opening_rate", "opening_value",
        "closing_balance", "closing_rate", "closing_value"
    ]
    return save_masters_bulk("tally_stock_items", "tally_guid", items_data, column_order)

def save_units(units_data):
    """Saves a list of unit data to the tally_units table."""
    column_order = [
        "tally_guid", "tally_name", "original_name", "base_units", "additional_units", 
        "conversion", "decimal_places", "is_simple_unit", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_units", "tally_guid", units_data, column_order)

def save_stockgroupwithgst(groups_data):
    """Saves a list of stock group GST data to the tally_stockgroupwithgst table."""
    column_order = [
        "name", "parent", "is_addable", "master_id", "alter_id",
        "gst_rate_duty_head", "gst_rate_valuation_type", "gst_rate",
        "applicable_from", "hsn_code", "hsn", "taxability",
        "is_reverse_charge_applicable", "is_non_gst_goods", "gst_ineligible_itc"
    ]
    return save_masters_bulk("tally_stockgroupwithgst", "name", groups_data, column_order)

def save_stockcategory(category_data):
    """Saves a list of stock category data to the tally_stockcategory table."""
    column_order = ["name", "parent", "master_id", "alter_id"]
    return save_masters_bulk("tally_stockcategory", "name", category_data, column_order)

def save_godown(godown_data):
    """Saves a list of godown data to the tally_godown table."""
    column_order = [
        "name", "parent", "has_no_space", "is_internal", 
        "is_external", "address", "master_id", "alter_id"
    ]
    return save_masters_bulk("tally_godown", "name", godown_data, column_order)

def save_stockitem_gst(gst_data):
    """Saves a list of stock item GST data to the tally_stockitem_gst table."""
    column_order = [
        "name", "master_id", "alter_id", "gst_rate_duty_head",
        "gst_rate_valuation_type", "gst_rate", "applicable_from",
        "hsn_code", "hsn", "taxability", "is_reverse_charge_applicable",
        "is_non_gst_goods", "gst_ineligible_itc"
    ]
    return save_masters_bulk("tally_stockitem_gst", "name", gst_data, column_order)

def save_stockitem_mrp(mrp_data):
    """Saves a list of stock item MRP data to the tally_stockitem_mrp table."""
    column_order = [
        "name", "master_id", "alter_id", "from_date",
        "state_name", "mrp_rate"
    ]
    return save_masters_bulk("tally_stockitem_mrp", "name", mrp_data, column_order)

def save_stockitem_bom(bom_data):
    """Saves a list of stock item BOM data to the tally_stockitem_bom table."""
    column_order = [
        "name", "master_id", "alter_id", "nature_of_item",
        "stockitem_name", "godown_name", "actual_qty",
        "component_list_name", "component_basic_qty"
    ]
    return save_masters_bulk("tally_stockitem_bom", "name", bom_data, column_order)

def save_stockitem_standardcost(cost_data):
    """Saves a list of stock item standard cost data to the tally_stockitem_standardcost table."""
    column_order = ["name", "master_id", "alter_id", "date", "rate"]
    return save_masters_bulk("tally_stockitem_standardcost", "name", cost_data, column_order)

def save_stockitem_standardprice(price_data):
    """Saves a list of stock item standard price data to the tally_stockitem_standardprice table."""
    column_order = ["name", "master_id", "alter_id", "date", "rate"]
    return save_masters_bulk("tally_stockitem_standardprice", "name", price_data, column_order)

def save_stockitem_batchdetails(batch_data):
    """Saves a list of stock item batch details to the tally_stockitem_batchdetails table."""
    column_order = [
        "name", "master_id", "alter_id", "mfg_date", "godown_name",
        "batch_name", "opening_balance", "opening_value", "opening_rate",
        "expiry_period"
    ]
    return save_masters_bulk("tally_stockitem_batchdetails", "name", batch_data, column_order)
