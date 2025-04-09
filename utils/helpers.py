# TallyPrimeConnect/utils/helpers.py
import json
import os
import requests
import xml.etree.ElementTree as ET
import logging
import datetime

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
        final_settings = defaults.copy(); final_settings.update(settings)
        logger.info("Settings loaded."); return final_settings
    except (json.JSONDecodeError, IOError) as e:
        logger.exception(f"Error loading settings: {e}. Using defaults."); return defaults
    except Exception as e:
        logger.exception(f"Unexpected error loading settings: {e}. Using defaults."); return defaults

def save_settings(settings: dict):
    """Saves settings to the JSON file."""
    logger.debug(f"Saving settings to: {SETTINGS_FILE_PATH}")
    if not isinstance(settings, dict) or "tally_host" not in settings or "tally_port" not in settings:
         logger.error(f"Invalid settings structure: {settings}"); raise ValueError("Invalid settings.")
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f: json.dump(settings, f, indent=4)
        logger.info("Settings saved.")
    except Exception as e: logger.exception(f"Error saving settings: {e}"); raise

# --- Tally Interaction (HTTP) ---
def check_tally_connection(host: str = 'localhost', port: str = '9000') -> bool:
    """Checks Tally connection using a simple HTTP GET request."""
    if not host or not port: logger.error("check_connection needs host/port."); return False
    url = f'http://{host}:{port}'; logger.info(f"Checking Tally GET at {url}...")
    try:
        response = requests.get(url, timeout=TALLY_TIMEOUT_STANDARD / 3) # Quick check
        logger.debug(f"Tally GET response status: {response.status_code}"); return response.status_code == 200
    except requests.exceptions.RequestException as e: logger.warning(f"Tally check fail: {e}"); return False
    except Exception as e: logger.exception(f"Unexpected check error: {e}"); return False

def _parse_tally_company_xml(xml_content: bytes) -> list[dict] | None:
    """Helper to parse XML for ListOfCompanies collection."""
    try:
        root = ET.fromstring(xml_content)
        status = root.find('.//RESPONSE/STATUS'); # Check for internal Tally errors
        if status is not None and status.text != '1': logger.error(f"Tally error (ListCompanies): {root.find('.//RESPONSE/DESC').text if root.find('.//RESPONSE/DESC') is not None else 'Unknown'}"); return None
        companies = []
        for el in root.findall('.//COMPANY'): # Find COMPANY tags
            name = el.findtext('.//NAME', default='').strip()
            num = el.findtext('.//COMPANYNUMBER', default='').strip()
            if name and num: companies.append({'name': name, 'number': num})
            else: logger.warning(f"Skip company entry, missing name/num: {ET.tostring(el, encoding='unicode')[:100]}...")
        return companies
    except ET.ParseError as e: logger.error(f"XML ParseError (ListCompanies): {e}"); return None
    except Exception as e: logger.exception(f"Unexpected parse error (ListCompanies): {e}"); return None

def get_tally_companies(host: str = 'localhost', port: str = '9000') -> list[dict] | None:
    """Fetches basic Name, Number list from Tally via HTTP XML."""
    if not host or not port: logger.error("get_tally_companies needs host/port."); return None
    url = f'http://{host}:{port}'; xml_req = "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>EXPORT</TALLYREQUEST><TYPE>COLLECTION</TYPE><ID>ListOfCompanies</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION Name=\"ListOfCompanies\"><TYPE>Company</TYPE><FETCH>Name,CompanyNumber</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>"
    headers = {'Content-Type': 'application/xml'}; logger.info(f"Fetching company list from {url}...")
    try:
        response = requests.post(url, data=xml_req.encode('utf-8'), headers=headers, timeout=TALLY_TIMEOUT_STANDARD); response.raise_for_status()
        if response.status_code == 200:
            logger.debug("Received OK for company list.");
            # Debug log raw XML if needed:
            # try: logger.debug(f"Raw XML List:\n{response.content.decode('utf-8', errors='ignore')[:1000]}...")
            # except Exception: pass
            companies = _parse_tally_company_xml(response.content)
            if companies is None: logger.error("Failed parse company list XML."); return None # Parsing failed
            logger.info(f"Fetched {len(companies)} companies from Tally list."); return companies
        else: logger.error(f"Tally non-200: {response.status_code}"); return None # HTTP error handled by raise_for_status usually
    except requests.exceptions.RequestException as e: logger.exception(f"HTTP error fetching company list: {e}"); return None
    except Exception as e: logger.exception(f"Unexpected error fetching companies: {e}"); return None

logger.debug("utils.helpers loaded.")