# TallyPrimeConnect/utils/helpers.py
import json
import os
import requests
import xml.etree.ElementTree as ET
import logging
import datetime # Keep if used by _convert_tally_value (though it's removed now)

logger = logging.getLogger(__name__)

# --- Constants & Config ---
try: BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError: BASE_DIR = os.path.dirname(os.getcwd())
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, 'settings.json')

DEFAULT_SETTINGS = { "tally_host": "localhost", "tally_port": "9000" }
TALLY_TIMEOUT_STANDARD = 15.0

# --- Settings Management ---
def load_settings() -> dict:
    """Loads Tally connection settings from the JSON file."""
    logger.debug(f"Loading settings from: {SETTINGS_FILE_PATH}")
    defaults = DEFAULT_SETTINGS.copy()
    if not os.path.exists(SETTINGS_FILE_PATH):
        logger.warning("Settings file not found. Creating defaults."); save_settings(defaults); return defaults
    try:
        with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f: settings = json.load(f)
        for key, value in defaults.items(): settings.setdefault(key, value)
        logger.info("Settings loaded."); return settings
    except (json.JSONDecodeError, IOError) as e:
        logger.exception(f"Error loading settings: {e}. Using defaults."); return defaults

def save_settings(settings: dict):
    """Saves settings to the JSON file."""
    logger.debug(f"Saving settings to: {SETTINGS_FILE_PATH}")
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(settings, f, indent=4)
        logger.info("Settings saved.")
    except IOError as e: logger.exception(f"Error saving settings: {e}")

# --- Tally Interaction (HTTP) ---
def check_tally_connection(host: str = 'localhost', port: str = '9000') -> bool:
    """Checks Tally connection using a simple HTTP GET request."""
    url = f'http://{host}:{port}'; logger.info(f"Checking Tally connection GET at {url}...")
    try:
        response = requests.get(url, timeout=TALLY_TIMEOUT_STANDARD / 2)
        logger.debug(f"Tally GET response status: {response.status_code}"); return response.status_code == 200
    except requests.exceptions.RequestException as e: logger.warning(f"Tally connection check failed: {e}"); return False

def _parse_tally_company_xml(xml_content: bytes) -> list[dict] | None:
    """Helper to parse XML response for ListOfCompanies collection."""
    try:
        root = ET.fromstring(xml_content)
        status = root.find('.//RESPONSE/STATUS');
        if status is not None and status.text != '1': logger.error(f"Tally internal error (ListOfCompanies): {root.find('.//RESPONSE/DESC').text if root.find('.//RESPONSE/DESC') is not None else 'Unknown'}"); return None
        companies = []
        for company_element in root.findall('.//COMPANY'):
            name = company_element.findtext('.//NAME', default='').strip() # Use findtext for simplicity
            number = company_element.findtext('.//COMPANYNUMBER', default='').strip()
            if name and number: companies.append({'name': name, 'number': number})
            else: logger.warning(f"Skipping company entry, missing name/number: {ET.tostring(company_element, encoding='unicode')[:100]}...")
        return companies
    except ET.ParseError as e: logger.error(f"XML ParseError (ListOfCompanies): {e}"); return None
    except Exception as e: logger.exception(f"Unexpected parsing error (ListOfCompanies): {e}"); return None

def get_tally_companies(host: str = 'localhost', port: str = '9000') -> list[dict] | None:
    """Fetches basic Name, Number list from Tally via XML."""
    url = f'http://{host}:{port}'; xml_request = "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>EXPORT</TALLYREQUEST><TYPE>COLLECTION</TYPE><ID>ListOfCompanies</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION Name=\"ListOfCompanies\"><TYPE>Company</TYPE><FETCH>Name,CompanyNumber</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>"
    headers = {'Content-Type': 'application/xml'}; logger.info(f"Fetching company list from {url}...")
    try:
        response = requests.post(url, data=xml_request.encode('utf-8'), headers=headers, timeout=TALLY_TIMEOUT_STANDARD); response.raise_for_status()
        if response.status_code == 200:
            logger.debug("Received OK for company list."); # Add raw XML debug log here if needed
            companies = _parse_tally_company_xml(response.content)
            if companies is None: logger.error("Failed to parse company list XML."); return None
            logger.info(f"Fetched {len(companies)} companies from Tally list."); return companies
        else: logger.error(f"Tally returned non-200: {response.status_code}"); return None
    except requests.exceptions.RequestException as e: logger.exception(f"HTTP error fetching company list: {e}"); return None

# --- Removed XML+$$ExecSQL Functions ---
# def fetch_company_details_xml_sql(...) - REMOVED as non-functional
# def _parse_execsql_response(...) - REMOVED
# def _convert_tally_value(...) - REMOVED (functionality merged into odbc_helper._convert_odbc_value)