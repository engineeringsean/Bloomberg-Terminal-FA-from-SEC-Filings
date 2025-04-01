# oauth.py

import os
import requests
import datetime
import base64
import webbrowser
import time
from loguru import logger

from settings import (
    CONFIG_FILE, OAUTH_AUTHORIZE_URL, OAUTH_TOKEN_URL,
    TOKEN_REFRESH_INTERVAL, MIN_TIME_BETWEEN_CALLS
)

# These will be set at runtime
APP_KEY = None
APP_SECRET = None
REDIRECT_URI = None
ACCESS_TOKEN = None
REFRESH_TOKEN = None
LAST_TOKEN_TIME = None

# We also store this in memory
LAST_CALL_TIME = 0.0


def load_config(file_path: str) -> None:
    """Load API credentials from a config file, prompting user if blank."""
    global APP_KEY, APP_SECRET, REDIRECT_URI
    global ACCESS_TOKEN, REFRESH_TOKEN, LAST_TOKEN_TIME

    # 1. Create a config file if it doesn't exist.
    if not os.path.exists(file_path):
        logger.warning(f"Config file not found at {file_path}. Creating a new one.")
        _create_blank_config(file_path)

    # 2. Read it in.
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    config_map = {}
    for line in lines:
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        config_map[key.strip()] = val.strip()

    # 3. Fill in memory from config_map or prompt user if empty.
    APP_KEY = config_map.get("APP_KEY", "")
    if not APP_KEY:
        APP_KEY = input("Please enter your Schwab APP_KEY: ").strip()
        config_map["APP_KEY"] = APP_KEY

    APP_SECRET = config_map.get("APP_SECRET", "")
    if not APP_SECRET:
        APP_SECRET = input("Please enter your Schwab APP_SECRET: ").strip()
        config_map["APP_SECRET"] = APP_SECRET

    REDIRECT_URI = config_map.get("REDIRECT_URI", "")
    if not REDIRECT_URI:
        REDIRECT_URI = input("Please enter your Schwab REDIRECT_URI: ").strip()
        config_map["REDIRECT_URI"] = REDIRECT_URI

    ACCESS_TOKEN = config_map.get("ACCESS_TOKEN", "")
    REFRESH_TOKEN = config_map.get("REFRESH_TOKEN", "")

    last_token_time_str = config_map.get("LAST_TOKEN_TIME", "")
    if last_token_time_str:
        try:
            LAST_TOKEN_TIME = datetime.datetime.fromisoformat(last_token_time_str)
        except ValueError:
            LAST_TOKEN_TIME = None
    else:
        LAST_TOKEN_TIME = None

    # 4. Save any newly provided values (so user wont be asked again next time).
    lines = [
        f"APP_KEY={APP_KEY}\n",
        f"APP_SECRET={APP_SECRET}\n",
        f"REDIRECT_URI={REDIRECT_URI}\n",
        f"ACCESS_TOKEN={ACCESS_TOKEN}\n",
        f"REFRESH_TOKEN={REFRESH_TOKEN}\n",
        f"LAST_TOKEN_TIME={LAST_TOKEN_TIME.isoformat() if LAST_TOKEN_TIME else ''}\n"
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def save_config(file_path: str) -> None:
    """Write current auth info to config file."""
    global APP_KEY, APP_SECRET, REDIRECT_URI
    global ACCESS_TOKEN, REFRESH_TOKEN, LAST_TOKEN_TIME

    lines = [
        f"APP_KEY={APP_KEY}\n",
        f"APP_SECRET={APP_SECRET}\n",
        f"REDIRECT_URI={REDIRECT_URI}\n",
        f"ACCESS_TOKEN={ACCESS_TOKEN}\n",
        f"REFRESH_TOKEN={REFRESH_TOKEN}\n",
        f"LAST_TOKEN_TIME={LAST_TOKEN_TIME.isoformat() if LAST_TOKEN_TIME else ''}\n"
    ]
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _create_blank_config(file_path: str):
    skeleton = (
        "APP_KEY=\n"
        "APP_SECRET=\n"
        "REDIRECT_URI=\n"
        "ACCESS_TOKEN=\n"
        "REFRESH_TOKEN=\n"
        "LAST_TOKEN_TIME=\n"
    )
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(skeleton)


def init_auth():
    """Perform the initial OAuth flow to get an authorization code, then exchange for tokens."""
    global APP_KEY, APP_SECRET, REDIRECT_URI, ACCESS_TOKEN, REFRESH_TOKEN, LAST_TOKEN_TIME

    auth_url = f"{OAUTH_AUTHORIZE_URL}?client_id={APP_KEY}&redirect_uri={REDIRECT_URI}"
    logger.info("Opening browser for Schwab authentication...")
    logger.info(f"URL:\n{auth_url}")
    webbrowser.open(auth_url)

    logger.info("Paste the ENTIRE redirect URL from your browser:")
    returned_url = input("Redirect URL: ").strip()
    if "code=" not in returned_url:
        logger.error("No 'code=' found in the returned URL. Aborting.")
        raise SystemExit("Invalid redirect URL.")

    # Extract code 
    code_idx = returned_url.index('code=') + len('code=')
    code_str = returned_url[code_idx : returned_url.index('%40')] + '@'
    logger.info(f"Retrieved code: {code_str}")

    credentials = f"{APP_KEY}:{APP_SECRET}"
    base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "authorization_code",
        "code": code_str,
        "redirect_uri": REDIRECT_URI,
    }
    logger.info("Requesting initial tokens from Schwab...")
    response = requests.post(OAUTH_TOKEN_URL, headers=headers, data=payload)

    if response.status_code != 200:
        logger.error(f"Initial token request failed: {response.text}")
        raise SystemExit("Failed to retrieve tokens.")

    token_json = response.json()
    ACCESS_TOKEN = token_json["access_token"]
    REFRESH_TOKEN = token_json["refresh_token"]
    LAST_TOKEN_TIME = datetime.datetime.now()
    logger.info("Successfully retrieved tokens.")
    save_config(CONFIG_FILE)


