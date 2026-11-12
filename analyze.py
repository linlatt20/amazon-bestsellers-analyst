"""Analyze a Kyobobook bestseller list exported to CSV.

Usage:
    python analyze.py data/sample_bestsellers.csv
    python analyze.py my_list.csv --as-of 2026-11-12 --top 10
"""

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "rank", "title", "author", "publisher", "pub_date",
    "list_price", "sale_price", "category", "rating", "review_count",
]


def load_csv(path: Path) -> pd.DataFrame:
    """Read the CSV, trying UTF-8 first and then CP949 (Korean Excel default)."""
    for encoding in ("utf-8-sig", "cp949"):
        try:
            df = pd.read_csv(path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Could not decode {path} as UTF-8 or CP949")

    df.columns = df.columns.str.strip().str.lower()
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")
    return df


def to_number(series: pd.Series) -> pd.Series:
    """'16,020원' -> 16020. Non-numeric values become NaN."""
    cleaned = series.astype(str).str.replace(r"[^\d.]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def clean(df: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    df = df.copy()
    for col in ("rank", "list_price", "sale_price", "rating", "review_count"):
        df[col] = to_number(df[col])
    df["pub_date"] = pd.to_datetime(df["pub_date"], errors="coerce")
    for col in ("title", "author", "publisher", "category"):
        df[col] = df[col].astype(str).str.strip()

    df["discount_rate"] = (1 - df["sale_price"] / df["list_price"]) * 100
    df["days_since_pub"] = (as_of - df["pub_date"]).dt.days
    df["rank_band"] = pd.cut(
        df["rank"], bins=[0, 10, 20, float("inf")], labels=["1-10", "11-20", "21+"]
    )
    return df.sort_values("rank").reset_index(drop=True)


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def analyze(df: pd.DataFrame, top: int) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}

    section("1. Overview")
    print(f"Books: {len(df)}")
    print(f"Categories: {df['category'].nunique()}  |  "
          f"Publishers: {df['publisher'].nunique()}  |  "
          f"Authors: {df['author'].nunique()}")
    print(f"Avg sale price: {df['sale_price'].mean():,.0f}원  |  "
          f"Avg rating: {df['rating'].mean():.2f}")

    section(f"2. Top {top} bestsellers")
    print(df.head(top)[["rank", "title", "author", "category", "sale_price"]]
          .to_string(index=False))

    section("3. Books by category")
    by_category = (
        df.groupby("category")
        .agg(books=("title", "count"),
             best_rank=("rank", "min"),
             avg_rank=("rank", "mean"),
             avg_price=("sale_price", "mean"),
             avg_rating=("rating", "mean"),
             total_reviews=("review_count", "sum"))
        .sort_values(["books", "avg_rank"], ascending=[False, True])
    )
    by_category["share_%"] = by_category["books"] / len(df) * 100
    print(by_category.round(1).to_string())
    results["by_category"] = by_category

    section("4. Publishers and authors with multiple bestsellers")
    by_publisher = (
        df.groupby("publisher")
        .agg(books=("title", "count"), best_rank=("rank", "min"))
        .sort_values(["books", "best_rank"], ascending=[False, True])
    )
    by_author = (
        df.groupby("author")
        .agg(books=("title", "count"), titles=("title", " / ".join))
        .sort_values("books", ascending=False)
    )
    print("Publishers:\n" + by_publisher[by_publisher["books"] > 1].to_string())
    print("\nAuthors:\n" + by_author[by_author["books"] > 1].to_string())
    results["by_publisher"] = by_publisher
    results["by_author"] = by_author

    section("5. Price and discount")
    print(df[["list_price", "sale_price", "discount_rate"]].describe().round(1).to_string())
    print("\nAverage sale price by rank band:")
    print(df.groupby("rank_band", observed=True)["sale_price"].mean().round(0).to_string())

    section("6. New releases vs. steady sellers")
    df_age = df.dropna(subset=["days_since_pub"])
    age_bands = pd.cut(
        df_age["days_since_pub"],
        bins=[-1, 90, 365, float("inf")],
        labels=["<= 3 months", "3-12 months", "> 1 year"],
    )
    by_age = df_age.groupby(age_bands, observed=True).agg(
        books=("title", "count"), avg_rank=("rank", "mean"),
        avg_reviews=("review_count", "mean"))
    print(by_age.round(1).to_string())
    results["by_age"] = by_age

    section("7. What correlates with a better rank?")
    print("(Spearman; negative = higher value goes with a better/smaller rank)")
    numeric = df[["rank", "rating", "review_count", "sale_price", "discount_rate", "days_since_pub"]]
    # Constant columns (e.g. the flat 10% discount under 도서정가제) have no correlation
    numeric = numeric.loc[:, numeric.nunique() > 1]
    corr = (
        numeric.corr(method="spearman")["rank"]
        .drop("rank")
        .round(2)
        .to_frame("corr_with_rank")
    )
    print(corr.to_string())
    results["rank_correlation"] = corr

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", type=Path, help="Bestseller CSV file")
    parser.add_argument("--as-of", default=None,
                        help="Date of the list (YYYY-MM-DD); defaults to today")
    parser.add_argument("--top", type=int, default=10, help="How many top books to show")
    parser.add_argument("--out", type=Path, default=Path("output"),
                        help="Folder for result CSVs")
    args = parser.parse_args()

    as_of = pd.Timestamp(args.as_of) if args.as_of else pd.Timestamp.today().normalize()
    df = clean(load_csv(args.csv), as_of)
    results = analyze(df, args.top)

    args.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out / "cleaned.csv", index=False, encoding="utf-8-sig")
    for name, table in results.items():
        table.to_csv(args.out / f"{name}.csv", encoding="utf-8-sig")
    print(f"\nSaved {len(results) + 1} CSV files to {args.out.resolve()}")


if __name__ == "__main__":
    main()
