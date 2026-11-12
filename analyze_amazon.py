import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "name", "author", "user_rating", "reviews",
    "price", "year", "genre",
]

def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: 
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    return df


df = load_csv("data/amazon_bestsellers.csv")


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")

# Section 1 - 개요 출력

section("1. Overview")
paid = df[df["price"] > 0]
print("Rows:", len(df), " | Unique books:", df["name"].nunique(), " | Authors:", df["author"].nunique(), 
      "\nAvg rating: %.2f" %df["user_rating"].mean(), " | Avg price (excluding $0): %.2f" %paid["price"].mean(), "\n\n")

# Section 2 - 장르별 추세

section("2. Fiction vs Non-Fiction")
by_genre = paid.groupby("genre").agg(
    books=("name", "count"),
    avg_price=("price", "mean"),
    avg_rating=("user_rating", "mean"),
    total_reviews=("reviews", "sum")
) 
print(by_genre.round(2))

# Section 3 - 가장 오래 베스트 셀러였던 책과 저자 

section("3. Most Frequent books & authors")
top_books = df["name"].value_counts().head(10)
top_authors = df["author"].value_counts().head(5)
print(top_books)
print(top_authors)