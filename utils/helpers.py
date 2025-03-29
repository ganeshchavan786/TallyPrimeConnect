# TallyPrimeConnect/utils/helpers.py
import json
import os
import requests
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)

# --- Constants & Config ---
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    BASE_DIR = os.path.dirname(os.getcwd())

CONFIG_DIR = os.path.join(BASE_DIR, 'config')
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, 'settings.json')

DEFAULT_SETTINGS = {
    "tally_host": "localhost",
    "tally_port": "9000"
}
TALLY_TIMEOUT = 10.0 # Seconds for Tally requests

# --- Settings Management ---
def load_settings() -> dict:
    """Loads Tally connection settings from the JSON file."""
    logger.debug(f"Attempting to load settings from: {SETTINGS_FILE_PATH}")
    defaults = DEFAULT_SETTINGS.copy()
    if not os.path.exists(SETTINGS_FILE_PATH):
        logger.warning("Settings file not found. Creating with defaults.")
        save_settings(defaults)
        return defaults
    try:
        with open(SETTINGS_FILE_PATH, 'r') as f:
            settings = json.load(f)
            # Ensure all default keys exist
            for key, value in defaults.items():
                settings.setdefault(key, value)
            logger.info("Settings loaded successfully.")
            return settings
    except (json.JSONDecodeError, IOError) as e:
        logger.exception(f"Error loading settings: {e}. Using default settings.")
        return defaults # Return defaults on error

def save_settings(settings: dict):
    """Saves settings to the JSON file."""
    logger.debug(f"Saving settings to: {SETTINGS_FILE_PATH}")
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SETTINGS_FILE_PATH, 'w') as f:
            json.dump(settings, f, indent=4)
        logger.info("Settings saved successfully.")
    except IOError as e:
        logger.exception(f"Error saving settings: {e}")


# --- Tally Interaction ---
def check_tally_connection(host: str = 'localhost', port: str = '9000') -> bool:
    """Checks Tally connection using a simple HTTP GET request."""
    url = f'http://{host}:{port}'
    logger.info(f"Checking Tally connection via GET at {url}...")
    try:
        response = requests.get(url, timeout=TALLY_TIMEOUT / 2) # Shorter timeout for basic check
        logger.debug(f"Tally GET response status: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.Timeout:
        logger.warning(f"Connection check to {url} timed out.")
        return False
    except requests.exceptions.ConnectionError:
        logger.warning(f"Connection check to {url} failed (Connection Refused/DNS Error).")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during Tally connection check: {e}", exc_info=False) # Log less detail for simple check
        return False


def _parse_tally_company_xml(xml_content: bytes) -> list[dict] | None:
    """Helper to parse XML response content for companies."""
    try:
        root = ET.fromstring(xml_content)
        companies = []
        for company_element in root.findall('.//COMPANY'):
            name_element = company_element.find('NAME')
            number_element = company_element.find('COMPANYNUMBER')
            name = name_element.text.strip() if name_element is not None and name_element.text else None
            number = number_element.text.strip() if number_element is not None and number_element.text else None

            if name and number: # Ensure both name and number are present
                companies.append({'name': name, 'number': number})
            else:
                 logger.warning(f"Skipping company entry due to missing name or number in XML: {ET.tostring(company_element, encoding='unicode')[:100]}...")
        return companies
    except ET.ParseError as e:
        logger.error(f"Error parsing Tally XML response: {e}")
        # Log snippet of invalid XML
        try:
            logger.debug(f"Invalid XML snippet: {xml_content[:500].decode('utf-8', errors='ignore')}...")
        except Exception: pass # Ignore decoding errors
        return None


def get_tally_companies(host: str = 'localhost', port: str = '9000') -> list[dict] | None:
    """
    Fetches the list of companies from Tally using XML request.
    Returns a list of company dictionaries or None on failure.
    """
    url = f'http://{host}:{port}'
    # Keep XML on one line or use textwrap.dedent for multi-line readability
    xml_request = "<ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>EXPORT</TALLYREQUEST><TYPE>COLLECTION</TYPE><ID>ListOfCompanies</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT></STATICVARIABLES><TDL><TDLMESSAGE><COLLECTION Name=\"ListOfCompanies\"><TYPE>Company</TYPE><FETCH>Name,CompanyNumber</FETCH></COLLECTION></TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>"
    headers = {'Content-Type': 'application/xml'}
    logger.info(f"Fetching companies from Tally at {url}...")

    try:
        response = requests.post(url, data=xml_request.encode('utf-8'), headers=headers, timeout=TALLY_TIMEOUT)
        response.raise_for_status() # Raise HTTPError for 4xx/5xx

        if response.status_code == 200:
            logger.debug("Received OK response from Tally for company list.")
            companies = _parse_tally_company_xml(response.content)

            if companies is None: # Check if parsing failed
                logger.error("Failed to parse company list XML from Tally.")
                return None # Indicate failure due to parsing

            if not companies:
                 # Check if Tally explicitly said 'ok, but no companies' vs just empty parse
                 if b'<RESPONSE><STATUS>1</STATUS></RESPONSE>' in response.content or \
                    b'<COMPANY NAME=' not in response.content: # Heuristic checks
                     logger.info("Tally responded successfully but returned no companies (or none parseable).")
                     # Check Tally state - maybe no company open?
                 else:
                     # This case means parsing worked but found zero valid <COMPANY> tags
                     logger.warning("Parsed Tally XML but found no valid company entries.")

            logger.info(f"Successfully fetched {len(companies)} companies from Tally.")
            return companies # Return list (possibly empty)
        else:
            # Should be caught by raise_for_status, but as fallback
            logger.error(f"Tally returned non-200 status: {response.status_code} for company list.")
            return None # Indicate fetch failure

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while fetching companies from {url}.")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection failed while fetching companies from {url} (Connection Refused/DNS Error).")
        return None
    except requests.exceptions.RequestException as e:
        logger.exception(f"HTTP error occurred during Tally company fetch: {e}") # Log full exception for HTTP errors
        return None