# Nigeria Road Accidents Data Cleaner

A Python script that reads, cleans, and preprocesses two CSV datasets covering
road accidents in Nigerian states from Q4 2020 to Q1 2022, then writes
three cleaned output files.


## Datasets

| File                            | Description                                                                 |
|---------------------------------|-----------------------------------------------------------------------------|
| nigeria_road_accidents.csv      | Per-state quarterly counts: fatalities, injuries, total cases, people involved |
| nigeria_road_accidents_causes.csv | Per-state quarterly counts broken down by 17 accident cause categories     |


## What the script does

### Text columns (state, period)
- Lowercases all values
- Strips punctuation
- Removes common English stopwords
- Tokenizes into a companion `*_tokens` list column

### Numeric columns
- Coerces non-numeric values to 0 via `pd.to_numeric(..., errors="coerce")`
- Clips negative values to 0 and reports any found
- Checks internal consistency: FATAL + SERIOUS + MINOR should equal TOTAL_CASES

### Column names
- Strips leading/trailing whitespace
- Lowercases and replaces spaces with underscores
- Cause abbreviations (SPV, TBT, BFL, ...) are expanded to full descriptive names

### Cause abbreviation reference

| Abbreviation | Full label                    |
|--------------|-------------------------------|
| SPV          | speed_violation               |
| UPD          | unknown_causes                |
| TBT          | tyre_burst                    |
| MDV          | mechanically_defective_vehicle|
| BFL          | brake_failure                 |
| OVL          | overloading                   |
| DOT          | dangerous_overtaking          |
| WOT          | route_obstruction             |
| DGD          | dangerous_driving             |
| BRD          | bad_road                      |
| RTV          | road_traffic_violation        |
| OBS          | obstruction                   |
| SOS          | sign_and_signal_violation     |
| DAD          | driver_alcohol_and_drugs      |
| PWR          | poor_weather                  |
| FTQ          | fatigue                       |
| SLV          | sleeping_while_driving        |

### Output files

| File                    | Contents                                              |
|-------------------------|-------------------------------------------------------|
| cleaned_accidents.csv   | Cleaned accidents summary with token columns added    |
| cleaned_causes.csv      | Cleaned causes with expanded column names + total_causes_recorded |
| cleaned_merged.csv      | Left-join of both on state + period                   |


## Requirements

Python 3.9+ and pandas. No other dependencies.

Install pandas if needed:

```bash
pip install pandas
```


## Running the script

Place the script and both input CSVs in the same directory, then run:

```bash
python clean_nigeria_accidents.py
```

Expected console output:

```
Reading nigeria_road_accidents.csv ...
  Raw shape: (222, 11)
  No missing values found.
  Clean shape: (222, 14)
Reading nigeria_road_accidents_causes.csv ...
  Raw shape: (245, 20)
  Dropping 3 fully-null row(s) (spreadsheet padding).
  Dropping 20 row(s) with null state (embedded legend or padding).
  No missing values found.
  Clean shape: (222, 23)
Merging datasets on state + period ...
  Merged shape: (222, 35)

Saved outputs:
  cleaned_accidents.csv  (222 rows)
  cleaned_causes.csv     (222 rows)
  cleaned_merged.csv     (222 rows)
Done.
```

The three output CSVs are written to the same directory.


## Notes

- The raw causes CSV (245 rows) contains 3 fully-null padding rows and 20 rows
  that form an embedded legend/key table at the bottom of the spreadsheet. The
  script detects and removes both automatically, leaving 222 clean records that
  align exactly with the accidents dataset.
- The `cases_check_ok` column in cleaned_accidents.csv flags any row where
  FATAL + SERIOUS + MINOR does not equal TOTAL_CASES. These rows are kept
  as-is so you can inspect them manually.
- Token columns (state_tokens, period_tokens) contain Python list representations.
  Load them with `ast.literal_eval` if you need actual list objects after reading
  the CSV back into Python.
