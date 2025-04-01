# data_split.py

import os
import csv
from tqdm import tqdm
from pathlib import Path
from itertools import islice

def split_updated_num(updated_num_file, output_dir, chunk_size=200_000):
    """
    Splits a large 'updated_num_file' into per-ticker TSVs without
    keeping all file handles open at the same time.
    Reads 'chunk_size' lines at a time, groups them by ticker,
    and writes them out in batch.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # First, read the header line
    with open(updated_num_file, 'r', encoding='utf-8', newline='') as f_in:
        reader = csv.reader(f_in, delimiter='\t')
        header = next(reader)  # store the column names

    # Count total rows (minus header) for tqdm
    with open(updated_num_file, 'r', encoding='utf-8') as f_in:
        total_lines = sum(1 for _ in f_in) - 1

    def write_chunk_rows(bucket, header):
        """
        Write all rows in 'bucket' to per-ticker files, then clear it.
        bucket: dict[ticker -> list of row dicts]
        """
        for ticker, rows in bucket.items():
            if not ticker.strip():
                continue
            file_path = os.path.join(output_dir, f"{ticker}.tsv")

            # Determine if file already exists to know if we write header
            file_exists = os.path.exists(file_path)

            # Open in append mode if exists, otherwise write mode
            mode = 'a' if file_exists else 'w'
            with open(file_path, mode, newline='', encoding='utf-8') as f_out:
                writer = csv.DictWriter(f_out, fieldnames=header, delimiter='\t')
                if not file_exists:
                    writer.writeheader()
                writer.writerows(rows)

        bucket.clear()  # release memory

    # Now read in chunks of lines
    with open(updated_num_file, 'r', encoding='utf-8', newline='') as f_in:
        reader = csv.DictReader(f_in, delimiter='\t', fieldnames=header)
        next(reader)  # skip the first line again (header) so we don't re-parse it

        pbar = tqdm(total=total_lines, desc="Splitting by ticker", unit="row")
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

    print(f"Ticker files saved to: {output_dir}")

