# DAX Measures — Steam Store BI Lakehouse

Source of truth for every DAX measure and calculated table in `steam_dashboard.pbix`. The `.pbix` is a binary build artifact and doesn't diff in git — this file does. If a measure changes, update it here too.

## Calculated table — YearTable

```dax
YearTable = 
VAR MinYear = CALCULATE(YEAR(MIN(fact_games[release_date])), ALL(fact_games))
VAR MaxYear = CALCULATE(YEAR(MAX(fact_games[release_date])), ALL(fact_games))
RETURN
SELECTCOLUMNS(
    GENERATESERIES(MinYear, MaxYear, 1),
    "Year", [Value],
    "IsPartialYear", [Value] = MaxYear
)
```

A lightweight year-grain table, not a full daily calendar — every temporal requirement in this project (releases by year, YoY growth) operates at year grain only, so a ~8,150-row daily calendar would support precision nothing here uses. `IsPartialYear` is `TRUE` only for the final year in the range, since the underlying data is confirmed (via SQL `MAX(release_date)`) to end mid-year (2019-05-01), not at year-end. Relationship: `YearTable[Year]` (1) → `fact_games[release_year]` (*), single direction.

## Total Games

```dax
Total Games = COUNTROWS(fact_games)
```

Counts `fact_games`, not `game_genres` — the bridge table fans out (76,462 rows for 27,075 games), so counting it directly would overcount. Correctly cross-filters from a genre slicer because the `fact_games` ↔ `game_genres` relationship is set to bidirectional.

## Average Price (Paid)

```dax
Average Price (Paid) = 
CALCULATE(
    AVERAGE(fact_games[price]),
    fact_games[is_free] = FALSE
)
```

Excludes $0 titles — blending them in would understate what a typical *paid* game costs. Validated against SQL answer key: $6.71.

```dax
Average Price (All) = AVERAGE(fact_games[price])
```

Blended figure, kept as a secondary measure — useful for showing how much free titles pull the average down, not intended as the headline card.

## Positive Review Rate

```dax
Positive Review Rate = 
DIVIDE(
    SUM(fact_games[positive_ratings]),
    SUM(fact_games[total_ratings])
)
```

Ratio of sums, not `AVERAGE()` of the per-game rate column. Averaging the rate directly would weight a 3-review game the same as a 500,000-review game — this is why raw `positive_ratings`/`negative_ratings` are kept as additive columns in Gold rather than only storing the pre-divided rate.

## Free-to-Play Ratio

```dax
Free-to-Play Ratio = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_games), fact_games[is_free] = TRUE),
    COUNTROWS(fact_games)
)
```

Validated: 9.5%.

## Genre Market Share

```dax
Genre Market Share = 
VAR GamesInGenre = COUNTROWS(fact_games)
VAR TotalGamesInContext = CALCULATE(COUNTROWS(fact_games), REMOVEFILTERS(game_genres))
RETURN DIVIDE(GamesInGenre, TotalGamesInContext)
```

Share of whatever's currently filtered — only the genre filter itself is removed — rather than always the full catalog. This makes cross-filtering by year or price tier meaningful (e.g. filtering to 2018 shows each genre's share of 2018's releases specifically). To make this always relative to the full unfiltered catalog instead, swap `REMOVEFILTERS(game_genres)` for `ALL(fact_games)`.

Genres are multi-label (85% of games carry more than one), so shares do not sum to 100% across genres — **never chart this as a pie or donut**; use a bar chart. Validated: Action, no other filters active ≈ 43.96%.

## YoY Release Growth

```dax
YoY Release Growth = 
VAR CurrentYear = SELECTEDVALUE(YearTable[Year])
VAR IsPartial = SELECTEDVALUE(YearTable[IsPartialYear])
VAR CurrentYearGames = COUNTROWS(fact_games)
VAR PriorYearGames = 
    CALCULATE(
        COUNTROWS(fact_games),
        REMOVEFILTERS(YearTable),
        YearTable[Year] = CurrentYear - 1
    )
RETURN
IF(
    ISBLANK(CurrentYear) || IsPartial,
    BLANK(),
    DIVIDE(CurrentYearGames - PriorYearGames, PriorYearGames)
)
```

Returns `BLANK()` for 2019 — the dataset's final year is a partial period (through 2019-05-01, confirmed via SQL), and a growth % comparing 4 months to 12 months isn't a real rate. `DIVIDE`'s blank-safe behavior also handles 1997 (no 1996 to compare against) with no separate guard needed. Validated: 2018 → 28.4%, 2017 → 45.8%, 2019 → blank.

## Supporting measures

```dax
Price Tier Sort = 
SWITCH(
    fact_games[price_tier],
    "Free", 0,
    "Budget ($0.01-$4.99)", 1,
    "Standard ($5-$14.99)", 2,
    "Premium ($15-$29.99)", 3,
    "AAA ($30+)", 4
)
```
Text sorts alphabetically by default (AAA, Budget, Free...) — this column, set via Column tools → Sort by Column, forces the price tier axis into logical price order instead.

```dax
% Windows = DIVIDE(CALCULATE(COUNTROWS(fact_games), fact_games[has_windows] = TRUE), COUNTROWS(fact_games))
% Mac     = DIVIDE(CALCULATE(COUNTROWS(fact_games), fact_games[has_mac]     = TRUE), COUNTROWS(fact_games))
% Linux   = DIVIDE(CALCULATE(COUNTROWS(fact_games), fact_games[has_linux]   = TRUE), COUNTROWS(fact_games))
```
`% Windows` will sit essentially flat near 100% across the whole timeline (only 5 non-Windows games exist in the catalog) — that's correct, not a broken chart. The real signal in "platform evolution" is the Mac/Linux trajectory.