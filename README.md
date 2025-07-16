# Bloomberg-Terminal-FA-from-SEC-Filings
 Uses SEC Financial Datasets and Filings to create Bloomberg-Style Financial Analysis Tables. Similar to what Yahoo Finance offers members for a $10 per month subscription.

**Transform SEC Financial Datasets into Bloomberg-Style KPI Tables with Integrated Price Data**

---

## 📄 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [Example Input & Output Data](#-example-input-output-data)
  - [Ticker-Based Data Example](#-ticker-based-data-example)
  - [Bloomberg-Style Annual Table](#-bloomberg-style-annual-table)
  - [Sample Screenshots](#-sample-screenshots)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Usage](#-usage)
- [Advanced Setup](#-advanced-setup)
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

![Sample Screenshot of Bloomberg-Style Table](https://github.com/engineeringsean/Bloomberg-Terminal-FA-from-SEC-Filings/blob/main/docs/assets/Bloomberg%20Terminal%20MSFT%20BS%20Example.PNG)

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
<a name="-example-input-output-data"></a>
## 🗼️ Example Input & Output Data

### 📄 Raw SEC Dataset Example

```
adsh	tag	version	ddate	qtrs	uom	dimh	iprx	value	footnote	footlen	dimn	coreg	durp	datp	dcml
0000320193-20-000096	Revenues	us-gaap/2020	20200930	4	USD	0xdd6adf652c868566bcc414c4acaf7af9	0	274515000000		0	3		0.021918058	4.0	-6
0000320193-21-000010	Revenues	us-gaap/2020	20201231	1	USD	0xb8ba6a9ef479afc51e87d63625c7949d	0	111439000000		0	3		0.013698995	5.0	-6
```

### 📄 Ticker-Based Data Example

```
ticker    form     cik       adsh                    tag         ddate       value         filed      price
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

#### Raw SEC Dataset Screenshot

<img 
  src="https://github.com/engineeringsean/Bloomberg-Terminal-FA-from-SEC-Filings/blob/main/docs/assets/SEC%20Financial%20Data%20Sets%20Example.PNG" 
  alt="Raw SEC Dataset Screenshot" 
  width="600" 
/>

#### Ticker-Based TSV Screenshot

<img 
  src="https://github.com/engineeringsean/Bloomberg-Terminal-FA-from-SEC-Filings/blob/main/docs/assets/Ticker-Based%20MSFT%20Example.PNG" 
  alt="Ticker-Based TSV Screenshot" 
  width="600" 
/>

#### Bloomberg-Style Table Screenshot

<img 
  src="https://github.com/engineeringsean/Bloomberg-Terminal-FA-from-SEC-Filings/blob/main/docs/assets/Bloomberg%20Terminal%20MSFT%20BS%20Example.PNG" 
  alt="Bloomberg-Style Table Screenshot" 
  width="600" 
/>

---

## 🚀 How It Works

### ⚡ Ultra-Efficient Streaming Processing (NEW!)
The pipeline now uses a revolutionary streaming approach that processes all data in a single pass:

**Memory-Efficient Mode (Default):**
- Builds in-memory lookup table for ticker mappings
- Processes num.tsv files in chunks without loading entire datasets
- Writes directly to final ticker format
- **50-80% faster** than the old approach
- **60-90% less memory usage**

**Database-Backed Mode (For Extremely Large Datasets):**
- Uses SQLite for ticker lookup table
- Handles datasets too large for memory
- Slightly slower but uses minimal RAM
- Perfect for processing years of SEC data

### 1. Build Ticker Lookup Table
- Streams through all `sub.tsv` files to create adsh → ticker mapping
- Fetches SEC ticker mappings from official source
- Creates efficient lookup structure

### 2. Process Num Files Directly to Final Format
- Streams through all `num.tsv` files in chunks
- Merges with ticker data on-the-fly
- Writes directly to per-ticker files
- **No intermediate files created**

### 3. Add Price Data (Optional)
- Uses **Charles Schwab Market Data API** to fetch price data **the day after filing date**
- Avoids look-ahead bias by only using publicly available price after filing

### 4. Format Like Bloomberg Terminal
- Transforms and pivots data into a **Bloomberg-style statement format**
- Separates into **Annual** and **Quarterly** financial tables
- Adds price data & filing IDs alongside financial metrics

---
<a name="-installation"></a>
## ⚙️ Installation

1. Clone this repo:
```bash
git clone https://github.com/engineeringsean/bloomberg-terminal-fa-from-sec-filings.git
cd bloomberg-terminal-fa-from-sec-filings
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
├── Final_Ticker_Files/          # Direct output (no intermediate files!)
├── Ticker_With_Price/           # Only if price data is added
└── Bloomberg_Style_Tables/      # Final Bloomberg-style tables
```

### 🚀 Performance Improvements

The new streaming approach provides significant improvements:

| Metric | Old Approach | New Approach | Improvement |
|--------|-------------|--------------|-------------|
| **Processing Steps** | 5 separate steps | 2 steps | 60% fewer steps |
| **Intermediate Files** | 3 large files | 0 | 100% reduction |
| **Memory Usage** | High (loads all data) | Low (chunk-based) | 60-90% reduction |
| **Processing Speed** | Slower (multiple I/O) | Faster (single pass) | 50-80% faster |
| **Disk Space** | High (intermediate files) | Low (direct output) | 70-80% reduction |

**Run the performance comparison:**
```bash
python performance_comparison.py
```

---
<a name="-advanced-setup"></a>
## 🗃️ Advanced Setup

**Database & API Layer (Coming Soon)**  
This project was built to support dynamic querying via:

- PostgreSQL Database
- Django REST API
- React Frontend

Once properly documented, these components will be source-available in this repository as well.

---

## 📚 SEC Data Sources

- [SEC Financial Notes and Datasets](https://www.sec.gov/data-research/sec-markets-data/financial-statement-notes-data-sets)
- [SEC Ticker-CIK Mapping](https://www.sec.gov/include/ticker.txt)

---

## 🌐 Future Roadmap

- [ ] Publicly accessible Bloomberg-Style Tables via website
- [ ] Document Database + API + React app on Github
- [ ] Add sample PostgreSQL schema & migrations
- [ ] Add Dockerized deployment

---

## 🧑‍💻 About

Built by a data engineer to make SEC data **actually usable for financial analysts, quants, and backtesters**.  
If you've ever been frustrated with raw financial datasets — this is for you.


