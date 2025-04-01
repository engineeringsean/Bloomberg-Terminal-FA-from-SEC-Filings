# data_combination.py

import os
import pandas as pd
import requests
from io import StringIO
from tqdm import tqdm
import csv

def combine_num_files(input_dir, output_file, selected_columns, na_fill_value=None):
    """Combine all num.tsv files in input_dir into one large TSV."""
    combined_df = pd.DataFrame()
    file_paths = []

    # Find all num.tsv files
    for subdir, _, files in os.walk(input_dir):
        for file in files:
            if file.lower() == "num.tsv":
                file_paths.append(os.path.join(subdir, file))

    if not file_paths:
        print(f"No num.tsv files found in {input_dir}")
        return

    for file_path in tqdm(file_paths, desc="Combining num.tsv files"):
        try:
            df = pd.read_csv(file_path, sep='\t', dtype=str, low_memory=False)
            # Select only the columns we need
            available_cols = [col for col in selected_columns if col in df.columns]
            df = df[available_cols]
            if na_fill_value is not None:
                df = df.fillna(na_fill_value)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    combined_df.to_csv(output_file, sep='\t', index=False)
    print(f"Combined num.tsv file saved to: {output_file}")


def combine_sub_files(input_dir, output_file, na_fill_value=None):
    """Combine all sub.tsv files in input_dir into one TSV, then add ticker column from SEC mapping."""
    combined_df = pd.DataFrame()
    file_paths = []

    # Gather all sub.tsv files
    for subdir, _, files in os.walk(input_dir):
        for file in files:
            if file.lower() == "sub.tsv":
                file_paths.append(os.path.join(subdir, file))

    if not file_paths:
        print(f"No sub.tsv files found in {input_dir}")
        return

    # Combine
    for file_path in tqdm(file_paths, desc="Combining sub.tsv files"):
        try:
            df = pd.read_csv(file_path, sep='\t', dtype=str, low_memory=False)
            if na_fill_value is not None:
                df = df.fillna(na_fill_value)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Fetch SEC ticker mapping
    tickers_url = 'https://www.sec.gov/include/ticker.txt'
    headers = {
        'User-Agent': 'Sample Company Name AdminContact@samplecompany.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    response = requests.get(tickers_url, headers=headers)
    tickers = pd.read_csv(StringIO(response.text), delimiter='\t', header=None)
    tickers.columns = ['ticker', 'cik']

    # Merge combined sub.tsv with ticker data
    combined_df['cik'] = combined_df['cik'].astype(str)
    tickers['cik'] = tickers['cik'].astype(str)
    merged_df = combined_df.merge(tickers, on='cik', how='left')

    # Reorder columns
    desired_columns = ["adsh", "ticker", "form", "cik", "filed"]
    merged_df = merged_df[[col for col in desired_columns if col in merged_df.columns]]
    merged_df.to_csv(output_file, sep='\t', index=False)
    print(f"Combined sub.tsv file (with ticker) saved to: {output_file}")


def merge_num_and_sub(num_file, sub_file, output_file):
    """Merge the combined num file with the combined sub file, matching on 'adsh'."""
    sub_df = pd.read_csv(
        sub_file, sep='\t', 
        usecols=["adsh", "ticker", "form", "cik", "filed"], 
        low_memory=False
    )
    chunk_size = 10**5
    first_chunk = True

    with open(output_file, 'w', encoding='utf-8') as out_f:
        for chunk in tqdm(pd.read_csv(num_file, sep='\t', chunksize=chunk_size, low_memory=False),
                          desc="Merging num and sub files", unit="chunk"):
            merged_chunk = chunk.merge(sub_df, on='adsh', how='left')
            # Reorder columns
            cols = ['ticker', 'form', 'cik'] + [col for col in merged_chunk.columns if col not in ['ticker', 'form', 'cik']]
            merged_chunk = merged_chunk[cols]
            merged_chunk.to_csv(
                out_f, sep='\t', index=False, header=first_chunk, mode='a'
            )
            first_chunk = False

    print(f"Updated combined num.tsv (merged with sub) saved to: {output_file}")
