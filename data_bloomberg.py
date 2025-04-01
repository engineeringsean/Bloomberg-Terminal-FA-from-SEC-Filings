# data_bloomberg.py

import os
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def transform_all_tickers(input_dir, output_dir):
    """
    Read every .tsv in `input_dir`, transform, and save resulting
    annual and quarterly .tsv files in `output_dir` with columns
    that match the new DB schema.
    """
    # Ensure output_dir exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Gather the TSV filenames we want to process
    tsv_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".tsv")]

    for filename in tqdm(tsv_files, desc="Processing TSV files", unit="file"):
        input_path = os.path.join(input_dir, filename)
        ticker_name = os.path.splitext(filename)[0]
        
        process_single_ticker_tsv(input_path, output_dir, ticker_name)


def process_single_ticker_tsv(input_path, output_dir, ticker):
    """
    Read one ticker's TSV file, drop duplicates, split into annual (qtrs=4)
    and quarterly (qtrs=1) data (plus qtrs=0 rows), pivot, and save results
    with underscore-lowercase column names.
    """
    df = pd.read_csv(input_path, sep="\t", dtype=str).drop_duplicates()

    # Convert relevant columns
    for col in ["qtrs", "ddate", "filed"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    
    # Ensure price is numeric
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
    else:
        df["price"] = float('nan')

    # Helper mappings
    def map_annual_col(ddate):
        """
        Given an integer ddate like 20200930, return 'fy_2020', 'fy_2021', etc.
        only if year is in 2020..2025.
        """
        year_str = str(ddate)[:4]
        if year_str in ["2020", "2021", "2022", "2023", "2024", "2025"]:
            return f"fy_{year_str}"
        return None

    def map_quarter_col(ddate):
        """
        Given an integer ddate like 20210331, return 'q1_2021', 'q2_2021', etc.,
        only if year in 2020..2025.
        """
        year_str = str(ddate)[:4]
        if year_str not in ["2020", "2021", "2022", "2023", "2024", "2025"]:
            return None

        month_str = str(ddate)[4:6]
        try:
            month = int(month_str)
        except ValueError:
            return None

        if 1 <= month <= 3:
            q = 1
        elif 4 <= month <= 6:
            q = 2
        elif 7 <= month <= 9:
            q = 3
        else:
            q = 4

        return f"q{q}_{year_str}"

    def find_earliest_adsh_for_ddate(subset_df, ddate):
        """
        Return the 'adsh' of the earliest-filed record whose filed >= ddate.
        """
        candidates = subset_df[(subset_df["ddate"] == ddate) & (subset_df["filed"] >= ddate)]
        if candidates.empty:
            return ""
        earliest = candidates.sort_values(by="filed", ascending=True).iloc[0]
        return earliest["adsh"] if pd.notnull(earliest["adsh"]) else ""

    def build_pivot_table(subset_df, col_namer, desired_columns, period_label, ticker_name):
        """
        1) Determine which column each row belongs in via col_namer().
        2) Pivot by 'tag' -> col_name, filling with 'value'.
        3) Insert special rows for 'period_label', 'FilingNumber', and 'SharePriceAfterFiledDate'.
        4) Reorder pivot's rows and columns, add 'ticker' column.
        """
        subset_df = subset_df.copy()
        subset_df["col_name"] = subset_df["ddate"].apply(col_namer)
        subset_df = subset_df[subset_df["col_name"].notna()]

        pivot = subset_df.pivot_table(
            index="tag",
            columns="col_name",
            values="value",
            aggfunc="first"
        )

        if pivot.empty or pivot.columns.empty:
            empty_cols = ["in_usd"] + desired_columns
            empty_df = pd.DataFrame(columns=empty_cols)
            empty_df.insert(0, "ticker", ticker_name)
            return empty_df

        # For each column in pivot, store the maximum ddate for earliest-adsh logic
        max_ddates = subset_df.groupby("col_name")["ddate"].max().to_dict()

        # Build row for period_label and FilingNumber
        ddate_values = {}
        adsh_values = {}
        for col in pivot.columns:
            official_ddate = max_ddates[col]
            ddate_values[col] = str(official_ddate)
            adsh_values[col] = find_earliest_adsh_for_ddate(subset_df, official_ddate)

        pivot.loc[period_label] = ddate_values
        pivot.loc["FilingNumber"] = adsh_values

        # Insert a row for Share Price
        share_price_values = {}
        for col in pivot.columns:
            col_adsh = adsh_values[col]
            if not col_adsh:
                share_price_values[col] = float('nan')
                continue
            matching = subset_df[subset_df["adsh"] == col_adsh]
            if matching.empty:
                share_price_values[col] = float('nan')
            else:
                share_price_values[col] = matching["price"].iloc[0]

        pivot.loc["SharePriceAfterFiledDate"] = share_price_values

        # Reorder pivot index so special rows are at the top
        new_index = [
            period_label,
            "FilingNumber",
            "SharePriceAfterFiledDate"
        ] + [ix for ix in pivot.index if ix not in (period_label, "FilingNumber", "SharePriceAfterFiledDate")]
        pivot = pivot.reindex(new_index)

        # Reindex columns in the desired order
        pivot = pivot.reindex(columns=desired_columns)

        # Move the old index "tag" into a column named "in_usd"
        pivot.reset_index(inplace=True)
        pivot.rename(columns={"tag": "in_usd"}, inplace=True)

        # Insert "ticker" column
        pivot.insert(0, "ticker", ticker_name)

        return pivot

    # -------------------------
    # ANNUAL FILE (qtrs=4 + qtrs=0)
    # -------------------------
    annual_ddates = df.loc[df["qtrs"] == 4, "ddate"].unique()
    annual_df = df.loc[
        (df["qtrs"] == 4) |
        ((df["qtrs"] == 0) & (df["ddate"].isin(annual_ddates)))
    ].copy()

    if not annual_df.empty:
        annual_cols = [f"fy_{yr}" for yr in ["2020", "2021", "2022", "2023", "2024", "2025"]]
        annual_pivot = build_pivot_table(
            annual_df,
            map_annual_col,
            annual_cols,
            period_label="12 Months Ending",
            ticker_name=ticker
        )
        annual_outfile = os.path.join(output_dir, f"{ticker}_annual.tsv")
        annual_pivot.to_csv(annual_outfile, sep="\t", index=False)

    # -------------------------
    # QUARTERLY FILE (qtrs=1 + qtrs=0)
    # -------------------------
    quarterly_ddates = df.loc[df["qtrs"] == 1, "ddate"].unique()
    quarterly_df = df.loc[
        (df["qtrs"] == 1) |
        ((df["qtrs"] == 0) & (df["ddate"].isin(quarterly_ddates)))
    ].copy()

    if not quarterly_df.empty:
        qtr_cols = []
        for y in ["2020", "2021", "2022", "2023", "2024", "2025"]:
            for q in [1, 2, 3, 4]:
                qtr_cols.append(f"q{q}_{y}")
        
        quarterly_pivot = build_pivot_table(
            quarterly_df,
            map_quarter_col,
            qtr_cols,
            period_label="3 Months Ending",
            ticker_name=ticker
        )
        quarterly_outfile = os.path.join(output_dir, f"{ticker}_quarterly.tsv")
        quarterly_pivot.to_csv(quarterly_outfile, sep="\t", index=False)

