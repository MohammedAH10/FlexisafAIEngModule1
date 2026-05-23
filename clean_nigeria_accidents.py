"""
Nigeria Road Accidents Dataset Cleaner
---------------------------------------
Reads, cleans, and preprocesses both the accidents summary and causes
datasets covering Q4 2020 through Q1 2022 across all Nigerian states.

Text columns are lowercased, punctuation stripped, and stopwords removed.
Numeric columns are validated, missing values reported, and column names
are normalized. The cleaned datasets are written to CSV.
"""

import re
import string
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_ACCIDENTS = "nigeria_road_accidents.csv"
INPUT_CAUSES    = "nigeria_road_accidents_causes.csv"
OUTPUT_ACCIDENTS = "cleaned_accidents.csv"
OUTPUT_CAUSES    = "cleaned_causes.csv"
OUTPUT_MERGED    = "cleaned_merged.csv"

# Cause column abbreviation -> full label mapping
CAUSE_LABELS = {
    "spv": "speed_violation",
    "upd": "unknown_causes",
    "tbt": "tyre_burst",
    "mdv": "mechanically_defective_vehicle",
    "bfl": "brake_failure",
    "ovl": "overloading",
    "dot": "dangerous_overtaking",
    "wot": "route_obstruction",
    "dgd": "dangerous_driving",
    "brd": "bad_road",
    "rtv": "road_traffic_violation",
    "obs": "obstruction",
    "sos": "sign_and_signal_violation",
    "dad":": driver_alcohol_and_drugs",
    "pwr": "poor_weather",
    "ftq": "fatigue",
    "slv": "sleeping_while_driving",
}

# Minimal English stopwords relevant to this dataset's text columns
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "was", "are", "were",
    "be", "been", "has", "have", "had", "this", "that", "it",
}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def normalize_text(value: str) -> str:
    """Lowercase, strip punctuation, remove stopwords, collapse whitespace."""
    if not isinstance(value, str):
        return value
    value = value.lower()
    value = value.translate(str.maketrans("", "", string.punctuation))
    tokens = value.split()
    tokens = [t for t in tokens if t not in STOPWORDS]
    return " ".join(tokens).strip()


def tokenize(value: str) -> list[str]:
    """Return a list of word tokens from a cleaned string."""
    if not isinstance(value, str):
        return []
    return value.split()


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase column names, replace spaces with underscores."""
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df


# ---------------------------------------------------------------------------
# Accidents dataset cleaner
# ---------------------------------------------------------------------------

def clean_accidents(path: str) -> pd.DataFrame:
    print(f"Reading {path} ...")
    df = pd.read_csv(path)
    print(f"  Raw shape: {df.shape}")

    # Normalize column names
    df = normalize_columns(df)

    # Report and drop full duplicates
    n_dupes = df.duplicated().sum()
    if n_dupes:
        print(f"  Dropping {n_dupes} duplicate row(s).")
        df = df.drop_duplicates()

    # Report missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print("  Missing values per column:")
        for col, cnt in missing.items():
            print(f"    {col}: {cnt}")
    else:
        print("  No missing values found.")

    # Clean text columns: state and period
    for col in ["state", "period"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)
            df[col + "_tokens"] = df[col].apply(tokenize)

    # Ensure all numeric columns are non-negative integers
    numeric_cols = [
        "fatal", "serious", "minor", "total_cases",
        "number_injured", "number_killed", "total_casualty", "people_involved",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            neg_count = (df[col] < 0).sum()
            if neg_count:
                print(f"  Warning: {neg_count} negative value(s) in '{col}' — setting to 0.")
                df[col] = df[col].clip(lower=0)

    # Derived sanity check: total_cases should equal fatal + serious + minor
    if all(c in df.columns for c in ["fatal", "serious", "minor", "total_cases"]):
        df["cases_check_ok"] = (
            df["fatal"] + df["serious"] + df["minor"] == df["total_cases"]
        )
        mismatch = (~df["cases_check_ok"]).sum()
        if mismatch:
            print(f"  Note: {mismatch} row(s) where FATAL+SERIOUS+MINOR != TOTAL_CASES.")

    print(f"  Clean shape: {df.shape}")
    return df


# ---------------------------------------------------------------------------
# Causes dataset cleaner
# ---------------------------------------------------------------------------

def clean_causes(path: str) -> pd.DataFrame:
    print(f"Reading {path} ...")
    df = pd.read_csv(path)
    print(f"  Raw shape: {df.shape}")

    df = normalize_columns(df)

    # Drop rows where every column is null (common spreadsheet padding artifact)
    fully_null = df.isnull().all(axis=1).sum()
    if fully_null:
        print(f"  Dropping {fully_null} fully-null row(s) (spreadsheet padding).")
        df = df.dropna(how="all")

    # Drop rows where the key identifier columns are null
    # (the causes CSV contains an embedded legend table at the bottom)
    if "state" in df.columns:
        legend_rows = df["state"].isnull().sum()
        if legend_rows:
            print(f"  Dropping {legend_rows} row(s) with null state (embedded legend or padding).")
            df = df[df["state"].notna()]

    n_dupes = df.duplicated().sum()
    if n_dupes:
        print(f"  Dropping {n_dupes} duplicate row(s).")
        df = df.drop_duplicates()

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print("  Missing values per column:")
        for col, cnt in missing.items():
            print(f"    {col}: {cnt}")
    else:
        print("  No missing values found.")

    # Clean text columns
    for col in ["state", "period"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)
            df[col + "_tokens"] = df[col].apply(tokenize)

    # Rename cause abbreviation columns to full descriptive names
    rename_map = {k: v for k, v in CAUSE_LABELS.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Ensure cause counts are non-negative integers
    cause_cols = list(rename_map.values())
    for col in cause_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
            df[col] = df[col].clip(lower=0)

    # Add a total_causes column summing all cause counts
    present_causes = [c for c in cause_cols if c in df.columns]
    df["total_causes_recorded"] = df[present_causes].sum(axis=1)

    print(f"  Clean shape: {df.shape}")
    return df


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def merge_datasets(df_acc: pd.DataFrame, df_cau: pd.DataFrame) -> pd.DataFrame:
    """Left-join accidents onto causes on state + period."""
    print("Merging datasets on state + period ...")
    merged = pd.merge(
        df_acc,
        df_cau,
        on=["state", "period"],
        how="left",
        suffixes=("_acc", "_cau"),
    )
    print(f"  Merged shape: {merged.shape}")
    return merged


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    base = Path(__file__).parent

    df_accidents = clean_accidents(base / INPUT_ACCIDENTS)
    df_causes    = clean_causes(base / INPUT_CAUSES)
    df_merged    = merge_datasets(df_accidents, df_causes)

    # Save outputs
    df_accidents.to_csv(base / OUTPUT_ACCIDENTS, index=False)
    df_causes.to_csv(base / OUTPUT_CAUSES, index=False)
    df_merged.to_csv(base / OUTPUT_MERGED, index=False)

    print()
    print("Saved outputs:")
    print(f"  {OUTPUT_ACCIDENTS}  ({len(df_accidents)} rows)")
    print(f"  {OUTPUT_CAUSES}     ({len(df_causes)} rows)")
    print(f"  {OUTPUT_MERGED}     ({len(df_merged)} rows)")
    print("Done.")


if __name__ == "__main__":
    main()
