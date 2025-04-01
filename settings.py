# settings.py

import os
import datetime
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env if available

# Default directories (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(PROJECT_ROOT, "data", "input_data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "output_data")

# Intermediate combined file paths
COMBINED_NUM_PATH = os.path.join(OUTPUT_DIR, "combined_num.tsv")
COMBINED_SUB_PATH = os.path.join(OUTPUT_DIR, "combined_sub.tsv")
UPDATED_COMBINED_NUM_PATH = os.path.join(OUTPUT_DIR, "updated_combined_num.tsv")

# Directories for per-ticker files
TICKER_SPLIT_DIR = os.path.join(OUTPUT_DIR, "Ticker_Split")
TICKER_PRICE_DIR = os.path.join(OUTPUT_DIR, "Ticker_With_Price")
FINAL_TICKER_DIR = os.path.join(OUTPUT_DIR, "Final_Ticker_Files")
BLOOMBERG_STYLE_DIR = os.path.join(OUTPUT_DIR, "Bloomberg_Style_Tables")

# Schwab API OAuth config
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.env")

# OAuth-related timing
LAST_CALL_TIME = 0.0
MIN_TIME_BETWEEN_CALLS = 60.0 / 115  # to avoid exceeding API rate limit of 120 calls per minute
TOKEN_REFRESH_INTERVAL = 1740  # 29 minutes to refresh access token just before it becomes deactivated

# OAuth endpoints
OAUTH_AUTHORIZE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
OAUTH_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
