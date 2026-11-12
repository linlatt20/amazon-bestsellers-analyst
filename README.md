# Kyobobook Bestseller Analysis

Analyze a Kyobobook (교보문고) bestseller list with Python and pandas.

## Setup

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```powershell
python analyze.py data/sample_bestsellers.csv --as-of 2026-11-12
```

The script prints the analysis and writes result tables to `output/`.

## CSV format

| Column | Example | Notes |
| --- | --- | --- |
| rank | 1 | Bestseller rank |
| title | 조용한 계절의 끝 | |
| author | 김하린 | |
| publisher | 푸른숲길 | |
| pub_date | 2026-09-15 | Any date format pandas can parse |
| list_price | 17,800원 | Commas and 원 are stripped |
| sale_price | 16,020원 | |
| category | 소설 | |
| rating | 9.6 | Kyobobook rating (out of 10) |
| review_count | 1284 | |

UTF-8 and CP949 (Korean Excel) encodings both work.

> **`data/sample_bestsellers.csv` contains made-up data** (fictional titles, authors and publishers) so the script runs out of the box. Replace it with a real Kyobobook list for actual results.

## Analysis

1. Overview: counts, average price and rating
2. Top N bestsellers
3. Category breakdown: count, share, best/average rank, price, rating, reviews
4. Publishers and authors with more than one bestseller
5. Price and discount statistics, price by rank band
6. New releases vs. steady sellers (by time since publication)
7. Spearman correlation of rank with rating, reviews, price, discount and book age
