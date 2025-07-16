# data_optimized.py

import os
import csv
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from itertools import islice

def process_to_final_tickers(updated_num_file, output_dir, chunk_size=200_000):
    """
    Optimized function that combines splitting by ticker and column simplification
    into a single step. Processes the merged num/sub file directly to the final
    ticker format without creating intermediate files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Define the final columns we want (without price data initially)
    selected_columns = [
        "ticker", "form", "cik", "adsh", "tag",
        "ddate", "qtrs", "value", "dimn", "filed"
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
    }

    # First, read the header line
    with open(updated_num_file, 'r', encoding='utf-8', newline='') as f_in:
        reader = csv.reader(f_in, delimiter='\t')
        header = next(reader)  # store the column names

    # Count total rows (minus header) for tqdm
    with open(updated_num_file, 'r', encoding='utf-8') as f_in:
        total_lines = sum(1 for _ in f_in) - 1

    def write_chunk_rows(bucket, header):
        """
        Write all rows in 'bucket' to per-ticker files with simplified columns,
        then clear it.
        bucket: dict[ticker -> list of row dicts]
        """
        for ticker, rows in bucket.items():
            if not ticker.strip():
                continue
                
            file_path = os.path.join(output_dir, f"{ticker}.tsv")

            # Convert rows to DataFrame for processing
            df = pd.DataFrame(rows)
            
            # Select only the columns we want
            available_cols = [col for col in selected_columns if col in df.columns]
            df = df[available_cols]
            
            # Apply data types
            for col, dtype in column_types.items():
                if col in df.columns:
                    try:
                        if dtype == int:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                        elif dtype == float:
                            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
                        else:
                            df[col] = df[col].astype(dtype)
                    except Exception as e:
                        print(f"Warning: Could not convert column {col} to {dtype}: {e}")

            # Write to file
            df.to_csv(file_path, sep='\t', index=False)

        bucket.clear()  # release memory

    # Now read in chunks of lines
    with open(updated_num_file, 'r', encoding='utf-8', newline='') as f_in:
        reader = csv.DictReader(f_in, delimiter='\t', fieldnames=header)
        next(reader)  # skip the first line again (header) so we don't re-parse it

        pbar = tqdm(total=total_lines, desc="Processing to final ticker format", unit="row")
        bucket = {}  # ticker -> list of row-dicts
        lines_in_bucket = 0

        for row in reader:
            pbar.update(1)
            ticker = (row.get('ticker') or '').strip()
            if ticker not in bucket:
                bucket[ticker] = []
            bucket[ticker].append(row)
            lines_in_bucket += 1

            # If bucket hits chunk_size, write out and reset
            if lines_in_bucket >= chunk_size:
                write_chunk_rows(bucket, header)
                lines_in_bucket = 0

        # Write any leftover rows
        if lines_in_bucket > 0:
            write_chunk_rows(bucket, header)

        pbar.close()

    print(f"Final ticker files saved to: {output_dir}") 