"""
Preprocessing script for Canada Food Pulse.

Reads:  data/processed/yelp_business_data_cleaned.csv  (104,665 rows × 18 cols)
Writes:
  - data/processed/df_businesses.csv      (1 row per business, ~23k rows)
  - data/processed/df_cuisine_stats.csv   (cuisine × city aggregates)
  - data/processed/df_peak_heatmap.csv    (city-level weekday × hour heatmap)

Run from the project root:
    python scripts/preprocess.py
"""

import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "data" / "processed" / "yelp_business_data_cleaned.csv"
OUT = ROOT / "data" / "processed"

# Actual cuisine / food-type categories — excludes generic segments like
# "Restaurants", "Food", "Bars", "Coffee & Tea", "Cafes", "Nightlife", etc.
FOOD_CATEGORIES = {
    # Cuisines by origin
    "Italian",
    "Chinese",
    "Mexican",
    "Japanese",
    "Thai",
    "Indian",
    "French",
    "Greek",
    "Mediterranean",
    "Vietnamese",
    "Korean",
    "American (Traditional)",
    "American (New)",
    "Middle Eastern",
    "Lebanese",
    "African",
    "Caribbean",
    "Latin American",
    "Spanish",
    "Pakistani",
    "Sri Lankan",
    "Filipino",
    "Himalayan/Nepalese",
    "Persian/Iranian",
    "Turkish",
    "Ethiopian",
    "Taiwanese",
    "Cantonese",
    "Szechuan",
    "Hong Kong Style Cafe",
    # Food types / formats
    "Seafood",
    "Steakhouses",
    "Sushi Bars",
    "Burgers",
    "Sandwiches",
    "Pizza",
    "Bakeries",
    "Breakfast & Brunch",
    "Diners",
    "Delis",
    "Tapas Bars",
    "Tapas/Small Plates",
    "Noodles",
    "Ramen",
    "Hot Pot",
    "Dim Sum",
    "Chicken Wings",
    "Barbeque",
    "Soup",
    "Waffles",
    "Poutineries",
    "Creperies",
    "Fondue",
    "Soul Food",
    "Comfort Food",
}

WEEKDAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load_source() -> pd.DataFrame:
    print(f"Loading {SRC} ...")
    df = pd.read_csv(SRC, low_memory=False)
    print(f"  Loaded {len(df):,} rows")
    return df


# ---------------------------------------------------------------------------
# df_businesses.csv — 1 row per business
# ---------------------------------------------------------------------------

def build_businesses(df: pd.DataFrame) -> pd.DataFrame:
    print("Building df_businesses ...")

    business_cols = [
        "business_id", "name", "neighborhood", "address", "city",
        "state", "postal_code", "latitude", "longitude", "stars",
        "review_count", "is_open", "categories", "city_clean",
    ]

    # Deduplicate: keep first occurrence for static fields
    df_biz = df[business_cols].drop_duplicates(subset="business_id").copy()

    # Total checkins across all weekdays per business
    checkins_total = (
        df.groupby("business_id")["total_checkins"]
        .sum()
        .reset_index()
        .rename(columns={"total_checkins": "total_checkins_all"})
    )

    # Overall peak hour = mode across weekdays (most common peak hour)
    def safe_mode(s):
        m = s.dropna().mode()
        return m.iloc[0] if len(m) > 0 else np.nan

    peak_mode = (
        df.groupby("business_id")["peak_hour"]
        .agg(safe_mode)
        .reset_index()
        .rename(columns={"peak_hour": "overall_peak_hour"})
    )

    df_biz = df_biz.merge(checkins_total, on="business_id", how="left")
    df_biz = df_biz.merge(peak_mode, on="business_id", how="left")

    # Clean up name column (strip surrounding quotes)
    df_biz["name"] = df_biz["name"].str.strip('"')
    df_biz["address"] = df_biz["address"].str.strip('"')

    print(f"  {len(df_biz):,} unique businesses")
    return df_biz


# ---------------------------------------------------------------------------
# df_cuisine_stats.csv — cuisine × city aggregates
# ---------------------------------------------------------------------------

def build_cuisine_stats(df_biz: pd.DataFrame) -> pd.DataFrame:
    print("Building df_cuisine_stats ...")

    df_exp = df_biz[["business_id", "city_clean", "stars", "review_count", "categories"]].copy()
    df_exp["cuisine"] = df_exp["categories"].str.split(";")
    df_exp = df_exp.explode("cuisine")
    df_exp["cuisine"] = df_exp["cuisine"].str.strip()

    # Filter to food-relevant categories only
    df_exp = df_exp[df_exp["cuisine"].isin(FOOD_CATEGORIES)]

    df_stats = (
        df_exp.groupby(["city_clean", "cuisine"], as_index=False)
        .agg(
            avg_stars=("stars", "mean"),
            total_reviews=("review_count", "sum"),
            business_count=("business_id", "nunique"),
        )
        .round({"avg_stars": 2})
        .sort_values(["city_clean", "total_reviews"], ascending=[True, False])
    )

    print(f"  {len(df_stats):,} cuisine × city rows")
    return df_stats


# ---------------------------------------------------------------------------
# df_peak_heatmap.csv — city-level weekday × hour heatmap
# ---------------------------------------------------------------------------

def build_peak_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    print("Building df_peak_heatmap ...")

    df_heat = (
        df.dropna(subset=["weekday", "peak_hour"])
        .groupby(["city_clean", "weekday", "peak_hour"], as_index=False)
        .agg(total_checkins=("total_checkins", "sum"))
    )

    # Ensure weekday is sorted in calendar order
    df_heat["weekday"] = pd.Categorical(
        df_heat["weekday"], categories=WEEKDAY_ORDER, ordered=True
    )
    df_heat = df_heat.sort_values(["city_clean", "weekday", "peak_hour"])

    print(f"  {len(df_heat):,} heatmap rows")
    return df_heat


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df = load_source()

    df_biz = build_businesses(df)
    df_biz.to_csv(OUT / "df_businesses.csv", index=False)
    print(f"  Saved df_businesses.csv ({len(df_biz):,} rows)")

    df_cuisine = build_cuisine_stats(df_biz)
    df_cuisine.to_csv(OUT / "df_cuisine_stats.csv", index=False)
    print(f"  Saved df_cuisine_stats.csv ({len(df_cuisine):,} rows)")

    df_heat = build_peak_heatmap(df)
    df_heat.to_csv(OUT / "df_peak_heatmap.csv", index=False)
    print(f"  Saved df_peak_heatmap.csv ({len(df_heat):,} rows)")

    print("\nDone.")


if __name__ == "__main__":
    main()
