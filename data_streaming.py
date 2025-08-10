# data_streaming.py

import os
import csv
import requests
from io import StringIO
from tqdm import tqdm
from pathlib import Path
from collections import defaultdict
import tempfile
import shutil
import sqlite3
import pickle

def process_all_data_streaming(input_dir, output_dir, chunk_size=50_000, use_db=False):
    """
    Ultra-efficient streaming approach that processes all num.tsv and sub.tsv files
    in a single pass, directly creating final ticker files without intermediate storage.
    
    This approach:
    1. Streams through all files without loading them entirely into memory
    2. Creates a temporary lookup table for sub data (adsh -> ticker info)
    3. Processes num files in chunks and writes directly to final ticker files
    4. Uses minimal memory by processing one chunk at a time
    
    Args:
        input_dir: Directory containing num.tsv and sub.tsv files
        output_dir: Directory to save final ticker files
        chunk_size: Number of rows to process at once
        use_db: If True, uses SQLite for lookup table (for very large datasets)
    """
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    if use_db:
        # Use SQLite for extremely large datasets
        process_with_sqlite(input_dir, output_dir, chunk_size)
    else:
        # Use in-memory lookup for most cases
        process_with_memory_lookup(input_dir, output_dir, chunk_size)

def process_with_memory_lookup(input_dir, output_dir, chunk_size):
    """Process using in-memory lookup table (faster for most datasets)."""
    # Step 1: Build adsh -> ticker lookup table (streaming)
    print("Building ticker lookup table...")
    adsh_lookup = build_adsh_lookup_streaming(input_dir)
    
    # Step 2: Process num files directly to final ticker format
    print("Processing num files to final ticker format...")
    process_num_files_streaming(input_dir, output_dir, adsh_lookup, chunk_size)
    
    print(f"Final ticker files saved to: {output_dir}")

def process_with_sqlite(input_dir, output_dir, chunk_size):
    """Process using SQLite database for lookup table (for extremely large datasets)."""
    # Create temporary SQLite database
    db_path = tempfile.mktemp(suffix='.db')
    
    try:
        # Step 1: Build SQLite lookup table
        print("Building SQLite ticker lookup table...")
        build_sqlite_lookup(input_dir, db_path)
        
        # Step 2: Process num files using SQLite lookup
        print("Processing num files using SQLite lookup...")
        process_num_files_with_sqlite(input_dir, output_dir, db_path, chunk_size)
        
        print(f"Final ticker files saved to: {output_dir}")
    
    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.remove(db_path)

