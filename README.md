# Bloomberg-Terminal-FA-from-SEC-Filings
 Uses SEC Financial Datasets and Filings to create Bloomberg-Style Financial Analysis Tables. Similar to what Yahoo Finance offers members for a $10 per month subscription.

**Transform SEC Financial Datasets into Bloomberg-Style KPI Tables with Integrated Price Data**

---

## 📄 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Example Output](#-example-output)
  - [Ticker-Based Raw Data Example](#-ticker-based-raw-data-example)
  - [Bloomberg-Style Annual Table](#-bloomberg-style-annual-table)
  - [Sample Screenshots](#-sample-screenshots)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Usage](#-usage)
- [Optional Advanced Setup](#-optional-advanced-setup)
- [SEC Data Sources](#-sec-data-sources)
- [Future Roadmap](#-future-roadmap)
- [About](#-about)

---

## 🗉 Project Overview

This project automates the tedious, time-consuming process of preparing company financial data from the U.S. Securities and Exchange Commission (SEC) into a **clean, user-friendly, analysis-ready format**.

**Source Problem**  
SEC financial datasets are published as a messy collection of `.tsv` files, often split into `num.tsv` (financial metrics) and `sub.tsv` (submission metadata). These datasets:
- Lack ticker symbols
- Contain extraneous metadata
- Are difficult to query or backtest due to missing price data and chronological structure

**Solution**  
This pipeline:
1. **Merges & cleans raw SEC `.tsv` files**
2. **Maps SEC CIK numbers to stock tickers**
3. **Splits data into per-ticker `.tsv` files**
4. **Enriches data with price history via Charles Schwab's Market Data API**
5. **Structures the output to mimic Bloomberg Terminal financial statement tables**
6. Integrates with a **PostgreSQL database + Django API + React frontend** *(code not yet included in this repo)*

---

## 🔥 Features

👉 Combines `num.tsv` & `sub.tsv` filings  
👉 Adds Ticker Symbols using SEC CIK mappings  
👉 Splits data into clean, ticker-based `.tsv` files  
👉 Enriches data with **Price Data (No Lookahead Bias)**  
👉 Outputs **Annual & Quarterly Financial Statement Tables**  
👉 Bloomberg-style formatting ready for KPI calculations & backtesting  
👉 Scalable and production-ready for large datasets

---

## 🗼️ Example Output

### 📄 Ticker-Based Raw Data Example

```
ticker    form     cik       adsh               tag         ddate      value      filed     price
AAPL      10-K     320193    0000320193-20-000096    Revenues    20200930    274515000000  20201030   110.44
AAPL      10-Q     320193    0000320193-21-000010    Revenues    20201231    111439000000  20210128   135.12
```

### 📊 Bloomberg-Style Annual Table

| ticker | in_usd               | fy_2020       | fy_2021       | fy_2022       |
|------|----------------------|---------------|---------------|---------------|
| AAPL | 12 Months Ending    | 20200930      | 20210930      | 20220930      |
| AAPL | FilingNumber       | 0000320193-20-000096 | 0000320193-21-000010 | 0000320193-22-000090 |
| AAPL | SharePriceAfterFiledDate | 110.44        | 135.12        | 140.78        |
| AAPL | Revenues           | 274515000000  | 365817000000  | 394328000000  |
| AAPL | NetIncome          | 57411000000   | 94680000000   | 99803000000   |

*(Sample data — illustrative only)*

### 📷 Sample Screenshots

#### Raw Per-Ticker TSV Example

![Raw Ticker TSV Example](https://raw.githubusercontent.com/yourusername/sec-financial-transformer/main/assets/ticker_tsv_example.png)

#### Bloomberg-Style Table Screenshot

![Sample Screenshot of Bloomberg-Style Table](https://raw.githubusercontent.com/yourusername/sec-financial-transformer/main/assets/sample_table.png)

---

## 🚀 How It Works

### 1. Combine SEC TSV Files
- Merges multiple `num.tsv` and `sub.tsv` files into single consolidated files.
- Filters only relevant columns to reduce noise.

### 2. Add Ticker Information
- Cross-references **CIK Numbers** with **SEC's Ticker Mapping**
- Adds stock tickers to each row of financial data

### 3. Split By Ticker
- Breaks down merged dataset into individual `.tsv` files by ticker symbol

### 4. Add Price Data
- Uses **Charles Schwab Market Data API** to fetch price data **the day after filing date**
- Avoids look-ahead bias by only using publicly available price after filing

### 5. Format Like Bloomberg Terminal
- Transforms and pivots data into a **Bloomberg-style statement format**
- Separates into **Annual** and **Quarterly** financial tables
- Adds price data & filing IDs alongside financial metrics

---

## ⚙️ Installation

1. Clone this repo:
```bash
git clone https://github.com/yourusername/sec-financial-transformer.git
cd sec-financial-transformer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Schwab API credentials in `config.env`:
```
APP_KEY=your_schwab_app_key
APP_SECRET=your_schwab_app_secret
REDIRECT_URI=your_redirect_uri
ACCESS_TOKEN=
REFRESH_TOKEN=
LAST_TOKEN_TIME=
```

---

## 🚦 Usage

Place your raw SEC `.tsv` files in the `data/input_data/` directory in subfolders.  
Then run:

```bash
python main.py
```

All output files will be saved in:

```
data/output_data/
├── combined_num.tsv
├── combined_sub.tsv
├── updated_combined_num.tsv
├── Ticker_Split/
├── Ticker_With_Price/
├── Final_Ticker_Files/
└── Bloomberg_Style_Tables/
```

---

## 🗃️ Optional Advanced Setup

**Database & API Layer (Coming Soon)**  
This project was built to support dynamic querying via:

- PostgreSQL Database
- Django REST API
- React Frontend

Once properly documented, these components will be open-sourced in this repository as well.

---

## 📚 SEC Data Sources

- [SEC Financial Notes and Datasets](https://www.sec.gov/dera/data/financial-statement-data-sets.html)
- [SEC Ticker-CIK Mapping](https://www.sec.gov/include/ticker.txt)

---

## 🌐 Future Roadmap

- [ ] Add Dockerized deployment
- [ ] Integrate Database + API + React app
- [ ] Add sample PostgreSQL schema & migrations
- [ ] Provide Jupyter Notebook for quick KPI analysis
- [ ] Optional cloud deployment guide

---

## 🧑‍💻 About

Built by a data engineer to make SEC data **actually usable for financial analysts, quants, and backtesters**.  
If you've ever been frustrated with raw financial datasets — this is for you.


