# data_price.py

import os
import datetime
import pandas as pd
from tqdm import tqdm
from loguru import logger

from oauth import get_bearer_token, get_price_for_date


def add_price_to_files(input_dir, output_dir):
    """
    For each ticker file in input_dir, look up the price for the day after 'filed'
    date and write a new file with a 'price' column to output_dir.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tsv_files = sorted([f for f in os.listdir(input_dir) if f.lower().endswith('.tsv')])

    # Count total rows for progress bar
    total_rows = 0
    for f in tsv_files:
        in_path = os.path.join(input_dir, f)
        try:
            df = pd.read_csv(in_path, sep='\t', low_memory=False)
            total_rows += len(df)
        except Exception:
            continue

    with tqdm(total=total_rows, desc="Adding price to ticker files") as pbar:
        for file in tsv_files:
            ticker = file[:-4]  # remove .tsv
            in_path = os.path.join(input_dir, file)
            out_path = os.path.join(output_dir, file)
            df = pd.read_csv(in_path, sep='\t')
            if 'filed' not in df.columns:
                logger.warning(f"Skipping {file}: no 'filed' column found.")
                pbar.update(len(df))
                continue

            unique_dates = df['filed'].unique()
            price_map = {}
            for date_str in unique_dates:
                # Convert filed date (YYYYMMDD) to datetime + 1 day
                try:
                    date_dt = datetime.datetime.strptime(str(date_str), "%Y%m%d") + datetime.timedelta(days=1)
                    price_map[date_str] = get_price_for_date(ticker, date_dt)
                except Exception as e:
                    price_map[date_str] = None
                    logger.error(f"Error fetching price for {ticker} on {date_str}: {e}")

            df['price'] = df['filed'].map(price_map)
            df.to_csv(out_path, sep='\t', index=False)
            pbar.update(len(df))

    print(f"Ticker files with price added saved to: {output_dir}")
