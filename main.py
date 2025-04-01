# main.py

from settings import (
    INPUT_DIR,
    OUTPUT_DIR,
    COMBINED_NUM_PATH,
    COMBINED_SUB_PATH,
    UPDATED_COMBINED_NUM_PATH,
    TICKER_SPLIT_DIR,
    TICKER_PRICE_DIR,
    FINAL_TICKER_DIR,
    CONFIG_FILE,
    BLOOMBERG_STYLE_DIR
)

from data_combination import combine_num_files, combine_sub_files, merge_num_and_sub
from data_split import split_updated_num
from oauth import load_config, get_bearer_token
from data_price import add_price_to_files
from data_simplify import simplify_ticker_files
from data_bloomberg import transform_all_tickers

def main():
    # Step 1: Combine num files
    selected_num_columns = ["adsh", "tag", "ddate", "qtrs", "value", "dimn"]
    combine_num_files(
        input_dir=INPUT_DIR,
        output_file=COMBINED_NUM_PATH,
        selected_columns=selected_num_columns,
        na_fill_value=None
    )

    # Step 2: Combine sub files + add ticker
    combine_sub_files(
        input_dir=INPUT_DIR,
        output_file=COMBINED_SUB_PATH,
        na_fill_value=None
    )

    # Step 3: Merge combined num & sub on 'adsh'
    merge_num_and_sub(
        num_file=COMBINED_NUM_PATH,
        sub_file=COMBINED_SUB_PATH,
        output_file=UPDATED_COMBINED_NUM_PATH
    )

    # Step 4: Split the updated file into per-ticker
    split_updated_num(
        updated_num_file=UPDATED_COMBINED_NUM_PATH,
        output_dir=TICKER_SPLIT_DIR
    )

    # Step 5: OAuth and add price data
    load_config(CONFIG_FILE)    # loads APP_KEY, ACCESS_TOKEN, etc.
    get_bearer_token()         # triggers OAuth flow if tokens missing/expired
    add_price_to_files(
        input_dir=TICKER_SPLIT_DIR,
        output_dir=TICKER_PRICE_DIR
    )

    # Step 6: Simplify columns
    simplify_ticker_files(
        input_dir=TICKER_PRICE_DIR,
        output_dir=FINAL_TICKER_DIR
    )

    # Step 7: Transform data into Bloomberg_Style tsv tables
    transform_all_tickers(
        input_dir=FINAL_TICKER_DIR,
        output_dir=BLOOMBERG_STYLE_DIR
    )

    print(f"Bloomberg-style tables are in: {BLOOMBERG_STYLE_DIR}")


if __name__ == "__main__":
    main()