def build_adsh_lookup_streaming(input_dir):
    """
    Build a lookup table from adsh to ticker info by streaming through sub.tsv files.
    Returns a dict: {adsh: {'ticker': ticker, 'form': form, 'cik': cik, 'filed': filed}}
    """
    # First, get the SEC ticker mapping
    tickers_map = get_sec_ticker_mapping()
    
    adsh_lookup = {}
    
    # Find all sub.tsv files
    sub_files = []
    for subdir, _, files in os.walk(input_dir):
        for file in files:
            if file.lower() == "sub.tsv":
                sub_files.append(os.path.join(subdir, file))
    
    if not sub_files:
        print(f"No sub.tsv files found in {input_dir}")
        return adsh_lookup
    
    # Process each sub.tsv file
    for file_path in tqdm(sub_files, desc="Building adsh lookup"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    adsh = row.get('adsh', '').strip()
                    cik = row.get('cik', '').strip()
                    
                    if adsh and cik:
                        # Get ticker from SEC mapping
                        ticker = tickers_map.get(cik, '')
                        
                        adsh_lookup[adsh] = {
                            'ticker': ticker,
                            'form': row.get('form', ''),
                            'cik': cik,
                            'filed': row.get('filed', '')
                        }
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    print(f"Built lookup table with {len(adsh_lookup)} entries")
    return adsh_lookup

def get_sec_ticker_mapping():
    """Fetch SEC ticker mapping and return as dict: {cik: ticker}"""
    try:
        tickers_url = 'https://www.sec.gov/include/ticker.txt'
        headers = {
            'User-Agent': 'Sample Company Name AdminContact@samplecompany.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        response = requests.get(tickers_url, headers=headers)
        response.raise_for_status()
        
        tickers_map = {}
        for line in response.text.strip().split('\n'):
            if '\t' in line:
                ticker, cik = line.split('\t', 1)
                tickers_map[cik] = ticker
        
        print(f"Fetched {len(tickers_map)} ticker mappings from SEC")
        return tickers_map
    except Exception as e:
        print(f"Error fetching SEC ticker mapping: {e}")
        return {}

def build_sqlite_lookup(input_dir, db_path):
    """Build SQLite database for adsh -> ticker lookup."""
    # Get SEC ticker mapping
    tickers_map = get_sec_ticker_mapping()
    
    # Create database and table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE adsh_lookup (
            adsh TEXT PRIMARY KEY,
            ticker TEXT,
            form TEXT,
            cik TEXT,
            filed TEXT
        )
    ''')
    
    # Find all sub.tsv files
    sub_files = []
    for subdir, _, files in os.walk(input_dir):
        for file in files:
            if file.lower() == "sub.tsv":
                sub_files.append(os.path.join(subdir, file))
    
    if not sub_files:
        print(f"No sub.tsv files found in {input_dir}")
        return
    
    # Process each sub.tsv file
    for file_path in tqdm(sub_files, desc="Building SQLite lookup"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                batch = []
                
                for row in reader:
                    adsh = row.get('adsh', '').strip()
                    cik = row.get('cik', '').strip()
                    
                    if adsh and cik:
                        ticker = tickers_map.get(cik, '')
                        batch.append((adsh, ticker, row.get('form', ''), cik, row.get('filed', '')))
                    
                    # Insert in batches for efficiency
                    if len(batch) >= 10000:
                        cursor.executemany(
                            'INSERT OR REPLACE INTO adsh_lookup VALUES (?, ?, ?, ?, ?)',
                            batch
                        )
                        conn.commit()
                        batch = []
                
                # Insert remaining batch
                if batch:
                    cursor.executemany(
                        'INSERT OR REPLACE INTO adsh_lookup VALUES (?, ?, ?, ?, ?)',
                        batch
                    )
                    conn.commit()
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX idx_adsh ON adsh_lookup(adsh)')
    conn.commit()
    
    # Get count
    cursor.execute('SELECT COUNT(*) FROM adsh_lookup')
    count = cursor.fetchone()[0]
    print(f"Built SQLite lookup table with {count} entries")
    
    conn.close()

def process_num_files_streaming(input_dir, output_dir, adsh_lookup, chunk_size):
    """
    Process all num.tsv files in chunks, merging with ticker data and writing
    directly to final ticker files without intermediate storage.
    """
    # Define the final columns we want
    selected_columns = ["adsh", "tag", "ddate", "qtrs", "value", "dimn"]
    final_columns = ["ticker", "form", "cik", "adsh", "tag", "ddate", "qtrs", "value", "dimn", "filed"]
    
    # Find all num.tsv files
    num_files = []
    for subdir, _, files in os.walk(input_dir):
        for file in files:
            if file.lower() == "num.tsv":
                num_files.append(os.path.join(subdir, file))
    
    if not num_files:
        print(f"No num.tsv files found in {input_dir}")
        return
    
    # Initialize ticker file writers
    ticker_writers = {}
    ticker_files = {}
    
    try:
        # Process each num.tsv file
        for file_path in tqdm(num_files, desc="Processing num files"):
            process_single_num_file(
                file_path, output_dir, adsh_lookup, selected_columns, 
                final_columns, ticker_writers, ticker_files, chunk_size
            )
    
    finally:
        # Close all file handles
        for file_handle in ticker_files.values():
            file_handle.close()

def process_single_num_file(file_path, output_dir, adsh_lookup, selected_columns, 
                           final_columns, ticker_writers, ticker_files, chunk_size):
    """Process a single num.tsv file in chunks."""
    
    # Read header
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
    
    # Find column indices
    col_indices = {}
    for col in selected_columns:
        if col in header:
            col_indices[col] = header.index(col)
    
    # Process file in chunks
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        
        chunk = []
        for row in reader:
            chunk.append(row)
            
            if len(chunk) >= chunk_size:
                process_chunk(chunk, col_indices, adsh_lookup, final_columns, 
                            output_dir, ticker_writers, ticker_files)
                chunk = []
        
        # Process remaining rows
        if chunk:
            process_chunk(chunk, col_indices, adsh_lookup, final_columns, 
                        output_dir, ticker_writers, ticker_files)

def process_chunk(chunk, col_indices, adsh_lookup, final_columns, 
                 output_dir, ticker_writers, ticker_files):
    """Process a chunk of rows and write to appropriate ticker files."""
    
    # Group rows by ticker
    ticker_groups = defaultdict(list)
    
    for row in chunk:
        # Extract data from row
        row_data = {}
        for col, idx in col_indices.items():
            if idx < len(row):
                row_data[col] = row[idx]
        
        # Get adsh and lookup ticker info
        adsh = row_data.get('adsh', '').strip()
        ticker_info = adsh_lookup.get(adsh, {})
        
        if ticker_info.get('ticker'):  # Only process if we have a ticker
            # Create final row
            final_row = {
                'ticker': ticker_info.get('ticker', ''),
                'form': ticker_info.get('form', ''),
                'cik': ticker_info.get('cik', ''),
                'adsh': adsh,
                'tag': row_data.get('tag', ''),
                'ddate': row_data.get('ddate', ''),
                'qtrs': row_data.get('qtrs', ''),
                'value': row_data.get('value', ''),
                'dimn': row_data.get('dimn', ''),
                'filed': ticker_info.get('filed', '')
            }
            
            ticker = ticker_info['ticker']
            ticker_groups[ticker].append(final_row)
    
    # Write grouped data to ticker files
    for ticker, rows in ticker_groups.items():
        if ticker not in ticker_writers:
            # Create new ticker file
            file_path = os.path.join(output_dir, f"{ticker}.tsv")
            file_handle = open(file_path, 'w', newline='', encoding='utf-8')
            writer = csv.DictWriter(file_handle, fieldnames=final_columns, delimiter='\t')
            writer.writeheader()
            
            ticker_writers[ticker] = writer
            ticker_files[ticker] = file_handle
        
        # Write rows
        ticker_writers[ticker].writerows(rows) 

def process_num_files_with_sqlite(input_dir, output_dir, db_path, chunk_size):
    """Process num files using SQLite lookup table."""
    # Define the final columns we want
    selected_columns = ["adsh", "tag", "ddate", "qtrs", "value", "dimn"]
    final_columns = ["ticker", "form", "cik", "adsh", "tag", "ddate", "qtrs", "value", "dimn", "filed"]
    
    # Find all num.tsv files
    num_files = []
    for subdir, _, files in os.walk(input_dir):
        for file in files:
            if file.lower() == "num.tsv":
                num_files.append(os.path.join(subdir, file))
    
    if not num_files:
        print(f"No num.tsv files found in {input_dir}")
        return
    
    # Initialize ticker file writers
    ticker_writers = {}
    ticker_files = {}
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Process each num.tsv file
        for file_path in tqdm(num_files, desc="Processing num files with SQLite"):
            process_single_num_file_with_sqlite(
                file_path, output_dir, cursor, selected_columns, 
                final_columns, ticker_writers, ticker_files, chunk_size
            )
    
    finally:
        # Close all file handles and database connection
        for file_handle in ticker_files.values():
            file_handle.close()
        conn.close()

def process_single_num_file_with_sqlite(file_path, output_dir, cursor, selected_columns, 
                                       final_columns, ticker_writers, ticker_files, chunk_size):
    """Process a single num.tsv file using SQLite lookup."""
    
    # Read header
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
    
    # Find column indices
    col_indices = {}
    for col in selected_columns:
        if col in header:
            col_indices[col] = header.index(col)
    
    # Process file in chunks
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        
        chunk = []
        for row in reader:
            chunk.append(row)
            
            if len(chunk) >= chunk_size:
                process_chunk_with_sqlite(chunk, col_indices, cursor, final_columns, 
                                        output_dir, ticker_writers, ticker_files)
                chunk = []
        
        # Process remaining rows
        if chunk:
            process_chunk_with_sqlite(chunk, col_indices, cursor, final_columns, 
                                    output_dir, ticker_writers, ticker_files)

def process_chunk_with_sqlite(chunk, col_indices, cursor, final_columns, 
                             output_dir, ticker_writers, ticker_files):
    """Process a chunk of rows using SQLite lookup."""
    
    # Group rows by ticker
    ticker_groups = defaultdict(list)
    
    for row in chunk:
        # Extract data from row
        row_data = {}
        for col, idx in col_indices.items():
            if idx < len(row):
                row_data[col] = row[idx]
        
        # Get adsh and lookup ticker info from SQLite
        adsh = row_data.get('adsh', '').strip()
        if adsh:
            cursor.execute('SELECT ticker, form, cik, filed FROM adsh_lookup WHERE adsh = ?', (adsh,))
            result = cursor.fetchone()
            
            if result and result[0]:  # Only process if we have a ticker
                ticker, form, cik, filed = result
                
                # Create final row
                final_row = {
                    'ticker': ticker,
                    'form': form,
                    'cik': cik,
                    'adsh': adsh,
                    'tag': row_data.get('tag', ''),
                    'ddate': row_data.get('ddate', ''),
                    'qtrs': row_data.get('qtrs', ''),
                    'value': row_data.get('value', ''),
                    'dimn': row_data.get('dimn', ''),
                    'filed': filed
                }
                
                ticker_groups[ticker].append(final_row)
    
    # Write grouped data to ticker files
    for ticker, rows in ticker_groups.items():
        if ticker not in ticker_writers:
            # Create new ticker file
            file_path = os.path.join(output_dir, f"{ticker}.tsv")
            file_handle = open(file_path, 'w', newline='', encoding='utf-8')
            writer = csv.DictWriter(file_handle, fieldnames=final_columns, delimiter='\t')
            writer.writeheader()
            
            ticker_writers[ticker] = writer
            ticker_files[ticker] = file_handle
        
        # Write rows
        ticker_writers[ticker].writerows(rows) 