def refresh_tokens():
    """Refresh access/refresh tokens using the existing refresh token."""
    global APP_KEY, APP_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, LAST_TOKEN_TIME
    logger.info("Refreshing Schwab tokens...")

    credentials = f"{APP_KEY}:{APP_SECRET}"
    base64_credentials = base64.b64encode(credentials.encode()).decode("utf-8")
    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }
    response = requests.post(OAUTH_TOKEN_URL, headers=headers, data=payload)
    if response.status_code == 200:
        tokens_dict = response.json()
        ACCESS_TOKEN = tokens_dict["access_token"]
        REFRESH_TOKEN = tokens_dict["refresh_token"]
        LAST_TOKEN_TIME = datetime.datetime.now()
        logger.info("Token successfully refreshed.")
        save_config(CONFIG_FILE)
    else:
        logger.error(f"Error refreshing access token: {response.status_code} {response.text}")
        init_auth()


def get_bearer_token() -> str:
    """Return a valid Bearer token, refreshing if needed."""
    global ACCESS_TOKEN, REFRESH_TOKEN, LAST_TOKEN_TIME

    if not ACCESS_TOKEN:
        if not REFRESH_TOKEN:
            init_auth()
        else:
            refresh_tokens()
        return ACCESS_TOKEN

    elapsed_seconds = (datetime.datetime.now() - LAST_TOKEN_TIME).total_seconds() if LAST_TOKEN_TIME else 0
    if elapsed_seconds > TOKEN_REFRESH_INTERVAL:
        refresh_tokens()

    return ACCESS_TOKEN


def _make_schwab_api_call(params):
    """Internal helper to rate-limit and call the Schwab API."""
    global LAST_CALL_TIME
    elapsed = time.time() - LAST_CALL_TIME
    if elapsed < MIN_TIME_BETWEEN_CALLS:
        time.sleep(MIN_TIME_BETWEEN_CALLS - elapsed)

    token = get_bearer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    ticker = params["symbol"]
    date_unix_ms = params["date"]

    PRICE_ENDPOINT = (
        f"https://api.schwabapi.com/marketdata/v1/pricehistory?"
        f"symbol={ticker}&periodType=month&frequencyType=daily"
        f"&startDate={date_unix_ms}&endDate={date_unix_ms}"
    )
    LAST_CALL_TIME = time.time()
    resp = requests.get(PRICE_ENDPOINT, headers=headers)
    resp.raise_for_status()
    return resp.json()


def get_price_for_date(ticker, date_after_filed_datetime):
    """Fetch historical price for `ticker` on `date_after_filed_datetime` (or next available day)."""
    for attempt in range(6):
        date_unix_ms = int(date_after_filed_datetime.timestamp() * 1000)
        params = {"symbol": ticker.upper(), "date": date_unix_ms}
        try:
            data_json = _make_schwab_api_call(params)
            price = data_json["candles"][0]["close"]
            return price
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 400:
                logger.warning(
                    f"[Attempt {attempt+1}/6] 400 error for {ticker} "
                    f"on {date_after_filed_datetime.strftime('%Y-%m-%d')}. Trying next day..."
                )
                date_after_filed_datetime += datetime.timedelta(days=1)
                continue
            else:
                raise
        except KeyError:
            logger.error(
                f"Response JSON missing fields for {ticker} on {date_after_filed_datetime.strftime('%Y-%m-%d')}."
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None
    logger.error(f"All attempts failed for {ticker}. Returning None.")
    return None
