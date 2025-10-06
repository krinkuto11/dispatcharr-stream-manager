"""
Groups upload utility for Dispatcharr.

This module synchronizes channel groups from a CSV file with Dispatcharr,
creating new groups and updating existing ones as needed.
"""

import csv
import logging
import os
import sys
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv, set_key
from pathlib import Path

# --- Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)


# --- API Utilities ---
def _get_base_url() -> Optional[str]:
    """
    Get the base URL from environment variables.
    
    Returns:
        Optional[str]: The Dispatcharr base URL or None if not set.
    """
    return os.getenv("DISPATCHARR_BASE_URL")

def _get_auth_headers() -> Dict[str, str]:
    """
    Get authorization headers for API requests.
    
    Returns:
        Dict[str, str]: Dictionary with authorization headers.
        
    Raises:
        SystemExit: If login fails or token unavailable.
    """
    current_token = os.getenv("DISPATCHARR_TOKEN")
    if not current_token:
        logging.info(
            "DISPATCHARR_TOKEN not found. Attempting to log in..."
        )
        if login():
            load_dotenv(dotenv_path=env_path, override=True)
            current_token = os.getenv("DISPATCHARR_TOKEN")
            if not current_token:
                logging.error(
                    "Login succeeded, token still not found. Aborting."
                )
                sys.exit(1)
        else:
            logging.error(
                "Login failed. Check credentials in .env. Aborting."
            )
            sys.exit(1)
    return {
        "Authorization": f"Bearer {current_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def login() -> bool:
    """
    Log into Dispatcharr and save token to .env file.
    
    Returns:
        bool: True if login successful, False otherwise.
    """
    username = os.getenv("DISPATCHARR_USER")
    password = os.getenv("DISPATCHARR_PASS")
    base_url = _get_base_url()

    if not all([username, password, base_url]):
        logging.error(
            "DISPATCHARR_USER, DISPATCHARR_PASS, and "
            "DISPATCHARR_BASE_URL must be set in .env file."
        )
        return False

    login_url = f"{base_url}/api/accounts/token/"
    logging.info(f"Attempting to log in to {base_url}...")

    try:
        resp = requests.post(
            login_url,
            headers={"Content-Type": "application/json"},
            json={"username": username, "password": password}
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access") or data.get("token")

        if token:
            set_key(env_path, "DISPATCHARR_TOKEN", token)
            logging.info("Login successful. Token saved.")
            return True
        else:
            logging.error(
                "Login failed: No access token in response."
            )
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Login failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response content: {e.response.text}")
        return False

def _refresh_token() -> bool:
    """
    Refresh the authentication token.
    
    Returns:
        bool: True if refresh successful, False otherwise.
    """
    logging.info("Token expired or invalid. Attempting to refresh...")
    if login():
        load_dotenv(dotenv_path=env_path, override=True)
        logging.info("Token refreshed successfully.")
        return True
    else:
        logging.error("Token refresh failed.")
        return False


def _make_request(
    method: str, url: str, **kwargs: Any
) -> requests.Response:
    """
    Make a request with authentication and retry logic.
    
    Parameters:
        method (str): HTTP method (GET, POST, PATCH, etc.).
        url (str): The URL to send the request to.
        **kwargs: Additional arguments to pass to requests.
        
    Returns:
        requests.Response: The response object.
        
    Raises:
        requests.exceptions.RequestException: If request fails.
    """
    try:
        resp = requests.request(
            method, url, headers=_get_auth_headers(), **kwargs
        )
        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            if _refresh_token():
                logging.info(
                    f"Retrying {method} request to {url} "
                    f"with new token..."
                )
                resp = requests.request(
                    method, url, headers=_get_auth_headers(), **kwargs
                )
                resp.raise_for_status()
                return resp
            else:
                raise
        else:
            logging.error(
                f"HTTP Error: {e.response.status_code} for URL: {url}"
            )
            logging.error(f"Response: {e.response.text}")
            raise
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        raise

# --- Main Functionality ---
def fetch_existing_groups() -> Dict[str, Dict[str, Any]]:
    """
    Fetch existing groups from Dispatcharr.
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping group IDs
            to group objects.
    """
    url = f"{_get_base_url()}/api/channels/groups/"
    try:
        response = _make_request("GET", url)
        if response.status_code == 200:
            return {str(g["id"]): g for g in response.json()}
        return {}
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch existing groups: {e}")
        return {}


def update_group(group_id: str, new_name: str) -> requests.Response:
    """
    Update an existing group in Dispatcharr.
    
    Parameters:
        group_id (str): The ID of the group to update.
        new_name (str): The new name for the group.
        
    Returns:
        requests.Response: The response object.
    """
    url = f"{_get_base_url()}/api/channels/groups/{group_id}/"
    payload = {"name": new_name}
    return _make_request("PATCH", url, json=payload)


def create_group(name: str) -> requests.Response:
    """
    Create a new group in Dispatcharr.
    
    Parameters:
        name (str): The name for the new group.
        
    Returns:
        requests.Response: The response object.
    """
    url = f"{_get_base_url()}/api/channels/groups/"
    payload = {"name": name}
    return _make_request("POST", url, json=payload)

def main() -> None:
    """
    Sync groups from a CSV file to Dispatcharr.
    
    Reads groups from csv/groups_template.csv and creates or updates
    them in Dispatcharr to match the CSV content.
    
    Raises:
        SystemExit: If CSV file not found.
    """
    csv_file = "csv/groups_template.csv"
    if not os.path.exists(csv_file):
        logging.error(f"Error: The file {csv_file} was not found.")
        sys.exit(1)

    logging.info("📥 Syncing groups from CSV...")
    existing_groups = fetch_existing_groups()

    with open(csv_file, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            gid = row.get("id", "").strip()
            name = row.get("name", "").strip()
            if not gid or not name:
                logging.warning(
                    f"Skipping row with missing id or name: {row}"
                )
                continue

            if gid in existing_groups:
                current_name = existing_groups[gid]["name"]
                if current_name != name:
                    try:
                        update_group(gid, name)
                        logging.info(
                            f"  🔁 Updated group ID {gid}: "
                            f"'{current_name}' → '{name}'"
                        )
                    except requests.exceptions.RequestException:
                        logging.error(
                            f"  ❌ Failed to update group ID {gid}"
                        )
                else:
                    logging.info(
                        f"  ✅ Group ID {gid} ('{name}') "
                        f"already up-to-date"
                    )
            else:
                try:
                    create_group(name)
                    logging.info(f"  ➕ Created new group: {name}")
                except requests.exceptions.RequestException:
                    logging.error(
                        f"  ❌ Failed to create group: {name}"
                    )

    logging.info("\n✅ Sync complete!")

if __name__ == "__main__":
    main()