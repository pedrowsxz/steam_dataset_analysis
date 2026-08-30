# Data Profiling Report — steam.csv

**Source:** Kaggle — `nikdavis/steam-store-games` (`steam.csv` only; see README for scope rationale)
**Rows / Columns:** 27,075 rows × 18 columns

## 1. Primary Key

`appid` is unique across all 27,075 rows (0 duplicates, 0 full-row duplicates). Confirmed as
the primary key — safe to use as the join key for Bronze → Silver → Gold, and for any future
enrichment with the dataset's other files (`steam_description_data.csv`, etc.), if ever needed.

## 2. Missing Values

| Column    | Nulls | % of rows |
|-----------|-------|-----------|
| developer | 1     | 0.004%    |
| publisher | 14    | 0.05%     |

**Decision:** Negligible volume — not worth dropping rows (the game itself is still valid for
price/genre/platform analysis without a developer/publisher). In Silver, these will be filled
with `"Unknown"` rather than dropped.

## 3. Structural findings — multi-value fields

`platforms`, `categories`, `genres`, and `steamspy_tags` are semicolon-delimited strings, e.g.
`"windows;mac;linux"`. **This is the key modeling decision for the whole project**: these
columns cannot be grouped on directly, or genre/platform counts will be wrong (a game with 3
genres needs to count as 3 rows in a genre breakdown, not be ignored or mis-bucketed into the
first tag). These will be **exploded into bridge tables** in the Silver layer.

*Note: the 3-row sample for `genres` happened to show single values only — don't generalize
from n=3. Run `df['genres'].str.contains(';').sum()` to get the real multi-genre count before
finalizing the Silver explode logic.*

## 4. Numeric distributions — flags for later

- **price**: max $421.99. Plausible for the dataset (it includes some non-typical
  "software"/simulation listings alongside games) but worth a manual spot-check in Silver —
  don't let one outlier skew "Average Price" without knowing what it is.
- **average_playtime / median_playtime**: median is 0 at the 50th percentile, meaning over
  half of all games have no recorded playtime data. This is a known coverage gap in the
  SteamSpy-sourced fields, not a data entry error. **Recommendation:** don't build a headline
  KPI on these fields without footnoting the coverage gap, or exclude them from Page 1/2 KPIs
  entirely.
- **price = 0.0**: represents free-to-play games, not missing data — confirmed distinct from
  the null-price case (there are no null prices). This is what powers the Free-to-Play Ratio
  measure in Phase 4.

## 5. Environment note

Dtypes printed as `str` rather than the classic pandas `object` — this just means the
environment has the newer pandas string dtype backend active; behaves identically to `object`
for everything in this project.