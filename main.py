# main.py

from settings import (
    INPUT_DIR,
    OUTPUT_DIR,
    TICKER_PRICE_DIR,
    FINAL_TICKER_DIR,
    CONFIG_FILE,
    BLOOMBERG_STYLE_DIR
)

from oauth import load_config, get_bearer_token
from data_price import add_price_to_files
from data_simplify import simplify_ticker_files
from data_bloomberg import transform_all_tickers
from data_streaming import process_all_data_streaming

def main():
    # Step 1: Process all data in a single streaming pass (ultra-efficient)
    print("Choose processing mode:")
    print("1. Memory-efficient (faster, uses more RAM)")
    print("2. Database-backed (slower, uses less RAM for very large datasets)")
    choice = input("Enter choice (1 or 2): ").strip()
    
    use_db = choice == "2"
    
    process_all_data_streaming(
        input_dir=INPUT_DIR,
        output_dir=FINAL_TICKER_DIR,
        use_db=use_db
    )

    # Step 2: OAuth and add price data if user accepts
    gotPrice = False

    print("Get prices for each ticker on filing dates using your Charles Schwab API credentials? (Y/N)")
    getPrice = input().strip().upper()

    if getPrice == "Y":
        load_config(CONFIG_FILE)    # loads APP_KEY, ACCESS_TOKEN, etc.
        get_bearer_token()         # triggers OAuth flow if tokens missing/expired
        add_price_to_files(
            input_dir=FINAL_TICKER_DIR,
            output_dir=TICKER_PRICE_DIR
        )
        gotPrice = True

    # Step 3: Simplify columns (only if price data was added)
    if gotPrice == True:
        simplify_ticker_files(
            gotPrice,
            input_dir=TICKER_PRICE_DIR,
            output_dir=FINAL_TICKER_DIR
        )
    # If no price data, the files are already in the correct format in FINAL_TICKER_DIR

    # Step 4: Transform data into Bloomberg_Style tsv tables
    transform_all_tickers(
        input_dir=FINAL_TICKER_DIR,
        output_dir=BLOOMBERG_STYLE_DIR
    )

    print(f"Bloomberg-style financial tables are in: {BLOOMBERG_STYLE_DIR}")


if __name__ == "__main__":
    main()

