# data_simplify.py

import os
import pandas as pd
from tqdm import tqdm

def simplify_ticker_files(input_dir, output_dir):
    """
    Reads each ticker file in input_dir, keeps only the selected columns,
    and writes the simplified file to output_dir.
    """
    selected_columns = [
        "ticker", "form", "cik", "adsh", "tag",
        "ddate", "qtrs", "value", "dimn", "filed", "price"
    ]
    column_types = {
        "ticker": str,
        "form": str,
        "cik": int,
        "adsh": str,
        "tag": str,
        "ddate": int,
        "qtrs": int,
        "value": float,
        "dimn": int,
        "filed": int,
        "price": float
    }

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tsv_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.tsv')]

    for filename in tqdm(tsv_files, desc="Simplifying ticker files", unit='file'):
        ticker = filename.replace('.tsv', '')
        file_path = os.path.join(input_dir, filename)
        df = pd.read_csv(
            file_path,
            sep='\t',
            usecols=selected_columns,
            dtype=column_types,
            na_values=["Unknown"]
        )
        output_path = os.path.join(output_dir, f"{ticker}.tsv")
        df.to_csv(output_path, sep="\t", index=False)

    print(f"Simplified ticker files saved to: {output_dir}")
